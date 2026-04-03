"""Cross-encoder reranker for selecting top-N chunks from retrieved candidates."""

from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import settings
from app.rag.retriever import RetrievedChunk


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """Load and cache the cross-encoder model (called once on startup)."""
    return CrossEncoder(settings.reranker_model)


def rerank(query: str, chunks: list[RetrievedChunk], top_n: int | None = None) -> list[RetrievedChunk]:
    """Score each (query, chunk) pair with the cross-encoder; return top_n sorted by score."""
    if not chunks:
        return []

    n = top_n or settings.rerank_top_n
    model = get_reranker()
    pairs = [[query, chunk.content] for chunk in chunks]
    scores: list[float] = model.predict(pairs).tolist()  # type: ignore[union-attr]

    scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:n]]
