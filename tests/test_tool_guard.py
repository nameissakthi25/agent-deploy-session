"""Table-driven tests for the tool guard.

This is the guard the session cares most about, so the table is the
documentation: read it and you know the whole policy.
"""

import pytest

from app.guards.tool_guard import TOOL_ALLOWLIST, ToolCallRejected, check_tool_call

# (agent, tool, arguments, phrase expected in the reason). None means allowed.
CASES = [
    ("tool_agent", "lookup_ticket", {"ticket_id": "INC-ALP-0001"}, None),
    ("tool_agent", "check_service_status", {"service_name": "vpn"}, None),
    ("retriever", "search_kb", {"query": "password reset policy"}, None),
    # On nobody's allowlist.
    ("tool_agent", "delete_everything", {}, "not on this agent's allowlist"),
    # Real tool, wrong agent -- the multi-agent surface the guard exists for.
    ("retriever", "lookup_ticket", {"ticket_id": "INC-ALP-0001"}, "allowlist"),
    # The synthesizer may never call anything.
    ("synthesizer", "search_kb", {"query": "anything"}, "no tools at all"),
    # Unknown caller.
    ("rogue_agent", "search_kb", {"query": "hello"}, "unknown agent"),
    # Malformed arguments: the failure demonstrated live at 0:58.
    ("tool_agent", "lookup_ticket", {"ticket_id": "DROP TABLE tickets"}, "invalid"),
    ("tool_agent", "lookup_ticket", {"ticket_id": "IT-1041"}, "invalid"),
    ("tool_agent", "check_service_status", {"service_name": "email"}, "invalid"),
    # Missing and extra arguments.
    ("tool_agent", "lookup_ticket", {}, "invalid"),
    ("retriever", "search_kb", {"query": "ok", "limit": 5}, "invalid"),
]


@pytest.mark.parametrize("agent,tool,arguments,expected", CASES)
def test_tool_guard(agent, tool, arguments, expected) -> None:
    if expected is None:
        assert check_tool_call(agent, tool, arguments)
        return
    with pytest.raises(ToolCallRejected) as caught:
        check_tool_call(agent, tool, arguments)
    assert expected in caught.value.reason
    # The exception carries who tried what, so the span can say so.
    assert caught.value.agent == agent
    assert caught.value.tool == tool


def test_allowlist_only_references_real_tools() -> None:
    """A typo in the allowlist would silently deny a legitimate call."""
    from app.tools.definitions import TOOL_NAMES

    for agent, tools in TOOL_ALLOWLIST.items():
        for tool in tools:
            assert tool in TOOL_NAMES, f"{agent} allows unknown tool {tool!r}"


def test_guard_returns_normalised_arguments() -> None:
    """The guard hands back what the schema validated, not the raw input."""
    result = check_tool_call("tool_agent", "lookup_ticket", {"ticket_id": "inc-alp-0001"})
    assert result["ticket_id"] == "INC-ALP-0001"


def test_malformed_argument_does_not_crash_the_tool_agent() -> None:
    """The acceptance criterion at 0:58: a bad argument is refused, not fatal.

    The run continues and the synthesizer is told the call was refused, which
    is what makes the live "break it deliberately" demo safe.
    """
    from app.agents import tool_agent
    from tests.conftest import StubClient, stub_tool_call

    client = StubClient(
        tool_calls=[stub_tool_call("lookup_ticket", '{"ticket_id": "nonsense"}')]
    )
    results = tool_agent.run(client, "look up ticket nonsense")

    assert len(results) == 1
    assert results[0]["tool"] == "lookup_ticket"
    assert "rejected" in results[0]
    assert "invalid" in results[0]["rejected"]
    assert "result" not in results[0]


def test_tool_agent_is_only_offered_its_own_tools() -> None:
    """search_kb belongs to the retriever, so it is never even offered here."""
    from app.agents.tool_agent import AGENT_NAME, OFFERED
    from app.guards.tool_guard import TOOL_ALLOWLIST

    offered = {t["function"]["name"] for t in OFFERED}
    assert offered == set(TOOL_ALLOWLIST[AGENT_NAME])
    assert "search_kb" not in offered
