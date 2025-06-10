"""Document domain schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Document list item schema."""
    id: UUID
    filename: str
    file_size: int
    created_at: datetime
    word_count: Optional[int] = None
    
    class Config:
        from_attributes = True


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