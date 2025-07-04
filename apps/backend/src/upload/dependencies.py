"""Dependencies for Upload domain."""

from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from ..document.dependencies import DocumentServiceDep
from ..folder.dependencies import FolderServiceDep
from ..storage.dependencies import StorageServiceDep
from .service import UploadService


def get_upload_service(
    storage_service: StorageServiceDep,
    document_service: DocumentServiceDep,
    folder_service: FolderServiceDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadService:
    """Get upload service instance."""
    return UploadService(
        storage_service=storage_service,
        document_service=document_service,
        folder_service=folder_service,
        settings=settings,
    )


UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]