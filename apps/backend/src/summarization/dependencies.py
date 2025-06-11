"""Dependencies for Summarization domain."""

from typing import Annotated

from fastapi import Depends
from langchain.schema.language_model import BaseLanguageModel

from ..common.dependencies import LLMFactoryDep
from ..common.exceptions import ServiceUnavailableError
from ..config import Settings, get_settings
from ..document.dependencies import DocumentServiceDep
from ..tag.dependencies import TagServiceDep
from .orchestrator import SummarizationOrchestrator
from .service import SummaryService


def get_llm(
    factory: LLMFactoryDep,
) -> BaseLanguageModel:
    """Get LLM instance."""
    try:
        return factory.create_chat_model()
    except Exception as e:
        raise ServiceUnavailableError(f"LLM service: {str(e)}")


def get_summary_service(
    llm: Annotated[BaseLanguageModel, Depends(get_llm)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SummaryService:
    """Get summary service instance."""
    return SummaryService(
        llm=llm, 
        chunk_size=settings.chunk_size, 
        chunk_overlap=settings.chunk_overlap
    )


def get_summarization_orchestrator(
    document_service: DocumentServiceDep,
    summary_service: Annotated[SummaryService, Depends(get_summary_service)],
    tag_service: TagServiceDep,
) -> SummarizationOrchestrator:
    """Get summarization orchestrator instance."""
    return SummarizationOrchestrator(
        document_service=document_service,
        summarizer_service=summary_service,
        tag_service=tag_service,
    )


# Type aliases for dependency injection
SummaryServiceDep = Annotated[SummaryService, Depends(get_summary_service)]
LLMDep = Annotated[BaseLanguageModel, Depends(get_llm)]
SummarizationOrchestratorDep = Annotated[
    SummarizationOrchestrator, 
    Depends(get_summarization_orchestrator)
]
