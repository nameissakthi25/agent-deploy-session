# agent-deploy-session

Demo repository for the session **"Serving and Shipping It Yourself: Chatbot → RAG →
Multi-Agent on Your Own GPU."** One use case, deployed three times against one
self-hosted model, on a single JarvisLabs A100 80GB box under Docker Compose.

The full brief is in [`build-spec.md`](build-spec.md); the run of show is in
[`session-plan-jarvislabs.md`](session-plan-jarvislabs.md).

## Build status

Following the build order in `build-spec.md` section 13. Get each step working
before starting the next.

- [x] 1. `compose.yaml` with just vLLM — model serves and answers a curl request
- [x] 2. `scripts/toolcall_check.py` — the tool-calling go/no-go gate
- [x] 3. Stage 1 app + Caddy — request works through the proxy
- [x] 4. Phoenix + `observability.py` — one trace arrives, 2 spans
- [x] 5. Guardrails, with their tests — 46 tests in 0.7s, guard eval scored
- [x] 6. Stage 2 + corpus indexing — 42 articles indexed, retrieval span verified
- [x] 7. Stage 3 + tool guard — trace tree verified, rejection span verified
- [x] 8. UI + feedback writing — thumbs write annotations, verified in Phoenix
- [x] 9. Eval runner — discriminates: stage 3 scores 100%, stage 1 fails at ~31%
- [x] 10. CI pipeline — written; needs a repo + secrets to run
- [ ] 11. `smoke_test.py`, then the full acceptance list

## Setup

```bash
cp .env.example .env      # then fill in HF_TOKEN
docker compose up -d      # weights download on first run; this is slow
docker compose logs -f vllm
```

Wait for the healthcheck to go healthy before doing anything else:

```bash
docker compose ps         # vllm should read (healthy)
```

Open Phoenix on the second screen — `http://localhost:6006`, or `/traces`
through the proxy. Every `/chat` response carries the `trace_id` of its own
request, so it can be pasted straight into Phoenix's search box.

Confirm the model answers:

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3","messages":[{"role":"user","content":"Say hello in five words."}]}'
```

## The tool-calling gate

Run this immediately after the model serves, before building anything else.
If tool calling is unreliable, every downstream stage is wasted work.

```bash
pip install -r requirements.txt
make data          # fetch the pinned dataset, build the committed tool data
make toolcheck
```

`make data` is only needed if you change `scripts/build_tool_data.py` —
`app/tools/tickets.json` and `services.json` are committed, so a fresh clone
can run `make toolcheck` directly.

20 queries, 3 runs each. Needs **at least 58/60** valid first-attempt tool
calls to proceed. It exits non-zero below that and prints every failure with
its reason.

## The UI

Open `http://<host>/` — Streamlit, one page. Pick a stage from the dropdown,
ask a question, and thumbs up/down each answer. The trace ID is shown next to
every response so it can be pasted into Phoenix by hand.

A thumb posts to `POST /v{n}/feedback`, which writes a `user_feedback`
annotation onto that response's trace. The UI never talks to Phoenix itself —
the app does the write, inside a traced process, so the annotation gets its
own `write_feedback` span.

## Pipeline

`.github/workflows/deploy.yml`, four jobs:

| Job | Trigger | What it does |
|---|---|---|
| `test` | every PR and push | install, `ruff`, fast tests |
| `build` | push to `main` | build the app image, tag it with the commit SHA, push to GHCR |
| `deploy` | after build | SSH to the instance, pull that SHA, restart **`chat-agents` only**, smoke test |
| `eval` | after deploy | score the deployed Stage 3; non-zero exit fails the job |

The app services carry both `image:` and `build:`. Locally `up --build`
builds and tags; in CI the deploy step sets `CHAT_APP_IMAGE` to the
SHA-pinned registry tag so `up` uses the pulled image instead of building on
the box.

**Secrets required** before this can run: `GPU_SSH_KEY`, `GPU_HOST_KEY`,
`GPU_HOST`, `GPU_USER`. Use a dedicated deploy key, not a personal one.

The `deploy` job carries a long comment marked to read out loud: it
authenticates with a long-lived SSH private key in repository secrets, which
does not expire, grants shell access rather than one permission, and leaves
no per-run audit trail. The `build` job right above it shows the contrast —
`secrets.GITHUB_TOKEN` is minted per run and expires with the job.

## Cost, measured

`make cost` sweeps concurrency on the real card and divides throughput into
the real hourly rate. Measured 2026-09-09 on an H100-80GB VM in IN2 at
INR 229.64/hour, Qwen3.8-27B-FP8, 256-token outputs:

| concurrent | tok/sec | median latency | USD / 1M output tokens |
|---|---|---|---|
| 1 | 76 | 1.09s | 9.54 |
| 4 | 203 | 1.52s | 3.57 |
| 8 | 434 | 1.77s | 1.67 |
| 16 | 793 | 1.96s | 0.91 |
| 32 | 1231 | 2.11s | 0.59 |

