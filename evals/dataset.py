"""Turn thumbs-downed traces into an eval dataset.

This is the second half of the feedback loop. The UI attaches a thumbs-down
to a request's trace; this filters for the unhappy ones and writes them out
as a dataset that evals/run_eval.py can score.

The chain is the lesson: no tracing means no examples, no examples means no
measurement, and without measurement "we improved it" is just a feeling.

    python evals/dataset.py                       # writes from_feedback.json
    python evals/dataset.py --label thumbs_up     # or the happy ones
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "evals" / "datasets"

PHOENIX_BASE_URL = "http://localhost:6006"
PROJECT = "it-support-assistant"
ANNOTATION_NAME = "user_feedback"

# What a thumbs-down means for scoring. Nobody wrote an expectation when they
# clicked the button, so the dataset carries this rubric instead -- the point
# of these examples is that the previous answer was judged bad, not that a
# specific better answer is known.
DEFAULT_EXPECTATION = (
    "Answers the question using retrieved evidence or a tool result, cites "
    "its source, and says plainly when it does not know. A user marked the "
    "previous answer to this question as unhelpful."
)


def fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.load(response)
    except Exception as error:
        sys.exit(f"Could not reach Phoenix at {url}: {error}")


def attribute(attributes: dict, key: str):
    """Read a span attribute, flat or nested.

    Phoenix returns some attributes flat ("input.value") and nests others
    ("input": {"value": ...}) -- it nests the OpenInference semantic
    conventions it recognises and leaves hand-set attributes flat. Reading
    only one form silently returns nothing for the other, which looked
    exactly like "no feedback has been collected yet".
    """
    if key in attributes:
        return attributes[key]
    node = attributes
    for part in key.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def collect(label: str) -> list[dict]:
    """Find traces annotated with this label, and recover their questions."""
    base = f"{PHOENIX_BASE_URL}/v1/projects/{urllib.parse.quote(PROJECT)}"

    spans = fetch_json(f"{base}/spans?limit=1000").get("data", [])
    if not spans:
        sys.exit(f"No spans in project {PROJECT!r}. Has anything been asked yet?")

    # The root "chat" span carries the question and answer as input.value and
    # output.value, so no digging into nested model-call spans is needed.
    roots = {}
    for span in spans:
        if span["name"] != "chat":
            continue
        attributes = span.get("attributes") or {}
        roots[span["context"]["trace_id"]] = {
            "question": attribute(attributes, "input.value"),
            "previous_answer": attribute(attributes, "output.value"),
            "stage": attribute(attributes, "stage"),
        }

    if not roots:
        sys.exit("No 'chat' root spans found. Nothing to build a dataset from.")

    query = urllib.parse.urlencode([("trace_ids", t) for t in roots])
    annotations = fetch_json(f"{base}/trace_annotations?{query}").get("data", [])

    examples = []
    for annotation in annotations:
        if annotation.get("name") != ANNOTATION_NAME:
            continue
        if ((annotation.get("result") or {}).get("label")) != label:
            continue
        root = roots.get(annotation["trace_id"], {})
        question = root.get("question")
        if not question:
            # A rejected input never reached the graph, so there is no
            # question worth scoring. Skip rather than emit a broken example.
            continue
        examples.append(
            {
                "question": question,
                "expected_behaviour": DEFAULT_EXPECTATION,
                "source_trace_id": annotation["trace_id"],
                "source_stage": root.get("stage"),
                "previous_answer": root.get("previous_answer"),
            }
        )
    return examples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="thumbs_down")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    examples = collect(args.label)
    print(f"Found {len(examples)} traces annotated {args.label!r}")
    if not examples:
        print("Nothing to write. Collect some feedback in the UI first.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else OUT_DIR / "from_feedback.json"
    out.write_text(
        json.dumps(
            {
                "name": f"from_feedback_{args.label}",
                "description": (
                    f"Built by evals/dataset.py from traces annotated "
                    f"{args.label!r} in Phoenix project {PROJECT!r}."
                ),
                "examples": examples,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Wrote {out.relative_to(ROOT)} with {len(examples)} examples")
    for example in examples:
        print(f"  stage {example['source_stage']}  {example['question'][:64]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
