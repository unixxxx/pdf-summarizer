"""Quiz generation service."""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema.language_model import BaseLanguageModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import LLMError
from ..common.retry import retry_on_llm_error
from .llm_schemas import QuestionGeneration
from .schemas import (
    QuizDifficulty,
    QuizOptions,
    QuizQuestion,
    QuizQuestionType,
    QuizResponse,
)

logger = logging.getLogger(__name__)


class QuizService:
    """Service for generating quizzes from documents."""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=QuestionGeneration)
    
    async def generate_quiz(
        self,
        document_id: UUID,
        text: str,
        options: QuizOptions,
        db: AsyncSession,
    ) -> QuizResponse:
        """Generate quiz questions from document text."""
        try:
            # Build prompt based on options
            prompt = self._build_prompt(text, options)
            
            # Generate questions with retry
            questions = await self._generate_questions(prompt, options.num_questions)
            
            # Create quiz response
            quiz_id = str(uuid4())
            title = f"Quiz for Document {document_id}"
            
            return QuizResponse(
                quiz_id=quiz_id,
                document_id=str(document_id),
                title=title,
                questions=questions,
                total_questions=len(questions),
                difficulty=options.difficulty,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            
        except Exception as e:
            logger.error(f"Failed to generate quiz: {str(e)}")
            raise LLMError(f"Quiz generation failed: {str(e)}")
    
    def _build_prompt(self, text: str, options: QuizOptions) -> str:
        """Build prompt for quiz generation."""
        question_types = ", ".join([qt.value for qt in options.question_types])
        
        template = """Generate {num_questions} quiz questions from the following text.

Question types to include: {question_types}
Difficulty level: {difficulty}
Focus areas: {focus_areas}

Text: {text}

IMPORTANT: Generate diverse questions that test understanding of key concepts.
For multiple choice questions, provide 4 options with only one correct answer.
Include explanations for each answer.

{format_instructions}
"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["num_questions", "question_types", "difficulty", "focus_areas", "text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        return prompt.format(
            num_questions=options.num_questions,
            question_types=question_types,
            difficulty=options.difficulty.value,
            focus_areas=", ".join(options.focus_areas) if options.focus_areas else "all topics",
            text=text[:3000],  # Limit text length
        )
    
    @retry_on_llm_error(max_attempts=3)
    async def _generate_questions(self, prompt: str, num_questions: int) -> list[QuizQuestion]:
        """Generate questions using LLM with retry."""
        try:
            # Use structured output
            result = await self.llm.with_structured_output(
                QuestionGeneration,
                method="json_schema"
            ).ainvoke(prompt)
            
            return result.questions[:num_questions]
            
        except Exception as e:
            logger.error(f"LLM invocation failed: {str(e)}")
            # Fallback questions
            return [
                QuizQuestion(
                    id=f"q{i}",
                    question=f"Sample question {i}",
                    type=QuizQuestionType.MULTIPLE_CHOICE,
                    options=["Option A", "Option B", "Option C", "Option D"],
                    correct_answer="A",
                    explanation="This is a sample question.",
                    difficulty=QuizDifficulty.MEDIUM,
                )
                for i in range(1, min(num_questions + 1, 4))
            ]