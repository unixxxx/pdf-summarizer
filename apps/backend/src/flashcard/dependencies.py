"""Dependencies for Flashcard domain."""

from typing import Annotated

from fastapi import Depends

from .async_service import AsyncFlashcardService


def get_async_flashcard_service() -> AsyncFlashcardService:
    """Get async flashcard service instance."""
    return AsyncFlashcardService()


AsyncFlashcardServiceDep = Annotated[AsyncFlashcardService, Depends(get_async_flashcard_service)]