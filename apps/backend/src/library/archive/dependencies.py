"""Dependencies for archive module."""

from typing import Annotated

from fastapi import Depends

from ...storage.dependencies import StorageServiceDep
from .service import ArchiveService


def get_archive_service(
    storage_service: StorageServiceDep, ) -> ArchiveService:
    """Get archive service instance."""
    return ArchiveService(storage_service)


ArchiveServiceDep = Annotated[ArchiveService, Depends(get_archive_service)]