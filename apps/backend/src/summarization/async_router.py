"""Async summarization router."""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import BadRequestException, NotFoundException
from ..database.session import get_db
from ..document.dependencies import DocumentServiceDep
from .dependencies import AsyncSummarizationServiceDep
from .schemas import CreateSummaryRequest

router = APIRouter(
    prefix="/summarization",
    tags=["Summarization"],
    responses={
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue summarization",
    description="Queue document or text summarization",
)
async def create_summary_async(
    request: CreateSummaryRequest,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    service: AsyncSummarizationServiceDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Queue summarization for a document or text."""
    # Validate request
    if not request.document_id and not request.text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either document_id or text must be provided",
        )
    
    if request.text and not request.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required when providing raw text",
        )
    
    try:
        # Get summary options from request
        options = request.get_summary_options()
        
        if request.document_id:
            # Summarize existing document
            result = await service.enqueue_summarization(
                document_id=request.document_id,
                user_id=current_user.id,
                document_service=document_service,
                db=db,
                options=options,
            )
        else:
            # Summarize raw text
            result = await service.enqueue_text_summarization(
                text=request.text,
                filename=request.filename,
                user_id=current_user.id,
                options=options,
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
            detail=f"Failed to queue summarization: {str(e)}",
        )


@router.get(
    "/job/{job_id}/status",
    summary="Get summarization status",
    description="Check the status of a summarization job",
)
async def get_summarization_job_status(
    job_id: str,
    current_user: CurrentUserDep,
    service: AsyncSummarizationServiceDep,
) -> dict:
    """Get the status of a summarization job."""
    try:
        result = await service.get_summarization_status(job_id)
        
        # TODO: Add security check to ensure user owns the document/summary
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )