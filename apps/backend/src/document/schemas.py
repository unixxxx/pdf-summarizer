"""Document domain schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..tag.schemas import TagResponse


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: UUID
    user_id: UUID
    filename: str
    file_size: int
    file_hash: str
    created_at: datetime
    storage_path: Optional[str] = None
    extracted_text: Optional[str] = None
    word_count: Optional[int] = None
    folder_ids: list[UUID] = []

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentMetadata(BaseModel):
    """Document metadata value object."""
    filename: str
    file_size: int = Field(gt=0)
    mime_type: str
    
    @property
    def is_valid_size(self) -> bool:
        """Check if file size is within limits (10MB)."""
        max_size = 10 * 1024 * 1024  # 10MB
        return self.file_size <= max_size
    
    @property
    def is_supported(self) -> bool:
        """Check if file type is supported."""
        supported_types = ["application/pdf", "text/plain"]
        return self.mime_type in supported_types


class LibraryItemResponse(BaseModel):
    """Library item response schema for browsing documents with summaries."""
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
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedLibraryResponse(BaseModel):
    """Paginated response for library items."""
    items: list[LibraryItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
    
    class Config:
        from_attributes = True