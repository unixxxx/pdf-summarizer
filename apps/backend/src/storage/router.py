"""Storage router for serving files from local storage."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import StorageError
from ..config import Settings, get_settings
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
    "/download/{document_id}",
    summary="Download document file",
    description="Download the original PDF file for a document",
)
async def download_document(
    document_id: UUID,
    storage_service: StorageServiceDep,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
):
    """Download a document file."""
    try:
        download_info = await storage_service.get_document_download_info(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
        )
        return download_info
    except StorageError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/text/{document_id}",
    summary="Download text document",
    description="Download a text document as a .txt file",
)
async def download_text_document(
    document_id: UUID,
    storage_service: StorageServiceDep,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
):
    """Download a text document as a .txt file."""
    try:
        content, filename = await storage_service.get_text_document_content(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
        )
        
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except StorageError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{storage_path:path}",
    summary="Get file from storage",
    description="Retrieve a file from local storage (only available when not using S3)",
)
async def get_file(
    storage_path: str,
    storage_service: StorageServiceDep,
    current_user: CurrentUserDep,
    settings: Settings = Depends(get_settings),
) -> Response:
    """Get a file from local storage."""
    # Only allow local storage access
    if settings.s3_enabled:
        raise HTTPException(
            status_code=404,
            detail="Direct file access not available with S3 storage",
        )
    
    try:
        # Retrieve the file with access check
        content = await storage_service.get_file_with_access_check(
            storage_path=storage_path,
            user_id=current_user.id,
        )
        
        # Determine content type
        content_type = storage_service.get_content_type_for_path(storage_path)
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={storage_path.split('/')[-1]}"
            }
        )
        
    except StorageError as e:
        if "access denied" in str(e).lower():
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))