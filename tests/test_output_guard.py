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
    assert len(clauses) == 3, "a clause was added or removed; check judgeability"

    # Phrasings that need evidence the judge never sees.
    forbidden = ("was not given", "not provided in", "invent", "grounded", "retrieved")
    for clause in clauses:
        for phrase in forbidden:
            assert phrase not in clause.lower(), (
                f"clause {clause!r} appears to require the evidence, which the "
                "judge is never shown"
            )


def test_judge_runs_at_temperature_zero(allowing_client) -> None:
    """A policy gate must be reproducible, not sampled.

    At the model card's generation temperature of 0.7 this judge blocked a
    correct answer roughly one time in five, which made the smoke test and the
    deploy gate intermittent.
    """
    check_output(allowing_client, "fine", 1, None)
    assert allowing_client.requests[0]["temperature"] == 0.0


def test_the_judge_is_shown_the_question(allowing_client) -> None:
    """Topicality is a property of the (question, answer) pair.

    Judged from the answer alone, "explaining ChatGPT" and "explaining why
    BitLocker fails to enable" are indistinguishable -- both describe an
    external product. A wording strong enough to catch the first blocked the
    second, and with it half the corpus. The question is what separates them.
    """
    check_output(
        allowing_client,
        "BitLocker needs an initialised TPM.",
        3,
        None,
        question="Why would BitLocker fail to enable?",
    )
    sent = allowing_client.requests[0]["messages"][0]["content"]
    assert "Why would BitLocker fail to enable?" in sent
    assert "BitLocker needs an initialised TPM." in sent
