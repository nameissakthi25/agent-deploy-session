"""The worker that writes the final answer.

The one place thinking is left on. It has the retrieved documents and any
tool results in front of it and has to turn them into something a person can
read, which is worth some reasoning. It is also on nobody's tool allowlist --
see TOOL_ALLOWLIST in app/guards/tool_guard.py -- so it cannot reach for a
tool no matter what it decides it wants.
"""

import json

from openai import OpenAI

from app.llm import chat

SYSTEM_PROMPT = (
    "You are the writer of an IT support system. Answer the user's question "
    "in at most four sentences using only the evidence below. Cite knowledge "
    "base articles by their source filename in brackets. If a tool call was "
    "refused, or the evidence does not answer the question, say so plainly."
)


def format_evidence(documents: list[dict], tool_results: list[dict]) -> str:
    """Lay the evidence out for the model, tools first then articles."""
    parts = []
    for entry in tool_results:
        if "rejected" in entry:
            parts.append(
                f"Tool {entry['tool']} was REFUSED by the tool guard: {entry['rejected']}"
            )
        else:
            parts.append(
                f"Tool {entry['tool']} returned: {json.dumps(entry['result'])[:1500]}"
            )
    for document in documents:
        parts.append(f"[{document['source']}] {document['text']}")
    return "\n\n---\n\n".join(parts) if parts else "No evidence was gathered."


def run(
    client: OpenAI, message: str, documents: list[dict], tool_results: list[dict]
) -> str:
    """Write the answer. Thinking on, at low effort."""
    response = chat(
        client,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Evidence:\n\n{format_evidence(documents, tool_results)}"
                    f"\n\nQuestion: {message}"
                ),
            },
        ],
        # The only node with thinking on. Low effort, not the xhigh default:
        # enough to compose an answer, not enough to make the trace unreadable.
        thinking=True,
        reasoning_effort="low",
        max_tokens=1024,
    )
    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        raise RuntimeError("The synthesizer returned an empty answer.")
    return answer.strip()
