"""Local data the tools read, loaded from the committed JSON files.

No network call at runtime. The files are produced from a pinned dataset
revision by scripts/build_tool_data.py and committed, so every rehearsal and
the session itself see identical data.

Loads on import and crashes if a file is missing or empty, rather than failing
on the first request.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent


def _load(filename: str, key: str) -> list[dict]:
    """Read one generated JSON file. Crash loudly if it is not usable."""
    path = HERE / filename
    if not path.exists():
        raise RuntimeError(f"{path} is missing. Run: python scripts/build_tool_data.py")
    payload = json.loads(path.read_text())
    rows = payload.get(key)
    if not rows:
        raise RuntimeError(f"{path} has no '{key}'. Rebuild it.")
    return rows


TICKETS = {row["ticket_id"]: row for row in _load("tickets.json", "tickets")}
SERVICES = {row["service_name"]: row for row in _load("services.json", "services")}

VALID_TICKET_IDS = sorted(TICKETS)
VALID_SERVICE_NAMES = sorted(SERVICES)
