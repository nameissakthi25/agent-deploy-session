"""Redact PII from the source text using the dataset's own answer key.

The source corpus deliberately ships unredacted PII, because upstream it is the
*input* to a redaction benchmark. We want the opposite for the knowledge base:
a real KB article would not carry the reporter's name, employee ID or phone
number, and a corpus full of PII makes the output guard trip on every RAG
answer.

So the corpus and the tool data are redacted using pii.json, which is an
authored answer key rather than a detector -- meaning the corpus is clean by
construction, not by our regexes being good.

The raw, unredacted text stays in data/ for evals/guard_eval.py to score
app/guards/input_guard.py against. Do not redact that copy.
"""

import json

from scripts.fetch_dataset import DATA_DIR


def load_pii_key() -> dict[str, list[tuple[str, str]]]:
    """Map ticket_id -> [(pii value, replacement token)], longest value first.

    Longest first matters: replacing "Monica" before "Monica Carson" would
    leave a stray surname behind.
    """
    path = DATA_DIR / "source" / "pii.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing. Run scripts/fetch_dataset.py.")

    key: dict[str, list[tuple[str, str]]] = {}
    for record in json.loads(path.read_text()):
        pairs = [
            (instance["value"], instance["expected_after_redaction"])
            for instance in record["pii_instances"]
        ]
        pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
        key[record["ticket_id"]] = pairs
    return key


def redact(text: str, pairs: list[tuple[str, str]]) -> str:
    """Replace every known PII value in one ticket's text with its token."""
    for value, token in pairs:
        text = text.replace(value, token)
    return text
