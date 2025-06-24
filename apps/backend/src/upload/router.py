"""Upload router for handling S3 direct uploads."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import NotFoundException, StorageError, ValidationError
from ..config import get_settings
from ..database.session import get_db
from ..processing.dependencies import ProcessingOrchestratorDep
from ..storage.dependencies import StorageServiceDep
from .schemas import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
)
from .service import UploadService

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
    responses={
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/presigned-url",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get presigned URL for upload",
    description="Generate a presigned URL for direct file upload to S3",
)
async def get_presigned_upload_url(
    request: PresignedUrlRequest,
    current_user: CurrentUserDep,
    storage_service: StorageServiceDep,
    db: AsyncSession = Depends(get_db),
) -> PresignedUrlResponse:
    """Generate presigned URL for direct S3 upload."""
    try:
        settings = get_settings()
        upload_service = UploadService(storage_service, settings)
        
        return await upload_service.create_presigned_upload_url(
            request=request,
            user_id=current_user.id,
            db=db,
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except StorageError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}",
        )


@router.post(
    "/complete",
    response_model=CompleteUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete file upload",
    description="Notify backend that file upload is complete and start processing",
)
async def complete_upload(
    request: CompleteUploadRequest,
    current_user: CurrentUserDep,
    storage_service: StorageServiceDep,
    db: AsyncSession = Depends(get_db),
) -> CompleteUploadResponse:
    """Handle post-upload processing initiation."""
    try:
        settings = get_settings()
        upload_service = UploadService(storage_service, settings)
        
        return await upload_service.complete_upload(
            request=request,
            user_id=current_user.id,
            db=db,
        )
        
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete upload: {str(e)}",
        )


@router.get(
    "/status/{upload_id}",
    status_code=status.HTTP_200_OK,
    summary="Get upload status",
    description="Check the processing status of an uploaded document",
)
async def get_upload_status(
    upload_id: str,
    current_user: CurrentUserDep,
) -> dict:
    """Get the processing status of an upload."""
    # This endpoint can be used to check Celery task status
    # For now, return a placeholder
    return {
        "upload_id": upload_id,
        "status": "processing",
        "stage": "extracting_text",
        "progress": 50,
    }


@router.post(
    "/process/{document_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger document processing",
    description="Manually trigger processing for an uploaded document",
)
async def trigger_document_processing(
    document_id: UUID,
    current_user: CurrentUserDep,
    orchestrator: ProcessingOrchestratorDep,
    storage_service: StorageServiceDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger document processing for an uploaded document."""
    from ..library.document.service import DocumentService
    
    try:
        # Get document to verify ownership
        document_service = DocumentService()
        document = await document_service.get_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
        )
        
        # Check if document needs processing
        if document.status == "completed":
            return {
                "document_id": str(document_id),
                "status": "already_processed",
                "message": "Document has already been processed"
            }
        
        # Update status to processing
        await document_service.update_document_status(
            document_id=document_id,
            status="processing",
            db=db,
        )
        
        # Get file content from storage
        file_content = await storage_service.get_file(document.storage_path)
        
        # Process document
        await orchestrator.process_uploaded_document(
            document_id=document_id,
            file_content=file_content,
            user_id=current_user.id,
            db=db,
        )
        
        # Update status to completed
        await document_service.update_document_status(
            document_id=document_id,
            status="completed",
            db=db,
        )
        
        await db.commit()
        
        return {
            "document_id": str(document_id),
            "status": "processing_started",
            "message": "Document processing has been triggered"
        }
        
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied",
        )
    except Exception as e:
        # Update status to failed
        await document_service.update_document_status(
            document_id=document_id,
            status="failed",
            db=db,
        )
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )