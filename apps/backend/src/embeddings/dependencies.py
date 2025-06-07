"""Dependencies for embeddings service."""

from typing import Annotated

from fastapi import Depends

from ..common.exceptions import ServiceUnavailableError
from ..config import Settings, get_settings
from .service import EmbeddingsService

# Cache the embeddings service
_embeddings_service: EmbeddingsService | None = None


def get_embeddings_service(settings: Settings = Depends(get_settings)) -> EmbeddingsService:
    """Get embeddings service instance."""
    global _embeddings_service
    
    if _embeddings_service is None:
        try:
            _embeddings_service = EmbeddingsService(settings)
        except Exception:
            raise ServiceUnavailableError("Embeddings")
    
    return _embeddings_service


# Type alias for dependency injection
EmbeddingsServiceDep = Annotated[EmbeddingsService, Depends(get_embeddings_service)]