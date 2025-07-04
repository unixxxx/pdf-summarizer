"""Async quiz router for quiz generation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import BadRequestException, NotFoundException
from ..database.session import get_db
from ..document.dependencies import DocumentServiceDep
from .dependencies import AsyncQuizServiceDep
from .schemas import QuizOptions

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"],
    responses={
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/document/{document_id}/generate/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate quiz asynchronously",
    description="Queue quiz generation for a document",
)
async def generate_quiz_async(
    document_id: UUID,
    options: QuizOptions,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    quiz_service: AsyncQuizServiceDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Queue quiz generation for a document."""
    try:
        # Enqueue quiz generation
        result = await quiz_service.enqueue_quiz_generation(
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
            detail=f"Failed to queue quiz generation: {str(e)}",
        )


@router.get(
    "/job/{job_id}/status",
    summary="Get quiz generation status",
    description="Check the status of a quiz generation job",
)
async def get_quiz_job_status(
    job_id: str,
    current_user: CurrentUserDep,
    quiz_service: AsyncQuizServiceDep,
) -> dict:
    """Get the status of a quiz generation job."""
    try:
        result = await quiz_service.get_quiz_status(job_id)
        
        # TODO: Add security check to ensure user owns the document/quiz
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )