"""Measure throughput on this GPU and do the cost-per-token arithmetic.

This is the 0:04 segment's payoff, computed rather than quoted. It measures
what the card actually does, then divides by what the card actually costs.

Three things get measured:

  1. Single-request throughput  -- one request at a time
  2. Batched throughput         -- N at once, which is why self-hosting works
  3. Cost per million tokens    -- throughput divided into the hourly rate

Rates come from `jl gpus` and are set below. Change them rather than trusting
the defaults; a stale price makes the whole comparison wrong.

    python scripts/cost_report.py
"""

import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

# From `jl gpus`, IN2 region, on-demand VM pricing, 2026-09-09.
INR_PER_HOUR = {
    "H100-80GB": 229.64,
    "A100-80GB": 126.85,
    "H200-141GB": 378.27,
    "L4-24GB": 37.18,
}
GPU = os.environ.get("GPU_NAME", "H100-80GB")

# Set this from a rate you have actually checked. It only affects the USD
# column; the rupee arithmetic stands on its own.
INR_PER_USD = float(os.environ.get("INR_PER_USD", "88.0"))

# A published hosted rate to compare against, USD per million output tokens.
# Replace with whatever you intend to quote on screen, and say which model.
HOSTED_COMPARISON = ("a hosted mid-size model", 0.60)

# Swept rather than fixed: cost per token depends almost entirely on how many
# requests the card is serving at once, so one number would be misleading.
# The top of the sweep matches --max-num-seqs in compose.model.yaml.
CONCURRENCY_SWEEP = [int(n) for n in os.environ.get("SWEEP", "1,4,8,16,32").split(",")]
OUTPUT_TOKENS = 256
PROMPT = (
    "Explain, in exactly one paragraph, why a VPN tunnel might drop "
    "immediately after multi-factor authentication succeeds."
)


def one_request(client: OpenAI, model: str) -> tuple[float, int]:
    """Return (seconds, completion tokens) for one request."""
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=OUTPUT_TOKENS,
        temperature=0.7,
        top_p=0.8,
        presence_penalty=1.5,
        extra_body={
            "top_k": 20,
            "chat_template_kwargs": {
                "enable_thinking": False,
                "preserve_thinking": False,
            },
        },
    )
    elapsed = time.perf_counter() - started
    return elapsed, response.usage.completion_tokens


def cost_per_million(
    inr_per_hour: float, tokens_per_second: float
) -> tuple[float, float]:
    """Return (INR, USD) per million output tokens at this throughput."""
    tokens_per_hour = tokens_per_second * 3600
    inr = inr_per_hour / tokens_per_hour * 1_000_000
    return inr, inr / INR_PER_USD


def main() -> int:
    base_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    model = os.environ.get("MODEL_NAME", "qwen3")
    if GPU not in INR_PER_HOUR:
        sys.exit(f"Unknown GPU {GPU!r}. Known: {', '.join(INR_PER_HOUR)}")
    rate = INR_PER_HOUR[GPU]

    client = OpenAI(base_url=base_url, api_key="not-needed", timeout=300.0)
    try:
        client.models.list()
    except Exception as error:
        sys.exit(f"Cannot reach the model server at {base_url}: {error}")

    print(f"GPU        : {GPU} at INR {rate:.2f}/hour")
    print(f"Model      : {model}")
    print(f"Output cap : {OUTPUT_TOKENS} tokens per request\n")

    # Warm up, so JIT compilation and cache effects do not land in the numbers.
    print("warming up...")
    one_request(client, model)

    name, hosted_usd = HOSTED_COMPARISON
    print(
        f"\n  {'concurrent':>10} {'tok/sec':>9} {'latency':>9} "
        f"{'INR/1M':>9} {'USD/1M':>8} {'vs hosted':>10}"
    )
    print("  " + "-" * 60)

    rows = []
    for concurrency in CONCURRENCY_SWEEP:
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            results = list(
                pool.map(lambda _: one_request(client, model), range(concurrency))
            )
        wall = time.perf_counter() - started
        throughput = sum(tokens for _, tokens in results) / wall
        latency = statistics.median(seconds for seconds, _ in results)
        inr, usd = cost_per_million(rate, throughput)
        rows.append((concurrency, throughput, latency, inr, usd))
        print(
            f"  {concurrency:>10} {throughput:>9.1f} {latency:>8.2f}s "
            f"{inr:>9.2f} {usd:>8.2f} {usd / hosted_usd:>9.2f}x"
        )

    best = min(rows, key=lambda r: r[4])
    worst = max(rows, key=lambda r: r[4])
    print(
        f"\n  {name}: INR {hosted_usd * INR_PER_USD:.2f} / USD "
        f"{hosted_usd:.2f} per million output tokens"
    )
    print(
        "  (a placeholder -- set HOSTED_COMPARISON to a rate you have actually checked)"
    )

    print("\n--- what the numbers say ---")
    print("  Batching is why self-hosting is viable at all: throughput goes")
    print(
        f"  from {rows[0][1]:.0f} to {best[1]:.0f} tokens/sec "
        f"({best[1] / rows[0][1]:.1f}x) between {rows[0][0]} and "
        f"{best[0]} concurrent requests,"
    )
    print(f"  while median latency only moves from {rows[0][2]:.2f}s to {best[2]:.2f}s.")
    print(
        f"\n  Cost per million output tokens therefore swings "
        f"{worst[4] / best[4]:.1f}x with utilisation alone:"
    )
    print(f"    idle-ish ({worst[0]} concurrent) : USD {worst[4]:.2f}")
    print(f"    busy     ({best[0]} concurrent) : USD {best[4]:.2f}")
    print("  You pay for the GPU whether anyone is asking questions or not,")
    print("  so utilisation -- not the hourly rate -- decides the unit cost.")
    verdict = "cheaper than" if best[4] < hosted_usd else "more expensive than"
    print(
        f"\n  At its best this card is {best[4] / hosted_usd:.2f}x the hosted"
        f" rate: {verdict} buying tokens."
    )
    print("  The honest reasons to self-host are data residency and")
    print("  predictable cost, not raw price.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
