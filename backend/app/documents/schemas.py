import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

FileType = Literal["pdf", "txt", "md", "csv", "xlsx", "pptx"]
DocumentStatus = Literal["pending", "processing", "ready", "failed"]

ALLOWED_EXTENSIONS: dict[str, FileType] = {
    ".pdf": "pdf",
    ".txt": "txt",
    ".md": "md",
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".pptx": "pptx",
}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    error_message: str | None
    page_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    limit: int
    pages: int
