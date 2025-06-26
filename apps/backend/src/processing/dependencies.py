"""Dependencies for processing module."""

from typing import Annotated

from fastapi import Depends

from ..document.dependencies import DocumentServiceDep
from ..storage.dependencies import StorageServiceDep
from .orchestrator import DocumentProcessingOrchestrator
from .service import ProcessingService


def get_document_processing_orchestrator(
    document_service: DocumentServiceDep,
    storage_service: StorageServiceDep,
) -> DocumentProcessingOrchestrator:
    """Get document processing orchestrator instance."""
    return DocumentProcessingOrchestrator(
        document_service=document_service,
        storage_service=storage_service,
    )


def get_processing_service() -> ProcessingService:
    """Get processing service instance."""
    return ProcessingService()


# Type aliases for dependency injection
ProcessingOrchestratorDep = Annotated[
    DocumentProcessingOrchestrator, 
    Depends(get_document_processing_orchestrator)
]

ProcessingServiceDep = Annotated[
    ProcessingService,
    Depends(get_processing_service)
]