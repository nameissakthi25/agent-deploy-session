"""Stage 3: a supervisor routing to three workers.

    START -> supervisor -> retriever   -> synthesizer -> END
                        -> tool_agent  -> synthesizer
                        -> synthesizer

Each node opens one span, so the picture on the slide and the picture in
Phoenix are the same picture, and every model call sits inside the node that
made it.

That one span per node is hand-written, which build-spec.md section 8 says to
avoid. It is here because the LangChain instrumentation alone does not give
the nesting the Stage 3 acceptance criteria require: it names the nodes, but
LangGraph runs them in its own execution context, so the model calls attach to
the request root instead of to their node. The result is a trace where you
cannot tell which node made which call -- which is exactly what 0:58 needs to
read. One obvious span per node fixes it and costs four lines.

The supervisor routes by emitting a tool call. That is deliberate: it makes
routing testable. Hand it a stubbed client that returns a fixed tool call and
you can assert which worker gets picked, with no model and no GPU. See
tests/test_routing.py.
"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from openai import OpenAI
from opentelemetry import trace

from app.agents import synthesizer, tool_agent
from app.agents.retriever import search
from app.llm import chat

Route = Literal["retriever", "tool_agent", "synthesizer"]

_tracer = trace.get_tracer(__name__)


class State(TypedDict, total=False):
    """What flows between the nodes."""

    message: str
    route: Route
    documents: list[dict]
    tool_results: list[dict]
    answer: str


SUPERVISOR_PROMPT = (
    "You are the supervisor of an IT support system. Choose exactly one "
    "worker for this question by calling exactly one tool. Do not answer the "
    "question yourself."
)

# Routing choices, expressed as tools so the decision is a tool call we can
# stub in a test. These are not the tools the workers call.
ROUTING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "route_to_retriever",
            "description": (
                "Send to the knowledge base worker. Use for how-to questions, "
                "policy questions, and 'why does X happen' questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "route_to_tool_agent",
            "description": (
                "Send to the systems worker. Use when the question names a "
                "ticket ID, or asks whether a named service is up or down."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "route_to_synthesizer",
            "description": (
                "Answer directly with no lookup. Use only for greetings and "
                "questions about what this assistant can do."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]

ROUTE_BY_TOOL: dict[str, Route] = {
    "route_to_retriever": "retriever",
    "route_to_tool_agent": "tool_agent",
    "route_to_synthesizer": "synthesizer",
}

# Where an unroutable question goes. With tool_choice="required" the
# supervisor always picks something, so this is a genuine safety net that
# should not fire. The retriever is the safe choice for it: it grounds the
# answer in a document rather than letting the model improvise.
DEFAULT_ROUTE: Route = "retriever"


def build_graph(client: OpenAI):
    """Compile the graph. The client is injected, which is what makes it testable."""

    def supervisor_node(state: State) -> State:
        with _tracer.start_as_current_span("supervisor") as span:
            span.set_attribute("openinference.span.kind", "CHAIN")
            response = chat(
                client,
                messages=[
                    {"role": "system", "content": SUPERVISOR_PROMPT},
                    {"role": "user", "content": state["message"]},
                ],
                tools=ROUTING_TOOLS,
                # The supervisor must route, not chat. Left on "auto", a
                # conversational closer produced no tool call at all and fell
                # through to DEFAULT_ROUTE -- see scripts/routing_check.py, which
                # measured that at 0/3 before this changed to "required".
                tool_choice="required",
                # Thinking OFF. A supervisor that reasons at length before every
                # routing decision makes every trace unreadable and every response
                # slow -- and Qwen3.8 thinks by default, so this must be explicit.
                thinking=False,
                max_tokens=128,
            )
            calls = response.choices[0].message.tool_calls or []
            route = (
                ROUTE_BY_TOOL.get(calls[0].function.name, DEFAULT_ROUTE)
                if calls
                else DEFAULT_ROUTE
            )
            # The routing decision, readable without expanding the span.
            span.set_attribute("route", route)
            span.set_attribute(
                "routed_by", calls[0].function.name if calls else "default"
            )
            return {"route": route}

    def retriever_node(state: State) -> State:
        with _tracer.start_as_current_span("retriever") as span:
            span.set_attribute("openinference.span.kind", "AGENT")
            return {"documents": search(state["message"])}

    def tool_agent_node(state: State) -> State:
        with _tracer.start_as_current_span("tool_agent") as span:
            span.set_attribute("openinference.span.kind", "AGENT")
            results = tool_agent.run(client, state["message"])
            span.set_attribute("tool_calls", len(results))
            span.set_attribute(
                "tool_calls_rejected", sum(1 for r in results if "rejected" in r)
            )
            return {"tool_results": results}

    def synthesizer_node(state: State) -> State:
        with _tracer.start_as_current_span("synthesizer") as span:
            span.set_attribute("openinference.span.kind", "AGENT")
            return {
                "answer": synthesizer.run(
                    client,
                    state["message"],
                    state.get("documents", []),
                    state.get("tool_results", []),
                )
            }

    def pick_worker(state: State) -> Route:
        return state.get("route", DEFAULT_ROUTE)

    graph = StateGraph(State)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("tool_agent", tool_agent_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        pick_worker,
        {
            "retriever": "retriever",
            "tool_agent": "tool_agent",
            "synthesizer": "synthesizer",
        },
    )
    graph.add_edge("retriever", "synthesizer")
    graph.add_edge("tool_agent", "synthesizer")
    graph.add_edge("synthesizer", END)
    return graph.compile()


def run(client: OpenAI, message: str) -> str:
    """Answer one message by routing it through the graph."""
    final = build_graph(client).invoke({"message": message})
    answer = final.get("answer")
    if not answer:
        raise RuntimeError("The graph produced no answer.")
    return answer
