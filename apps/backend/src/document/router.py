"""Document domain router."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import NotFoundError
from ..database.models import Document, Summary, Tag, document_folders, document_tags
from ..database.session import get_db
from ..tag.schemas import TagResponse
from .dependencies import DocumentServiceDep
from .schemas import DocumentResponse, LibraryItemResponse, PaginatedLibraryResponse

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
    response_model=PaginatedLibraryResponse,
    summary="Browse documents with summaries",
    description="Get documents with summaries, filterable by folder, search and tags",
    responses={
        200: {"description": "Documents retrieved successfully"},
    },
)
async def browse_documents(
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
    folder_id: Optional[UUID] = Query(None, description="Filter by folder ID"),
    unfiled: bool = Query(False, description="Get only unfiled documents"),
    search: Optional[str] = Query(None, description="Search in filename and content"),
    tags: list[str] = Query([], description="Filter by tag slugs"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> PaginatedLibraryResponse:
    """Browse documents with summaries."""
    # Build base query
    query = (
        select(Document, Summary)
        .join(Summary, Document.id == Summary.document_id)
        .options(selectinload(Document.tags))
        .where(
            Document.user_id == current_user.id,
            Document.deleted_at.is_(None)  # Exclude trashed documents
        )
    )
    
    # Apply folder filter
    if folder_id:
        query = query.join(document_folders).where(document_folders.c.folder_id == folder_id)
    elif unfiled:
        # Get documents not in any folder
        query = query.where(
            ~Document.id.in_(
                select(document_folders.c.document_id)
            )
        )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Document.filename.ilike(search_term)) |
            (Summary.summary_text.ilike(search_term))
        )
    
    # Apply tag filter
    if tags:
        # Subquery to get documents with all specified tags
        tag_subquery = (
            select(document_tags.c.document_id)
            .join(Tag, Tag.id == document_tags.c.tag_id)
            .where(Tag.slug.in_(tags))
            .group_by(document_tags.c.document_id)
            .having(func.count(Tag.id) == len(tags))
        )
        query = query.where(Document.id.in_(tag_subquery))
    
    # Order by creation date
    query = query.order_by(Document.created_at.desc())
    
    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    rows = result.all()
    
    # Transform to response
    library_items = []
    for document, summary in rows:
        library_items.append(
            LibraryItemResponse(
                id=summary.id,
                document_id=document.id,
                filename=document.filename,
                file_size=document.file_size,
                summary=summary.summary_text,
                created_at=summary.created_at,
                processing_time=summary.processing_time,
                word_count=summary.original_word_count or 0,
                tags=[
                    TagResponse(
                        id=tag.id,
                        name=tag.name,
                        slug=tag.slug,
                        color=tag.color,
                    )
                    for tag in document.tags
                ],
            )
        )
    
    return PaginatedLibraryResponse(
        items=library_items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Get detailed information about a specific document",
)
async def get_document(
    document_id: UUID,
    current_user: CurrentUserDep,
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
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )