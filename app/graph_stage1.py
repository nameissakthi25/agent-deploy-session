"""Stage 1: no graph at all. One model call and a dictionary, no tools.

Deliberately boring. The interesting part of Stage 1 is not the chatbot, it is
what happens when you try to put it in front of people -- where state goes,
where the keys live, and who can reach which port.

CONVERSATIONS below is the whole lesson. It is a module-level dictionary: the
wrong place for conversation state, chosen on purpose. It is gone when the
container restarts, and it is not shared if you ever run two copies. Restart
chat-v1 mid-conversation and watch the history vanish -- that is the 0:18
demo, and it needs the state to exist before it can be destroyed.
"""

from openai import OpenAI

from app.llm import chat

SYSTEM_PROMPT = (
    "You are an internal IT support assistant. Answer in at most three "
    "sentences. If you do not know something, say so plainly. "
    # Without this line the model answers "I cannot store information between
    # conversations" even though the history is right there in the prompt --
    # and then reads its own denial back on the next turn and repeats it.
    # Measured: turn two received four input messages and still claimed to
    # have none. The 0:18 demo depends on the model actually using history.
    "You can see the conversation so far in this request. Use it: if the user "
    "told you something earlier in the conversation, refer back to it."
)

# Conversation history, keyed by session. In a process, in a variable.
#
# This is what a prototype does and what a product must not: it dies with the
# process, it is invisible to a second copy of this container, and it grows
# without limit. Where it would have to live instead is a database or a cache
# outside the container -- which is exactly the move Stage 2 makes with the
# vector index.
CONVERSATIONS: dict[str, list[dict]] = {}

# How many previous turns to send back to the model. A cap, because the
# history goes into the prompt and the prompt costs tokens.
MAX_HISTORY_TURNS = 6


def run(client: OpenAI, message: str, session_id: str = "default") -> str:
    """Answer one message, remembering the session -- until a restart."""
    history = CONVERSATIONS.setdefault(session_id, [])

    response = chat(
        client,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *history[-(MAX_HISTORY_TURNS * 2) :],
            {"role": "user", "content": message},
        ],
        thinking=False,
    )
    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        raise RuntimeError("The model returned an empty answer.")
    answer = answer.strip()

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})
    return answer
