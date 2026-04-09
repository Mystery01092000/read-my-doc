import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Chunk, Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        storage_path: str,
    ) -> Document:
        doc = Document(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            storage_path=storage_path,
        )
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def get(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Document], int]:
        count_result = await self._session.execute(
            select(func.count()).where(Document.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars()), total

    async def set_status(
        self,
        document_id: uuid.UUID,
        status: str,
        error_message: str | None = None,
        page_count: int | None = None,
        tokens_embedded: int | None = None,
    ) -> None:
        values: dict = {"status": status}
        if error_message is not None:
            values["error_message"] = error_message
        if page_count is not None:
            values["page_count"] = page_count
        if tokens_embedded is not None:
            values["tokens_embedded"] = tokens_embedded
        await self._session.execute(
            update(Document).where(Document.id == document_id).values(**values)
        )

    async def delete(self, document_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        doc = await self.get(document_id, user_id)
        if doc is None:
            return False
        await self._session.delete(doc)
        return True


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, chunks: list[Chunk]) -> None:
        self._session.add_all(chunks)
        await self._session.flush()

    async def get_by_ids(self, chunk_ids: list[uuid.UUID]) -> list[Chunk]:
        result = await self._session.execute(
            select(Chunk).where(Chunk.id.in_(chunk_ids))
        )
        return list(result.scalars())
