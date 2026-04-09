"""Singleton wrapper around sentence-transformers for embedding text."""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


def estimate_tokens(text: str) -> int:
    """Approximate token count — 1 token ≈ 4 characters for English text."""
    return max(1, len(text) // 4)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load and cache the embedding model (called once on startup)."""
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return normalized embeddings for a batch of texts."""
    if not texts:
        return []
    model = get_embedder()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Return a single normalized embedding for a query string."""
    result = embed_texts([query])
    return result[0]
