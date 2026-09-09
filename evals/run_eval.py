"""Score a dataset against the deployed Stage 3 pipeline.

Separate from the fast suite on purpose. The fast tests assert things that
are predictable; this scores something that is not. Whether an answer is
GOOD cannot be asserted -- you run it across a batch, score the batch, and
check the average clears a line. That is a release decision, not a
per-commit one.

No stubs anywhere: it posts to the real deployed endpoint through the proxy
and judges with the real model.

    python evals/run_eval.py                                  # baseline
    python evals/run_eval.py evals/datasets/from_feedback.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# app/config.py validates a container-shaped environment at import; these are
# meaningless to a host-side script but must be present. See routing_check.py.
os.environ.setdefault("STAGE", "3")
os.environ.setdefault("APP_PORT", "8103")
os.environ.setdefault("VLLM_BASE_URL", "http://localhost:8000/v1")
os.environ.setdefault("MODEL_NAME", "qwen3")
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")

import httpx

from app.llm import chat, make_client

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "evals" / "datasets" / "baseline.json"

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost")
STAGE_ROUTE = os.environ.get("EVAL_ROUTE", "v3")

# The release gate. Below this the job fails and the deploy does not ship.
PASS_THRESHOLD = 0.70

JUDGE_PROMPT = """\
You are scoring one answer from an IT support assistant.

QUESTION:
{question}

EXPECTED BEHAVIOUR:
{expected}

ACTUAL ANSWER:
{answer}

Score how well the actual answer matches the expected behaviour, from 1 to 5:
5 = fully matches
4 = matches with a minor omission
3 = partially matches
2 = mostly wrong
1 = wrong, or invents information

Reply with the digit, then a space, then one short sentence of reason.
Nothing else."""


def ask_pipeline(question: str) -> tuple[str | None, str | None]:
    """Post to the deployed stage. Returns (answer, error)."""
    try:
        response = httpx.post(
            f"{GATEWAY_URL}/{STAGE_ROUTE}/chat",
            json={"message": question},
            timeout=300.0,
        )
    except Exception as error:
        return None, f"request failed: {error}"

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text[:120]
        # A guardrail rejection is a real outcome, not a crash. It scores 1:
        # the question went unanswered.
        return None, f"HTTP {response.status_code}: {detail}"
    return response.json().get("answer"), None


def judge(client, question: str, expected: str, answer: str) -> tuple[int, str]:
    """Score one answer 1-5 with a short reason."""
    response = chat(
        client,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    question=question, expected=expected, answer=answer
                ),
            }
        ],
        thinking=False,
        max_tokens=96,
    )
    text = (response.choices[0].message.content or "").strip()
    digit = next((c for c in text if c.isdigit()), None)
    if digit is None or not 1 <= int(digit) <= 5:
        return 1, f"judge returned no usable score: {text[:60]!r}"
    reason = text[text.index(digit) + 1 :].strip(" .:-")
    return int(digit), reason[:80]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", nargs="?", default=str(DEFAULT_DATASET))
    args = parser.parse_args()

    path = Path(args.dataset)
    if not path.exists():
        sys.exit(f"{path} does not exist. Build one with evals/dataset.py.")
    data = json.loads(path.read_text())
    examples = data.get("examples") or []
    if not examples:
        sys.exit(f"{path} has no examples.")

    print(f"Dataset : {data.get('name', path.stem)} ({len(examples)} examples)")
    print(f"Target  : {GATEWAY_URL}/{STAGE_ROUTE}/chat")
    print(f"Threshold: {PASS_THRESHOLD:.0%}\n")

    client = make_client()
    rows = []
    for index, example in enumerate(examples, start=1):
        question = example["question"]
        expected = example.get("expected_behaviour", "")
        answer, error = ask_pipeline(question)
        if error:
            score, reason = 1, error[:80]
        else:
            score, reason = judge(client, question, expected, answer)
        rows.append((index, score, question, reason))
        print(f"  {index:2}/{len(examples)}  score {score}/5  {question[:44]}")

    print(f"\n{'#':>3}  {'score':>5}  {'question':44}  reason")
    print("-" * 110)
    for index, score, question, reason in rows:
        print(f"{index:3}  {score:>3}/5  {question[:44]:44}  {reason}")

    average = sum(score for _, score, _, _ in rows) / len(rows)
    normalised = (average - 1) / 4
    print(f"\nAverage score : {average:.2f}/5")
    print(f"Normalised    : {normalised:.1%}")

    if normalised < PASS_THRESHOLD:
        print(
            f"\nFAIL: {normalised:.1%} is below the {PASS_THRESHOLD:.0%} "
            "threshold. This is the gate that stops a bad version shipping."
        )
        return 1
    print(f"\nPASS: at or above {PASS_THRESHOLD:.0%}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
