"""Load corpus/*.md into the vector database. Run once.

This is the only manual step after `docker compose up`. It is deliberately
separate: indexing is not something you want happening on every container
start, and the index outliving the containers is the whole point of Stage 2.

Embedding runs on CPU through ONNX, so the GPU stays free for generation.

    python scripts/index_corpus.py
"""

import os
import sys
import uuid
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "corpus"

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "it-kb")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Articles are short -- roughly 3KB. One vector per article keeps the
# retrieval span readable on stage: a document comes back, not fragment 7 of
# 12. Chunking would be the right call on a real corpus; say so out loud.
CHUNK_PER_FILE = 1


def read_articles() -> list[tuple[str, str]]:
    """Return (filename, text) for every article, skipping SOURCES.md."""
    if not CORPUS_DIR.exists():
        sys.exit("corpus/ does not exist. Run: python scripts/build_corpus.py")
    files = sorted(p for p in CORPUS_DIR.glob("*.md") if p.name != "SOURCES.md")
    if not files:
        sys.exit("corpus/ has no articles. Run: python scripts/build_corpus.py")
    return [(p.name, p.read_text()) for p in files]


def main() -> None:
    articles = read_articles()
    print(f"Read {len(articles)} articles from corpus/")

    embedder = TextEmbedding(model_name=EMBED_MODEL)
    vectors = list(embedder.embed([text for _, text in articles]))
    dimension = len(vectors[0])
    print(f"Embedded with {EMBED_MODEL} on CPU, {dimension} dimensions")

    client = QdrantClient(url=QDRANT_URL, timeout=60)

    # Recreate rather than upsert into whatever was there. Indexing twice with
    # a changed corpus otherwise leaves orphaned documents that retrieval can
    # still return, which is a confusing thing to debug on stage.
    if client.collection_exists(COLLECTION):
        print(f"Collection {COLLECTION!r} exists, deleting it first")
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            # A stable ID derived from the filename, so re-indexing the same
            # article does not create a second copy of it.
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, name)),
            vector=vector.tolist(),
            payload={
                "source": name,
                "title": text.splitlines()[0].lstrip("# ").strip(),
                "text": text,
            },
        )
        # strict: a length mismatch here would silently drop documents
        # from the index, which is the worst kind of bug to debug on stage.
        for (name, text), vector in zip(articles, vectors, strict=True)
    ]
    client.upsert(collection_name=COLLECTION, points=points, wait=True)

    count = client.count(COLLECTION, exact=True).count
    print(f"Indexed {count} documents into {QDRANT_URL} collection {COLLECTION!r}")
    if count != len(articles):
        sys.exit(f"Expected {len(articles)} documents, found {count}.")


if __name__ == "__main__":
    main()
