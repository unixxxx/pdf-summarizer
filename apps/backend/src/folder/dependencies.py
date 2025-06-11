"""Dependencies for Folder module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db
from ..storage.dependencies import StorageServiceDep
from .service import FolderService


def get_folder_service(
    storage_service: StorageServiceDep,
    db: AsyncSession = Depends(get_db)
) -> FolderService:
    """Get folder service instance."""
    return FolderService(db, storage_service)


FolderServiceDep = Annotated[FolderService, Depends(get_folder_service)]