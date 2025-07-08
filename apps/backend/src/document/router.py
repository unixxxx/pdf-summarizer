"""Document domain router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import NotFoundException
from ..database.session import get_db
from .dependencies import DocumentServiceDep
from .organize_service import DocumentOrganizeService
from .schemas import (
    DocumentDetailResponse,
    DocumentsListResponse,
    ExportFormat,
)

router = APIRouter(
    prefix="/document",
    tags=["Document"],
    responses={
        400: {"description": "Bad request"},
        404: {"description": "Document not found"},
        409: {"description": "Document already exists"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "",  # Note: /document endpoint
    response_model=DocumentsListResponse,
    summary="Get documents",
    description="Get all documents, filterable by folder and search",
    responses={
        200: {"description": "Documents retrieved successfully"},
    },
)
async def get_documents(
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
    folder_id: UUID | None = Query(None, description="Filter by folder ID"),
    unfiled: bool = Query(False, description="Get only unfiled documents"),
    search: str | None = Query(None, description="Search in filename and content"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> DocumentsListResponse:
    """Get documents with filters and pagination."""
    return await document_service.get_documents(
        user_id=current_user.id,
        db=db,
        folder_id=folder_id,
        unfiled=unfiled,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    description="Get detailed information about a specific document",
)
async def get_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """Get a specific document."""
    try:
        return await document_service.get_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
        )
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete a document and all associated data",
)
async def delete_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document."""
    try:
        await document_service.delete_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
        )
        await db.commit()
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )


@router.get(
    "/{document_id}/export",
    summary="Export document",
    description="Export a document in various formats (PDF, Markdown, Text)",
)
async def export_document(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
    format: ExportFormat = Query(ExportFormat.MARKDOWN),
) -> Response:
    """Export a document in the specified format."""
    try:
        return await document_service.export_document(
            document_id=document_id,
            user_id=current_user.id,
            format=format,
            db=db,
        )
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )


@router.post(
    "/{document_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry failed document processing",
    description="Retry processing for a failed document",
    responses={
        202: {"description": "Processing retry queued successfully"},
        400: {"description": "Document is not in failed state"},
        404: {"description": "Document not found"},
    },
)
async def retry_document_processing(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retry processing for a failed document."""
    try:
        return await document_service.retry_document_processing(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
        )
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/organize/suggestions")
async def get_organization_suggestions(
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get suggestions for organizing unfiled documents into folders based on tag similarity.
    
    This endpoint uses vector embeddings to find the best folder matches for documents
    based on their tags.
    
    Returns:
        Organization suggestions with similarity scores
    """
    organize_service = DocumentOrganizeService()
    
    try:
        result = await organize_service.get_organization_suggestions(
            user_id=current_user.id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization suggestions: {str(e)}"
        )


@router.post("/organize/apply")
async def apply_organization(
    current_user: CurrentUserDep,
    assignments: list[dict[str, str]],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Apply document organization by moving selected documents to their assigned folders.
    
    Args:
        assignments: List of document-folder assignments
            [{"document_id": "...", "folder_id": "..."}, ...]
        
    Returns:
        Organization results
    """
    organize_service = DocumentOrganizeService()
    
    try:
        result = await organize_service.apply_organization(
            user_id=current_user.id,
            assignments=assignments,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply organization: {str(e)}"
        )
