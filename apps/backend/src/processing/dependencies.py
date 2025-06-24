"""Dependencies for processing module."""

from typing import Annotated

from fastapi import Depends

from ..library.document.dependencies import DocumentServiceDep
from ..storage.dependencies import StorageServiceDep
from .orchestrator import DocumentProcessingOrchestrator


def get_document_processing_orchestrator(
    document_service: DocumentServiceDep,
    storage_service: StorageServiceDep,
) -> DocumentProcessingOrchestrator:
    """Get document processing orchestrator instance."""
    return DocumentProcessingOrchestrator(
        document_service=document_service,
        storage_service=storage_service,
    )


# Type aliases for dependency injection
ProcessingOrchestratorDep = Annotated[
    DocumentProcessingOrchestrator, 
    Depends(get_document_processing_orchestrator)
]