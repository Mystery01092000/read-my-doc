"""LLM generator with citation enforcement, structured output validation, and token tracking."""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, field_validator

from app.config import settings
from app.rag.embedder import estimate_tokens
from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from app.rag.retriever import RetrievedChunk


# ── Token usage ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TokenUsage:
    """Immutable record of all token consumption for one RAG query."""

    prompt_tokens: int = 0          # LLM input tokens (system + context + question)
    completion_tokens: int = 0      # LLM output tokens (answer)
    embedding_tokens: int = 0       # Tokens embedded for the query vector
    rerank_tokens: int = 0          # Estimated tokens scored by the cross-encoder

    @property
    def llm_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def total_tokens(self) -> int:
        return self.llm_tokens + self.embedding_tokens + self.rerank_tokens

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "llm_tokens": self.llm_tokens,
            "embedding_tokens": self.embedding_tokens,
            "rerank_tokens": self.rerank_tokens,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def zero(cls) -> "TokenUsage":
        return cls()


def estimate_rerank_tokens(query: str, chunks: list[RetrievedChunk]) -> int:
    """Estimate tokens scored by the cross-encoder (query + chunk content per pair)."""
    query_tokens = estimate_tokens(query)
    return sum(query_tokens + estimate_tokens(c.content) for c in chunks)


# ── Pydantic output models ────────────────────────────────────────────────────

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


# ── Citation post-processing ──────────────────────────────────────────────────

def _strip_invalid_citations(
    answer: GeneratedAnswer, valid_chunk_ids: set[str]
) -> GeneratedAnswer:
    """Remove any citations whose chunk_id was not in the retrieved set."""
    valid_citations = [c for c in answer.citations if c.chunk_id in valid_chunk_ids]
    removed_ids = {c.chunk_id for c in answer.citations} - {c.chunk_id for c in valid_citations}
    clean_answer = answer.answer
    for cid in removed_ids:
        clean_answer = clean_answer.replace(f"[chunk:{cid}]", "")
    return GeneratedAnswer(answer=clean_answer.strip(), citations=valid_citations)


def _parse_llm_response(raw: str) -> GeneratedAnswer:
    """Extract and parse JSON from LLM response, with fallback."""
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return GeneratedAnswer.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return GeneratedAnswer(answer=raw.strip(), citations=[])


# ── Public API ────────────────────────────────────────────────────────────────

def _to_chunk_dicts(chunks: list[RetrievedChunk]) -> list[dict]:
    return [
        {
            "chunk_id": str(c.chunk_id),
            "filename": c.filename,
            "content": c.content,
            "page_number": c.page_number,
            "section_heading": c.section_heading,
        }
        for c in chunks
    ]


async def generate_answer(
    query: str,
    chunks: list[RetrievedChunk],
    query_embedding_tokens: int = 0,
) -> tuple[GeneratedAnswer, TokenUsage]:
    """Generate a cited answer. Returns (answer, token_usage)."""
    if not chunks:
        return (
            GeneratedAnswer(
                answer="I cannot find this information in the provided documents.",
                citations=[],
            ),
            TokenUsage(embedding_tokens=query_embedding_tokens),
        )

    chunk_dicts = _to_chunk_dicts(chunks)
    valid_ids = {str(c.chunk_id) for c in chunks}
    user_prompt = build_user_prompt(query, chunk_dicts)
    rerank_tokens = estimate_rerank_tokens(query, chunks)

    raw, prompt_tokens, completion_tokens = await _call_llm(user_prompt)
    parsed = _parse_llm_response(raw)
    cleaned = _strip_invalid_citations(parsed, valid_ids)

    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        embedding_tokens=query_embedding_tokens,
        rerank_tokens=rerank_tokens,
    )
    return cleaned, usage


