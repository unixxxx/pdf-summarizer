"""Flashcard router for flashcard generation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.dependencies import LLMFactoryDep
from ..common.exceptions import NotFoundException
from ..database.session import get_db
from ..document.dependencies import DocumentServiceDep
from .schemas import (
    FlashcardOptions,
    FlashcardProgress,
    FlashcardSessionUpdate,
    FlashcardSetResponse,
)
from .service import FlashcardService

router = APIRouter(
    prefix="/flashcard",
    tags=["Flashcard"],
    responses={
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/document/{document_id}/generate",
    response_model=FlashcardSetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate flashcards",
    description="Generate flashcards from a document",
)
async def generate_flashcards(
    document_id: UUID,
    options: FlashcardOptions,
    current_user: CurrentUserDep,
    llm_factory: LLMFactoryDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> FlashcardSetResponse:
    """Generate flashcards from a document."""
    try:
        # Create flashcard service
        llm = llm_factory.create_chat_model()
        flashcard_service = FlashcardService(llm)
        
        # Generate flashcards (document validation handled in service)
        flashcard_set = await flashcard_service.generate_flashcards_from_document(
            document_id=document_id,
            user_id=current_user.id,
            options=options,
            document_service=document_service,
            db=db,
        )
        
        return flashcard_set
        
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except Exception as e:
        from ..common.exceptions import BadRequestException
        if isinstance(e, BadRequestException):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.detail,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}",
        )


@router.post(
    "/session/update",
    status_code=status.HTTP_200_OK,
    summary="Update study session",
    description="Update flashcard study session with review results",
)
async def update_study_session(
    session_update: FlashcardSessionUpdate,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update flashcard study session."""
    try:
        # TODO: Implement session update logic
        # For now, return success response
        
        return {
            "status": "success",
            "message": f"Updated {len(session_update.reviews)} reviews for session {session_update.session_id}",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}",
        )


@router.get(
    "/set/{flashcard_set_id}/progress",
    response_model=FlashcardProgress,
    summary="Get flashcard progress",
    description="Get user's progress with a flashcard set",
)
async def get_flashcard_progress(
    flashcard_set_id: str,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> FlashcardProgress:
    """Get user's progress with a flashcard set."""
    try:
        # TODO: Implement progress retrieval logic
        # For now, return mock progress
        
        from datetime import datetime
        
        return FlashcardProgress(
            flashcard_set_id=flashcard_set_id,
            cards_reviewed=15,
            total_cards=20,
            average_confidence=3.5,
            last_reviewed=datetime.now(),
            next_review=None,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}",
        )