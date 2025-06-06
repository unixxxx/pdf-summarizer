from fastapi import APIRouter

from ..auth.dependencies import CurrentUser
from ..common.exceptions import EmptyContentError
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
) -> TextSummaryResponse:
    """Generate a summary of the provided text content."""
    # Validate text has content
    if not request.text.strip():
        raise EmptyContentError("text input")

    # Generate summary
    summary = await summarizer.summarize_text(request.text, request.max_length)

    # Calculate statistics
    original_words = len(request.text.split())
    summary_words = len(summary.split())

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
