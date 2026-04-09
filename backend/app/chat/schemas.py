import uuid
from datetime import datetime

from pydantic import BaseModel


class CitationSchema(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: int | None
    snippet: str


class TokenUsageSchema(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    llm_tokens: int = 0
    embedding_tokens: int = 0
    rerank_tokens: int = 0
    total_tokens: int = 0


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[CitationSchema]
    token_usage: TokenUsageSchema | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateSessionRequest(BaseModel):
    document_ids: list[uuid.UUID]
    title: str | None = None


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    document_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: list[MessageResponse]


class SessionListResponse(BaseModel):
    items: list[ChatSessionResponse]
    total: int
    page: int
    limit: int
    pages: int


class SendMessageRequest(BaseModel):
    content: str
