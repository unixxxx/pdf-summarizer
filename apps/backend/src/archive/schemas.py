"""Schemas for archive functionality."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArchiveItemBase(BaseModel):
    """Base schema for archive items."""
    
    id: UUID
    name: str
    archived_at: datetime
    user_id: UUID


class ArchivedDocument(ArchiveItemBase):
    """Schema for archived documents."""
    
    file_size: int
    page_count: int | None = None
    folder_id: UUID | None = None
    folder_name: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class ArchivedFolder(ArchiveItemBase):
    """Schema for archived folders."""
    
    description: str | None = None
    color: str | None = None
    parent_id: UUID | None = None
    parent_name: str | None = None
    document_count: int = 0
    children_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ArchivedFolderWithChildren(ArchivedFolder):
    """Schema for archived folder with children."""
    
    children: list["ArchivedFolderWithChildren"] = []
    documents: list[ArchivedDocument] = []


class ArchiveStats(BaseModel):
    """Statistics about archive content."""
    
    total_documents: int
    total_folders: int
    total_size: int  # Total size in bytes
    oldest_item_date: datetime | None = None


class RestoreFolderRequest(BaseModel):
    """Request to restore a folder."""
    
    folder_id: UUID
    restore_children: bool = True
    new_parent_id: UUID | None = None


class RestoreDocumentRequest(BaseModel):
    """Request to restore documents."""
    
    document_ids: list[UUID]
    folder_id: UUID | None = None


class EmptyArchiveRequest(BaseModel):
    """Request to empty archive."""
    
    confirm: bool = True
    delete_all: bool = False  # If false, only delete items older than 30 days


class DeleteDocumentsRequest(BaseModel):
    """Request to permanently delete specific documents."""
    
    document_ids: list[UUID]
    confirm: bool = True


class DeleteFolderRequest(BaseModel):
    """Request to permanently delete a specific folder."""
    
    folder_id: UUID
    delete_children: bool = True
    confirm: bool = True