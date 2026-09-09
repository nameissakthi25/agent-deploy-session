"""The 60-run tool-calling reliability test.

Run this as soon as the model serves a curl request, before any application
code exists. If tool calling is unreliable, everything downstream is wasted
work -- this is the highest-risk item in the build.

20 queries, 3 runs each. A run counts as valid only if the model's FIRST
response is exactly one tool call, with the expected tool name, and arguments
that validate against that tool's Pydantic model.

Acceptance: at least 58 of 60.

    python scripts/toolcall_check.py
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

from app.tools.definitions import ARG_MODELS, TOOLS

RUNS_PER_QUERY = 3
PASS_THRESHOLD = 58

SYSTEM_PROMPT = (
    "You are an internal IT support assistant. You have tools available. "
    "When a tool can answer the user, call exactly one tool. Do not answer "
    "from memory and do not ask a clarifying question first."
)

# (query, expected tool name). Ticket IDs and service names are the real ones
# from app/tools/tickets.json and services.json, so a query the model gets
# right here is a query that works end to end.
QUERIES = [
    ("What was the root cause of INC-ALP-0001?", "lookup_ticket"),
    ("Can you pull up INC-VDA-0001 for me", "lookup_ticket"),
    ("How did we fix ticket INC-PDQ-0001?", "lookup_ticket"),
    ("I need the resolution steps from INC-SML-0002", "lookup_ticket"),
    ("Someone referenced INC-SDA-0001 - what happened there?", "lookup_ticket"),
    ("Look up INC-OES-0002 please", "lookup_ticket"),
    ("Is the vpn degraded right now?", "check_service_status"),
    ("Are we having print-server problems?", "check_service_status"),
    ("Is sso up?", "check_service_status"),
    ("Check whether exchange-online is having issues", "check_service_status"),
    ("What's the current state of the wifi service?", "check_service_status"),
    ("Is payroll-portal available?", "check_service_status"),
    ("Any known issues with dns at the moment?", "check_service_status"),
    ("How do I reset my password?", "search_kb"),
    ("What's the policy on requesting a new laptop?", "search_kb"),
    ("How do I get a piece of software approved?", "search_kb"),
    ("Why would BitLocker fail to enable on a managed device?", "search_kb"),
    ("Walk me through setting up the VPN on a new machine", "search_kb"),
    ("What usually causes an MFA prompt loop?", "search_kb"),
    ("How do I get access to a finance shared drive?", "search_kb"),
]


def require_env(name: str, default: str) -> str:
    """Read an environment variable, falling back to a documented default."""
    value = os.environ.get(name, default)
    if not value:
        sys.exit(f"{name} is set but empty. Fix it or unset it to use {default!r}.")
    return value


def check_one_attempt(client: OpenAI, model: str, query: str, expected: str) -> str:
    """Run one query. Return an empty string if valid, else the reason it failed."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        tools=TOOLS,
        tool_choice="auto",
        # Qwen3.8's own recommendation for non-thinking mode. temperature=0.0
        # would be the obvious choice, but the model card asks for these, and
        # this check exists to measure the model as it will actually be run.
        temperature=0.7,
        top_p=0.8,
        presence_penalty=1.5,
        max_tokens=512,
        extra_body={
            "top_k": 20,
            # Qwen3.8 thinks by DEFAULT at reasoning_effort=xhigh, so opting
            # out is explicit. Run exactly as the Stage 3 supervisor will:
            # a supervisor that reasons at length before every routing
            # decision makes traces unreadable and responses slow.
            #
            # preserve_thinking defaults to True and retains thinking blocks
            # from every historical message, which inflates the prompt on the
            # Stage 3 fan-out. Off here for the same reason.
            "chat_template_kwargs": {
                "enable_thinking": False,
                "preserve_thinking": False,
            },
        },
    )

    message = response.choices[0].message
    calls = message.tool_calls or []

    if not calls:
        text = (message.content or "").strip().replace("\n", " ")
        return f"no tool call (said: {text[:60]!r})"
    if len(calls) > 1:
        return f"{len(calls)} tool calls, expected 1"

    call = calls[0]
    if call.function.name != expected:
        return f"called {call.function.name}, expected {expected}"

    try:
        arguments = json.loads(call.function.arguments)
    except json.JSONDecodeError as error:
        return f"arguments were not valid JSON ({error})"

    model_for_tool = ARG_MODELS[expected]
    try:
        model_for_tool(**arguments)
    except Exception as error:
        first_line = str(error).split("\n")[0]
        return f"arguments failed validation ({first_line})"

    return ""


def main() -> int:
    base_url = require_env("VLLM_BASE_URL", "http://localhost:8000/v1")
    model = require_env("MODEL_NAME", "qwen3")

    # Fail loudly now rather than on the first request.
    client = OpenAI(base_url=base_url, api_key="not-needed", timeout=120.0)
    try:
        client.models.list()
    except Exception as error:
        sys.exit(f"Cannot reach the model server at {base_url}: {error}")

    print(f"Model server: {base_url}")
    print(f"Model name:   {model}")
    print(f"Running {len(QUERIES)} queries x {RUNS_PER_QUERY} runs\n")

    total_valid = 0
    failures: list[str] = []

    for query, expected in QUERIES:
        valid_for_query = 0
        for _ in range(RUNS_PER_QUERY):
            reason = check_one_attempt(client, model, query, expected)
            if reason:
                failures.append(f"  {query[:50]!r} -> {reason}")
            else:
                valid_for_query += 1
        total_valid += valid_for_query
        mark = "ok " if valid_for_query == RUNS_PER_QUERY else "BAD"
        print(f"{mark} {valid_for_query}/{RUNS_PER_QUERY}  {expected:22} {query[:46]}")

    total_runs = len(QUERIES) * RUNS_PER_QUERY
    print(f"\nValid first-attempt tool calls: {total_valid}/{total_runs}")

    if failures:
        print("\nFailures:")
        for line in failures:
            print(line)

    if total_valid < PASS_THRESHOLD:
        print(
            f"\nFAIL: below the {PASS_THRESHOLD}/{total_runs} threshold. "
            "Do not build Stage 3 on this model and parser combination."
        )
        return 1

    print(f"\nPASS: at or above the {PASS_THRESHOLD}/{total_runs} threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
