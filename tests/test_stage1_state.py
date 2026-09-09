"""Stage 1 keeps conversation history in a variable, on purpose.

These tests pin the behaviour the 0:18 demo depends on: history accumulates
per session, sessions do not leak into each other, and losing the process
loses the conversation.
"""

from app import graph_stage1
from tests.conftest import StubClient


def setup_function() -> None:
    """Each test starts from an empty process, like a fresh container."""
    graph_stage1.CONVERSATIONS.clear()


def test_history_is_sent_back_to_the_model() -> None:
    client = StubClient(replies=["first answer", "second answer"])
    graph_stage1.run(client, "remember the number 42", "room")
    graph_stage1.run(client, "what number?", "room")

    # The second request must carry the first exchange.
    second = client.requests[1]["messages"]
    contents = [m["content"] for m in second]
    assert "remember the number 42" in contents
    assert "first answer" in contents
    assert contents[-1] == "what number?"


def test_sessions_do_not_leak_into_each_other() -> None:
    client = StubClient(replies=["a", "b"])
    graph_stage1.run(client, "my number is 42", "room-a")
    graph_stage1.run(client, "what is my number?", "room-b")

    second = [m["content"] for m in client.requests[1]["messages"]]
    assert "my number is 42" not in second


def test_losing_the_process_loses_the_conversation() -> None:
    """The 0:18 demo: restarting the container empties this dictionary."""
    client = StubClient(replies=["a", "b"])
    graph_stage1.run(client, "remember 42", "room")
    assert graph_stage1.CONVERSATIONS["room"]

    # A restart is exactly this: the module is imported fresh, empty.
    graph_stage1.CONVERSATIONS.clear()

    graph_stage1.run(client, "what number?", "room")
    second = [m["content"] for m in client.requests[1]["messages"]]
    assert "remember 42" not in second


def test_history_is_capped() -> None:
    """The history goes into the prompt, so it cannot grow without limit."""
    client = StubClient(replies=[f"answer {n}" for n in range(20)])
    for n in range(12):
        graph_stage1.run(client, f"turn {n}", "room")

    last = client.requests[-1]["messages"]
    # system prompt + at most MAX_HISTORY_TURNS exchanges + this turn
    assert len(last) <= 1 + graph_stage1.MAX_HISTORY_TURNS * 2 + 1
