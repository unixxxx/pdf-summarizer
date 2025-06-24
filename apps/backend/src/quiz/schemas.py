"""Schemas for quiz module."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class QuizQuestionType(str, Enum):
    """Types of quiz questions."""
    
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class QuizDifficulty(str, Enum):
    """Quiz difficulty levels."""
    
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class QuizOptions(BaseModel):
    """Options for quiz generation."""
    
    num_questions: int = Field(10, ge=1, le=50, description="Number of questions")
    question_types: list[QuizQuestionType] = Field(
        default=[QuizQuestionType.MULTIPLE_CHOICE],
        description="Types of questions to generate"
    )
    difficulty: QuizDifficulty = Field(
        default=QuizDifficulty.MEDIUM,
        description="Difficulty level"
    )
    focus_areas: list[str] | None = Field(
        None,
        description="Specific topics to focus on"
    )


class QuizQuestion(BaseModel):
    """A single quiz question."""
    
    id: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    type: QuizQuestionType = Field(..., description="Question type")
    options: list[str] | None = Field(None, description="Options for multiple choice")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Explanation of the answer")
    difficulty: QuizDifficulty | None = Field(None, description="Question difficulty")
    tags: list[str] = Field(default_factory=list, description="Question tags")


class QuizResponse(BaseModel):
    """Response containing generated quiz."""
    
    quiz_id: str = Field(..., description="Unique quiz ID")
    document_id: str = Field(..., description="Source document ID")
    title: str = Field(..., description="Quiz title")
    questions: list[QuizQuestion] = Field(..., description="Quiz questions")
    total_questions: int = Field(..., description="Total number of questions")
    difficulty: QuizDifficulty = Field(..., description="Overall difficulty")
    created_at: datetime = Field(..., description="When quiz was created")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class QuizSubmission(BaseModel):
    """User's quiz submission."""
    
    quiz_id: str = Field(..., description="Quiz ID")
    answers: dict[str, str] = Field(..., description="User's answers by question ID")


class QuizResult(BaseModel):
    """Quiz submission results."""
    
    quiz_id: str = Field(..., description="Quiz ID")
    score: int = Field(..., description="Number of correct answers")
    total: int = Field(..., description="Total number of questions")
    percentage: float = Field(..., description="Score percentage")
    results: dict[str, dict] = Field(..., description="Detailed results by question")
    completed_at: datetime = Field(..., description="When quiz was completed")