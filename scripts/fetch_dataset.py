"""Download the source dataset, pinned to one exact revision.

Pinned for the same reason every dependency is pinned: the corpus and the tool
data must be byte-identical between rehearsal 1, rehearsal 2 and the session,
or the recorded fallback runs will not match what happens live.

Writes into data/, which is git-ignored. The committed artefacts are produced
from it by scripts/build_tool_data.py.

    python scripts/build_tool_data.py     # calls this first if data/ is empty
    python scripts/fetch_dataset.py       # or run it on its own
"""

import sys
from pathlib import Path

from huggingface_hub import snapshot_download

# ameau01/synthetic-it-support-tickets, MIT licensed.
# Revision 4 (2026-06-15): 745 incidents, PII + retention sidecars, user directory.
DATASET_ID = "ameau01/synthetic-it-support-tickets"
DATASET_REVISION = "e5ebd6c6bb955c136c9f45b6fe1503d8331d0a91"

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Everything the build needs. The sidecars are large and only the guard eval
# reads them, but they are pinned to the same revision so the whole set is
# internally consistent.
WANTED = [
    "LICENSE",
    "README.md",
    "data/train.parquet",
    "pii.json",
    "retention.json",
    "users_directory.json",
]


def fetch() -> Path:
    """Download the pinned revision into data/. Returns the local directory."""
    DATA_DIR.mkdir(exist_ok=True)
    try:
        local = snapshot_download(
            repo_id=DATASET_ID,
            repo_type="dataset",
            revision=DATASET_REVISION,
            allow_patterns=WANTED,
            local_dir=DATA_DIR / "source",
        )
    except Exception as error:
        sys.exit(
            f"Could not download {DATASET_ID} at {DATASET_REVISION[:12]}: {error}\n"
            "This needs network access and, for gated repos, `huggingface-cli login`."
        )
    return Path(local)


if __name__ == "__main__":
    where = fetch()
    print(f"{DATASET_ID} @ {DATASET_REVISION[:12]}")
    for path in sorted(where.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(where)}  {path.stat().st_size:,} bytes")
