"""Document domain router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...auth.dependencies import CurrentUserDep
from ...common.exceptions import NotFoundException
from ...database.models import Document, Summary
from ...database.session import get_db
from ..tag.schemas import TagResponse
from .dependencies import DocumentServiceDep
from .export_service import DocumentExporter
from .schemas import (
    CreateTextDocumentRequest,
    DocumentResponse,
    ExportFormat,
    LibraryItemResponse,
    PaginatedLibraryResponse,
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
    response_model=PaginatedLibraryResponse,
    summary="Browse documents",
    description="Get all documents, filterable by folder and search",
    responses={
        200: {"description": "Documents retrieved successfully"},
    },
)
async def browse_documents(
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
    folder_id: UUID | None = Query(None, description="Filter by folder ID"),
    unfiled: bool = Query(False, description="Get only unfiled documents"),
    search: str | None = Query(None, description="Search in filename and content"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> PaginatedLibraryResponse:
    """Browse documents with summaries."""
    # Build base query
    query = (
        select(Document)
        .options(selectinload(Document.tags))
        .where(
            Document.user_id == current_user.id,
            Document.archived_at.is_(None)  # Exclude archived documents
        )
    )
    
    # Apply folder filter
    if folder_id:
        query = query.where(Document.folder_id == folder_id)
    elif unfiled:
        # Get documents not in any folder
        query = query.where(Document.folder_id.is_(None))
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Document.filename.ilike(search_term)) |
            (Document.extracted_text.ilike(search_term))
        )
    
    
    # Order by creation date
    query = query.order_by(Document.created_at.desc())
    
    # Get total count before pagination - more efficient without subquery
    count_query = (
        select(func.count(Document.id))
        .select_from(Document)
        .where(
            Document.user_id == current_user.id,
            Document.archived_at.is_(None)
        )
    )
    
    # Apply same filters to count query
    if folder_id:
        count_query = count_query.where(Document.folder_id == folder_id)
    elif unfiled:
        count_query = count_query.where(Document.folder_id.is_(None))
    
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            (Document.filename.ilike(search_term)) |
            (Document.extracted_text.ilike(search_term))
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Transform to response
    library_items = []
    for document in documents:
        library_items.append(
            LibraryItemResponse(
                id=document.id,  # Use document ID instead of summary ID
                document_id=document.id,
                filename=document.filename,
                file_size=document.file_size,
                summary=document.extracted_text[:200] + "..." if document.extracted_text else "",  # First 200 chars
                created_at=document.created_at,
                word_count=document.word_count or 0,
                tags=[
                    TagResponse(
                        id=tag.id,
                        name=tag.name,
                        slug=tag.slug,
                        color=tag.color,
                    )
                    for tag in document.tags
                ],
                status=document.status,  # Include document processing status
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
    db: AsyncSession = Depends(get_db),
    format: ExportFormat = Query(ExportFormat.MARKDOWN),
) -> Response:
    """Export a document in the specified format."""
    # Get document with optional summary
    query = (
        select(Document, Summary)
        .outerjoin(Summary, Document.id == Summary.document_id)
        .where(
            Document.id == document_id,
            Document.user_id == current_user.id,
            Document.archived_at.is_(None)
        )
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    document, summary = row
    
    # Get document content
    content = document.extracted_text or "No content available"
    
    # Prepare metadata
    metadata = {
        "filename": document.filename,
        "file_size": document.file_size,
        "created_at": document.created_at,
    }
    
    # Get summary text if available
    summary_text = summary.summary_text if summary else None
    
    # Export based on format
    exporter = DocumentExporter()
    
    if format == ExportFormat.MARKDOWN:
        content_str = exporter.export_document_as_markdown(
            content=content,
            metadata=metadata,
            summary=summary_text,
        )
        filename = f"{document.filename.rsplit('.', 1)[0]}.md"
        media_type = "text/markdown"
    
    elif format == ExportFormat.TEXT:
        content_str = exporter.export_document_as_text(
            content=content,
            metadata=metadata,
            summary=summary_text,
        )
        filename = f"{document.filename.rsplit('.', 1)[0]}.txt"
        media_type = "text/plain"
    
    elif format == ExportFormat.PDF:
        pdf_content = await exporter.export_document_as_pdf(
            content=content,
            metadata=metadata,
            summary=summary_text,
        )
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{document.filename.rsplit(".", 1)[0]}.pdf"'
            }
        )
    
    # Return text-based formats
    return Response(
        content=content_str,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post(
    "/text",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create text document",
    description="Create a new document from text content",
)
async def create_text_document(
    request: CreateTextDocumentRequest,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Create a new document from text content."""
    try:
        # Create document with text content
        document = await document_service.create_text_document(
            user_id=current_user.id,
            title=request.title,
            content=request.content,
            folder_id=request.folder_id,
            db=db,
        )
        
        await db.commit()
        await db.refresh(document)
        
        # Convert folder_id to list for response
        folder_ids = [document.folder_id] if document.folder_id else []
        
        return DocumentResponse(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            file_size=document.file_size,
            file_hash=document.file_hash,
            status=document.status,
            created_at=document.created_at,
            extracted_text=document.extracted_text,
            word_count=document.word_count,
            folder_ids=folder_ids,
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )