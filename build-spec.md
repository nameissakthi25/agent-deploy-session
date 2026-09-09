# Build Spec — Session Demo Repo

**For:** Claude Code
**Goal:** A working self-hosted multi-agent stack that runs three versions of one app side by side on a single GPU box, used to teach production deployment in a 2-hour session.
**Target machine:** One JarvisLabs A100 80GB instance, Ubuntu, Docker and Docker Compose installed.

---

## 1. What we are building

One repository that produces:

- A model server (vLLM) serving an open model with an OpenAI-compatible API
- Three versions of the same application, running at the same time, each in its own container:
  - **Stage 1** — plain chatbot, one model call, no memory
  - **Stage 2** — RAG chatbot, retrieving from an external vector database
  - **Stage 3** — multi-agent system, a supervisor routing to three workers
- A tracing service (Phoenix) collecting traces from all three
- A reverse proxy routing to all three plus the UI
- A Streamlit UI with a thumbs up/down control
- A test suite, an eval runner, and a GitHub Actions pipeline

All three app versions come from **one image**. A `STAGE` environment variable decides which graph gets built at startup. Do not create separate branches or tags for the three stages.

## 2. Ground rules

Follow these strictly. They matter more than elegance.

- **Pin every dependency to an exact version.** No ranges, no "latest". A resolver surprise on the day of the session cannot be recovered from.
- **Everything must run from one `docker compose up`.** No manual steps after that, other than indexing the corpus once.
- **No cleverness.** This code gets read aloud to a room. Prefer obvious over short. A function that does one plain thing beats a compact expression.
- **No abstraction layers that hide the lesson.** For example, do not wrap the guardrails in a decorator framework — the point is that a learner can read the guard function and see exactly what it checks.
- **Every file under 200 lines.** If it grows past that, split it.
- **Fail loudly at startup.** If a required environment variable is missing, or the model server is unreachable, crash with a clear message rather than failing on the first request.

## 3. The use case

> **DECIDE BEFORE BUILDING.** This determines the document corpus and the tools the agents call. Replace this section.
>
> **Default if not replaced:** an internal IT support assistant. Corpus is 30–50 short markdown documents covering company IT policy, VPN setup, password resets, laptop requests, and software approvals. Tools are: `lookup_ticket(ticket_id)`, `check_service_status(service_name)`, and `search_kb(query)` — all backed by a small local fake data file, no external API needed.

The default is chosen because it needs no real external service, the answers are checkable by anyone in the room, and the tools are easy to describe in one sentence each. If you swap it, keep those three properties.

## 4. Repository layout

```
agent-deploy-session/
  compose.yaml
  .env.example
  Makefile
  README.md
  requirements.txt          # pinned, exact versions

  app/
    config.py               # reads env, validates on import, crashes if missing
    llm.py                  # OpenAI-compatible client pointed at vLLM
    observability.py        # Phoenix setup, ~10 lines
    schemas.py              # Pydantic models for request and response
    api.py                  # FastAPI, one /chat endpoint, one /health endpoint
    graph_stage1.py         # no graph, direct model call
    graph_stage2.py         # retrieve, then answer
    graph_stage3.py         # LangGraph supervisor + 3 workers
    agents/
      retriever.py
      tool_agent.py
      synthesizer.py
    guards/
      input_guard.py
      tool_guard.py
      output_guard.py
    tools/
      definitions.py        # tool schemas passed to the model
      handlers.py           # what each tool actually does
      fake_data.py          # local data the tools read

  ui/
    app.py                  # Streamlit, chat + thumbs control

  scripts/
    index_corpus.py         # one-time, loads corpus into vector DB
    toolcall_check.py       # the 60-run tool-calling reliability test
    smoke_test.py           # hits all three stages, exits non-zero on failure

  tests/
    conftest.py
    test_input_guard.py
    test_tool_guard.py
    test_output_guard.py
    test_schemas.py
    test_routing.py         # stubbed model, asserts which worker is picked

  evals/
    dataset.py              # pulls negatively-annotated traces from Phoenix
    run_eval.py             # scores a dataset, exits non-zero below threshold

  docker/
    Dockerfile.app
    Dockerfile.ui
    Caddyfile

  corpus/
    *.md                    # the document set

  .github/workflows/
    deploy.yml
```

