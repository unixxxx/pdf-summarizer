"""Folder schemas for the library module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TagInfo(BaseModel):
    """Minimal tag information for folder association."""

    id: UUID
    name: str
    color: str | None = None


class TagCreateData(BaseModel):
    """Data for creating a new tag inline."""

    id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=100)
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class FolderBase(BaseModel):
    """Base folder schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    parent_id: UUID | None = None


class FolderCreate(FolderBase):
    """Schema for creating a folder."""

    tags: list[TagCreateData] = Field(
        default_factory=list, description="Tags to create"
    )


class FolderUpdate(BaseModel):
    """Schema for updating a folder."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    parent_id: UUID | None = None
    tags: list[TagCreateData] | None = Field(
        None, description="Tags to associate with folder (None means no change)"
    )


class FolderResponse(BaseModel):
    """Schema for folder response."""

    id: UUID
    name: str
    description: str | None = None
    color: str | None = None
    parent_id: UUID | None = None
    tags: list[TagInfo] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    children_count: int = 0

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class FolderWithChildren(FolderResponse):
    """Schema for folder with children."""

    children: list["FolderWithChildren"] = []


class FolderTree(BaseModel):
    """Schema for folder tree response."""

    folders: list[FolderWithChildren]
    total_count: int  # Total number of folders
    unfiled_count: int = 0
    total_document_count: int = 0  # Total number of documents across all folders

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AddDocumentToFolderRequest(BaseModel):
    """Schema for adding documents to a folder."""

    document_ids: list[UUID]


class RemoveDocumentFromFolderRequest(BaseModel):
    """Schema for removing documents from a folder."""

    document_ids: list[UUID]


class MoveFolderRequest(BaseModel):
    """Schema for moving a folder."""

    parent_id: UUID | None = None


class SyncFolderRequest(BaseModel):
    """Schema for syncing folder documents based on tags."""

    folder_id: UUID


# Update forward references
FolderWithChildren.model_rebuild()
