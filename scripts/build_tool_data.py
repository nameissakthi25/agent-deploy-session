"""Build the committed tool data from the pinned source dataset.

Writes app/tools/tickets.json and app/tools/services.json. Both are committed,
so the containers never make a network call at runtime and the data is
identical in every rehearsal.

    python scripts/build_tool_data.py

Provenance and the one authored field are documented in corpus/SOURCES.md.
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fetch_dataset import DATA_DIR, DATASET_ID, DATASET_REVISION, fetch
from scripts.redact import load_pii_key, redact

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "app" / "tools"

# How many tickets lookup_ticket can serve. Small on purpose: they get read
# aloud, and a short list is checkable by anyone in the room.
TICKETS_PER_FAMILY = 2

# The dataset's 14 issue families, mapped to the service each one belongs to.
# Mapping by family rather than by application name because the raw
# `applications` field has 490 messy variants ("Outlook", "Microsoft Outlook",
# "Outlook Desktop"), and the family prefix is exact.
FAMILY_TO_SERVICE = {
    "AIT": "api-gateway",
    "ALP": "password-reset-portal",
    "CES": "load-balancer",
    "DCP": "intune",
    "DRF": "dns",
    "EDE": "device-encryption",
    "LPD": "laptop-support",
    "OES": "exchange-online",
    "PDQ": "print-server",
    "SDA": "shared-drive",
    "SIB": "software-center",
    "SML": "sso",
    "VDA": "vpn",
    "WCI": "wifi",
}

# The one field NOT derived from the dataset. The source has no live service
# status (all 745 incidents are closed), so current state is authored here to
# give the demo some variety. Incident counts and last-incident dates below
# ARE real. Say this out loud rather than implying the whole row is data.
AUTHORED_STATE = {
    "vpn": ("degraded", "Elevated disconnects on the EMEA gateway"),
    "payroll-portal": ("maintenance", "Planned window until 18:00 UTC"),
    "print-server": ("degraded", "Jobs queueing on PS-PRINT01"),
}
DEFAULT_STATE = ("operational", "")


def load_source() -> pd.DataFrame:
    """Load the pinned parquet, fetching it first if data/ is empty."""
    parquet = DATA_DIR / "source" / "data" / "train.parquet"
    if not parquet.exists():
        print("data/ is empty, fetching the pinned revision first...")
        fetch()
    if not parquet.exists():
        sys.exit(f"Expected {parquet} after fetch. Run scripts/fetch_dataset.py.")

    frame = pd.read_parquet(parquet)
    ticket = pd.json_normalize(frame["ticket"])
    return frame.assign(
        family=frame.record_id.str.split("-").str[1],
        title=ticket.submitted_title,
        priority=ticket.priority,
        submitted_at=ticket.submitted_at,
        description=ticket.submitted_description,
    )


def build_tickets(frame: pd.DataFrame) -> list[dict]:
    """Pick a stable, stratified slice of tickets for lookup_ticket.

    Free text is redacted with the dataset's own PII answer key. Every one of
    the source incidents carries names, employee IDs and IPs in its root cause
    and resolution steps, and a tool that hands that back would trip the output
    guard on every call.
    """
    pii_key = load_pii_key()
    rows = []
    for family in sorted(FAMILY_TO_SERVICE):
        # Sorted by record_id, so the same tickets are picked every run.
        subset = frame[frame.family == family].sort_values("record_id")
        for _, row in subset.head(TICKETS_PER_FAMILY).iterrows():
            rows.append(
                {
                    "ticket_id": row.record_id,
                    "subject": row.title,
                    # Every incident in the source is closed. lookup_ticket
                    # therefore answers "how was this resolved", which is a
                    # more useful tool than a status poll anyway.
                    "status": row.status,
                    "priority": row.priority,
                    "opened": row.submitted_at[:10],
                    "service": FAMILY_TO_SERVICE[family],
                    "root_cause": redact(row.root_cause, pii_key[row.record_id]),
                    "resolution_steps": [
                        redact(step, pii_key[row.record_id])
                        for step in row.resolution["steps"]
                    ],
                }
            )
    return rows


def build_services(frame: pd.DataFrame) -> list[dict]:
    """One row per service, with real incident counts and an authored state."""
    rows = []
    for family, service in sorted(FAMILY_TO_SERVICE.items(), key=lambda kv: kv[1]):
        subset = frame[frame.family == family]
        state, note = AUTHORED_STATE.get(service, DEFAULT_STATE)
        rows.append(
            {
                "service_name": service,
                "state": state,
                "note": note,
                "incidents_on_record": int(len(subset)),
                "last_incident": max(subset.submitted_at)[:10],
            }
        )
    # A service with no incidents in the source, so the tools have a case where
    # the honest answer is "nothing on record".
    state, note = AUTHORED_STATE["payroll-portal"]
    rows.append(
        {
            "service_name": "payroll-portal",
            "state": state,
            "note": note,
            "incidents_on_record": 0,
            "last_incident": None,
        }
    )
    return sorted(rows, key=lambda row: row["service_name"])


def write(path: Path, payload: object, count_label: str) -> None:
    header = {
        "_source": DATASET_ID,
        "_revision": DATASET_REVISION,
        "_license": "MIT (c) 2026 Alexander Meau",
        "_generated_by": "scripts/build_tool_data.py - do not edit by hand",
    }
    path.write_text(json.dumps({**header, count_label: payload}, indent=2) + "\n")
    print(f"  {path.relative_to(ROOT)}  {len(payload)} {count_label}")


def main() -> None:
    frame = load_source()
    print(f"Loaded {len(frame)} incidents from {DATASET_ID} @ {DATASET_REVISION[:12]}")
    write(OUT_DIR / "tickets.json", build_tickets(frame), "tickets")
    write(OUT_DIR / "services.json", build_services(frame), "services")


if __name__ == "__main__":
    main()