## 5. Compose services

| Service | Image | Port | Notes |
|---|---|---|---|
| `vllm` | official vLLM image | 8000 | GPU access, model and parser flags, healthcheck |
| `chat-v1` | built from `Dockerfile.app` | 8101 | `STAGE=1` |
| `chat-rag` | same image | 8102 | `STAGE=2` |
| `chat-agents` | same image | 8103 | `STAGE=3` |
| `phoenix` | official Phoenix image | 6006 | persist to a named volume |
| `ui` | built from `Dockerfile.ui` | 8501 | |
| `caddy` | official Caddy image | 80 | routes below |

The three app services must `depends_on` the `vllm` service with `condition: service_healthy`. They will start before the model finishes loading otherwise, and crash.

Caddy routes:

```
/v1/*   -> chat-v1:8101
/v2/*   -> chat-rag:8102
/v3/*   -> chat-agents:8103
/traces -> phoenix:6006
/        -> ui:8501
```

## 6. Model server

- Model: **Qwen3-32B**
- Serve with vLLM, tool calling enabled, using the Hermes tool parser
- FP8 if it loads cleanly, otherwise BF16
- Set the GPU memory fraction so there is real KV cache headroom left — Stage 3 fans out into roughly a dozen concurrent calls and will run out otherwise
- Set a max context that comfortably fits the RAG prompt plus history
- **Thinking mode must be off for the supervisor node.** A supervisor that reasons at length before every routing decision makes every trace unreadable and every response slow. Leave it on for the synthesizer only.

Put every one of these flags in `compose.yaml` with a short comment explaining what it does. This file gets shown on screen.

## 7. Guardrails

Three separate files, three separate jobs. Each guard is a plain function taking input and returning either the value or raising a specific exception. No shared base class.

**`input_guard.py`** — runs before anything else.
- Reject inputs over a set character length
- Reject on a list of injection phrases (keep the list in the file, visible, about 15 entries)
- Reject on regex matches for email addresses, phone numbers, and card-shaped digit strings
- Raise `InputRejected(reason)`

**`tool_guard.py`** — runs before every single tool call.
- Takes the calling agent's name, the tool name, and the arguments
- Checks the tool is in that agent's allowlist. The allowlist is a plain dictionary mapping agent name to a list of tool names.
- Validates arguments against a Pydantic model for that tool
- Raise `ToolCallRejected(agent, tool, reason)`

This is the most important guard in the session. Make it the clearest file in the repo.

**`output_guard.py`** — runs before the response is returned.
- Validates the response against the Pydantic response schema
- Runs one cheap model call asking whether the response violates a short policy, kept as a visible constant in the file
- Raise `OutputRejected(reason)`

**All three rejections must appear as spans in the trace**, with the reason as a span attribute. This is demonstrated live, so it has to work.

## 8. Tracing

`observability.py` should be about ten lines: register Phoenix, turn on auto-instrumentation, done. Do not write custom span code for the model calls or the graph — the instrumentation handles those.

Do add explicit spans for the three guardrail rejections, and for the thumbs up/down annotation write.

Each response from `/chat` must return its trace ID so the UI can attach feedback to it.

## 9. Tests

Split by whether the thing is predictable.

**Fast tests — no model calls, must finish in under 20 seconds total.** This speed is demonstrated live, so keep it true.
- Guardrails: table-driven, a list of input/expected-outcome pairs, one test function per guard
- Schemas: valid and invalid examples
- Routing: stub the model client to return a fixed tool call, then assert the supervisor picks the expected worker. This needs the graph to accept an injected client — design for that.

**Eval runner — separate, not part of the fast suite.**
- Takes a dataset of question/expected-behaviour pairs
- Runs the full Stage 3 path
- Scores with a model-based judge
- Prints a per-example table and an average
- Exits non-zero if the average falls below a threshold set in the file

## 10. CI pipeline

`.github/workflows/deploy.yml`:

