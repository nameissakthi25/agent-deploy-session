"""Shared fixtures for the fast suite.

The whole point of this suite is that it needs no model. StubClient stands in
for the OpenAI client: it returns whatever it was told to, and records what it
was asked. That is what lets the routing tests assert which worker the
supervisor picked without a GPU anywhere in sight.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# app/config.py validates the environment at import time and exits if
# anything is missing -- that is deliberate, so a misconfigured container
# crashes at startup rather than on its first request. The fast suite still
# has to import those modules, so it supplies a valid environment here.
# Nothing in this suite connects to any of these addresses.
os.environ.setdefault("STAGE", "1")
os.environ.setdefault("APP_PORT", "8101")
os.environ.setdefault("VLLM_BASE_URL", "http://vllm.invalid:8000/v1")
os.environ.setdefault("MODEL_NAME", "qwen3")
os.environ.setdefault(
    "PHOENIX_COLLECTOR_ENDPOINT", "http://phoenix.invalid:6006/v1/traces"
)


def stub_tool_call(name: str, arguments: str = "{}"):
    """Build a fake tool call, shaped like the OpenAI client returns one."""
    return SimpleNamespace(
        id=f"call_{name}",
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class StubClient:
    """Stands in for OpenAI. Returns canned replies, records the requests."""

    def __init__(self, replies: list[str] | None = None, tool_calls=None):
        self.replies = list(replies or ["ALLOW"])
        self.tool_calls = tool_calls
        self.requests: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        content = self.replies.pop(0) if self.replies else "ALLOW"
        # tool_calls may be a list of per-call scripted responses, so a graph
        # making several calls can get a different answer at each step.
        calls = self.tool_calls
        if isinstance(calls, list) and calls and isinstance(calls[0], list):
            calls = calls.pop(0) if calls else None
        message = SimpleNamespace(role="assistant", content=content, tool_calls=calls)
        return SimpleNamespace(
            choices=[SimpleNamespace(index=0, message=message, finish_reason="stop")]
        )


@pytest.fixture
def allowing_client() -> StubClient:
    """A client whose policy judge always says ALLOW."""
    return StubClient(replies=["ALLOW"])


@pytest.fixture
def blocking_client() -> StubClient:
    """A client whose policy judge always says BLOCK."""
    return StubClient(replies=["BLOCK"])
