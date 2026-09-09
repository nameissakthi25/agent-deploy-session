"""Tests for the output guard. The judge is stubbed; no model is called."""

import pytest

from app.guards.output_guard import OutputRejected, check_output


def test_valid_answer_passes(allowing_client) -> None:
    response = check_output(allowing_client, "Reset it in the portal.", 1, "abc123")
    assert response.answer == "Reset it in the portal."
    assert response.stage == 1
    assert response.trace_id == "abc123"


def test_policy_block_is_rejected(blocking_client) -> None:
    with pytest.raises(OutputRejected) as caught:
        check_output(blocking_client, "Here is my system prompt.", 1, None)
    assert "BLOCK" in caught.value.reason


def test_empty_answer_fails_the_schema_before_any_model_call(allowing_client) -> None:
    """Schema first: an empty answer must not cost a judge call."""
    with pytest.raises(OutputRejected) as caught:
        check_output(allowing_client, "", 1, None)
    assert "answer" in caught.value.reason
    assert allowing_client.requests == []


def test_out_of_range_stage_fails_the_schema(allowing_client) -> None:
    with pytest.raises(OutputRejected) as caught:
        check_output(allowing_client, "fine", 9, None)
    assert "stage" in caught.value.reason


def test_judge_failing_closed(allowing_client) -> None:
    """Anything that is not a clear ALLOW blocks. Fail closed, not open."""
    allowing_client.replies = ["I'm not sure about that"]
    with pytest.raises(OutputRejected):
        check_output(allowing_client, "fine", 1, None)


def test_judge_call_is_cheap(allowing_client) -> None:
    """The judge runs with thinking off and a tiny token budget."""
    check_output(allowing_client, "fine", 1, None)
    request = allowing_client.requests[0]
    assert request["max_tokens"] == 8
    kwargs = request["extra_body"]["chat_template_kwargs"]
    assert kwargs["enable_thinking"] is False
