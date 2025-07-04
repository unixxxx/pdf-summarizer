"""Async flashcard router for flashcard generation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import BadRequestException, NotFoundException
from ..database.session import get_db
from ..document.dependencies import DocumentServiceDep
from .dependencies import AsyncFlashcardServiceDep
from .schemas import FlashcardOptions

router = APIRouter(
    prefix="/flashcard",
    tags=["Flashcard"],
    responses={
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/document/{document_id}/generate/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate flashcards asynchronously",
    description="Queue flashcard generation for a document",
)
async def generate_flashcards_async(
    document_id: UUID,
    options: FlashcardOptions,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    flashcard_service: AsyncFlashcardServiceDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Queue flashcard generation for a document."""
    try:
        # Enqueue flashcard generation
        result = await flashcard_service.enqueue_flashcard_generation(
            document_id=document_id,
            user_id=current_user.id,
            options=options,
            document_service=document_service,
            db=db,
        )
        
        return result
        
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue flashcard generation: {str(e)}",
        )


@router.get(
    "/job/{job_id}/status",
    summary="Get flashcard generation status",
    description="Check the status of a flashcard generation job",
)
async def get_flashcard_job_status(
    job_id: str,
    current_user: CurrentUserDep,
    flashcard_service: AsyncFlashcardServiceDep,
) -> dict:
    """Get the status of a flashcard generation job."""
    try:
        result = await flashcard_service.get_flashcard_status(job_id)
        
        # TODO: Add security check to ensure user owns the document/flashcards
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )