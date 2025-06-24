"""Schemas for flashcard module."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FlashcardType(str, Enum):
    """Types of flashcards."""
    
    DEFINITION = "definition"
    CONCEPT = "concept"
    FORMULA = "formula"
    FACT = "fact"


class FlashcardDifficulty(str, Enum):
    """Flashcard difficulty levels."""
    
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class FlashcardOptions(BaseModel):
    """Options for flashcard generation."""
    
    num_cards: int = Field(20, ge=1, le=100, description="Number of flashcards")
    card_types: list[FlashcardType] = Field(
        default=[FlashcardType.DEFINITION, FlashcardType.CONCEPT],
        description="Types of flashcards to generate"
    )
    difficulty: FlashcardDifficulty = Field(
        default=FlashcardDifficulty.MIXED,
        description="Difficulty level"
    )


class Flashcard(BaseModel):
    """A single flashcard."""
    
    id: str = Field(..., description="Flashcard ID")
    front: str = Field(..., description="Front side of the card")
    back: str = Field(..., description="Back side of the card")
    type: FlashcardType = Field(..., description="Card type")
    difficulty: FlashcardDifficulty = Field(..., description="Card difficulty")
    tags: list[str] = Field(default_factory=list, description="Card tags")
    hint: str | None = Field(None, description="Optional hint")


class FlashcardSetResponse(BaseModel):
    """Response containing generated flashcard set."""
    
    flashcard_set_id: str = Field(..., description="Unique flashcard set ID")
    document_id: str = Field(..., description="Source document ID")
    title: str = Field(..., description="Flashcard set title")
    cards: list[Flashcard] = Field(..., description="Flashcards")
    total_cards: int = Field(..., description="Total number of cards")
    difficulty: FlashcardDifficulty = Field(..., description="Overall difficulty")
    created_at: datetime = Field(..., description="When set was created")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class FlashcardReview(BaseModel):
    """Review data for a flashcard."""
    
    card_id: str = Field(..., description="Flashcard ID")
    confidence: int = Field(..., ge=1, le=5, description="Confidence level (1-5)")
    time_spent: int = Field(..., ge=0, description="Time spent in seconds")


class FlashcardSessionUpdate(BaseModel):
    """Update for a flashcard study session."""
    
    session_id: str = Field(..., description="Study session ID")
    reviews: list[FlashcardReview] = Field(..., description="Card reviews")
    
    
class FlashcardProgress(BaseModel):
    """User's progress with a flashcard set."""
    
    flashcard_set_id: str = Field(..., description="Flashcard set ID")
    cards_reviewed: int = Field(..., description="Number of cards reviewed")
    total_cards: int = Field(..., description="Total cards in set")
    average_confidence: float = Field(..., description="Average confidence score")
    last_reviewed: datetime = Field(..., description="Last review date")
    next_review: datetime | None = Field(None, description="Suggested next review")