"""Schemas for trash functionality."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TrashItemBase(BaseModel):
    """Base schema for trash items."""
    
    id: UUID
    name: str
    deleted_at: datetime
    user_id: UUID


class TrashedDocument(TrashItemBase):
    """Schema for trashed documents."""
    
    file_size: int
    page_count: Optional[int] = None
    folder_id: Optional[UUID] = None
    folder_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TrashedFolder(TrashItemBase):
    """Schema for trashed folders."""
    
    description: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[UUID] = None
    parent_name: Optional[str] = None
    document_count: int = 0
    children_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class TrashedFolderWithChildren(TrashedFolder):
    """Schema for trashed folder with children."""
    
    children: list["TrashedFolderWithChildren"] = []
    documents: list[TrashedDocument] = []


class TrashStats(BaseModel):
    """Statistics about trash content."""
    
    total_documents: int
    total_folders: int
    total_size: int  # Total size in bytes
    oldest_item_date: Optional[datetime] = None


class RestoreFolderRequest(BaseModel):
    """Request to restore a folder."""
    
    folder_id: UUID
    restore_children: bool = True
    new_parent_id: Optional[UUID] = None


class RestoreDocumentRequest(BaseModel):
    """Request to restore documents."""
    
    document_ids: list[UUID]
    folder_id: Optional[UUID] = None


class EmptyTrashRequest(BaseModel):
    """Request to empty trash."""
    
    confirm: bool = True
    delete_all: bool = False  # If false, only delete items older than 30 days