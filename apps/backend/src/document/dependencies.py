"""Dependencies for Document domain."""

from typing import Annotated

from fastapi import Depends, Request

from ..config import Settings, get_settings
from .service import DocumentService


def get_document_service(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentService:
    """Get document service instance."""
    service = DocumentService()
    
    # If search service is available in app state, use it
    if hasattr(request.app.state, "search_service"):
        service.search_service = request.app.state.search_service
    
    return service


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]