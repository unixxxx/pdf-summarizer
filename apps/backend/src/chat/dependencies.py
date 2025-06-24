"""Dependencies for chat service."""

from typing import Annotated

from fastapi import Depends

from ..common.dependencies import LLMFactoryDep
from ..common.exceptions import ServiceUnavailableError
from ..config import Settings, get_settings
from .service import ChatService

# Cache the chat service
_chat_service: ChatService | None = None


def get_chat_service(
    factory: LLMFactoryDep, settings: Settings = Depends(get_settings),
) -> ChatService:
    """Get chat service instance."""
    global _chat_service
    
    if _chat_service is None:
        # Try to get embeddings service, but don't fail if unavailable
        embeddings_service = None
        try:
            from ..embeddings.dependencies import get_embeddings_service
            # Create a dummy function to get embeddings without FastAPI DI
            embeddings_service = get_embeddings_service(factory, settings)
        except Exception as e:
            # Log but don't fail - chat can work without embeddings
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Embeddings service unavailable for chat: {str(e)}")
        
        try:
            _chat_service = ChatService(settings, embeddings_service, factory)
        except Exception as e:
            raise ServiceUnavailableError(f"Chat service initialization failed: {str(e)}")
    
    return _chat_service


# Type alias for dependency injection
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]