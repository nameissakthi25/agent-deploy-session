"""Valid and invalid examples for the request and response shapes."""

import pytest
from pydantic import ValidationError

from app.schemas import ChatRequest, ChatResponse

VALID_REQUESTS = [{"message": "How do I reset my password?"}, {"message": "x"}]
INVALID_REQUESTS = [
    {},  # message is required
    {"message": ""},  # too short
    {"message": "x" * 4001},  # too long
    {"message": "ok", "extra": 1},  # extra: forbid
    {"message": 5},  # wrong type
]

VALID_RESPONSES = [
    {"answer": "yes", "stage": 1},
    {"answer": "yes", "stage": 3, "trace_id": "a" * 32},
]
INVALID_RESPONSES = [
    {"answer": "", "stage": 1},  # answer must not be empty
    {"answer": "yes", "stage": 0},  # stage out of range
    {"answer": "yes", "stage": 4},
    {"answer": "yes"},  # stage is required
    {"answer": "yes", "stage": 1, "x": 1},  # extra: forbid
]


@pytest.mark.parametrize("payload", VALID_REQUESTS)
def test_valid_requests(payload) -> None:
    assert ChatRequest(**payload)


@pytest.mark.parametrize("payload", INVALID_REQUESTS)
def test_invalid_requests(payload) -> None:
    with pytest.raises(ValidationError):
        ChatRequest(**payload)


@pytest.mark.parametrize("payload", VALID_RESPONSES)
def test_valid_responses(payload) -> None:
    assert ChatResponse(**payload)


@pytest.mark.parametrize("payload", INVALID_RESPONSES)
def test_invalid_responses(payload) -> None:
    with pytest.raises(ValidationError):
        ChatResponse(**payload)


def test_session_id_defaults_and_validates() -> None:
    """Stage 1 keys its in-process history on this."""
    assert ChatRequest(message="hi").session_id == "default"
    assert ChatRequest(message="hi", session_id="room-42").session_id == "room-42"
    with pytest.raises(ValidationError):
        ChatRequest(message="hi", session_id="")
    with pytest.raises(ValidationError):
        ChatRequest(message="hi", session_id="x" * 65)
