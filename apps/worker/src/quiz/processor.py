"""Quiz generation tasks for the worker."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from shared.models import Document
from sqlalchemy import select

from ..common.config import get_settings
from ..common.database import get_db_session
from ..common.llm_factory import UnifiedLLMFactory
from ..common.logger import logger
from ..common.retry import retry_on_llm_error

settings = get_settings()


# Schema definitions (copied from backend)
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


class QuizQuestion(BaseModel):
    """A single quiz question."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    type: QuizQuestionType
    options: list[str] | None = None
    correct_answer: str
    explanation: str
    difficulty: QuizDifficulty | None = None
    tags: list[str] = Field(default_factory=list)


class QuestionGeneration(BaseModel):
    """Structured output for quiz generation."""
    questions: list[QuizQuestion]


async def generate_quiz(
    ctx: dict, 
    document_id: str, 
    user_id: str,
    num_questions: int = 10,
    question_types: list[str] | None = None,
    difficulty: str = "medium",
    focus_areas: list[str] | None = None
) -> dict[str, Any]:
    """
    Generate quiz questions from a document.
    
    Args:
        ctx: arq context
        document_id: Document to generate quiz from
        user_id: User who owns the document
        num_questions: Number of questions to generate
        question_types: Types of questions to generate
        difficulty: Difficulty level
        focus_areas: Specific topics to focus on
        
    Returns:
        Generated quiz data
    """
    job_id = ctx.get("job_id", f"quiz:{document_id}")
    
    try:
        # Initialize LLM factory
        llm_factory = UnifiedLLMFactory(settings)
        llm = llm_factory.create_chat_model(temperature=0.5)
        
        # 1. Fetch document
        async with get_db_session() as db:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            if document.user_id != user_id:
                raise ValueError(f"Document {document_id} does not belong to user {user_id}")
            
            if not document.extracted_text:
                raise ValueError(f"Document {document_id} has no extracted text")
            
            filename = document.filename
            text = document.extracted_text
        
        # 2. Prepare question types
        if not question_types:
            question_types = ["multiple_choice"]
        
        question_types_str = ", ".join(question_types)
        
        # 3. Create structured output parser
        structured_llm = llm.with_structured_output(QuestionGeneration)
        
        # 4. Create the prompt
        prompt = f"""Generate {num_questions} quiz questions from the following document.

Requirements:
- Question types: {question_types_str}
- Difficulty: {difficulty}
{"- Focus on: " + ", ".join(focus_areas) if focus_areas else ""}
- For multiple choice questions, provide 4 options
- For true/false questions, the correct answer should be "True" or "False"
- For short answer questions, keep the correct answer concise
- Provide clear explanations for each answer
- Make questions test understanding, not just memorization

Document: {filename}

Content:
{text[:10000]}  # Limit context to avoid token limits

Generate the quiz questions in the required format."""
        
        # 5. Generate quiz with retry
        @retry_on_llm_error(max_attempts=3)
        async def generate_questions() -> QuestionGeneration:
            return await structured_llm.ainvoke(prompt)
        
        result = await generate_questions()
        
        # 6. Format response
        quiz_id = str(uuid4())
        quiz_data = {
            "quiz_id": quiz_id,
            "document_id": document_id,
            "title": f"Quiz: {filename}",
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "type": q.type,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty or difficulty,
                    "tags": q.tags
                }
                for q in result.questions
            ],
            "total_questions": len(result.questions),
            "difficulty": difficulty,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "llm_model": llm_factory.get_provider_info()["model"],
                "document_title": filename,
                "focus_areas": focus_areas
            }
        }
        
        logger.info(
            "Quiz generated",
            document_id=document_id,
            quiz_id=quiz_id,
            questions=len(result.questions)
        )
        
        return {
            "success": True,
            "quiz": quiz_data
        }
        
    except Exception as e:
        logger.error(
            "Quiz generation failed",
            document_id=document_id,
            error=str(e),
            exc_info=True
        )
        raise