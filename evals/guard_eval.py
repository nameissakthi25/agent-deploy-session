"""Score app/guards/input_guard.py against an authored answer key.

The guard is hand-written regex. Nothing in the fast suite tells you whether
it actually works -- three prepared inputs tripping three guards is a demo
that cannot fail, which makes it weak evidence.

The source dataset ships two authored ground-truth sidecars:

  pii.json        every PII value that must be caught       (the REMOVE key)
  retention.json  technical strings that must NOT be caught (the KEEP key)

Both were authored at generation time rather than produced by a detector, so
scoring against them is not circular. Three numbers come out:

  1. Detection rate on the PII types the guard actually targets
  2. Coverage gap  -- PII types the guard cannot see at all
  3. False positives on retain-class technical strings

Run it against the raw, unredacted text in data/ -- not the redacted corpus.

    python evals/guard_eval.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.guards.input_guard import PII_PATTERNS
from scripts.fetch_dataset import DATA_DIR, fetch

# The guard's three regexes target these sidecar types. Everything else in the
# key is a type it was never written to catch -- reported as the coverage gap
# rather than counted as a miss, because calling it a miss would be dishonest.
TARGETED_TYPES = {"email", "phone"}

# Fail the run below this detection rate on the targeted types.
DETECTION_THRESHOLD = 0.80
# Fail above this false-positive rate on retain-class strings.
FALSE_POSITIVE_CEILING = 0.05


def load() -> tuple[pd.DataFrame, list, list]:
    """Load the raw corpus and both sidecars, fetching if data/ is empty."""
    source = DATA_DIR / "source"
    if not (source / "data" / "train.parquet").exists():
        print("data/ is empty, fetching the pinned revision first...")
        fetch()
    frame = pd.read_parquet(source / "data" / "train.parquet")
    # The two sidecars are shaped differently: pii.json is a bare list of
    # per-ticket records, retention.json wraps the same list under "tickets"
    # alongside a "provenance" block. Handle both rather than assuming.
    pii = json.loads((source / "pii.json").read_text())
    retention = json.loads((source / "retention.json").read_text())
    if isinstance(pii, dict):
        pii = pii["tickets"]
    if isinstance(retention, dict):
        retention = retention["tickets"]
    return frame, pii, retention


def matches_any_pattern(value: str) -> str | None:
    """Return the name of the first pattern that fires, or None."""
    for label, pattern in PII_PATTERNS.items():
        if pattern.search(value):
            return label
    return None


def score_detection(pii: list) -> tuple[Counter, Counter, Counter]:
    """How many PII values does the guard catch, by type?"""
    caught: Counter = Counter()
    missed: Counter = Counter()
    total: Counter = Counter()
    for record in pii:
        for instance in record["pii_instances"]:
            kind = instance["type"]
            total[kind] += 1
            if matches_any_pattern(instance["value"]):
                caught[kind] += 1
            else:
                missed[kind] += 1
    return caught, missed, total


def score_false_positives(retention: list) -> tuple[Counter, Counter]:
    """Which technical strings does the guard wrongly flag as PII?"""
    flagged: Counter = Counter()
    total: Counter = Counter()
    for record in retention:
        for instance in record["retain_instances"]:
            kind = instance["type"]
            total[kind] += 1
            if matches_any_pattern(instance["value"]):
                flagged[kind] += 1
    return flagged, total


def percent(part: int, whole: int) -> str:
    return f"{100.0 * part / whole:5.1f}%" if whole else "    --"


def main() -> int:
    frame, pii, retention = load()
    print(f"Scoring input_guard against {len(frame)} tickets\n")

    caught, missed, total = score_detection(pii)

    print("Detection by PII type (the answer key's REMOVE set)")
    print(f"  {'type':12} {'total':>7} {'caught':>7} {'rate':>7}   targeted")
    for kind in sorted(total, key=lambda k: -total[k]):
        mark = "yes" if kind in TARGETED_TYPES else "no  <- blind"
        print(
            f"  {kind:12} {total[kind]:7} {caught[kind]:7} "
            f"{percent(caught[kind], total[kind])}   {mark}"
        )

    targeted_total = sum(total[k] for k in TARGETED_TYPES)
    targeted_caught = sum(caught[k] for k in TARGETED_TYPES)
    all_total = sum(total.values())
    blind_total = all_total - targeted_total

    print(
        f"\n  Detection on targeted types : {percent(targeted_caught, targeted_total)}"
        f"  ({targeted_caught}/{targeted_total})"
    )
    print(
        f"  Coverage gap                : {percent(blind_total, all_total)}"
        f"  ({blind_total}/{all_total} values are types the guard cannot see)"
    )

    flagged, retain_total = score_false_positives(retention)
    print("\nFalse positives (the answer key's KEEP set -- these must NOT fire)")
    print(f"  {'type':18} {'total':>7} {'flagged':>8} {'rate':>7}")
    for kind in sorted(retain_total, key=lambda k: -flagged[k]):
        if flagged[kind]:
            print(
                f"  {kind:18} {retain_total[kind]:7} {flagged[kind]:8} "
                f"{percent(flagged[kind], retain_total[kind])}"
            )
    fp_total = sum(flagged.values())
    retain_all = sum(retain_total.values())
    print(
        f"\n  False positive rate         : {percent(fp_total, retain_all)}"
        f"  ({fp_total}/{retain_all})"
    )

    detection_rate = targeted_caught / targeted_total if targeted_total else 0.0
    fp_rate = fp_total / retain_all if retain_all else 0.0
    failed = False
    if detection_rate < DETECTION_THRESHOLD:
        print(
            f"\nFAIL: detection {detection_rate:.1%} is below "
            f"{DETECTION_THRESHOLD:.0%} on the types the guard targets."
        )
        failed = True
    if fp_rate > FALSE_POSITIVE_CEILING:
        print(
            f"\nFAIL: false positive rate {fp_rate:.1%} is above "
            f"{FALSE_POSITIVE_CEILING:.0%}. The guard is rejecting "
            "legitimate technical text."
        )
        failed = True
    if not failed:
        print("\nPASS: within both thresholds.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
