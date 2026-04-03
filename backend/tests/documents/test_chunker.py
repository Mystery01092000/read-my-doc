"""Unit tests for the text chunker."""

import pytest

from app.documents.chunker import TARGET_CHARS, chunk_pages
from app.documents.parser import ParsedPage


def _page(text: str, page_num: int | None = None) -> ParsedPage:
    return ParsedPage(page_number=page_num, section_heading=None, text=text)


def test_short_text_single_chunk() -> None:
    pages = [_page("Short text.", page_num=1)]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].content == "Short text."
    assert chunks[0].page_number == 1


def test_long_text_multiple_chunks() -> None:
    long_text = "word " * 1000  # ~5000 chars
    pages = [_page(long_text)]
    chunks = chunk_pages(pages)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.content) <= TARGET_CHARS * 1.1  # allow small overage


def test_chunk_indices_sequential() -> None:
    pages = [_page("text " * 500), _page("more " * 500)]
    chunks = chunk_pages(pages)
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


def test_empty_pages_no_chunks() -> None:
    pages = [_page("   "), _page("")]
    chunks = chunk_pages(pages)
    assert chunks == []


def test_page_metadata_preserved() -> None:
    pages = [_page("Some content here.", page_num=3)]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].page_number == 3


def test_token_count_reasonable() -> None:
    text = "word " * 100
    pages = [_page(text)]
    chunks = chunk_pages(pages)
    for chunk in chunks:
        assert chunk.token_count > 0
