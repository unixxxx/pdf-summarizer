"""Library domain router for document browsing and organization."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth.dependencies import CurrentUser
from ..database.models import Document, Summary, Tag, document_tags
from ..database.session import get_db
from .dependencies import TagServiceDep
from .schemas import ExportFormat, LibraryItemResponse, TagResponse

router = APIRouter(
    prefix="/library",
    tags=["Library"],
    responses={
        400: {"description": "Bad request"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "",
    response_model=list[LibraryItemResponse],
    summary="Browse document library",
    description="Get all documents with summaries, filterable by search and tags",
    responses={
        200: {"description": "Library items retrieved successfully"},
    },
)
async def browse_library(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(None, description="Search in filename and content"),
    tags: list[str] = Query([], description="Filter by tag slugs"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> list[LibraryItemResponse]:
    """Browse the document library with filtering."""
    # Build base query
    query = (
        select(Document, Summary)
        .join(Summary, Document.id == Summary.document_id)
        .options(selectinload(Document.tags))
        .where(Document.user_id == current_user.id)
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
    
    return library_items


@router.get(
    "/tags",
    response_model=list[TagResponse],
    summary="Get all tags",
    description="Get all tags that have at least one document associated with them",
)
async def get_tags(
    tag_service: TagServiceDep,
    db: AsyncSession = Depends(get_db),
) -> list[TagResponse]:
    """Get all tags with their document counts."""
    tags_with_counts = await tag_service.get_all_tags_with_counts(db)
    
    return [
        TagResponse(
            id=tag_data["id"],
            name=tag_data["name"],
            slug=tag_data["slug"],
            color=tag_data["color"],
            document_count=tag_data["document_count"],
        )
        for tag_data in tags_with_counts
    ]


@router.get(
    "/export/{summary_id}",
    summary="Export summary",
    description="Export a summary in different formats",
)
async def export_summary(
    summary_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    format: ExportFormat = Query(ExportFormat.MARKDOWN),
):
    """Export a summary in the specified format."""
    # Get summary with document info
    result = await db.execute(
        select(Summary, Document)
        .join(Document, Summary.document_id == Document.id)
        .where(
            Summary.id == summary_id,
            Document.user_id == current_user.id,
        )
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found",
        )
    
    summary, document = row
    
    # Export based on format
    if format == ExportFormat.MARKDOWN:
        content = f"""# {document.filename}

## Summary

{summary.summary_text}

---
*Generated on {summary.created_at.strftime('%Y-%m-%d %H:%M:%S')}*
*Processing time: {summary.processing_time:.2f} seconds*
"""
        filename = f"{document.filename.rsplit('.', 1)[0]}_summary.md"
        media_type = "text/markdown"
    
    elif format == ExportFormat.TEXT:
        content = f"""{document.filename}

Summary:
{summary.summary_text}

Generated on {summary.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Processing time: {summary.processing_time:.2f} seconds
"""
        filename = f"{document.filename.rsplit('.', 1)[0]}_summary.txt"
        media_type = "text/plain"
    
    elif format == ExportFormat.PDF:
        # For PDF export, we'll use the PDF export functionality
        from .pdf_exporter import PDFExporter
        exporter = PDFExporter()
        
        pdf_content = await exporter.export_summary_as_pdf(
            summary_text=summary.summary_text,
            metadata={
                "filename": document.filename,
                "created_at": summary.created_at.isoformat(),
                "processing_time": summary.processing_time,
            }
        )
        
        from fastapi.responses import Response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{document.filename.rsplit(".", 1)[0]}_summary.pdf"'
            }
        )
    
    # Return text-based formats
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete(
    "/summaries/{summary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete summary",
    description="Delete a summary (keeps the document)",
)
async def delete_summary(
    summary_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a summary while keeping the document."""
    # Verify ownership
    result = await db.execute(
        select(Summary)
        .join(Document, Summary.document_id == Document.id)
        .where(
            Summary.id == summary_id,
            Document.user_id == current_user.id,
        )
    )
    summary = result.scalar_one_or_none()
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found",
        )
    
    await db.delete(summary)
    await db.commit()