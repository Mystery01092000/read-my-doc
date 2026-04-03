"""Chat service: session management + RAG pipeline orchestration."""

import json
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.repository import ChatSessionRepository, MessageRepository
from app.chat.schemas import (
    ChatSessionDetailResponse,
    ChatSessionResponse,
    MessageResponse,
    SessionListResponse,
)
from app.common.exceptions import NotFoundError, UnprocessableError
from app.config import settings
from app.rag.generator import GeneratedAnswer, generate_answer, generate_answer_stream
from app.rag.reranker import rerank
from app.rag.retriever import retrieve


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._sessions = ChatSessionRepository(session)
        self._messages = MessageRepository(session)
        self._db = session

    async def create_session(
        self,
        user_id: uuid.UUID,
        document_ids: list[uuid.UUID],
        title: str | None = None,
    ) -> ChatSessionResponse:
        if not document_ids:
            raise UnprocessableError("At least one document must be selected")

        cs = await self._sessions.create(user_id, document_ids, title or "New Chat")
        doc_ids = await self._sessions.get_document_ids(cs.id)
        return ChatSessionResponse(
            id=cs.id,
            title=cs.title,
            document_ids=doc_ids,
            created_at=cs.created_at,
            updated_at=cs.updated_at,
        )

    async def list_sessions(
        self, user_id: uuid.UUID, page: int = 1, limit: int = 20
    ) -> SessionListResponse:
        offset = (page - 1) * limit
        sessions, total = await self._sessions.list_for_user(user_id, offset=offset, limit=limit)
        pages = (total + limit - 1) // limit

        items = [
            ChatSessionResponse(
                id=s.id,
                title=s.title,
                document_ids=[sd.document_id for sd in s.session_documents],
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ]
        return SessionListResponse(items=items, total=total, page=page, limit=limit, pages=pages)

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChatSessionDetailResponse:
        cs = await self._sessions.get(session_id, user_id, with_messages=True)
        if cs is None:
            raise NotFoundError("ChatSession", str(session_id))
        doc_ids = [sd.document_id for sd in cs.session_documents]
        return ChatSessionDetailResponse(
            id=cs.id,
            title=cs.title,
            document_ids=doc_ids,
            created_at=cs.created_at,
            updated_at=cs.updated_at,
            messages=[MessageResponse.model_validate(m) for m in cs.messages],
        )

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        deleted = await self._sessions.delete(session_id, user_id)
        if not deleted:
            raise NotFoundError("ChatSession", str(session_id))

    async def send_message_stream(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> AsyncIterator[str]:
        """Save user message, run RAG pipeline, stream response as SSE."""
        cs = await self._sessions.get(session_id, user_id)
        if cs is None:
            raise NotFoundError("ChatSession", str(session_id))

        doc_ids = await self._sessions.get_document_ids(session_id)

        # Save user message
        await self._messages.create(session_id, "user", content)

        # RAG pipeline
        candidates = await retrieve(
            self._db, content, doc_ids, top_k=settings.retrieval_top_k
        )
        ranked_chunks = rerank(content, candidates, top_n=settings.rerank_top_n)

        # Stream answer
        full_answer = ""
        final_citations: list[dict] = []

        async def _stream() -> AsyncIterator[str]:
            nonlocal full_answer, final_citations
            async for token in generate_answer_stream(content, ranked_chunks):
                if token.startswith("\n\n[CITATIONS]"):
                    citation_json = token[len("\n\n[CITATIONS]"):]
                    try:
                        final_citations = json.loads(citation_json)
                    except json.JSONDecodeError:
                        final_citations = []
                    # Don't yield the citations marker — handled after stream ends
                    break
                full_answer += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Enrich citations with chunk metadata
            enriched_citations = _enrich_citations(final_citations, ranked_chunks)

            # Persist assistant message
            await self._messages.create(
                session_id, "assistant", full_answer, citations=enriched_citations
            )
            await self._sessions.touch(session_id)

            # Auto-title if first assistant message
            if cs.title == "New Chat":
                short_title = content[:80] + ("…" if len(content) > 80 else "")
                await self._sessions.update_title(session_id, short_title)

            # Send final citations event
            yield f"data: {json.dumps({'type': 'citations', 'citations': enriched_citations})}\n\n"
            yield "data: [DONE]\n\n"

        return _stream()


def _enrich_citations(
    raw_citations: list[dict],
    chunks: list,
) -> list[dict]:
    """Map chunk_id citations to full metadata from retrieved chunks."""
    chunk_map = {str(c.chunk_id): c for c in chunks}
    enriched = []
    for cit in raw_citations:
        chunk_id = cit.get("chunk_id", "")
        chunk = chunk_map.get(chunk_id)
        if chunk is None:
            continue
        enriched.append(
            {
                "chunk_id": chunk_id,
                "document_id": str(chunk.document_id),
                "filename": chunk.filename,
                "page": chunk.page_number,
                "snippet": cit.get("quote", chunk.content[:200]),
            }
        )
    return enriched
