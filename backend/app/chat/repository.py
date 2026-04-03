import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.chat.models import ChatSession, ChatSessionDocument, Message


class ChatSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, user_id: uuid.UUID, document_ids: list[uuid.UUID], title: str = "New Chat"
    ) -> ChatSession:
        chat_session = ChatSession(user_id=user_id, title=title)
        self._session.add(chat_session)
        await self._session.flush()

        for doc_id in document_ids:
            link = ChatSessionDocument(session_id=chat_session.id, document_id=doc_id)
            self._session.add(link)

        await self._session.flush()
        return chat_session

    async def get(
        self, session_id: uuid.UUID, user_id: uuid.UUID, with_messages: bool = False
    ) -> ChatSession | None:
        q = select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
        if with_messages:
            q = q.options(
                selectinload(ChatSession.messages),
                selectinload(ChatSession.session_documents),
            )
        result = await self._session.execute(q)
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[ChatSession], int]:
        count_result = await self._session.execute(
            select(func.count()).where(ChatSession.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.session_documents))
            .order_by(ChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars()), total

    async def update_title(self, session_id: uuid.UUID, title: str) -> None:
        await self._session.execute(
            update(ChatSession).where(ChatSession.id == session_id).values(title=title)
        )

    async def touch(self, session_id: uuid.UUID) -> None:
        await self._session.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.utcnow())
        )

    async def delete(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        cs = await self.get(session_id, user_id)
        if cs is None:
            return False
        await self._session.delete(cs)
        return True

    async def get_document_ids(self, session_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(ChatSessionDocument.document_id).where(
                ChatSessionDocument.session_id == session_id
            )
        )
        return [row[0] for row in result.fetchall()]


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        citations: list[dict] | None = None,
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations or [],
        )
        self._session.add(msg)
        await self._session.flush()
        return msg
