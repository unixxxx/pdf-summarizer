"""Dependencies for trash module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db
from ..storage.dependencies import StorageServiceDep
from .service import TrashService


def get_trash_service(
    storage_service: StorageServiceDep,
    db: AsyncSession = Depends(get_db)
) -> TrashService:
    """Get trash service instance."""
    return TrashService(db, storage_service)


TrashServiceDep = Annotated[TrashService, Depends(get_trash_service)]