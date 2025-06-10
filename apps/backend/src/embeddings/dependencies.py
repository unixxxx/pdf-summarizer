"""Dependencies for embeddings service."""

from typing import Annotated

from fastapi import Depends

from ..common.dependencies import LLMFactoryDep
from ..common.exceptions import ServiceUnavailableError
from ..config import Settings, get_settings
from .embeddings_service import EmbeddingsService

# Cache the embeddings service
_embeddings_service: EmbeddingsService | None = None


def get_embeddings_service(
    factory: LLMFactoryDep,
    settings: Settings = Depends(get_settings),
) -> EmbeddingsService:
    """Get embeddings service instance."""
    global _embeddings_service
    
    if _embeddings_service is None:
        try:
            _embeddings_service = EmbeddingsService(settings, factory)
        except Exception:
            raise ServiceUnavailableError("Embeddings")
    
    return _embeddings_service


# Type alias for dependency injection
EmbeddingsServiceDep = Annotated[EmbeddingsService, Depends(get_embeddings_service)]