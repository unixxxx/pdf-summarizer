"""LLM-specific schemas for flashcard module."""

from pydantic import BaseModel

from .schemas import Flashcard


class FlashcardGeneration(BaseModel):
    """Model for LLM flashcard generation output.
    
    This model is used for structured output from LLM when generating flashcards.
    """
    cards: list[Flashcard]