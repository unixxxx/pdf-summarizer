"""Dependencies for Summarization domain."""

from typing import Annotated

from fastapi import Depends

from .async_service import AsyncSummarizationService


def get_async_summarization_service() -> AsyncSummarizationService:
    """Get async summarization service instance."""
    return AsyncSummarizationService()


AsyncSummarizationServiceDep = Annotated[AsyncSummarizationService, Depends(get_async_summarization_service)]