"""Retrieval against the vector database.

Used by Stage 2 directly and by the Stage 3 retriever worker. The application
holds a connection string and nothing else -- it has no idea where the index
physically lives, which is the point of moving it out of the container.

The retrieval span here is hand-written, because the instrumentation cannot
see it: Qdrant is not the OpenAI client. It follows the OpenInference
retriever conventions so Phoenix renders it as a retrieval step with the
documents listed, which is what the 0:40 segment reads on screen.
"""

from functools import lru_cache

from fastembed import TextEmbedding
from opentelemetry import trace
from qdrant_client import QdrantClient

from app.config import EMBED_MODEL, QDRANT_COLLECTION, require_qdrant_url

DEFAULT_LIMIT = 4

_tracer = trace.get_tracer(__name__)


@lru_cache(maxsize=1)
def _embedder() -> TextEmbedding:
    """Built once. Loading the ONNX model takes a second or two."""
    return TextEmbedding(model_name=EMBED_MODEL)


@lru_cache(maxsize=1)
def _client() -> QdrantClient:
    return QdrantClient(url=require_qdrant_url(), timeout=30)


def search(query: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Return the closest articles as dicts of source, title, text and score."""
    with _tracer.start_as_current_span("retrieve") as span:
        # Marks this as a retrieval step rather than a generic span, so
        # Phoenix shows the documents in its retrieval view.
        span.set_attribute("openinference.span.kind", "RETRIEVER")
        span.set_attribute("input.value", query)
        span.set_attribute("retrieval.limit", limit)

        vector = list(_embedder().embed([query]))[0].tolist()
        hits = (
            _client()
            .query_points(collection_name=QDRANT_COLLECTION, query=vector, limit=limit)
            .points
        )

        documents = [
            {
                "source": hit.payload["source"],
                "title": hit.payload["title"],
                "text": hit.payload["text"],
                "score": hit.score,
            }
            for hit in hits
        ]

        for index, document in enumerate(documents):
            prefix = f"retrieval.documents.{index}.document"
            span.set_attribute(f"{prefix}.id", document["source"])
            span.set_attribute(f"{prefix}.score", document["score"])
            span.set_attribute(f"{prefix}.content", document["text"])
            # Duplicated as a short attribute so the span list is readable
            # without expanding each document.
            span.set_attribute(f"retrieval.documents.{index}.title", document["title"])

        span.set_attribute("retrieval.document_count", len(documents))
        return documents