**16.2x more throughput from 1 to 32 concurrent, while median latency only
goes 1.09s to 2.11s.** That is continuous batching, and it is why self-hosting
is viable at all. It also means unit cost swings 16x on utilisation alone --
utilisation, not the hourly rate, decides what a token costs you.

Against a hosted rate of USD 0.60/1M this card reaches **0.98x at full
saturation** and is 16x worse when idle. So self-hosting breaks even only at
close to 100% utilisation. Set `HOSTED_COMPARISON` in
`scripts/cost_report.py` to a rate you have actually checked, and name the
model on screen -- the verdict depends entirely on which model you compare to.

One consequence worth stating at 0:58: a Stage 3 request makes its model
calls **sequentially**, so a single user's request is a batch of one and pays
the ~USD 9.54 rate, not the 0.59 one. Batching only helps when many users are
asking at once.

## Evaluation

Two halves of the 1:13 lesson, deliberately separate:

- `make test` — the predictable things, asserted. 55 tests, under a second.
- `make eval` — the unpredictable things, scored. Posts to the real deployed
  endpoint, judges with the real model, exits non-zero below a threshold set
  in `evals/run_eval.py`.

The same dataset against different stages shows the gate is real:

| Target | Average | Normalised | Gate |
|---|---|---|---|
| Stage 3 (`v3`) | 5.00/5 | 100% | PASS, exit 0 |
| Stage 1 (`v1`) | ~2.3/5 | ~31–34% | FAIL, exit 1 |

`make dataset` turns thumbs-downed traces into `evals/datasets/from_feedback.json`.
Note that only feedback collected **after** the root span carried
`input.value` can be recovered — earlier annotations have no question to
score and are skipped.

## Routes

Served by Caddy on port 80 once step 3 lands. Nothing but `vllm` is up yet.

| Route | Service | Port | Stage |
|---|---|---|---|
| `/v1/*` | `chat-v1` | 8101 | 1 — plain chatbot **(live)** |
| `/v2/*` | `chat-rag` | 8102 | 2 — RAG **(live)** |
| `/v3/*` | `chat-agents` | 8103 | 3 — multi-agent **(live)** |
| `/traces` | `phoenix` | 6006 | tracing UI **(live)** |
| `/` | `ui` | 8501 | Streamlit **(live)** |
| — | `vllm` | 8000 | model server, published directly |
| — | `qdrant` | 6333 | vector database, its own container and volume |

## Make targets

| Target | What it does |
|---|---|
| `make up` / `make down` | Bring the stack up or down |
| `make logs` | Follow the vLLM logs (weight loading, tokens/sec) |
| `make fetch` | Download the pinned source dataset into `data/` |
| `make data` | Rebuild the committed tool data from `data/` |
| `make toolcheck` | The 60-run tool-calling gate |
| `make test` | Fast test suite — 46 tests, under a second |
| `make guardeval` | Score `input_guard` against the PII answer key |
| `make corpus` | Rebuild the 42 KB articles from `data/` |
| `make index` | Index the corpus into Qdrant — the one manual step |
| `make dataset` | Build a dataset from thumbs-downed traces |
| `make eval` | Score the deployed pipeline; exits non-zero below threshold |
| `make lint` | ruff check + format check, as CI runs them |
| `make cost` | Sweep concurrency and price a million tokens |
| `make smoke` | 23 assertions across all three stages and the guards |

## Use case

An **internal IT support assistant**, the spec's stated default. Three tools:

| Tool | Backed by | Returns |
|---|---|---|
| `lookup_ticket(ticket_id)` | `app/tools/tickets.json` | Root cause and resolution steps for one past incident |
| `check_service_status(service_name)` | `app/tools/services.json` | Current state, plus real incident counts |
| `search_kb(query)` | `corpus/` via the vector DB | Knowledge-base passages (step 6) |

Both JSON files are generated from a pinned revision of
[`ameau01/synthetic-it-support-tickets`](https://huggingface.co/datasets/ameau01/synthetic-it-support-tickets)
(MIT) and committed, so the containers make no network call at runtime. See
[`ATTRIBUTION.md`](ATTRIBUTION.md) for provenance, licensing, and the two
things about this data worth saying out loud during the session.

The corpus (step 6) will be 30–50 markdown KB articles built from the same
source — the dataset has 14 issue families and, for instance, 26 incidents
sharing the title "GlobalProtect VPN disconnects immediately", so retrieval has
genuine near-duplicate documents to get wrong.

## Cost

**Pause the instance after every single session.** An A100 left running
overnight costs about $36 — more than the entire planned spend. Retained
storage keeps billing while paused, so tear the filesystem down when the
session is over.
