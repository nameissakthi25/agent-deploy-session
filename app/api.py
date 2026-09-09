"""FastAPI: one /chat endpoint and one /health endpoint.

One image serves all three stages. STAGE decides which graph gets built at
startup -- there are no branches or tags for the three stages, and the only
difference between what runs on 8101, 8102 and 8103 is that variable.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from opentelemetry.trace import Status, StatusCode

from app import graph_stage1, graph_stage2, graph_stage3
from app.config import (
    APP_PORT,
    MODEL_NAME,
    PHOENIX_BASE_URL,
    STAGE,
    VLLM_BASE_URL,
)
from app.feedback import THUMBS_DOWN, THUMBS_UP, annotate_trace
from app.guards.input_guard import InputRejected, check_input
from app.guards.output_guard import OutputRejected, check_output
from app.llm import assert_model_server_reachable, make_client
from app.observability import current_trace_id, setup_tracing
from app.schemas import ChatRequest, ChatResponse, FeedbackRequest

# Must run before the OpenAI client is built, so the instrumentation is in
# place by the time the client is created.
_tracer = setup_tracing()

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


def record_rejection(span, guard: str, reason: str) -> None:
    """Put a guardrail rejection in the trace, with the reason readable.

    The guards themselves stay pure functions with no tracing in them -- they
    raise, and the span is recorded here, in one visible place. That is what
    lets the fast tests exercise them without any OpenTelemetry setup.
    """
    span.set_attribute("guardrail.rejected_by", guard)
    span.set_attribute("guardrail.reason", reason)
    span.set_status(Status(StatusCode.ERROR, f"{guard}: {reason}"))


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
            message = check_input(request.message)
        except InputRejected as error:
            record_rejection(span, "input_guard", error.reason)
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
            response = check_output(_client, answer, STAGE, trace_id, message)
            span.set_attribute("output.value", response.answer)
            return response
        except OutputRejected as error:
            record_rejection(span, "output_guard", error.reason)
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
