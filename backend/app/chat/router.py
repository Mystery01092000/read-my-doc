import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.schemas import (
    ChatSessionDetailResponse,
    ChatSessionResponse,
    CreateSessionRequest,
    SendMessageRequest,
    SessionListResponse,
)
from app.chat.service import ChatService
from app.common.database import get_db
from app.dependencies import get_current_user_id

router = APIRouter()


def _service(session: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(session)


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    svc: ChatService = Depends(_service),
) -> SessionListResponse:
    return await svc.list_sessions(uuid.UUID(user_id), page=page, limit=limit)


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    req: CreateSessionRequest,
    user_id: str = Depends(get_current_user_id),
    svc: ChatService = Depends(_service),
) -> ChatSessionResponse:
    return await svc.create_session(uuid.UUID(user_id), req.document_ids, req.title)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_session(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    svc: ChatService = Depends(_service),
) -> ChatSessionDetailResponse:
    return await svc.get_session(session_id, uuid.UUID(user_id))


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    svc: ChatService = Depends(_service),
) -> None:
    await svc.delete_session(session_id, uuid.UUID(user_id))


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    req: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
    svc: ChatService = Depends(_service),
) -> StreamingResponse:
    stream = await svc.send_message_stream(session_id, uuid.UUID(user_id), req.content)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
