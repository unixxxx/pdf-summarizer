"""Folder schemas for the library module."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FolderBase(BaseModel):
    """Base folder schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    parent_id: Optional[UUID] = None


class FolderCreate(FolderBase):
    """Schema for creating a folder."""

    pass


class FolderUpdate(BaseModel):
    """Schema for updating a folder."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    parent_id: Optional[UUID] = None


class FolderResponse(FolderBase):
    """Schema for folder response."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    children_count: int = 0

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


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
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AddDocumentToFolderRequest(BaseModel):
    """Schema for adding documents to a folder."""

    document_ids: list[UUID]


class RemoveDocumentFromFolderRequest(BaseModel):
    """Schema for removing documents from a folder."""

    document_ids: list[UUID]


class MoveFolderRequest(BaseModel):
    """Schema for moving a folder."""

    parent_id: Optional[UUID] = None


# Update forward references
FolderWithChildren.model_rebuild()