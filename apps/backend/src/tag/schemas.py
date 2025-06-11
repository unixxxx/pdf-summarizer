"""Tag schemas for document classification."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TagResponse(BaseModel):
    """Tag response schema."""
    id: UUID
    name: str
    slug: str
    color: Optional[str] = None
    document_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class TagGenerationRequest(BaseModel):
    """Schema for tag generation requests."""
    summary_id: UUID


class TagGenerationRequestInternal(BaseModel):
    """Internal schema for tag generation."""
    content: str
    filename: str
    max_tags: int = 5