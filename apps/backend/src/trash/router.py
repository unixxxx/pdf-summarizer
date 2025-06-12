"""API routes for trash functionality."""

from fastapi import APIRouter, HTTPException, status

from ..auth.dependencies import CurrentUserDep
from .dependencies import TrashServiceDep
from .schemas import (
    DeleteDocumentsRequest,
    DeleteFolderRequest,
    EmptyTrashRequest,
    RestoreDocumentRequest,
    RestoreFolderRequest,
    TrashedDocument,
    TrashedFolderWithChildren,
    TrashStats,
)

router = APIRouter(prefix="/trash", tags=["trash"])


@router.get("/stats", response_model=TrashStats)
async def get_trash_stats(
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> TrashStats:
    """Get statistics about user's trash."""
    return await trash_service.get_trash_stats(current_user)


@router.get("/documents", response_model=list[TrashedDocument])
async def get_trashed_documents(
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> list[TrashedDocument]:
    """Get all trashed documents."""
    return await trash_service.get_trashed_documents(current_user)


@router.get("/folders", response_model=list[TrashedFolderWithChildren])
async def get_trashed_folders(
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> list[TrashedFolderWithChildren]:
    """Get all trashed folders in a tree structure."""
    return await trash_service.get_trashed_folders(current_user)


@router.post("/restore/folder", status_code=status.HTTP_204_NO_CONTENT)
async def restore_folder(
    request: RestoreFolderRequest,
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> None:
    """Restore a folder from trash."""
    try:
        await trash_service.restore_folder(current_user, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/restore/documents", status_code=status.HTTP_204_NO_CONTENT)
async def restore_documents(
    request: RestoreDocumentRequest,
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> None:
    """Restore documents from trash."""
    try:
        await trash_service.restore_documents(current_user, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/documents", status_code=status.HTTP_204_NO_CONTENT)
async def delete_documents_permanently(
    request: DeleteDocumentsRequest,
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> None:
    """Permanently delete specific documents from trash."""
    try:
        await trash_service.delete_documents_permanently(current_user, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/folder", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder_permanently(
    request: DeleteFolderRequest,
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> None:
    """Permanently delete a specific folder from trash."""
    try:
        await trash_service.delete_folder_permanently(current_user, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/empty", status_code=status.HTTP_204_NO_CONTENT)
async def empty_trash(
    request: EmptyTrashRequest,
    current_user: CurrentUserDep,
    trash_service: TrashServiceDep,
) -> None:
    """Empty the trash, permanently deleting items."""
    try:
        await trash_service.empty_trash(current_user, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )