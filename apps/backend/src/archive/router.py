"""API routes for archive functionality."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..database.session import get_db
from .dependencies import ArchiveServiceDep
from .schemas import (
    ArchivedDocument,
    ArchivedFolderWithChildren,
    ArchiveStats,
    DeleteDocumentsRequest,
    DeleteFolderRequest,
    EmptyArchiveRequest,
    RestoreDocumentRequest,
    RestoreFolderRequest,
)

router = APIRouter(prefix="/archive", tags=["archive"])


@router.get("/stats", response_model=ArchiveStats)
async def get_archive_stats(
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> ArchiveStats:
    """Get statistics about user's archive."""
    return await archive_service.get_archive_stats(db, current_user)


@router.get("/documents", response_model=list[ArchivedDocument])
async def get_archived_documents(
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> list[ArchivedDocument]:
    """Get all archived documents."""
    return await archive_service.get_archived_documents(db, current_user)


@router.get("/folders", response_model=list[ArchivedFolderWithChildren])
async def get_archived_folders(
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> list[ArchivedFolderWithChildren]:
    """Get all archived folders in a tree structure."""
    return await archive_service.get_archived_folders(db, current_user)


@router.post("/restore/folder", status_code=status.HTTP_204_NO_CONTENT)
async def restore_folder(
    request: RestoreFolderRequest,
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Restore a folder from archive."""
    await archive_service.restore_folder(db, current_user, request.folder_id)


@router.post("/restore/documents", status_code=status.HTTP_204_NO_CONTENT)
async def restore_documents(
    request: RestoreDocumentRequest,
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Restore documents from archive."""
    await archive_service.restore_documents(db, current_user, request.document_ids)


@router.delete("/documents", status_code=status.HTTP_204_NO_CONTENT)
async def delete_documents_permanently(
    request: DeleteDocumentsRequest,
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete specific documents from archive."""
    await archive_service.permanently_delete_documents(db, current_user, request.document_ids)


@router.delete("/folder", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder_permanently(
    request: DeleteFolderRequest,
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete a specific folder from archive."""
    await archive_service.permanently_delete_folder(db, current_user, request.folder_id)


@router.post("/empty", status_code=status.HTTP_204_NO_CONTENT)
async def empty_archive(
    request: EmptyArchiveRequest,
    current_user: CurrentUserDep,
    archive_service: ArchiveServiceDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Empty the archive, permanently deleting items."""
    await archive_service.empty_archive(db, current_user)