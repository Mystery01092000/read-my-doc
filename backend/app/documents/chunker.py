"""Recursive text splitter that produces overlapping chunks with metadata."""

from dataclasses import dataclass

from app.documents.parser import ParsedPage

# Approximate token count (1 token ≈ 4 chars for English)
_CHARS_PER_TOKEN = 4
TARGET_TOKENS = 512
OVERLAP_TOKENS = 64
TARGET_CHARS = TARGET_TOKENS * _CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * _CHARS_PER_TOKEN

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    token_count: int
    page_number: int | None
    section_heading: str | None


def chunk_pages(pages: list[ParsedPage]) -> list[TextChunk]:
    """Split parsed pages into overlapping chunks."""
    all_chunks: list[TextChunk] = []
    for page in pages:
        raw_chunks = _split_text(page.text)
        for text in raw_chunks:
            stripped = text.strip()
            if not stripped:
                continue
            all_chunks.append(
                TextChunk(
                    chunk_index=len(all_chunks),
                    content=stripped,
                    token_count=max(1, len(stripped) // _CHARS_PER_TOKEN),
                    page_number=page.page_number,
                    section_heading=page.section_heading,
                )
            )
    return all_chunks


def _split_text(text: str, depth: int = 0) -> list[str]:
    if len(text) <= TARGET_CHARS:
        return [text]

    separator = _SEPARATORS[min(depth, len(_SEPARATORS) - 1)]

    if separator == "":
        # Hard split at character level
        parts = [text[i : i + TARGET_CHARS] for i in range(0, len(text), TARGET_CHARS - OVERLAP_CHARS)]
        return parts

    splits = text.split(separator)
    chunks: list[str] = []
    current = ""

    for part in splits:
        candidate = (current + separator + part).lstrip(separator) if current else part
        if len(candidate) <= TARGET_CHARS:
            current = candidate
        else:
            if current:
                chunks.append(current)
                # Start new chunk with overlap
                current = _overlap_prefix(current) + separator + part if len(part) <= TARGET_CHARS else part
            else:
                # Single part too large — recurse
                chunks.extend(_split_text(part, depth + 1))
                current = ""

    if current:
        chunks.append(current)

    return chunks


def _overlap_prefix(text: str) -> str:
    """Return the last OVERLAP_CHARS characters of text as context for the next chunk."""
    if len(text) <= OVERLAP_CHARS:
        return text
    return text[-OVERLAP_CHARS:]
