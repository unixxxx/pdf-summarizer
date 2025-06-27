"""Dependencies for processing module."""

from typing import Annotated

from fastapi import Depends

from .service import ProcessingService


def get_processing_service() -> ProcessingService:
    """Get processing service instance."""
    return ProcessingService()


# Type aliases for dependency injection
ProcessingServiceDep = Annotated[
    ProcessingService,
    Depends(get_processing_service)
]