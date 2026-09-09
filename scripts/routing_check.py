"""Measure supervisor routing quality against the real model.

scripts/toolcall_check.py proved the model emits well-formed tool calls. It
did not prove the supervisor picks the RIGHT worker -- that a service question
goes to the systems worker and a policy question goes to the knowledge base.
Routing quality is a different property and it is the one most likely to need
prompt work before the session.

No stubs. This calls the real model through the real supervisor prompt and
the real routing tools, so what it measures is what will happen live.

    python scripts/routing_check.py
"""

import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# This script imports the real supervisor prompt and routing tools from the
# graph, which transitively imports app/config.py -- and that validates a
# container-shaped environment at import time and exits if anything is
# missing. STAGE and APP_PORT are meaningless to a host-side script, so
# supply them. VLLM_BASE_URL and MODEL_NAME are read from the real
# environment below and are the ones that matter.
os.environ.setdefault("STAGE", "3")
os.environ.setdefault("APP_PORT", "8103")
os.environ.setdefault("VLLM_BASE_URL", "http://localhost:8000/v1")
os.environ.setdefault("MODEL_NAME", "qwen3")
os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")

from openai import OpenAI

from app.graph_stage3 import (
    DEFAULT_ROUTE,
    ROUTE_BY_TOOL,
    ROUTING_TOOLS,
    SUPERVISOR_PROMPT,
)
from app.llm import chat

RUNS_PER_QUERY = 3
PASS_THRESHOLD = 0.90

# (question, the worker that should handle it)
#
# tool_agent  -- names a ticket ID, or asks if a named service is up
# retriever   -- how-to, policy, or "why does X happen"
# synthesizer -- no lookup needed at all
CASES = [
    ("What was the root cause of INC-ALP-0001?", "tool_agent"),
    ("Can you pull up INC-VDA-0001 for me", "tool_agent"),
    ("How did we fix ticket INC-PDQ-0001?", "tool_agent"),
    ("Is the vpn degraded right now?", "tool_agent"),
    ("Is sso up?", "tool_agent"),
    ("Are we having print-server problems?", "tool_agent"),
    ("Is payroll-portal available?", "tool_agent"),
    ("Check whether exchange-online is having issues", "tool_agent"),
    ("How do I reset my password?", "retriever"),
    ("What's the policy on requesting a new laptop?", "retriever"),
    ("How do I get a piece of software approved?", "retriever"),
    ("Why would BitLocker fail to enable on a managed device?", "retriever"),
    ("What usually causes an MFA prompt loop?", "retriever"),
    ("Walk me through setting up the VPN on a new machine", "retriever"),
    ("Why do print jobs get stuck on a print server?", "retriever"),
    ("How do I get access to a finance shared drive?", "retriever"),
    ("Hello", "synthesizer"),
    ("What can you help me with?", "synthesizer"),
    ("Who are you?", "synthesizer"),
    ("Thanks, that's all", "synthesizer"),
]


def route_once(client: OpenAI, model: str, question: str) -> str:
    """Ask the real supervisor to route one question. Returns the worker.

    Calls app.llm.chat() with exactly the arguments graph_stage3's supervisor
    node uses, rather than rebuilding the request here. An earlier version
    duplicated the parameters and silently measured tool_choice="auto" after
    the graph had moved to "required" -- so this check reported a failure the
    real system no longer had.
    """
    response = chat(
        client,
        messages=[
            {"role": "system", "content": SUPERVISOR_PROMPT},
            {"role": "user", "content": question},
        ],
        tools=ROUTING_TOOLS,
        tool_choice="required",
        thinking=False,
        max_tokens=128,
    )
    calls = response.choices[0].message.tool_calls or []
    if not calls:
        return f"{DEFAULT_ROUTE} (no tool call)"
    return ROUTE_BY_TOOL.get(calls[0].function.name, f"unknown:{calls[0].function.name}")


def main() -> int:
    base_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    model = os.environ.get("MODEL_NAME", "qwen3")

    client = OpenAI(base_url=base_url, api_key="not-needed", timeout=120.0)
    try:
        client.models.list()
    except Exception as error:
        sys.exit(f"Cannot reach the model server at {base_url}: {error}")

    print(f"Supervisor routing check against {model} at {base_url}")
    print(f"{len(CASES)} questions x {RUNS_PER_QUERY} runs\n")

    correct = 0
    total = 0
    confusion: Counter = Counter()
    problems: list[str] = []

    for question, expected in CASES:
        picked = [route_once(client, model, question) for _ in range(RUNS_PER_QUERY)]
        hits = sum(1 for p in picked if p == expected)
        correct += hits
        total += len(picked)
        for p in picked:
            if p != expected:
                confusion[(expected, p)] += 1
        mark = "ok " if hits == RUNS_PER_QUERY else "BAD"
        chose = Counter(picked).most_common(1)[0][0]
        print(
            f"{mark} {hits}/{RUNS_PER_QUERY}  want={expected:12} "
            f"got={chose:12} {question[:44]}"
        )
        if hits < RUNS_PER_QUERY:
            problems.append(
                f"  {question!r}\n    wanted {expected}, got {Counter(picked)}"
            )

    accuracy = correct / total if total else 0.0
    print(f"\nRouting accuracy: {correct}/{total} = {accuracy:.1%}")

    if confusion:
        print("\nConfusions (wanted -> got):")
        for (wanted, got), count in confusion.most_common():
            print(f"  {wanted:12} -> {got:24} {count}x")

    if problems:
        print("\nQuestions that did not route cleanly:")
        for line in problems:
            print(line)

    if accuracy < PASS_THRESHOLD:
        print(
            f"\nFAIL: below {PASS_THRESHOLD:.0%}. The supervisor prompt or the "
            "routing tool descriptions need work before the session."
        )
        return 1
    print(f"\nPASS: at or above {PASS_THRESHOLD:.0%}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
