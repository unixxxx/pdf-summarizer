"""Quiz router for quiz generation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.dependencies import LLMFactoryDep
from ..common.exceptions import NotFoundException
from ..database.session import get_db
from ..document.dependencies import DocumentServiceDep
from .schemas import QuizOptions, QuizResponse, QuizResult, QuizSubmission
from .service import QuizService

router = APIRouter(
    prefix="/quiz",
    tags=["Quiz"],
    responses={
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/document/{document_id}/generate",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate quiz",
    description="Generate quiz questions from a document",
)
async def generate_quiz(
    document_id: UUID,
    options: QuizOptions,
    current_user: CurrentUserDep,
    llm_factory: LLMFactoryDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> QuizResponse:
    """Generate quiz questions from a document."""
    try:
        # Create quiz service
        llm = llm_factory.create_chat_model()
        quiz_service = QuizService(llm)
        
        # Generate quiz (document validation handled in service)
        quiz = await quiz_service.generate_quiz_from_document(
            document_id=document_id,
            user_id=current_user.id,
            options=options,
            document_service=document_service,
            db=db,
        )
        
        return quiz
        
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
            detail=f"Failed to generate quiz: {str(e)}",
        )


@router.post(
    "/{quiz_id}/submit",
    response_model=QuizResult,
    summary="Submit quiz answers",
    description="Submit answers for a quiz and get results",
)
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmission,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> QuizResult:
    """Submit quiz answers and get results."""
    try:
        # TODO: Implement quiz submission logic
        # For now, return mock results
        
        return QuizResult(
            quiz_id=quiz_id,
            score=8,
            total=10,
            percentage=80.0,
            results={
                "q1": {"correct": True, "user_answer": "A", "correct_answer": "A"},
                "q2": {"correct": False, "user_answer": "B", "correct_answer": "C"},
            },
            completed_at="2024-01-01T00:00:00Z",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process quiz submission: {str(e)}",
        )