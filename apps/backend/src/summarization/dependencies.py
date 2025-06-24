"""Dependencies for Summarization domain."""

from typing import Annotated

from fastapi import Depends
from langchain.schema.language_model import BaseLanguageModel

from ..common.dependencies import LLMFactoryDep
from ..common.exceptions import ServiceUnavailableError
from ..library.document.dependencies import DocumentServiceDep
from ..library.folder.dependencies import FolderServiceDep
from ..library.tag.dependencies import TagServiceDep
from .orchestrator import SummarizationOrchestrator
from .service import SummaryService


def get_llm(
    factory: LLMFactoryDep, ) -> BaseLanguageModel:
    """Get LLM instance."""
    try:
        return factory.create_chat_model()
    except Exception as e:
        raise ServiceUnavailableError(f"LLM service: {str(e)}")


def get_summary_service(
    llm: Annotated[BaseLanguageModel, Depends(get_llm)],
) -> SummaryService:
    """Get summary service instance."""
    return SummaryService(llm=llm)


def get_summarization_orchestrator(
    document_service: DocumentServiceDep,
    summary_service: Annotated[SummaryService, Depends(get_summary_service)],
    tag_service: TagServiceDep,
    folder_service: FolderServiceDep,
) -> SummarizationOrchestrator:
    """Get summarization orchestrator instance (legacy - for backwards compatibility)."""
    # Don't inject embeddings service - it's optional and can fail if LLM is not available
    return SummarizationOrchestrator(
        document_service=document_service,
        summarizer_service=summary_service,
        tag_service=tag_service,
        folder_service=folder_service,
        embeddings_service=None,  # Will be injected when actually needed
    )


# Type aliases for dependency injection
SummaryServiceDep = Annotated[SummaryService, Depends(get_summary_service)]
LLMDep = Annotated[BaseLanguageModel, Depends(get_llm)]
SummarizationOrchestratorDep = Annotated[
    SummarizationOrchestrator, 
    Depends(get_summarization_orchestrator)
]
