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


def test_policy_clauses_are_all_judgeable_from_the_answer_alone() -> None:
    """A canary on the policy, not a behaviour test.

    Every clause must be assessable from the ANSWER, because that is all the
    judge is shown. A clause about groundedness once blocked every correct
    answer here, and the same mistake later reappeared in the eval dataset.
    If a clause is added that needs the evidence, this test is the reminder.
    """
    from app.guards.output_guard import POLICY

    clauses = [line for line in POLICY.splitlines() if line.startswith("- ")]
    assert len(clauses) == 4, "a clause was added or removed; check judgeability"

    # Phrasings that need evidence the judge never sees.
    forbidden = ("was not given", "not provided in", "invent", "grounded", "retrieved")
    for clause in clauses:
        for phrase in forbidden:
            assert phrase not in clause.lower(), (
                f"clause {clause!r} appears to require the evidence, which the "
                "judge is never shown"
            )
