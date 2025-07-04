"""Document domain schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field
from shared.models import DocumentStatus

from ..tag.schemas import TagResponse


class ExportFormat(str, Enum):
    """Supported export formats."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"


class DocumentDetailResponse(BaseModel):
    """Document detail response schema for individual document."""

    id: UUID
    filename: str
    file_size: int
    file_hash: str
    status: DocumentStatus
    created_at: datetime
    storage_path: str | None = None
    extracted_text: str | None = None
    word_count: int | None = None
    folder_id: UUID | None = None
    error_message: str | None = None  # Error message if processing failed
    tags: list[TagResponse] = []

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}



class DocumentListItemResponse(BaseModel):
    """Document list item response schema for browsing documents."""

    id: UUID  # Document ID (not summary ID anymore)
    document_id: UUID
    filename: str
    file_size: int
    summary: str  # First 200 chars of extracted_text
    created_at: datetime
    word_count: int
    tags: list[TagResponse]
    status: DocumentStatus  # Document processing status
    folder_id: UUID | None = None
    error_message: str | None = None  # Error message if processing failed

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class DocumentsListResponse(BaseModel):
    """Paginated response for documents."""

    items: list[DocumentListItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

    class Config:
        from_attributes = True


class TextDocumentCreate(BaseModel):
    """Request schema for creating a text document."""

    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    folder_id: UUID | None = Field(None, description="Optional folder ID")
