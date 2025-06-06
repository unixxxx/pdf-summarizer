import hashlib
import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser
from ..common.exceptions import EmptyContentError
from ..database.models import Document, Summary
from ..database.session import get_db
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
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> TextSummaryResponse:
    """Generate a summary of the provided text content."""
    start_time = time.time()
    
    # Validate text has content
    if not request.text.strip():
        raise EmptyContentError("text input")

    # Generate summary
    summary = await summarizer.summarize_text(
        request.text, request.max_length, request.format, request.instructions
    )

    # Calculate statistics
    original_words = len(request.text.split())
    summary_words = len(summary.split())
    processing_time = time.time() - start_time
    
    # Create a hash of the text content for deduplication
    text_hash = hashlib.sha256(request.text.encode()).hexdigest()
    
    # Create a document record for the text input
    # Use a descriptive filename for text inputs
    preview = request.text[:50] + "..." if len(request.text) > 50 else request.text
    filename = f"Text: {preview}"
    
    document = Document(
        user_id=current_user.id,
        filename=filename,
        file_size=len(request.text.encode()),
        file_hash=text_hash,
        page_count=1,  # Text input is considered 1 page
        storage_path=None,  # No file storage for text input
    )
    db.add(document)
    await db.flush()
    
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