async def generate_answer_stream(
    query: str,
    chunks: list[RetrievedChunk],
    query_embedding_tokens: int = 0,
) -> AsyncIterator[str]:
    """Stream answer tokens then yield a final [META] line with citations + token usage.

    Buffers the full LLM response first so the JSON wrapper can be stripped before
    streaming, ensuring only the plain answer text is sent to the client.
    """
    if not chunks:
        yield "I cannot find this information in the provided documents."
        meta = {
            "citations": [],
            "token_usage": TokenUsage(embedding_tokens=query_embedding_tokens).to_dict(),
        }
        yield "\n\n[META]" + json.dumps(meta)
        return

    chunk_dicts = _to_chunk_dicts(chunks)
    valid_ids = {str(c.chunk_id) for c in chunks}
    user_prompt = build_user_prompt(query, chunk_dicts)
    rerank_tokens = estimate_rerank_tokens(query, chunks)

    full_response = ""
    prompt_tokens = 0
    completion_tokens = 0

    # Buffer the entire LLM output so we can parse JSON before streaming to the client.
    async for item in _stream_llm(user_prompt):
        if isinstance(item, str):
            full_response += item
        else:
            prompt_tokens, completion_tokens = item

    parsed = _parse_llm_response(full_response)
    cleaned = _strip_invalid_citations(parsed, valid_ids)

    # Stream the clean answer word-by-word to preserve the streaming UX.
    words = cleaned.answer.split(" ")
    for i, word in enumerate(words):
        yield word if i == len(words) - 1 else word + " "

    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        embedding_tokens=query_embedding_tokens,
        rerank_tokens=rerank_tokens,
    )
    meta = {
        "citations": [c.model_dump() for c in cleaned.citations],
        "token_usage": usage.to_dict(),
    }
    yield "\n\n[META]" + json.dumps(meta)


# ── LLM dispatch ─────────────────────────────────────────────────────────────

async def _call_llm(user_prompt: str) -> tuple[str, int, int]:
    """Returns (response_text, prompt_tokens, completion_tokens)."""
    if settings.llm_provider == "openai":
        return await _call_openai(user_prompt)
    if settings.llm_provider == "groq":
        return await _call_groq(user_prompt)
    return await _call_ollama(user_prompt)


async def _stream_llm(user_prompt: str) -> AsyncIterator[str | tuple[int, int]]:
    """Yields str tokens then a final (prompt_tokens, completion_tokens) tuple."""
    if settings.llm_provider == "openai":
        async for item in _stream_openai(user_prompt):
            yield item
    elif settings.llm_provider == "groq":
        async for item in _stream_groq(user_prompt):
            yield item
    else:
        async for item in _stream_ollama(user_prompt):
            yield item


# ── Ollama ────────────────────────────────────────────────────────────────────

async def _call_ollama(user_prompt: str) -> tuple[str, int, int]:
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
        text = data["message"]["content"]
        prompt_tokens = data.get("prompt_eval_count", estimate_tokens(user_prompt))
        completion_tokens = data.get("eval_count", estimate_tokens(text))
        return text, prompt_tokens, completion_tokens


async def _stream_ollama(user_prompt: str) -> AsyncIterator[str | tuple[int, int]]:
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
                "format": "json",
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
                    # Ollama sends final stats in the last chunk (done=true)
                    if chunk.get("done"):
                        yield (
                            chunk.get("prompt_eval_count", 0),
                            chunk.get("eval_count", 0),
                        )
                except json.JSONDecodeError:
                    continue


# ── OpenAI ────────────────────────────────────────────────────────────────────

async def _call_openai(user_prompt: str) -> tuple[str, int, int]:
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
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


async def _stream_openai(user_prompt: str) -> AsyncIterator[str | tuple[int, int]]:
    total_content = ""
    prompt_tokens = 0
    completion_tokens = 0
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
                "stream_options": {"include_usage": True},
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
                        total_content += token
                        yield token
                    if usage := data.get("usage"):
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)
                except (json.JSONDecodeError, KeyError):
                    continue
    # Fallback to estimates if stream_options not available
    yield (
        prompt_tokens or estimate_tokens(SYSTEM_PROMPT + user_prompt),
        completion_tokens or estimate_tokens(total_content),
    )


# ── Groq (OpenAI-compatible) ──────────────────────────────────────────────────

async def _call_groq(user_prompt: str) -> tuple[str, int, int]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.groq_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


async def _stream_groq(user_prompt: str) -> AsyncIterator[str | tuple[int, int]]:
    total_content = ""
    prompt_tokens = 0
    completion_tokens = 0
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{settings.groq_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": True,
                "stream_options": {"include_usage": True},
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
                        total_content += token
                        yield token
                    if usage := data.get("usage"):
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)
                except (json.JSONDecodeError, KeyError):
                    continue
    yield (
        prompt_tokens or estimate_tokens(SYSTEM_PROMPT + user_prompt),
        completion_tokens or estimate_tokens(total_content),
    )
