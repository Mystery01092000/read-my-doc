import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.database import get_db
from app.dependencies import get_current_user_id
from app.documents.schemas import DocumentListResponse, DocumentResponse
from app.documents.service import DocumentService

router = APIRouter()


def _service(session: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(session)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    svc: DocumentService = Depends(_service),
) -> DocumentListResponse:
    return await svc.list_documents(uuid.UUID(user_id), page=page, limit=limit)


@router.post("", response_model=DocumentResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    svc: DocumentService = Depends(_service),
) -> DocumentResponse:
    return await svc.upload(uuid.UUID(user_id), file)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    svc: DocumentService = Depends(_service),
) -> DocumentResponse:
    return await svc.get_document(document_id, uuid.UUID(user_id))


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    svc: DocumentService = Depends(_service),
) -> None:
    await svc.delete_document(document_id, uuid.UUID(user_id))
