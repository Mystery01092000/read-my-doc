"""LLM generator with citation enforcement and structured output validation."""

import json
import re
from collections.abc import AsyncIterator
from uuid import UUID

import httpx
from pydantic import BaseModel, field_validator

from app.config import settings
from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from app.rag.retriever import RetrievedChunk


class CitationItem(BaseModel):
    chunk_id: str
    quote: str


class GeneratedAnswer(BaseModel):
    answer: str
    citations: list[CitationItem]

    @field_validator("citations")
    @classmethod
    def citations_not_empty_strings(cls, v: list[CitationItem]) -> list[CitationItem]:
        return [c for c in v if c.chunk_id.strip()]


def _strip_invalid_citations(
    answer: GeneratedAnswer, valid_chunk_ids: set[str]
) -> GeneratedAnswer:
    """Remove any citations whose chunk_id was not in the retrieved set."""
    valid_citations = [c for c in answer.citations if c.chunk_id in valid_chunk_ids]
    # Also strip inline references from the answer text for removed citations
    removed_ids = {c.chunk_id for c in answer.citations} - {c.chunk_id for c in valid_citations}
    clean_answer = answer.answer
    for cid in removed_ids:
        clean_answer = clean_answer.replace(f"[chunk:{cid}]", "")

    return GeneratedAnswer(answer=clean_answer.strip(), citations=valid_citations)


def _parse_llm_response(raw: str) -> GeneratedAnswer:
    """Extract and parse JSON from LLM response, with fallback."""
    # Try to find JSON block
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return GeneratedAnswer.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: treat as plain answer with no citations
    return GeneratedAnswer(answer=raw.strip(), citations=[])


async def generate_answer(
    query: str,
    chunks: list[RetrievedChunk],
) -> GeneratedAnswer:
    """Generate a cited answer from retrieved chunks."""
    if not chunks:
        return GeneratedAnswer(
            answer="I cannot find this information in the provided documents.",
            citations=[],
        )

    chunk_dicts = [
        {
            "chunk_id": str(c.chunk_id),
            "filename": c.filename,
            "content": c.content,
            "page_number": c.page_number,
            "section_heading": c.section_heading,
        }
        for c in chunks
    ]
    valid_ids = {str(c.chunk_id) for c in chunks}
    user_prompt = build_user_prompt(query, chunk_dicts)

    raw = await _call_llm(user_prompt)
    parsed = _parse_llm_response(raw)
    return _strip_invalid_citations(parsed, valid_ids)


async def generate_answer_stream(
    query: str,
    chunks: list[RetrievedChunk],
) -> AsyncIterator[str]:
    """Stream the answer token by token, then yield a final citations JSON line."""
    if not chunks:
        yield "I cannot find this information in the provided documents."
        yield "\n\n[CITATIONS]" + json.dumps([])
        return

    chunk_dicts = [
        {
            "chunk_id": str(c.chunk_id),
            "filename": c.filename,
            "content": c.content,
            "page_number": c.page_number,
            "section_heading": c.section_heading,
        }
        for c in chunks
    ]
    valid_ids = {str(c.chunk_id) for c in chunks}
    user_prompt = build_user_prompt(query, chunk_dicts)

    # Collect full response (Ollama streaming), then parse + validate
    full_response = ""
    async for token in _stream_llm(user_prompt):
        full_response += token
        yield token

    parsed = _parse_llm_response(full_response)
    cleaned = _strip_invalid_citations(parsed, valid_ids)
    yield "\n\n[CITATIONS]" + json.dumps([c.model_dump() for c in cleaned.citations])


async def _call_llm(user_prompt: str) -> str:
    """Call Ollama (or OpenAI) and return the full response string."""
    if settings.llm_provider == "openai":
        return await _call_openai(user_prompt)
    return await _call_ollama(user_prompt)


async def _stream_llm(user_prompt: str) -> AsyncIterator[str]:
    if settings.llm_provider == "openai":
        async for token in _stream_openai(user_prompt):
            yield token
    else:
        async for token in _stream_ollama(user_prompt):
            yield token


async def _call_ollama(user_prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "format": "json",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


async def _stream_ollama(user_prompt: str) -> AsyncIterator[str]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    if token := chunk.get("message", {}).get("content", ""):
                        yield token
                except json.JSONDecodeError:
                    continue


async def _call_openai(user_prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def _stream_openai(user_prompt: str) -> AsyncIterator[str]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if token := data["choices"][0]["delta"].get("content", ""):
                        yield token
                except (json.JSONDecodeError, KeyError):
                    continue
