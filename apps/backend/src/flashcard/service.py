"""Flashcard generation service."""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema.language_model import BaseLanguageModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import LLMError
from ..common.retry import retry_on_llm_error
from .llm_schemas import FlashcardGeneration
from .schemas import (
    Flashcard,
    FlashcardDifficulty,
    FlashcardOptions,
    FlashcardSetResponse,
    FlashcardType,
)

logger = logging.getLogger(__name__)


class FlashcardService:
    """Service for generating flashcards from documents."""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=FlashcardGeneration)
    
    async def generate_flashcards(
        self,
        document_id: UUID,
        text: str,
        options: FlashcardOptions,
        db: AsyncSession,
    ) -> FlashcardSetResponse:
        """Generate flashcards from document text."""
        try:
            # Build prompt based on options
            prompt = self._build_prompt(text, options)
            
            # Generate flashcards with retry
            flashcards = await self._generate_flashcards(prompt, options.num_cards)
            
            # Create flashcard set response
            set_id = str(uuid4())
            title = f"Flashcards for Document {document_id}"
            
            return FlashcardSetResponse(
                flashcard_set_id=set_id,
                document_id=str(document_id),
                title=title,
                cards=flashcards,
                total_cards=len(flashcards),
                difficulty=options.difficulty,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            
        except Exception as e:
            logger.error(f"Failed to generate flashcards: {str(e)}")
            raise LLMError(f"Flashcard generation failed: {str(e)}")
    
    def _build_prompt(self, text: str, options: FlashcardOptions) -> str:
        """Build prompt for flashcard generation."""
        card_types = ", ".join([ct.value for ct in options.card_types])
        
        template = """Generate {num_cards} flashcards from the following text.

Card types to include: {card_types}
Difficulty level: {difficulty}

Text: {text}

IMPORTANT: Create flashcards that help memorize key concepts, definitions, and important facts.
- For definition cards, put the term on the front and definition on the back
- For concept cards, put a question on the front and answer on the back
- For formula cards, put the formula name/description on front and the formula on back
- Include relevant tags for each card
- Keep cards concise and focused on one concept each

{format_instructions}
"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["num_cards", "card_types", "difficulty", "text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        return prompt.format(
            num_cards=options.num_cards,
            card_types=card_types,
            difficulty=options.difficulty.value,
            text=text[:3000],  # Limit text length
        )
    
    @retry_on_llm_error(max_attempts=3)
    async def _generate_flashcards(self, prompt: str, num_cards: int) -> list[Flashcard]:
        """Generate flashcards using LLM with retry."""
        try:
            # Use structured output
            result = await self.llm.with_structured_output(
                FlashcardGeneration,
                method="json_schema"
            ).ainvoke(prompt)
            
            return result.cards[:num_cards]
            
        except Exception as e:
            logger.error(f"LLM invocation failed: {str(e)}")
            # Fallback flashcards
            return [
                Flashcard(
                    id=f"c{i}",
                    front=f"Sample concept {i}",
                    back=f"This is the explanation for concept {i}",
                    type=FlashcardType.CONCEPT,
                    difficulty=FlashcardDifficulty.MEDIUM,
                    tags=["sample", "fallback"],
                )
                for i in range(1, min(num_cards + 1, 4))
            ]