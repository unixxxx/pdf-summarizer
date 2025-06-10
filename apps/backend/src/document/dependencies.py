"""Dependencies for Document domain."""

from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from .document_service import DocumentService


def get_document_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentService:
    """Get document service instance."""
    return DocumentService()


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]