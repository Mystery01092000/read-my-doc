"""Tests for the RAG generator: citation enforcement and validation."""

import json
import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from app.config import settings
from app.rag.generator import (
    CitationItem,
    GeneratedAnswer,
    _call_groq,
    _call_llm,
    _parse_llm_response,
    _stream_groq,
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


# ── _call_groq tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_call_groq_returns_text_and_tokens() -> None:
    """_call_groq parses response text and token usage from Groq API."""
    groq_url = f"{settings.groq_base_url}/chat/completions"
    respx.post(groq_url).mock(return_value=httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": '{"answer": "test answer", "citations": []}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
    ))

    with patch.object(settings, "groq_api_key", "test-key"), \
         patch.object(settings, "groq_model", "llama3-70b-8192"):
        text, prompt_tokens, completion_tokens = await _call_groq("What is X?")

    assert "test answer" in text
    assert prompt_tokens == 10
    assert completion_tokens == 5


@pytest.mark.asyncio
@respx.mock
async def test_call_groq_fallback_tokens_when_usage_missing() -> None:
    """_call_groq returns 0 tokens when usage field is absent."""
    groq_url = f"{settings.groq_base_url}/chat/completions"
    respx.post(groq_url).mock(return_value=httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": '{"answer": "hello", "citations": []}'}}],
        },
    ))

    with patch.object(settings, "groq_api_key", "test-key"), \
         patch.object(settings, "groq_model", "llama3-70b-8192"):
        text, prompt_tokens, completion_tokens = await _call_groq("Hello?")

    assert prompt_tokens == 0
    assert completion_tokens == 0


# ── _stream_groq tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_stream_groq_yields_tokens_then_usage() -> None:
    """_stream_groq yields string tokens then a (prompt_tokens, completion_tokens) tuple."""
    groq_url = f"{settings.groq_base_url}/chat/completions"

    sse_lines = [
        'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
        'data: {"choices": [{"delta": {"content": " world"}}], "usage": {"prompt_tokens": 8, "completion_tokens": 2}}\n',
        "data: [DONE]\n",
    ]
    sse_body = "".join(sse_lines)

    respx.post(groq_url).mock(return_value=httpx.Response(
        200,
        content=sse_body.encode(),
        headers={"content-type": "text/event-stream"},
    ))

    with patch.object(settings, "groq_api_key", "test-key"), \
         patch.object(settings, "groq_model", "llama3-70b-8192"):
        items: list[str | tuple[int, int]] = []
        async for item in _stream_groq("Say hello"):
            items.append(item)

    str_tokens = [i for i in items if isinstance(i, str)]
    final_tuple = items[-1]

    assert "Hello" in str_tokens
    assert " world" in str_tokens
    assert isinstance(final_tuple, tuple)
    assert len(final_tuple) == 2


@pytest.mark.asyncio
async def test_call_llm_dispatches_to_groq() -> None:
    """_call_llm dispatches to _call_groq when llm_provider is 'groq'."""
    with patch("app.rag.generator._call_groq", new_callable=AsyncMock) as mock_groq, \
         patch.object(settings, "llm_provider", "groq"):
        mock_groq.return_value = ("answer", 5, 3)
        result = await _call_llm("test prompt")

    mock_groq.assert_called_once_with("test prompt")
    assert result == ("answer", 5, 3)
