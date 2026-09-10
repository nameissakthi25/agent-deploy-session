"""FastAPI: one /chat endpoint and one /health endpoint.

One image serves all three stages. STAGE decides which graph gets built at
startup -- there are no branches or tags for the three stages, and the only
difference between what runs on 8101, 8102 and 8103 is that variable.
"""

from contextlib import asynccontextmanager, contextmanager

from fastapi import FastAPI, HTTPException
from opentelemetry.trace import Status, StatusCode

from app import graph_stage1, graph_stage2, graph_stage3
from app.config import (
    APP_PORT,
    GUARD_BACKEND,
    MODEL_NAME,
    PHOENIX_BASE_URL,
    STAGE,
    VLLM_BASE_URL,
)
from app.feedback import THUMBS_DOWN, THUMBS_UP, annotate_trace
from app.guards.input_guard import InputRejected
from app.guards.input_guard import check_input as check_input_hand
from app.guards.output_guard import OutputRejected, check_output
from app.llm import assert_model_server_reachable, make_client
from app.observability import current_trace_id, setup_tracing
from app.schemas import ChatRequest, ChatResponse, FeedbackRequest

# Must run before the OpenAI client is built, so the instrumentation is in
# place by the time the client is created.
_tracer = setup_tracing()


def _select_input_guard():
    """Pick the input guard. Imported lazily -- Guardrails AI is heavy, and a
    container running the default should not pay to import it."""
    if GUARD_BACKEND == "framework":
        from app.guards.framework_guard import BACKEND, check_input

        print(f"input guard: {BACKEND}")
        return check_input
    print("input guard: hand-written")
    return check_input_hand


check_input = _select_input_guard()

# Built once at startup, so an unsupported STAGE fails immediately rather than
# on the first request.
_client = make_client()


def build_graph(stage: int):
    """Return the function that answers one message, for this stage."""
    if stage == 1:
        return graph_stage1.run
    if stage == 2:
        return graph_stage2.run
    if stage == 3:
        return graph_stage3.run
    raise NotImplementedError(f"STAGE={stage} has no graph.")


_graph = build_graph(STAGE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Check the model server before accepting any traffic."""
    assert_model_server_reachable()
    print(f"stage={STAGE} port={APP_PORT} model={MODEL_NAME} at {VLLM_BASE_URL}")
    yield


app = FastAPI(title=f"IT support assistant - stage {STAGE}", lifespan=lifespan)


@contextmanager
def guard_span(name: str):
    """Run one guardrail inside its own span, pass or fail.

    Every invocation gets a span, not just the refusals. Before this, a
    request that passed all three guards produced a trace with no evidence
    the guards existed -- which made "guardrails are part of the recorded
    history" true only when something went wrong.

    The durations are the point. input_guard is regex and lands in
    microseconds; output_guard spends a whole model call and lands in the
    hundreds of milliseconds. Those two numbers side by side are the argument
    for doing cheap checks first, and a span is the only one of the available
    options that carries a duration.

    The guards themselves stay pure functions with no tracing in them. They
    raise; this records. That is what lets the fast tests exercise them with
    no OpenTelemetry setup at all.
    """
    with _tracer.start_as_current_span(name) as span:
        span.set_attribute("guardrail.name", name)
        try:
            yield span
        except (InputRejected, OutputRejected) as error:
            span.set_attribute("guardrail.passed", False)
            span.set_attribute("guardrail.reason", error.reason)
            span.set_status(Status(StatusCode.ERROR, f"{name}: {error.reason}"))
            raise
        span.set_attribute("guardrail.passed", True)


@app.get("/health")
def health() -> dict:
    """Liveness only. Does not call the model, so it stays fast and cheap."""
    return {"status": "ok", "stage": STAGE, "model": MODEL_NAME}


@app.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest) -> ChatResponse:
    """Answer one message.

    One explicit span wraps the request. It is the only hand-written span on
    this path -- the model call inside it is traced by the instrumentation --
    and it exists to give the response a trace ID to hand back.

    The guards wrap this at step 5.
    """
    with _tracer.start_as_current_span("chat") as span:
        span.set_attribute("stage", STAGE)
        # The question and answer on the root span. Two reasons: Phoenix's
        # trace list becomes readable at a glance, and evals/dataset.py can
        # recover the question from a thumbs-downed trace without digging
        # into the nested model-call spans.
        span.set_attribute("input.value", request.message)
        trace_id = current_trace_id()

        # Guard 1: before anything reaches the model.
        try:
            with guard_span("input_guard"):
                message = check_input(request.message)
        except InputRejected as error:
            raise HTTPException(status_code=400, detail=error.reason) from error

        span.set_attribute("session_id", request.session_id)
        try:
            # Only Stage 1 takes a session: it is the stage whose whole lesson
            # is that in-process conversation state is the wrong place for it.
            if STAGE == 1:
                answer = _graph(_client, message, request.session_id)
            else:
                answer = _graph(_client, message)
        except RuntimeError as error:
            # A model-layer failure. 502 rather than 500: the fault is upstream.
            raise HTTPException(status_code=502, detail=str(error)) from error

        # Guard 3: before anything reaches the user. Guard 2 is the tool guard,
        # which runs inside the Stage 3 graph rather than here.
        try:
            with guard_span("output_guard"):
                response = check_output(_client, answer, STAGE, trace_id, message)
            span.set_attribute("output.value", response.answer)
            return response
        except OutputRejected as error:
            raise HTTPException(status_code=422, detail=error.reason) from error


@app.post("/feedback", status_code=204)
def post_feedback(request: FeedbackRequest) -> None:
    """Attach a thumbs up or down to an earlier response's trace.

    Written here rather than in the UI so the annotation write happens inside
    a traced process and gets its own span -- and so the UI needs to know
    nothing about Phoenix beyond a trace ID it was already given.
    """
    label, score = THUMBS_UP if request.helpful else THUMBS_DOWN
    try:
        annotate_trace(PHOENIX_BASE_URL, request.trace_id, label, score, STAGE)
    except Exception as error:
        raise HTTPException(
            status_code=502, detail=f"Could not write the annotation: {error}"
        ) from error
