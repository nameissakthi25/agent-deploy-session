"""Routing tests: which worker does the supervisor pick?

No model call, no GPU. The graph takes an injected client, so a stub that
returns a fixed tool call is enough to assert the routing decision. This is
the answer to "agent systems can't be tested" -- the routing part absolutely
can, because the decision is a tool call and a tool call is checkable.
"""

import pytest

from app.graph_stage3 import DEFAULT_ROUTE, ROUTE_BY_TOOL, build_graph
from tests.conftest import StubClient, stub_tool_call

# (the tool the supervisor emits, the worker that should run)
ROUTING_CASES = [
    ("route_to_retriever", "retriever"),
    ("route_to_tool_agent", "tool_agent"),
    ("route_to_synthesizer", "synthesizer"),
]


def supervisor_only(client: StubClient, message: str) -> str:
    """Run just the supervisor node and return the route it chose."""
    graph = build_graph(client)
    # Interrupting after the supervisor keeps the assertion about routing
    # rather than about whatever the workers then did.
    state = graph.invoke({"message": message}, interrupt_after=["supervisor"])
    return state["route"]


@pytest.mark.parametrize("tool_name,expected_worker", ROUTING_CASES)
def test_supervisor_routes_to_expected_worker(tool_name, expected_worker) -> None:
    client = StubClient(tool_calls=[stub_tool_call(tool_name)])
    assert supervisor_only(client, "any question at all") == expected_worker


def test_no_tool_call_falls_back_to_the_default_route() -> None:
    """A supervisor that answers in prose instead of routing must not crash."""
    client = StubClient(replies=["I think you should try turning it off"])
    assert supervisor_only(client, "vague question") == DEFAULT_ROUTE


def test_unknown_routing_tool_falls_back_to_the_default_route() -> None:
    """A hallucinated route name must not take the graph down."""
    client = StubClient(tool_calls=[stub_tool_call("route_to_the_moon")])
    assert supervisor_only(client, "question") == DEFAULT_ROUTE


def test_supervisor_runs_with_thinking_off() -> None:
    """The supervisor must not reason at length before routing."""
    client = StubClient(tool_calls=[stub_tool_call("route_to_retriever")])
    supervisor_only(client, "question")
    kwargs = client.requests[0]["extra_body"]["chat_template_kwargs"]
    assert kwargs["enable_thinking"] is False
    assert "reasoning_effort" not in client.requests[0]


def test_every_routing_tool_maps_to_a_real_node() -> None:
    """A typo in ROUTE_BY_TOOL would silently send work to the default."""
    from app.graph_stage3 import ROUTING_TOOLS

    offered = {t["function"]["name"] for t in ROUTING_TOOLS}
    assert offered == set(ROUTE_BY_TOOL)
    assert set(ROUTE_BY_TOOL.values()) == {"retriever", "tool_agent", "synthesizer"}
