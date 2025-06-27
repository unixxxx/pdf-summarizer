"""Flashcard generation tasks for the worker."""

from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..common.database import get_db_session
from shared.models import Document
from ..common.logger import logger
from ..common.config import get_settings
from ..common.llm_factory import UnifiedLLMFactory
from ..common.retry import retry_on_llm_error

settings = get_settings()


# Schema definitions (copied from backend)
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


class Flashcard(BaseModel):
    """A single flashcard."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    front: str
    back: str
    type: FlashcardType
    difficulty: FlashcardDifficulty
    tags: List[str] = Field(default_factory=list)
    hint: str | None = None


class FlashcardGeneration(BaseModel):
    """Structured output for flashcard generation."""
    flashcards: List[Flashcard]


async def generate_flashcards(
    ctx: dict,
    document_id: str,
    user_id: str,
    num_cards: int = 20,
    card_types: List[str] | None = None,
    difficulty: str = "mixed"
) -> Dict[str, Any]:
    """
    Generate flashcards from a document.
    
    Args:
        ctx: arq context
        document_id: Document to generate flashcards from
        user_id: User who owns the document
        num_cards: Number of flashcards to generate
        card_types: Types of flashcards to generate
        difficulty: Difficulty level
        
    Returns:
        Generated flashcard set data
    """
    job_id = ctx.get("job_id", f"flashcards:{document_id}")
    
    try:
        # Initialize LLM factory
        llm_factory = UnifiedLLMFactory(settings)
        llm = llm_factory.create_chat_model(temperature=0.7)
        
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
        
        # 2. Prepare card types
        if not card_types:
            card_types = ["definition", "concept"]
        
        card_types_str = ", ".join(card_types)
        
        # 3. Create structured output parser
        structured_llm = llm.with_structured_output(FlashcardGeneration)
        
        # 4. Create the prompt
        prompt = f"""Generate {num_cards} flashcards from the following document.

Requirements:
- Card types: {card_types_str}
- Difficulty: {difficulty}
- Front side should contain a question, term, or prompt
- Back side should contain the answer, definition, or explanation
- For definition cards: term on front, definition on back
- For concept cards: concept/question on front, explanation on back
- For formula cards: formula name/usage on front, formula on back
- For fact cards: question on front, fact on back
- Include hints where helpful
- Add relevant tags for categorization
- Vary difficulty levels if "mixed" is selected

Document: {filename}

Content:
{text[:10000]}  # Limit context to avoid token limits

Generate the flashcards in the required format."""
        
        # 5. Generate flashcards with retry
        @retry_on_llm_error(max_attempts=3)
        async def generate_cards() -> FlashcardGeneration:
            return await structured_llm.ainvoke(prompt)
        
        result = await generate_cards()
        
        # 6. Format response
        flashcard_set_id = str(uuid4())
        flashcard_data = {
            "flashcard_set_id": flashcard_set_id,
            "document_id": document_id,
            "title": f"Flashcards: {filename}",
            "cards": [
                {
                    "id": card.id,
                    "front": card.front,
                    "back": card.back,
                    "type": card.type,
                    "difficulty": card.difficulty,
                    "tags": card.tags,
                    "hint": card.hint
                }
                for card in result.flashcards
            ],
            "total_cards": len(result.flashcards),
            "difficulty": difficulty,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "llm_model": llm_factory.get_provider_info()["model"],
                "document_title": filename,
                "card_types": card_types
            }
        }
        
        logger.info(
            "Flashcards generated",
            document_id=document_id,
            flashcard_set_id=flashcard_set_id,
            cards=len(result.flashcards)
        )
        
        return {
            "success": True,
            "flashcard_set": flashcard_data
        }
        
    except Exception as e:
        logger.error(
            "Flashcard generation failed",
            document_id=document_id,
            error=str(e),
            exc_info=True
        )
        raise