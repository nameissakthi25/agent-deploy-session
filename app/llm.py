"""The model client, pointed at vLLM.

vLLM speaks the OpenAI protocol, so this is the ordinary OpenAI client with a
different base URL. Worth saying out loud during the session: nothing in the
application knows the model is self-hosted.

`chat()` takes the client as its first argument rather than reaching for a
global. That is what lets the routing tests inject a stub client and assert
which worker the supervisor picks without making a model call.
"""

import httpx
from openai import OpenAI

from app.config import MODEL_NAME, VLLM_API_KEY, VLLM_BASE_URL

# Qwen3.8 thinks by default at reasoning_effort=xhigh. Every call site must
# therefore opt out explicitly. These are the model card's recommended
# sampling parameters for each mode -- they differ, which is easy to miss.
NON_THINKING = {
    "temperature": 0.7,
    "top_p": 0.8,
    "presence_penalty": 1.5,
    "extra_body": {"top_k": 20},
}
THINKING = {
    "temperature": 1.0,
    "top_p": 0.95,
    "presence_penalty": 0.0,
    "extra_body": {"top_k": 20},
}


def make_client() -> OpenAI:
    """Build the client. Read the base URL once, at import of config."""
    return OpenAI(base_url=VLLM_BASE_URL, api_key=VLLM_API_KEY, timeout=120.0)


def assert_model_server_reachable() -> None:
    """Crash at startup if vLLM is not answering, rather than on request one.

    A plain HTTP GET rather than client.models.list(): the OpenAI client is
    instrumented, so calling it here would put a stray startup trace in
    Phoenix. The first trace the room sees should be a request they made.
    """
    url = VLLM_BASE_URL.rstrip("/") + "/models"
    try:
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
    except Exception as error:
        raise RuntimeError(
            f"Model server at {url} is not reachable: {error}. "
            "The app services depend_on vllm with condition: service_healthy, "
            "so seeing this usually means the healthcheck was bypassed."
        ) from error


def chat(
    client: OpenAI,
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_choice: str = "auto",
    thinking: bool = False,
    reasoning_effort: str = "low",
    max_tokens: int = 1024,
    temperature: float | None = None,
):
    """One chat completion.

    thinking=False is the default on purpose. Thinking is expensive, and a
    node that reasons at length before every decision makes the trace
    unreadable. The synthesizer is the one place it is turned on.
    """
    mode = THINKING if thinking else NON_THINKING
    # The model card's sampling values are tuned for generation. A call that
    # classifies rather than writes wants temperature 0 instead, so callers
    # can override it -- see the output guard's policy judge.
    sampling_temperature = mode["temperature"] if temperature is None else temperature
    extra_body = dict(mode["extra_body"])
    extra_body["chat_template_kwargs"] = {
        "enable_thinking": thinking,
        # Defaults to True, and retains the thinking blocks of every previous
        # message. That inflates the prompt badly once Stage 3 fans out.
        "preserve_thinking": False,
    }

    request = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": sampling_temperature,
        "top_p": mode["top_p"],
        "presence_penalty": mode["presence_penalty"],
        "max_tokens": max_tokens,
        "extra_body": extra_body,
    }
    if thinking:
        request["reasoning_effort"] = reasoning_effort
    if tools:
        request["tools"] = tools
        # "required" forces the model to call one of the offered tools. The
        # supervisor uses it: measured on the real model, a conversational
        # closer like "thanks, that's all" made it answer in prose instead of
        # routing, which then fell through to the default route.
        request["tool_choice"] = tool_choice

    return client.chat.completions.create(**request)
