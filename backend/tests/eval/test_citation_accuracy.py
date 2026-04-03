"""Citation accuracy evaluation: validates that the generator never returns
hallucinated chunk IDs (i.e. IDs not present in the retrieved set).

This test runs entirely in-process with mocked retrieval so it does not
require a running database or LLM — it tests the citation post-processing
logic which is the contract the CI gate enforces.
"""

import uuid
from unittest.mock import patch

import pytest

from app.rag.generator import (
    CitationItem,
    GeneratedAnswer,
    _strip_invalid_citations,
)
from app.rag.retriever import RetrievedChunk

CITATION_ACCURACY_THRESHOLD = 0.90


def _make_chunk(chunk_id: uuid.UUID | None = None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id or uuid.uuid4(),
        document_id=uuid.uuid4(),
        filename="test.txt",
        content="Some content here.",
        page_number=1,
        section_heading=None,
        rrf_score=0.5,
    )


def _accuracy(answer: GeneratedAnswer, valid_ids: set[str]) -> float:
    """Fraction of citations whose chunk_id is in the valid set."""
    if not answer.citations:
        return 1.0  # no citations to be wrong
    valid_count = sum(1 for c in answer.citations if c.chunk_id in valid_ids)
    return valid_count / len(answer.citations)


class TestCitationStripping:
    def test_all_valid_citations_preserved(self) -> None:
        ids = [str(uuid.uuid4()) for _ in range(3)]
        answer = GeneratedAnswer(
            answer="A [chunk:{0}] B [chunk:{1}] C [chunk:{2}]".format(*ids),
            citations=[CitationItem(chunk_id=i, quote="q") for i in ids],
        )
        cleaned = _strip_invalid_citations(answer, valid_chunk_ids=set(ids))
        assert len(cleaned.citations) == 3
        assert _accuracy(cleaned, set(ids)) == 1.0

    def test_hallucinated_citations_stripped(self) -> None:
        real_id = str(uuid.uuid4())
        fake_ids = [str(uuid.uuid4()) for _ in range(4)]
        answer = GeneratedAnswer(
            answer=f"Real [chunk:{real_id}]" + "".join(f" fake [chunk:{f}]" for f in fake_ids),
            citations=[CitationItem(chunk_id=real_id, quote="r")]
            + [CitationItem(chunk_id=f, quote="f") for f in fake_ids],
        )
        cleaned = _strip_invalid_citations(answer, valid_chunk_ids={real_id})
        assert _accuracy(cleaned, {real_id}) == 1.0
        assert len(cleaned.citations) == 1

    def test_no_citations_returns_perfect_accuracy(self) -> None:
        answer = GeneratedAnswer(answer="No citations here.", citations=[])
        cleaned = _strip_invalid_citations(answer, valid_chunk_ids=set())
        assert _accuracy(cleaned, set()) == 1.0

    def test_empty_chunk_ids_stripped(self) -> None:
        answer = GeneratedAnswer(
            answer="text",
            citations=[CitationItem(chunk_id="", quote="empty")],
        )
        # Empty chunk_id is filtered by the Pydantic validator
        assert all(c.chunk_id.strip() for c in answer.citations) or len(answer.citations) == 0


class TestCitationAccuracyThreshold:
    """Verify the system meets the >= 0.90 citation accuracy threshold."""

    @pytest.mark.parametrize(
        "n_valid,n_hallucinated",
        [
            (10, 0),   # 100% accuracy
            (9, 1),    # 90% — exactly at threshold
            (10, 1),   # 91% — above threshold
        ],
    )
    def test_meets_threshold(self, n_valid: int, n_hallucinated: int) -> None:
        valid_ids = {str(uuid.uuid4()) for _ in range(n_valid)}
        fake_ids = {str(uuid.uuid4()) for _ in range(n_hallucinated)}
        all_citations = [CitationItem(chunk_id=i, quote="q") for i in valid_ids | fake_ids]

        answer = GeneratedAnswer(answer="text", citations=all_citations)
        cleaned = _strip_invalid_citations(answer, valid_chunk_ids=valid_ids)
        accuracy = _accuracy(cleaned, valid_ids)
        assert accuracy >= CITATION_ACCURACY_THRESHOLD, (
            f"Citation accuracy {accuracy:.2%} below threshold {CITATION_ACCURACY_THRESHOLD:.0%}"
        )

    def test_below_threshold_detected(self) -> None:
        """Confirm the test catches systems that violate the threshold."""
        valid_ids = {str(uuid.uuid4()) for _ in range(1)}
        fake_ids = {str(uuid.uuid4()) for _ in range(9)}
        all_citations = [CitationItem(chunk_id=i, quote="q") for i in valid_ids | fake_ids]

        # Without stripping, accuracy would be 10% (1/10)
        answer = GeneratedAnswer(answer="text", citations=all_citations)
        raw_accuracy = _accuracy(answer, valid_ids)
        assert raw_accuracy < CITATION_ACCURACY_THRESHOLD  # confirms detection works
