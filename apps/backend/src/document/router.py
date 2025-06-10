"""Document domain router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser
from ..common.exceptions import NotFoundError
from ..database.session import get_db
from .dependencies import DocumentServiceDep
from .schemas import DocumentListResponse, DocumentResponse

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
    "",
    response_model=list[DocumentListResponse],
    summary="List user documents",
    description="Get all documents for the current user",
    responses={
        200: {"description": "Documents retrieved successfully"},
    },
)
async def list_documents(
    current_user: CurrentUser,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> list[DocumentListResponse]:
    """List all documents for the current user."""
    documents = await document_service.list_user_documents(
        user_id=current_user.id,
        db=db,
    )
    return [DocumentListResponse.model_validate(doc) for doc in documents]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Get detailed information about a specific document",
)
async def get_document(
    document_id: UUID,
    current_user: CurrentUser,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a specific document."""
    try:
        document = await document_service.get_document(
            document_id=document_id,
            user_id=current_user.id,
            db=db,
        )
        return DocumentResponse.model_validate(document)
    except NotFoundError:
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
    current_user: CurrentUser,
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
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )