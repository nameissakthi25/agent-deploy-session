"""The tool-calling worker.

Asks the model which tool to use, then runs it -- but every call passes
through tool_guard first. That is the whole point of this file: the arguments
arriving here were written by a model, not a person, and nobody reviewed them.
"""

import json
from contextlib import contextmanager

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from app.guards.tool_guard import ToolCallRejected, check_tool_call
from app.llm import chat
from app.tools.definitions import TOOLS
from app.tools.handlers import HANDLERS

AGENT_NAME = "tool_agent"

_tracer = trace.get_tracer(__name__)


@contextmanager
def tool_guard_span(agent: str, tool: str):
    """One span per tool call the guard inspects, allowed or refused.

    Every call gets a span, not only the refusals -- otherwise a Stage 3 trace
    where everything worked shows no sign the allowlist was ever consulted.
    A refused call is marked ERROR and carries the reason, so it stands out in
    the tree and can be clicked into rather than grepped for.
    """
    with _tracer.start_as_current_span("tool_guard") as span:
        span.set_attribute("guardrail.name", "tool_guard")
        span.set_attribute("guardrail.agent", agent)
        span.set_attribute("guardrail.tool", tool)
        try:
            yield span
        except ToolCallRejected as error:
            span.set_attribute("guardrail.passed", False)
            span.set_attribute("guardrail.reason", error.reason)
            span.set_status(Status(StatusCode.ERROR, f"tool_guard: {error.reason}"))
            raise
        span.set_attribute("guardrail.passed", True)


def record_json_failure(agent: str, tool: str, reason: str) -> None:
    """Arguments that were not even JSON never reach the guard."""
    with _tracer.start_as_current_span("tool_guard") as span:
        span.set_attribute("guardrail.name", "tool_guard")
        span.set_attribute("guardrail.agent", agent)
        span.set_attribute("guardrail.tool", tool)
        span.set_attribute("guardrail.passed", False)
        span.set_attribute("guardrail.reason", reason)
        span.set_status(Status(StatusCode.ERROR, f"tool_guard: {reason}"))


SYSTEM_PROMPT = (
    "You are the tools worker of an IT support system. Call exactly one tool "
    "to answer the question. Do not answer from memory."
)

# Only the tools this agent is allowed to call are even offered to it. The
# guard still checks -- offering a tool and permitting it are different
# things, and the guard is what makes that true rather than hoped for.
OFFERED = [
    t for t in TOOLS if t["function"]["name"] in {"lookup_ticket", "check_service_status"}
]


def run(client: OpenAI, message: str) -> list[dict]:
    """Return a list of {tool, arguments, result} or {tool, rejected}."""
    response = chat(
        client,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        tools=OFFERED,
        thinking=False,
    )

    calls = response.choices[0].message.tool_calls or []
    if not calls:
        return []

    results = []
    for call in calls:
        name = call.function.name
        try:
            raw = json.loads(call.function.arguments)
        except json.JSONDecodeError as error:
            reason = f"arguments were not JSON: {error}"
            record_json_failure(AGENT_NAME, name, reason)
            results.append({"tool": name, "rejected": reason})
            continue

        try:
            with tool_guard_span(AGENT_NAME, name):
                arguments = check_tool_call(AGENT_NAME, name, raw)
        except ToolCallRejected as error:
            # The run continues. A rejected tool call is not a crash -- the
            # synthesizer is told the call was refused and answers accordingly.
            results.append({"tool": name, "rejected": error.reason})
            continue

        results.append(
            {"tool": name, "arguments": arguments, "result": HANDLERS[name](**arguments)}
        )
    return results
