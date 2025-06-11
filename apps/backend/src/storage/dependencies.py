"""Dependencies for storage module."""

from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from .service import StorageService


def get_storage_service(settings: Annotated[Settings, Depends(get_settings)]) -> StorageService:
    """Get storage service instance."""
    return StorageService(settings)


StorageServiceDep = Annotated[StorageService, Depends(get_storage_service)]