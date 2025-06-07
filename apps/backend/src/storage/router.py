"""Storage router for serving files from local storage."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser
from ..config import Settings, get_settings
from ..database.models import Document
from ..database.session import get_db
from .dependencies import StorageServiceDep

router = APIRouter(
    prefix="/storage",
    tags=["Storage"],
    responses={
        404: {"description": "File not found"},
        500: {"description": "Storage error"},
    },
)


@router.get(
    "/{storage_path:path}",
    summary="Get file from storage",
    description="Retrieve a file from local storage (only available when not using S3)",
)
async def get_file(
    storage_path: str,
    storage_service: StorageServiceDep,
    current_user: CurrentUser,
    settings: Settings = Depends(get_settings),
) -> Response:
    """Get a file from local storage."""
    # Only allow local storage access
    if settings.s3_enabled:
        raise HTTPException(
            status_code=404,
            detail="Direct file access not available with S3 storage",
        )
    
    # Security: Ensure the user can only access their own files
    if not storage_path.startswith(str(current_user.id)):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    
    try:
        # Retrieve the file
        content = await storage_service.retrieve_file(storage_path)
        
        # Determine content type based on extension
        if storage_path.endswith('.pdf'):
            content_type = "application/pdf"
        elif storage_path.endswith('.txt'):
            content_type = "text/plain; charset=utf-8"
        else:
            content_type = "application/octet-stream"
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={storage_path.split('/')[-1]}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {str(e)}",
        )


@router.get(
    "/download/{document_id}",
    summary="Download document file",
    description="Download the original PDF file for a document",
)
async def download_document(
    document_id: UUID,
    storage_service: StorageServiceDep,
    current_user: CurrentUser,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
):
    """Download a document file."""
    # Get document from database
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )
    
    if not document.storage_path:
        raise HTTPException(
            status_code=404,
            detail="Document file not available",
        )
    
    # For S3, generate presigned URL and redirect
    if settings.s3_enabled:
        try:
            presigned_url = await storage_service.get_file_url(
                document.storage_path,
                expires_in=3600  # 1 hour
            )
            return RedirectResponse(url=presigned_url)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate download URL: {str(e)}",
            )
    
    # For local storage, serve the file directly
    try:
        content = await storage_service.retrieve_file(document.storage_path)
        
        return Response(
            content=content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{document.filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {str(e)}",
        )