1. On pull request: install, lint, run the fast tests
2. On push to main: run the fast tests, build the app image, tag it with the commit SHA, push to a registry
3. Then SSH to the instance, pull the new image, and restart `chat-agents` only
4. Then run `scripts/smoke_test.py` against it
5. Then run `evals/run_eval.py` and fail the job if the score is below threshold

Authentication uses an API key and an SSH key stored in GitHub secrets. **Add a comment in the workflow file saying this is a compromise** — on a managed cloud you would use short-lived credentials issued per run, with no permanent key stored anywhere. This comment gets read aloud during the session.

## 11. UI

Streamlit, one page, deliberately plain.

- A dropdown to pick which stage to talk to (v1, v2, v3)
- A text input and a conversation display
- Thumbs up and thumbs down buttons under each response
- Pressing either one writes an annotation to that response's trace in Phoenix
- Show the trace ID next to each response, so it can be found by hand during the session

## 12. Acceptance criteria

The build is done when all of these pass. Check them in order.

**Setup**
- [ ] `docker compose up` brings up all seven services with no manual intervention
- [ ] `compose.yaml` has a comment on every non-obvious flag
- [ ] Missing environment variables cause a crash at startup with a clear message, not a failure on first request
- [ ] `scripts/index_corpus.py` runs once and populates the external vector database

**Stage 1**
- [ ] `POST /v1/chat` returns an answer and a trace ID
- [ ] Restarting `chat-v1` loses conversation state, visibly
- [x] One trace appears in Phoenix, small enough to read at a glance.
      Now **five** spans, not three: the guardrails emit a span per
      invocation rather than only on refusal, so a request that passes
      still shows they ran. The original three-span target predates the
      output guard's judge call.

**Stage 2**
- [ ] `POST /v2/chat` returns an answer grounded in the corpus
- [ ] The trace contains a retrieval span showing which documents came back
- [ ] Rebuilding the image after a code-only change takes under 15 seconds, because the dependency layer is cached

**Stage 3**
- [ ] `POST /v3/chat` returns an answer after routing through the supervisor
- [ ] The trace shows the supervisor and all worker nodes as named, nested spans
- [ ] `scripts/toolcall_check.py` runs 20 queries 3 times each and reports at least 58/60 valid first-attempt tool calls
- [ ] Sending a malformed tool argument produces a `ToolCallRejected` span, and the run does not crash

**Guardrails**
- [ ] Three prepared inputs each trip exactly one guard, and no others
- [ ] All three rejections appear as spans with a readable reason attribute

**Tests and CI**
- [ ] `pytest tests/` finishes in under 20 seconds and passes
- [ ] `evals/run_eval.py` runs, prints a table, and exits non-zero when below threshold
- [ ] The pipeline runs green end to end at least twice

**Feedback loop**
- [ ] A thumbs down in the UI writes an annotation onto the correct trace
- [ ] `evals/dataset.py` can pull negatively-annotated traces and turn them into a dataset
- [ ] Running an eval on that dataset produces a score

## 13. Build order

Do not build the whole thing and then test it. Get each step working before starting the next.

1. `compose.yaml` with just vLLM. Confirm the model serves and answers a curl request.
2. **Run `toolcall_check.py` immediately.** If tool calling is unreliable, everything downstream is wasted work. This is the highest-risk item in the build — find out now, not in three days.
3. Stage 1 app + Caddy. Confirm a request works through the proxy.
4. Phoenix + `observability.py`. Confirm one trace arrives.
5. Guardrails, with their tests.
6. Stage 2 + corpus indexing.
7. Stage 3 + tool guard.
8. UI + feedback writing.
9. Eval runner.
10. CI pipeline.
11. `smoke_test.py`, then run the full acceptance list.

## 14. Do not build

- Authentication or user accounts
- A database for conversation history
- Streaming responses
- Any Kubernetes or Helm anything
- Weighted routing or canary deployment — this is explained on a whiteboard during the session, not built
- A settings page, admin panel, or anything configurable at runtime
- Retry logic beyond a single retry on the model call
- Anything not listed in section 4

## 15. Also produce

- `README.md` with setup steps, the compose command, and a table of the routes
- `Makefile` with targets: `up`, `down`, `test`, `index`, `toolcheck`, `eval`, `smoke`
- `.env.example` listing every variable with a comment on each
