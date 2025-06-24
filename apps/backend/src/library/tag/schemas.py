"""Tag schemas for document classification."""

from uuid import UUID

from pydantic import BaseModel


class TagResponse(BaseModel):
    """Tag response schema."""
    id: UUID
    name: str
    slug: str
    color: str | None = None
    
    model_config = {"from_attributes": True}