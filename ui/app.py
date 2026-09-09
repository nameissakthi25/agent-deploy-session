"""Streamlit UI. One page, deliberately plain.

Its only interesting feature is the thumbs control: clicking either button
writes an annotation onto that response's trace in Phoenix, which is what
turns real complaints into an eval dataset at 1:33.

The trace ID is shown next to every response on purpose, so it can be pasted
into Phoenix's search box by hand during the session.
"""

import os

import httpx
import streamlit as st

# Where to send requests. Through Caddy, exactly as a user would reach it --
# so the UI exercises the same path the room sees.
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://caddy:80")
# Phoenix as reached from the viewer's browser, for the clickable link.
PHOENIX_PUBLIC_URL = os.environ.get("PHOENIX_PUBLIC_URL", "/traces")

STAGES = {
    "v1 - plain chatbot": ("v1", 1),
    "v2 - RAG": ("v2", 2),
    "v3 - multi-agent": ("v3", 3),
}


def ask(route: str, message: str) -> dict:
    """Post one message to one stage through the proxy."""
    response = httpx.post(
        f"{GATEWAY_URL}/{route}/chat",
        json={"message": message},
        # Generous: a Stage 3 request fans out into roughly a dozen model
        # calls on a single GPU.
        timeout=300.0,
    )
    if response.status_code >= 400:
        detail = response.json().get("detail", response.text)
        return {"error": detail, "status": response.status_code}
    return response.json()


def send_feedback(turn: dict, route: str, helpful: bool) -> None:
    """Ask the app to attach a thumb to this response's trace.

    The UI does not talk to Phoenix. It hands back the trace ID it was given
    and lets the app -- which is already traced -- do the write.
    """
    try:
        response = httpx.post(
            f"{GATEWAY_URL}/{route}/feedback",
            json={"trace_id": turn["trace_id"], "helpful": helpful},
            timeout=30.0,
        )
        response.raise_for_status()
        turn["feedback"] = "👍 helpful" if helpful else "👎 not helpful"
    except Exception as error:
        turn["feedback_error"] = str(error)


st.set_page_config(page_title="IT support assistant", layout="centered")
st.title("Internal IT support assistant")

label = st.selectbox("Which version are you talking to?", list(STAGES))
route, stage = STAGES[label]
st.caption(f"POST {GATEWAY_URL}/{route}/chat")

if "turns" not in st.session_state:
    st.session_state.turns = []

question = st.chat_input("Ask about a ticket, a service, or IT policy")
if question:
    with st.spinner("thinking..."):
        result = ask(route, question)
    st.session_state.turns.append(
        {"question": question, "stage": stage, "route": route, **result}
    )

for index, turn in enumerate(st.session_state.turns):
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        if "error" in turn:
            # A guardrail rejection lands here. Shown rather than hidden --
            # the point is that the system said no, and why.
            st.error(f"{turn['status']}: {turn['error']}")
            continue

        st.write(turn["answer"])

        trace_id = turn.get("trace_id")
        if not trace_id:
            st.caption("no trace id returned")
            continue

        st.caption(f"stage {turn['stage']} · trace `{trace_id}`")

        if turn.get("feedback"):
            st.success(f"recorded: {turn['feedback']}")
        elif turn.get("feedback_error"):
            st.warning(f"could not record feedback: {turn['feedback_error']}")
        else:
            # Icons rather than words: the text labels were wide enough to be
            # truncated to "thu..." in these columns, which is worse than no
            # label at all. help= carries the meaning for anyone hovering or
            # using a screen reader.
            up, down, link = st.columns([1, 1, 10])
            up.button(
                "👍",
                key=f"up-{index}",
                help="This answer was helpful",
                on_click=send_feedback,
                args=(turn, turn["route"], True),
            )
            down.button(
                "👎",
                key=f"down-{index}",
                help="This answer was not helpful",
                on_click=send_feedback,
                args=(turn, turn["route"], False),
            )
            link.markdown(f"[open in Phoenix]({PHOENIX_PUBLIC_URL})")
