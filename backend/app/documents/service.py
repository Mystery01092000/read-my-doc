import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenError, NotFoundError, UnprocessableError
from app.config import settings
from app.documents.repository import DocumentRepository
from app.documents.schemas import ALLOWED_EXTENSIONS, DocumentListResponse, DocumentResponse


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = DocumentRepository(session)

    async def upload(self, user_id: uuid.UUID, file: UploadFile) -> DocumentResponse:
        filename = file.filename or "upload"
        suffix = Path(filename).suffix.lower()
        file_type = ALLOWED_EXTENSIONS.get(suffix)
        if file_type is None:
            raise UnprocessableError(
                f"Unsupported file type '{suffix}'. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}"
            )

        contents = await file.read()
        size_bytes = len(contents)
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise UnprocessableError(
                f"File too large ({size_bytes // 1024 // 1024} MB). "
                f"Max: {settings.max_upload_size_mb} MB"
            )

        # Persist file
        upload_dir = Path(settings.upload_dir) / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        doc_id = uuid.uuid4()
        storage_path = str(upload_dir / f"{doc_id}{suffix}")
        Path(storage_path).write_bytes(contents)

        doc = await self._repo.create(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=size_bytes,
            storage_path=storage_path,
        )

        # Enqueue processing
        from tasks.document_tasks import process_document
        process_document.delay(str(doc.id))

        return DocumentResponse.model_validate(doc)

    async def list_documents(
        self, user_id: uuid.UUID, page: int = 1, limit: int = 20
    ) -> DocumentListResponse:
        offset = (page - 1) * limit
        docs, total = await self._repo.list_for_user(user_id, offset=offset, limit=limit)
        pages = (total + limit - 1) // limit
        return DocumentListResponse(
            items=[DocumentResponse.model_validate(d) for d in docs],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    async def get_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> DocumentResponse:
        doc = await self._repo.get(document_id, user_id)
        if doc is None:
            raise NotFoundError("Document", str(document_id))
        return DocumentResponse.model_validate(doc)

    async def delete_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        doc = await self._repo.get(document_id, user_id)
        if doc is None:
            raise NotFoundError("Document", str(document_id))
        deleted = await self._repo.delete(document_id, user_id)
        if not deleted:
            raise ForbiddenError("Cannot delete this document")
        # Remove stored file
        try:
            Path(doc.storage_path).unlink(missing_ok=True)
        except OSError:
            pass
