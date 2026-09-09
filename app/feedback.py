"""Writing thumbs up/down back onto a trace in Phoenix.

This is the first half of the feedback loop: a thumbs-down in the interface
attaches itself to that request's trace, so the unhappy requests can be
filtered out later and turned into an eval dataset. The second half is
evals/dataset.py.

Phoenix annotates by trace ID, which is exactly what /chat already returns --
so the UI never has to know anything about spans.
"""

import httpx
from opentelemetry import trace

# One annotation name, so every thumb lands in the same place and can be
# filtered on. Changing it orphans everything already collected.
ANNOTATION_NAME = "user_feedback"

THUMBS_UP = ("thumbs_up", 1.0)
THUMBS_DOWN = ("thumbs_down", 0.0)

_tracer = trace.get_tracer(__name__)


def annotate_trace(
    phoenix_base_url: str,
    trace_id: str,
    label: str,
    score: float,
    stage: int,
) -> None:
    """Write one annotation onto one trace. Raises on failure.

    sync=true so the call does not return until Phoenix has stored it -- the
    session refreshes the Phoenix UI immediately after clicking, and an
    annotation that is still queued looks like a broken feature.
    """
    with _tracer.start_as_current_span("write_feedback") as span:
        span.set_attribute("feedback.trace_id", trace_id)
        span.set_attribute("feedback.label", label)
        span.set_attribute("feedback.stage", stage)

        response = httpx.post(
            f"{phoenix_base_url.rstrip('/')}/v1/trace_annotations",
            params={"sync": "true"},
            json={
                "data": [
                    {
                        "trace_id": trace_id,
                        "name": ANNOTATION_NAME,
                        "annotator_kind": "HUMAN",
                        "result": {"label": label, "score": score},
                        "metadata": {"stage": stage},
                    }
                ]
            },
            timeout=20.0,
        )
        response.raise_for_status()
