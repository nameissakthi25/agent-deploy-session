"""The second guard: runs before every single tool call.

This is the most important guard in the session, and the one almost nobody
has. In a single-agent system the model calls tools you chose and configured.
In a multi-agent system, one agent's output becomes another agent's tool
input -- nobody wrote that input and nobody reviewed it. That surface does not
exist in simpler systems.

Two checks, both boring on purpose:

  1. Is this tool on this agent's allowlist?
  2. Do these arguments validate against the tool's schema?

The schema is the same ARG_MODELS the model was shown in its tools parameter,
so what we advertise and what we validate cannot drift apart.
"""

from pydantic import ValidationError

from app.tools.definitions import ARG_MODELS


class ToolCallRejected(Exception):
    """Raised when an agent tried to call a tool it should not have."""

    def __init__(self, agent: str, tool: str, reason: str) -> None:
        super().__init__(f"{agent} -> {tool}: {reason}")
        self.agent = agent
        self.tool = tool
        self.reason = reason


# A plain dictionary, not a policy engine. Agent name to the tools that agent
# is allowed to call. The synthesizer appears with an empty list on purpose:
# it writes the final answer and must never reach for a tool.
TOOL_ALLOWLIST: dict[str, list[str]] = {
    "retriever": ["search_kb"],
    "tool_agent": ["lookup_ticket", "check_service_status"],
    "synthesizer": [],
}


def check_tool_call(agent: str, tool: str, arguments: dict) -> dict:
    """Return validated arguments, or raise ToolCallRejected saying why."""
    if agent not in TOOL_ALLOWLIST:
        raise ToolCallRejected(
            agent, tool, f"unknown agent. Known agents: {', '.join(TOOL_ALLOWLIST)}"
        )

    allowed = TOOL_ALLOWLIST[agent]
    if tool not in allowed:
        allowed_text = ", ".join(allowed) if allowed else "no tools at all"
        raise ToolCallRejected(
            agent, tool, f"not on this agent's allowlist, which permits {allowed_text}"
        )

    if tool not in ARG_MODELS:
        raise ToolCallRejected(agent, tool, "no argument schema exists for this tool")

    try:
        validated = ARG_MODELS[tool](**arguments)
    except ValidationError as error:
        first = error.errors()[0]
        field = ".".join(str(part) for part in first["loc"]) or "arguments"
        raise ToolCallRejected(
            agent, tool, f"argument {field} is invalid: {first['msg']}"
        ) from error

    return validated.model_dump()
