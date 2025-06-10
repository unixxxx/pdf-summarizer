"""Library domain schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ExportFormat(str, Enum):
    """Supported export formats."""
    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"


class TagResponse(BaseModel):
    """Tag response schema."""
    id: UUID
    name: str
    slug: str
    color: Optional[str] = None
    document_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class LibraryItemResponse(BaseModel):
    """Library item response schema."""
    id: UUID  # Summary ID
    document_id: UUID
    filename: str
    file_size: int
    summary: str
    created_at: datetime
    processing_time: float
    word_count: int
    tags: list[TagResponse]
    
    class Config:
        from_attributes = True