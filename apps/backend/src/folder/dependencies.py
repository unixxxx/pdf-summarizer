"""Dependencies for Folder module."""

from typing import Annotated

from fastapi import Depends

from ..tag.dependencies import TagServiceDep
from .service import FolderService


def get_folder_service(tag_service: TagServiceDep) -> FolderService:
    """Get folder service instance."""
    return FolderService(tag_service)


FolderServiceDep = Annotated[FolderService, Depends(get_folder_service)]