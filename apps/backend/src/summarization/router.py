import hashlib
import random
import time

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser
from ..common.exceptions import EmptyContentError
from ..database.models import Document, Summary, Tag
from ..database.session import get_db
from ..embeddings.dependencies import EmbeddingsServiceDep
from ..storage.dependencies import StorageServiceDep
from .dependencies import SummarizerServiceDep
from .schemas import TextSummaryRequest, TextSummaryResponse

router = APIRouter(
    prefix="/summarize",
    tags=["Text Summarization"],
    responses={
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable"},
    },
)


@router.post(
    "/text",
    response_model=TextSummaryResponse,
    summary="Summarize text",
    description="Generate an AI-powered summary of the provided text",
)
async def summarize_text(
    request: TextSummaryRequest,
    summarizer: SummarizerServiceDep,
    embeddings_service: EmbeddingsServiceDep,
    storage_service: StorageServiceDep,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TextSummaryResponse:
    """Generate a summary of the provided text content."""
    start_time = time.time()
    
    # Validate text has content
    if not request.text.strip():
        raise EmptyContentError("text input")

    # Generate summary with tags using the same method as PDF
    summary_result = await summarizer.summarize_pdf(
        request.text, request.max_length, request.format, request.instructions
    )

    # Extract summary and stats
    summary = summary_result["summary"]
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Create a hash of the text content for deduplication
    text_hash = hashlib.sha256(request.text.encode()).hexdigest()
    
    # Create a document record for the text input
    # Use a descriptive filename for text inputs
    preview = request.text[:50] + "..." if len(request.text) > 50 else request.text
    filename = f"Text: {preview}"
    
    # Store text as a file
    storage_path, file_size = await storage_service.store_text_as_file(
        text=request.text,
        user_id=str(current_user.id),
        title=preview,
    )
    
    document = Document(
        user_id=current_user.id,
        filename=filename,
        file_size=file_size,
        file_hash=text_hash,
        page_count=1,  # Text input is considered 1 page
        storage_path=storage_path,
    )
    db.add(document)
    await db.flush()
    
    # Generate embeddings for the text document
    await embeddings_service.create_document_embeddings(
        document_id=str(document.id),
        text=request.text,
        db=db,
    )
    
    # Process and create tags (same logic as PDF endpoint)
    generated_tags = summary_result.get("tags", [])
    print(f"DEBUG: Text summarization generated {len(generated_tags)} tags: {generated_tags}")
    
    if generated_tags:
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
            
            # Add tag to document using explicit query to avoid lazy loading
            # Check if this tag is already associated with the document
            from ..database.models import document_tags
            existing_association = await db.execute(
                select(document_tags).where(
                    document_tags.c.document_id == document.id,
                    document_tags.c.tag_id == tag.id
                )
            )
            if not existing_association.first():
                # Create the association
                await db.execute(
                    document_tags.insert().values(
                        document_id=document.id,
                        tag_id=tag.id
                    )
                )
        
        # Flush to ensure the many-to-many relationships are saved
        await db.flush()
        print(f"DEBUG: Added {len(generated_tags)} tags to text document {document.id}")
    
    # Get stats from the result
    original_words = summary_result["stats"].get("original_words", len(request.text.split()))
    summary_words = summary_result["stats"].get("summary_words", len(summary.split()))
    
    # Create summary record
    summary_record = Summary(
        user_id=current_user.id,
        document_id=document.id,
        summary_text=summary,
        original_word_count=original_words,
        summary_word_count=summary_words,
        compression_ratio=original_words / summary_words if summary_words > 0 else 0,
        processing_time=processing_time,
        llm_provider=summarizer.provider_name,
        llm_model=summarizer.model_name,
    )
    db.add(summary_record)
    await db.commit()

    return TextSummaryResponse(
        summary=summary,
        original_length=len(request.text),
        summary_length=len(summary),
        original_words=original_words,
        summary_words=summary_words,
        compression_ratio=round((1 - summary_words / original_words) * 100, 2)
        if original_words > 0
        else 0,
    )


@router.get(
    "/info",
    summary="Get summarization service info",
    description="Get information about the summarization service configuration",
)
async def get_service_info(
    summarizer: SummarizerServiceDep,
    current_user: CurrentUser,
) -> dict:
    """Get information about the summarization service."""
    return summarizer.get_service_info()
