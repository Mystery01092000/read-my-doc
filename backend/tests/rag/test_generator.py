"""Tests for the RAG generator: citation enforcement and validation."""

import json
import uuid

import pytest

from app.rag.generator import (
    GeneratedAnswer,
    CitationItem,
    _parse_llm_response,
    _strip_invalid_citations,
)


def test_parse_valid_json_response() -> None:
    chunk_id = str(uuid.uuid4())
    raw = json.dumps({
        "answer": f"The answer is 42 [chunk:{chunk_id}].",
        "citations": [{"chunk_id": chunk_id, "quote": "The answer is 42"}],
    })
    result = _parse_llm_response(raw)
    assert isinstance(result, GeneratedAnswer)
    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == chunk_id


def test_parse_json_embedded_in_text() -> None:
    chunk_id = str(uuid.uuid4())
    raw = f'Sure, here is my answer:\n{{"answer": "42 [chunk:{chunk_id}]", "citations": [{{"chunk_id": "{chunk_id}", "quote": "42"}}]}}'
    result = _parse_llm_response(raw)
    assert result.citations[0].chunk_id == chunk_id


def test_parse_invalid_json_falls_back_to_plain() -> None:
    result = _parse_llm_response("This is just plain text with no JSON.")
    assert result.answer == "This is just plain text with no JSON."
    assert result.citations == []


def test_strip_invalid_citations_removes_hallucinated() -> None:
    real_id = str(uuid.uuid4())
    fake_id = str(uuid.uuid4())

    answer = GeneratedAnswer(
        answer=f"Real info [chunk:{real_id}]. Fake info [chunk:{fake_id}].",
        citations=[
            CitationItem(chunk_id=real_id, quote="real"),
            CitationItem(chunk_id=fake_id, quote="fake"),
        ],
    )
    cleaned = _strip_invalid_citations(answer, valid_chunk_ids={real_id})
    assert len(cleaned.citations) == 1
    assert cleaned.citations[0].chunk_id == real_id
    assert fake_id not in cleaned.answer


def test_strip_invalid_citations_all_valid() -> None:
    ids = [str(uuid.uuid4()) for _ in range(3)]
    answer = GeneratedAnswer(
        answer="All valid",
        citations=[CitationItem(chunk_id=cid, quote="q") for cid in ids],
    )
    cleaned = _strip_invalid_citations(answer, valid_chunk_ids=set(ids))
    assert len(cleaned.citations) == 3


def test_strip_invalid_citations_none_valid() -> None:
    fake_id = str(uuid.uuid4())
    answer = GeneratedAnswer(
        answer=f"Hallucinated [chunk:{fake_id}].",
        citations=[CitationItem(chunk_id=fake_id, quote="hallucinated")],
    )
    cleaned = _strip_invalid_citations(answer, valid_chunk_ids=set())
    assert cleaned.citations == []
    assert fake_id not in cleaned.answer
