"""Phoenix tracing. Register, auto-instrument, done.

Deliberately tiny. The OpenInference instrumentation already traces every
model call and the graph structure, so there is no custom span code for those
-- writing any would just duplicate what the instrumentation does, and hide
the lesson that this is standard OpenTelemetry.

The explicit spans in this repo are only for the things instrumentation cannot
see: the three guardrail rejections (step 5) and the thumbs annotation write
(step 8). Both use the tracer exported here.

Because vLLM speaks the OpenAI protocol, this traces a self-hosted model
exactly as it would a hosted one.
"""

from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace
from phoenix.otel import register

from app.config import PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_PROJECT_NAME


def setup_tracing() -> trace.Tracer:
    """Point OpenTelemetry at Phoenix and instrument the OpenAI client."""
    register(
        endpoint=PHOENIX_COLLECTOR_ENDPOINT,
        project_name=PHOENIX_PROJECT_NAME,
        # Discovers and instruments every openinference package that happens
        # to be installed. That is convenient and slightly dangerous: adding a
        # dependency can silently change the shape of your traces. Stage 3
        # deliberately does NOT install
        # openinference-instrumentation-langchain, because it produces a
        # second set of node spans that duplicate the ones graph_stage3.py
        # opens, without nesting the model calls inside them.
        auto_instrument=True,
        # batch=False so a span appears in the UI immediately. Wrong for
        # production, right for a demo where we refresh Phoenix on stage.
        batch=False,
        set_global_tracer_provider=True,
    )
    OpenAIInstrumentor().instrument()
    return trace.get_tracer(__name__)


def current_trace_id() -> str | None:
    """The active trace as 32 hex characters, or None outside a span.

    Returned with every /chat response so the UI can attach a thumbs up or
    down to this exact request, and so the ID can be pasted into Phoenix's
    search box by hand during the session.
    """
    context = trace.get_current_span().get_span_context()
    if not context.trace_id:
        return None
    return format(context.trace_id, "032x")
