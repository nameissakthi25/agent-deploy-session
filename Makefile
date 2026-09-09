# Targets used during the session. Everything else is one docker compose up.

.PHONY: up down logs applogs uilogs reload-proxy fetch data corpus toolcheck routecheck cost chat test guardeval index dataset eval smoke lint

# Bring up the stack. At this point in the build that is the model server only.
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f vllm

applogs:
	docker compose logs -f chat-v1

uilogs:
	docker compose logs -f ui

# Editing docker/Caddyfile alone does NOT restart Caddy -- it is a bind
# mount, not part of the image. Use this after changing routes.
reload-proxy:
	docker compose restart caddy

traces:
	@echo "Phoenix: http://localhost:6006  (or /traces through the proxy)"

# One request through the proxy, the way the session does it live.
chat:
	curl -s -X POST http://localhost/v1/chat \
	  -H 'Content-Type: application/json' \
	  -d '{"message":"How do I reset my password?"}'

# Download the pinned source dataset into data/ (git-ignored).
fetch:
	python3 scripts/fetch_dataset.py

# Rebuild the committed tool data from data/. Fetches first if data/ is empty.
data:
	python3 scripts/build_tool_data.py

# Measures whether the supervisor sends questions to the right worker.
# Real model, no stubs. Run after toolcheck passes.
routecheck:
	python3 scripts/routing_check.py

# Sweeps concurrency on the real card and does the cost-per-token
# arithmetic. This is the 0:04 segment, measured rather than quoted.
cost:
	python3 scripts/cost_report.py

lint:
	ruff check app ui scripts evals tests
	ruff format --check app ui scripts evals tests

# Rebuild the 42 knowledge-base articles from data/.
corpus:
	python3 scripts/build_corpus.py

# The go/no-go gate: 20 queries x 3 runs, needs 58/60 valid first-attempt
# tool calls. Run this before building anything downstream of the model.
toolcheck:
	python3 scripts/toolcall_check.py

# --- not built yet; see build-spec.md section 13 for the order --------------

test:
	pytest tests/

# Scores input_guard against the dataset's authored PII answer key. Not part
# of the fast suite -- it reads the raw corpus in data/.
guardeval:
	python3 evals/guard_eval.py

# The one manual step after `docker compose up`. Run it once; the index
# outlives the containers, which is the Stage 2 lesson.
index:
	QDRANT_URL=http://localhost:6333 python3 scripts/index_corpus.py

# Scores the deployed Stage 3 pipeline against a dataset. Exits non-zero
# below the threshold in the file -- this is the release gate CI uses.
eval:
	python3 evals/run_eval.py

# Builds a dataset from thumbs-downed traces in Phoenix.
dataset:
	python3 evals/dataset.py

# Hits all three stages, the guards, and the proxy routes. Fast, all hard
# assertions. Runs after a deploy and before the eval.
smoke:
	python3 scripts/smoke_test.py
