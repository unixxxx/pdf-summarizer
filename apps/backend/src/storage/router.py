"""Storage router for serving files from local storage."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..auth.dependencies import CurrentUser
from ..config import Settings, get_settings
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