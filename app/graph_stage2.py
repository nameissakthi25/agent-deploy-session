"""Stage 2: retrieve, then answer. Still no graph, still no tools.

The room already knows RAG. The only new thing here is a deployment lesson:
the index cannot live inside the container, so it moved out, and the app now
holds a connection string instead of a filesystem path.

The one thing worth reading on screen is the trace: there is a retrieval step
in it now, showing which documents came back. For the first time you can check
whether the answer came from the documents or whether the model filled the gap
itself.
"""

from openai import OpenAI

from app.agents.retriever import search
from app.llm import chat

SYSTEM_PROMPT = (
    "You are an internal IT support assistant. Answer using ONLY the "
    "knowledge base articles provided. Cite the source filename of each "
    "article you use, in brackets. If the articles do not answer the "
    "question, say so plainly rather than guessing."
)

USER_TEMPLATE = """Knowledge base articles:

{context}

Question: {question}"""


def build_context(documents: list[dict]) -> str:
    """Format retrieved articles for the prompt, source filename first."""
    return "\n\n---\n\n".join(
        f"[{document['source']}] {document['text']}" for document in documents
    )


def run(client: OpenAI, message: str) -> str:
    """Retrieve, then answer from what came back."""
    documents = search(message)
    if not documents:
        return (
            "I could not find anything in the knowledge base for that. "
            "The index may not have been built -- see scripts/index_corpus.py."
        )

    response = chat(
        client,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_TEMPLATE.format(
                    context=build_context(documents), question=message
                ),
            },
        ],
        thinking=False,
        max_tokens=1024,
    )
    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        raise RuntimeError("The model returned an empty answer.")
    return answer.strip()
