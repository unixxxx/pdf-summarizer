"""Dependencies for chat service."""

from typing import Annotated

from fastapi import Depends

from ..common.dependencies import LLMFactoryDep
from ..common.exceptions import ServiceUnavailableError
from ..config import Settings, get_settings
from ..embeddings.dependencies import get_embeddings_service
from ..embeddings.service import EmbeddingsService
from .service import ChatService

# Cache the chat service
_chat_service: ChatService | None = None


def get_chat_service(
    factory: LLMFactoryDep,
    settings: Settings = Depends(get_settings),
    embeddings_service: EmbeddingsService = Depends(get_embeddings_service),
) -> ChatService:
    """Get chat service instance."""
    global _chat_service
    
    if _chat_service is None:
        try:
            _chat_service = ChatService(settings, embeddings_service, factory)
        except Exception:
            raise ServiceUnavailableError("Chat")
    
    return _chat_service


# Type alias for dependency injection
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]