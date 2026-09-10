"""Environment configuration, validated at import time.

Every value the app needs is read and checked here, when the module is first
imported. A missing or nonsensical variable crashes the container at startup
with a message naming the variable -- not on the first request, which is the
failure mode that wastes ten minutes of a live session.
"""

import os
import sys


def _require(name: str, hint: str) -> str:
    """Read a required variable, or exit with a message naming it."""
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"FATAL: {name} is not set. {hint}")
    return value


def _require_stage() -> int:
    """Read STAGE. One image serves all three stages; this picks which."""
    raw = _require(
        "STAGE",
        "Set STAGE to 1 (plain chatbot), 2 (RAG) or 3 (multi-agent). "
        "It is set per service in compose.yaml.",
    )
    if raw not in {"1", "2", "3"}:
        sys.exit(f"FATAL: STAGE must be 1, 2 or 3. Got {raw!r}.")
    return int(raw)


def _require_port() -> int:
    """Read the port this app listens on inside its container."""
    raw = _require("APP_PORT", "Set APP_PORT, e.g. 8101 for chat-v1.")
    if not raw.isdigit():
        sys.exit(f"FATAL: APP_PORT must be a number. Got {raw!r}.")
    return int(raw)


STAGE = _require_stage()
APP_PORT = _require_port()

VLLM_BASE_URL = _require(
    "VLLM_BASE_URL",
    "Set it to the vLLM OpenAI-compatible endpoint, "
    "e.g. http://vllm:8000/v1 from inside another container.",
)

MODEL_NAME = _require(
    "MODEL_NAME",
    "Set it to the name vLLM was started with via --served-model-name.",
)

# vLLM needs no key, but the OpenAI client refuses to construct without one.
VLLM_API_KEY = os.environ.get("VLLM_API_KEY", "not-needed")

PHOENIX_COLLECTOR_ENDPOINT = _require(
    "PHOENIX_COLLECTOR_ENDPOINT",
    "Set it to the Phoenix OTLP traces endpoint, "
    "e.g. http://phoenix:6006/v1/traces from inside another container.",
)

# Stages 2 and 3 retrieve; stage 1 does not, so this is only required when it
# is actually needed. Checked lazily by the retriever rather than at import,
# so chat-v1 does not demand a vector database it never uses.
QDRANT_URL = os.environ.get("QDRANT_URL", "").strip()
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "it-kb").strip()

# The embedding model. ONNX on CPU: embedding never touches the GPU, so the
# whole card stays available for generation.
EMBED_MODEL = os.environ.get("EMBED_MODEL", "BAAI/bge-small-en-v1.5").strip()


def require_qdrant_url() -> str:
    """Read QDRANT_URL, or exit. Called by the retriever, not at import."""
    if not QDRANT_URL:
        sys.exit(
            "FATAL: QDRANT_URL is not set, but STAGE "
            f"{STAGE} retrieves. Set it to e.g. http://qdrant:6333"
        )
    return QDRANT_URL


# Which input guard runs: "hand" (default) or "framework" (Guardrails AI).
# Both raise InputRejected with the same reason string, so nothing downstream
# changes. See app/guards/framework_guard.py and evals/guard_eval.py, which
# scores whichever ones are available.
GUARD_BACKEND = os.environ.get("GUARD_BACKEND", "hand").strip().lower()
if GUARD_BACKEND not in {"hand", "framework"}:
    sys.exit(
        f"FATAL: GUARD_BACKEND must be 'hand' or 'framework'. Got {GUARD_BACKEND!r}."
    )

# The Phoenix REST API, used to write thumbs up/down annotations. Distinct
# from the OTLP collector endpoint above: that one receives spans, this one
# takes annotations. Defaults to the collector endpoint with the OTLP path
# stripped, which is right whenever both are the same Phoenix.
PHOENIX_BASE_URL = os.environ.get(
    "PHOENIX_BASE_URL", PHOENIX_COLLECTOR_ENDPOINT.replace("/v1/traces", "")
).rstrip("/")

# All three stages report into one project, so their traces sit side by side
# and can be compared directly at 1:44.
PHOENIX_PROJECT_NAME = os.environ.get("PHOENIX_PROJECT_NAME", "it-support-assistant")
