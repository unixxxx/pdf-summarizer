"""Dependencies for flashcard module."""

from typing import Annotated

from fastapi import Depends

from ..common.dependencies import LLMFactoryDep
from .service import FlashcardService


async def get_flashcard_service(
    llm_factory: LLMFactoryDep, ) -> FlashcardService:
    """Get flashcard service instance."""
    llm = llm_factory.create_chat_model()
    return FlashcardService(llm)


FlashcardServiceDep = Annotated[FlashcardService, Depends(get_flashcard_service)]