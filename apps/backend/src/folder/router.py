"""Folder router module."""

from uuid import UUID

from fastapi import APIRouter, status

from ..auth.dependencies import CurrentUserDep
from .dependencies import FolderServiceDep
from .schemas import (
    AddDocumentToFolderRequest,
    FolderCreate,
    FolderResponse,
    FolderTree,
    FolderUpdate,
    MoveFolderRequest,
    RemoveDocumentFromFolderRequest,
)

router = APIRouter(prefix="/folder", tags=["folders"])


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> FolderResponse:
    """Create a new folder."""
    return await service.create_folder(current_user, folder_data)


@router.get("/tree", response_model=FolderTree)
async def get_folders_tree(
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> FolderTree:
    """Get all folders in a tree structure."""
    folders = await service.get_folders_tree(current_user)
    unfiled_count = await service.get_unfiled_document_count(current_user)
    total_document_count = await service.get_total_document_count(current_user)
    return FolderTree(
        folders=folders, 
        total_count=len(folders),
        unfiled_count=unfiled_count,
        total_document_count=total_document_count
    )


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: UUID,
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> FolderResponse:
    """Get a specific folder."""
    return await service.get_folder(current_user, folder_id)


@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    folder_data: FolderUpdate,
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> FolderResponse:
    """Update a folder."""
    return await service.update_folder(current_user, folder_id, folder_data)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> None:
    """Delete a folder and all its contents."""
    await service.delete_folder(current_user, folder_id)


@router.post("/{folder_id}/documents", response_model=FolderResponse)
async def add_documents_to_folder(
    folder_id: UUID,
    request: AddDocumentToFolderRequest,
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> FolderResponse:
    """Add documents to a folder (removes from other folders first)."""
    return await service.add_documents_to_folder(
        current_user, folder_id, request.document_ids
    )


@router.delete("/{folder_id}/documents", response_model=FolderResponse)
async def remove_documents_from_folder(
    folder_id: UUID,
    request: RemoveDocumentFromFolderRequest,
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> FolderResponse:
    """Remove documents from a folder."""
    return await service.remove_documents_from_folder(
        current_user, folder_id, request.document_ids
    )




@router.post("/{folder_id}/move", response_model=FolderResponse)
async def move_folder(
    folder_id: UUID,
    request: MoveFolderRequest,
    current_user: CurrentUserDep,
    service: FolderServiceDep,
) -> FolderResponse:
    """Move a folder to a different parent."""
    return await service.update_folder(
        current_user, folder_id, FolderUpdate(parent_id=request.parent_id)
    )