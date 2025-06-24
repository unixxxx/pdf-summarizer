"""LLM-specific schemas for quiz module."""

from pydantic import BaseModel

from .schemas import QuizQuestion


class QuestionGeneration(BaseModel):
    """Model for LLM quiz generation output.
    
    This model is used for structured output from LLM when generating quiz questions.
    """
    questions: list[QuizQuestion]