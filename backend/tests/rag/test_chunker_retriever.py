"""Tests for chunker integration with retriever concepts."""

import pytest

from app.documents.chunker import chunk_pages, TARGET_CHARS
from app.documents.parser import ParsedPage


def _make_pages(*texts: str) -> list[ParsedPage]:
    return [ParsedPage(page_number=i + 1, section_heading=None, text=t) for i, t in enumerate(texts)]


def test_chunks_cover_all_content() -> None:
    """All content from pages should appear in chunks."""
    pages = _make_pages("Alpha beta gamma.", "Delta epsilon zeta.")
    chunks = chunk_pages(pages)
    combined = " ".join(c.content for c in chunks)
    assert "Alpha beta gamma" in combined
    assert "Delta epsilon zeta" in combined


def test_overlap_shares_content_between_chunks() -> None:
    """Adjacent chunks from a long text should share some content (overlap)."""
    long_text = "sentence. " * 300  # ~3000 chars
    pages = _make_pages(long_text)
    chunks = chunk_pages(pages)
    if len(chunks) > 1:
        # The end of chunk[0] and beginning of chunk[1] should overlap
        end_of_first = chunks[0].content[-50:]
        start_of_second = chunks[1].content[:200]
        assert any(word in start_of_second for word in end_of_first.split() if len(word) > 3)


def test_no_empty_chunks() -> None:
    pages = _make_pages("  ", "\n\n", "Valid content here.")
    chunks = chunk_pages(pages)
    for chunk in chunks:
        assert chunk.content.strip() != ""
