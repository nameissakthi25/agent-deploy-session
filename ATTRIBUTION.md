# Third-party data

## Source dataset

**[ameau01/synthetic-it-support-tickets](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets)**
— 745 synthetic IT service-management incident records, with two authored
PII ground-truth sidecars and a synthetic user directory.

- **Licence:** MIT, © 2026 Alexander Meau. Full text in `data/source/LICENSE`
  after `make fetch`.
- **Revision pinned:** `e5ebd6c6bb955c136c9f45b6fe1503d8331d0a91` (revision 4,
  2026-06-15). Pinned for the same reason the dependencies are pinned — the
  data must be byte-identical across both rehearsals and the session, or the
  recorded fallback runs will not match what happens live.
- **All records are synthetic.** No real personal data, and the PII in the raw
  text was injected at generation time.

MIT is permissive, so learners can reuse this repository including the derived
data, on client work included. That ruled out the more popular alternatives on
the Hub (`Tobi-Bueck/customer-support-tickets`, `mindweave/help-desk-tickets`),
which are CC BY-NC 4.0.

## What is derived from it

| Artefact | Built by | Contents |
|---|---|---|
| `app/tools/tickets.json` | `scripts/build_tool_data.py` | 28 incidents, 2 per issue family, PII-redacted |
| `app/tools/services.json` | `scripts/build_tool_data.py` | 15 services, real incident counts, authored state |

## Two honest notes, to say out loud rather than gloss

**The data is synthetic.** Every IT-helpdesk dataset on the Hugging Face Hub is.
This is somebody else's generated data — better structured and larger than
anything hand-written for the session, but not real ticket history.

**Service state is authored, not measured.** All 745 source incidents are
`closed`, so the dataset carries no live service status. In
`app/tools/services.json` the `state` and `note` fields are written by hand to
give the demo some variety; `incidents_on_record` and `last_incident` are real
counts from the source. The authored values are marked in
`scripts/build_tool_data.py` as `AUTHORED_STATE`.

## Redaction

The source ships unredacted PII on purpose — upstream it is the *input* to a
redaction benchmark. The derived tool data is redacted with the dataset's own
`pii.json` answer key (`scripts/redact.py`), so it is clean by construction
rather than by our regexes being good. All 28 selected incidents contained PII
before redaction.

The raw, unredacted copy stays in `data/` and is git-ignored. It is the scoring
set for the input guard — see `evals/guard_eval.py` when step 5 lands.
