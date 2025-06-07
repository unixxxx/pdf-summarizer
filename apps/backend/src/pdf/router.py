import hashlib
import random
import time
import urllib.parse
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..auth.dependencies import CurrentUser
from ..database.models import Document, Summary, Tag
from ..database.session import get_db
from ..embeddings.dependencies import EmbeddingsServiceDep
from ..storage.dependencies import StorageServiceDep
from ..summarization.dependencies import SummarizerServiceDep
from .dependencies import PDFServiceDep, ValidatedPDFFile
from .export import ExportService
from .schemas import (
    PDFSummaryHistoryItem,
    PDFSummaryResponse,
    PDFTextExtractionResponse,
    TagSchema,
)

router = APIRouter(
    prefix="/pdf",
    tags=["PDF Operations"],
    responses={
        400: {"description": "Bad request"},
        413: {"description": "File too large"},
        422: {"description": "Unprocessable entity"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/extract-text",
    response_model=PDFTextExtractionResponse,
    summary="Extract text from PDF",
    description="Extract all text content from a PDF file",
)
async def extract_pdf_text(
    file: ValidatedPDFFile,
    pdf_service: PDFServiceDep,
    current_user: CurrentUser,
) -> PDFTextExtractionResponse:
    """Extract text content from uploaded PDF file."""
    # Read file content
    pdf_content = await file.read()

    # Validate PDF
    await pdf_service.validate_pdf(pdf_content, file.filename)

    # Extract text
    text, extraction_time = await pdf_service.extract_text(pdf_content)

    # Extract metadata
    metadata = await pdf_service.extract_metadata(pdf_content, file.filename)

    return PDFTextExtractionResponse(
        text=text, metadata=metadata, extraction_time=extraction_time
    )


@router.post(
    "/summarize",
    response_model=PDFSummaryResponse,
    summary="Summarize PDF content",
    description="Upload a PDF file and get an AI-generated summary",
)
async def summarize_pdf(
    file: ValidatedPDFFile,
    pdf_service: PDFServiceDep,
    summarizer: SummarizerServiceDep,
    embeddings_service: EmbeddingsServiceDep,
    storage_service: StorageServiceDep,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    max_length: Annotated[
        Optional[int],
        Query(description="Maximum summary length in words", ge=50, le=2000),
    ] = 500,
    format: Annotated[
        Optional[str],
        Query(
            description="Summary format: 'paragraph', 'bullets', or 'keypoints'",
            pattern="^(paragraph|bullets|keypoints)$"
        ),
    ] = "paragraph",
    instructions: Annotated[
        Optional[str],
        Query(description="Additional instructions for summary generation", max_length=500),
    ] = None,
    include_metadata: Annotated[
        bool, Query(description="Include PDF metadata in response")
    ] = True,
) -> PDFSummaryResponse:
    """Generate a summary of uploaded PDF content."""
    start_time = time.time()

    # Read file content
    pdf_content = await file.read()

    # Validate PDF
    await pdf_service.validate_pdf(pdf_content, file.filename)

    # Extract text
    text, _ = await pdf_service.extract_text(pdf_content)

    # Extract metadata if requested
    metadata = None
    if include_metadata:
        metadata = await pdf_service.extract_metadata(pdf_content, file.filename)

    # Generate summary
    summary_result = await summarizer.summarize_pdf(text, max_length, format, instructions)

    # Calculate processing time
    processing_time = time.time() - start_time

    # Calculate file hash
    file_hash = hashlib.sha256(pdf_content).hexdigest()

    # Check if document already exists
    existing_doc = await db.execute(
        select(Document).options(selectinload(Document.tags)).where(
            Document.user_id == current_user.id, Document.file_hash == file_hash
        )
    )
    document = existing_doc.scalar_one_or_none()

    # Create document if it doesn't exist
    if not document:
        # Store the PDF file
        storage_path = await storage_service.store_file(
            content=pdf_content,
            user_id=str(current_user.id),
            file_type='pdf',
            original_filename=file.filename,
        )
        
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_size=len(pdf_content),
            file_hash=file_hash,
            page_count=metadata.pages if metadata else None,
            storage_path=storage_path,
        )
        db.add(document)
        await db.flush()
        
        # Generate embeddings for the document
        await embeddings_service.create_document_embeddings(
            document_id=str(document.id),
            text=text,
            db=db,
        )
    
    # Process and create tags (for both new and existing documents)
    generated_tags = summary_result.get("tags", [])
    tag_objects = []
    print(f"DEBUG: Generated {len(generated_tags)} tags from summarization: {generated_tags}")
    
    # Only process tags if document doesn't already have them
    # For existing documents, check if they have tags
    existing_tags = []
    if document.id:  # Check if it's an existing document
        # Query to check if document has tags
        tag_check = await db.execute(
            select(func.count(Tag.id))
            .join(Document.tags)
            .where(Document.id == document.id)
        )
        tag_count = tag_check.scalar()
        existing_tags = tag_count > 0
    
    if not existing_tags:
        print(f"DEBUG: Document has no tags, creating them...")
        for tag_name in generated_tags:
            if not tag_name:
                continue
                
            # Ensure tag name is not too long (max 100 chars in DB)
            tag_name = tag_name[:50] if len(tag_name) > 50 else tag_name
            
            # Create slug from tag name
            slug = tag_name.lower().strip().replace(' ', '-')
            slug = slug[:50] if len(slug) > 50 else slug
            
            # Check if tag already exists
            existing_tag = await db.execute(
                select(Tag).where(Tag.slug == slug)
            )
            tag = existing_tag.scalar_one_or_none()
            
            if not tag:
                # Generate a random color for the tag
                colors = [
                    "#3B82F6",  # Blue
                    "#10B981",  # Green
                    "#F59E0B",  # Yellow
                    "#EF4444",  # Red
                    "#8B5CF6",  # Purple
                    "#EC4899",  # Pink
                    "#14B8A6",  # Teal
                    "#F97316",  # Orange
                    "#6366F1",  # Indigo
                    "#84CC16",  # Lime
                ]
                color = random.choice(colors)
                
                # Create new tag
                tag = Tag(
                    name=tag_name,
                    slug=slug,
                    color=color,
                )
                db.add(tag)
                await db.flush()
            
            tag_objects.append(tag)
        
        # Add all tags to the document at once
        if tag_objects:
            print(f"DEBUG: Adding {len(tag_objects)} tags to document {document.id}")
            # Use a more explicit approach to avoid lazy loading issues
            document.tags.extend(tag_objects)
            print(f"DEBUG: Document now has {len(document.tags)} tags")
            # Flush to ensure the many-to-many relationships are saved
            await db.flush()
            print(f"DEBUG: Added {len(tag_objects)} tags to document {document.id}")
    else:
        print(f"DEBUG: Document already has tags, skipping tag creation")

    # Calculate word counts
    original_words = len(text.split())
    summary_words = summary_result["stats"].get(
        "summary_words", len(summary_result["summary"].split())
    )

    # Create summary record
    summary = Summary(
        user_id=current_user.id,
        document_id=document.id,
        summary_text=summary_result["summary"],
        original_word_count=original_words,
        summary_word_count=summary_words,
        compression_ratio=original_words / summary_words if summary_words > 0 else 0,
        processing_time=processing_time,
        llm_provider=summarizer.provider_name,
        llm_model=summarizer.model_name,
    )
    db.add(summary)
    await db.commit()

    return PDFSummaryResponse(
        summary=summary_result["summary"],
        metadata=metadata,
        processing_time=processing_time,
        summary_stats=summary_result["stats"],
    )


@router.get(
    "/library",
    response_model=list[PDFSummaryHistoryItem],
    summary="Get document library",
    description="Get all documents with filtering and search capabilities",
)
async def get_document_library(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    search: Annotated[Optional[str], Query(description="Search in filename and summary")] = None,
    tag: Annotated[Optional[str], Query(description="Filter by tag slug")] = None,
    tags: Annotated[Optional[list[str]], Query(description="Filter by multiple tag slugs")] = None,
    limit: Annotated[int, Query(description="Maximum number of results", ge=1, le=100)] = 50,
    offset: Annotated[int, Query(description="Number of results to skip", ge=0)] = 0,
) -> list[PDFSummaryHistoryItem]:
    """Get user's document library with search and filtering."""
    from sqlalchemy import or_
    
    # Build base query with proper eager loading
    query = (
        select(Summary)
        .where(Summary.user_id == current_user.id)
        .options(
            joinedload(Summary.document).joinedload(Document.tags)
        )
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        # Join Document for search
        query = query.join(Summary.document).where(
            or_(
                Document.filename.ilike(search_term),
                Summary.summary_text.ilike(search_term)
            )
        )
    
    # Apply tag filter
    if tag or tags:
        # Combine single tag and multiple tags
        tag_slugs = []
        if tag:
            tag_slugs.append(tag)
        if tags:
            tag_slugs.extend(tags)
        
        # Filter documents that have any of the specified tags
        # Join through document if not already joined
        if not search:
            query = query.join(Summary.document)
        query = query.join(Document.tags).where(Tag.slug.in_(tag_slugs))
    
    # Apply ordering, limit and offset
    query = query.order_by(desc(Summary.created_at)).limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)

    # Transform results to response schema
    history_items = []
    summaries = result.scalars().unique().all()
    
    for summary in summaries:
        document = summary.document
        history_items.append(
            PDFSummaryHistoryItem(
                id=summary.id,
                document_id=document.id,
                fileName=document.filename,
                fileSize=document.file_size,
                summary=summary.summary_text,
                original_word_count=summary.original_word_count,
                wordCount=summary.summary_word_count,
                compression_ratio=summary.compression_ratio,
                processingTime=summary.processing_time,
                llm_provider=summary.llm_provider,
                llm_model=summary.llm_model,
                createdAt=summary.created_at,
                tags=[
                    TagSchema(
                        id=tag.id,
                        name=tag.name,
                        slug=tag.slug,
                        color=tag.color
                    )
                    for tag in document.tags
                ],
            )
        )

    return history_items


@router.delete(
    "/history/{summary_id}",
    summary="Delete document and all associated data",
    description="Delete a document along with its summary, embeddings, and all chat sessions",
)
async def delete_pdf_summary(
    summary_id: UUID,
    storage_service: StorageServiceDep,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a PDF summary and its associated document from history."""
    # Find the summary with its document
    result = await db.execute(
        select(Summary, Document)
        .join(Document, Summary.document_id == Document.id)
        .where(
            Summary.id == summary_id, 
            Summary.user_id == current_user.id
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    summary, document = row

    # Delete the file from storage if it exists
    if document.storage_path:
        try:
            await storage_service.delete_file(document.storage_path)
        except Exception as e:
            # Log error but don't fail the deletion
            print(f"Failed to delete file from storage: {e}")

    # Delete the document (this will cascade delete summaries, chunks, and chats)
    await db.delete(document)
    await db.commit()

    return {"message": "Document and all associated data deleted successfully"}


@router.get(
    "/export/{summary_id}",
    summary="Export summary in various formats",
    description="Export a PDF summary as Markdown, PDF, or plain text",
)
async def export_summary(
    summary_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    format: Annotated[str, Query(description="Export format", pattern="^(markdown|pdf|text)$")] = "markdown",
):
    """Export a summary in the specified format."""
    from fastapi.responses import Response
    
    # Get summary with document and tags
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Summary, Document)
        .join(Document, Summary.document_id == Document.id)
        .where(
            Summary.id == summary_id,
            Summary.user_id == current_user.id
        )
        .options(selectinload(Document.tags))
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    summary, document = row
    
    # Prepare metadata
    metadata = {
        "pages": document.page_count,
        "size_mb": round(document.file_size / (1024 * 1024), 2),
        "author": None,  # Could be extracted from PDF metadata if stored
    }
    
    # Get tag names
    tags = [tag.name for tag in document.tags]
    
    # Export based on format
    export_service = ExportService()
    
    if format == "markdown":
        content = await export_service.export_as_markdown(
            summary.summary_text,
            document.filename,
            metadata,
            tags
        )
        media_type = "text/markdown"
        extension = "md"
    elif format == "pdf":
        content = await export_service.export_as_pdf(
            summary.summary_text,
            document.filename,
            metadata,
            tags
        )
        media_type = "application/pdf"
        extension = "pdf"
    else:  # text
        content = await export_service.export_as_text(
            summary.summary_text,
            document.filename,
            metadata,
            tags
        )
        media_type = "text/plain"
        extension = "txt"
    
    # Generate filename
    base_filename = document.filename.rsplit('.', 1)[0]
    export_filename = f"{base_filename}_summary.{extension}"
    
    # Properly encode filename for Content-Disposition header
    # Use RFC 5987 encoding for non-ASCII filenames
    encoded_filename = urllib.parse.quote(export_filename.encode('utf-8'))
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get(
    "/tags",
    response_model=list[dict],
    summary="Get all tags",
    description="Get all available tags with document counts",
)
async def get_tags(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get all tags used by the current user's documents."""
    from sqlalchemy import func
    
    # Query tags with document counts
    result = await db.execute(
        select(
            Tag,
            func.count(Document.id).label('document_count')
        )
        .join(Tag.documents)
        .where(Document.user_id == current_user.id)
        .group_by(Tag.id)
        .order_by(func.count(Document.id).desc())
    )
    
    # Transform results
    tags = []
    for tag, count in result:
        tags.append({
            "id": tag.id,
            "name": tag.name,
            "slug": tag.slug,
            "color": tag.color,
            "document_count": count
        })
    
    return tags


# Keep the old history endpoint for backward compatibility
@router.get(
    "/history",
    response_model=list[PDFSummaryHistoryItem],
    summary="Get PDF summary history (deprecated)",
    description="Deprecated: Use /library instead. Get all PDF summaries for the current user",
    deprecated=True,
)
async def get_pdf_history(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[PDFSummaryHistoryItem]:
    """Get user's PDF summary history (deprecated - use /library)."""
    # Redirect to library endpoint
    return await get_document_library(current_user, db)
