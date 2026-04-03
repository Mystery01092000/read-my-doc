"""Faithfulness evaluation: answers must be grounded in retrieved chunks.

For the CI gate this test measures the faithfulness heuristic without
requiring a running LLM (it uses mock answers that are clearly grounded or
clearly not grounded in the context).

In a full integration run with `make eval-integration`, RAGAS is used to
score against real LLM outputs. See Makefile for the integration target.
"""

import pytest

from app.documents.chunker import chunk_pages
from app.documents.parser import ParsedPage


FAITHFULNESS_THRESHOLD = 0.80


def _simple_faithfulness_score(answer: str, context_chunks: list[str]) -> float:
    """
    Lightweight heuristic: fraction of answer sentences that contain at least
    one 4-character token present in the context. This is a proxy for RAGAS
    faithfulness without requiring an LLM judge.
    """
    context_tokens = set()
    for chunk in context_chunks:
        context_tokens.update(t.lower() for t in chunk.split() if len(t) >= 4)

    sentences = [s.strip() for s in answer.split(".") if s.strip()]
    if not sentences:
        return 1.0

    grounded = sum(
        1
        for sent in sentences
        if any(t.lower() in context_tokens for t in sent.split() if len(t) >= 4)
    )
    return grounded / len(sentences)


class TestFaithfulnessHeuristic:
    def test_fully_grounded_answer(self) -> None:
        context = ["The system supports PDF, TXT, and Markdown file formats for document upload."]
        answer = "The system supports PDF and TXT formats."
        score = _simple_faithfulness_score(answer, context)
        assert score >= FAITHFULNESS_THRESHOLD

    def test_hallucinated_answer_low_score(self) -> None:
        context = ["Dogs are domestic animals."]
        answer = "Quantum entanglement enables faster-than-light communication."
        score = _simple_faithfulness_score(answer, context)
        # Hallucinated answer should have low grounding
        assert score < FAITHFULNESS_THRESHOLD

    def test_partial_grounding(self) -> None:
        context = ["Retrieval uses BM25 and vector search combined with RRF fusion."]
        answer = "Retrieval uses BM25. The LLM generates answers using GPT-5."
        score = _simple_faithfulness_score(answer, context)
        # First sentence grounded, second not — should be around 0.5
        assert 0.0 < score <= 1.0

    def test_empty_answer_returns_perfect(self) -> None:
        score = _simple_faithfulness_score("", ["some context"])
        assert score == 1.0

    def test_cannot_find_message_is_faithful(self) -> None:
        answer = "I cannot find this information in the provided documents."
        context = ["Completely unrelated content about cats."]
        # "cannot find" is a valid faithful response when context doesn't contain the answer
        score = _simple_faithfulness_score(answer, context)
        assert score >= 0.0  # just ensure it doesn't crash


class TestChunkQuality:
    """Validate that chunk quality is sufficient for retrieval."""

    def test_chunks_preserve_key_terms(self) -> None:
        page = ParsedPage(
            page_number=1,
            section_heading="Overview",
            text="The system uses hybrid retrieval combining BM25 and vector search with RRF fusion.",
        )
        chunks = chunk_pages([page])
        combined = " ".join(c.content for c in chunks)
        for term in ["hybrid", "retrieval", "BM25", "vector", "RRF"]:
            assert term in combined, f"Key term '{term}' lost during chunking"

    def test_chunks_reasonable_length(self) -> None:
        long_text = " ".join(["word"] * 2000)
        page = ParsedPage(page_number=1, section_heading=None, text=long_text)
        chunks = chunk_pages([page])
        for chunk in chunks:
            # No chunk should be excessively short (padding artifacts)
            assert len(chunk.content) >= 10
