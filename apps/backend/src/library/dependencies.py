"""Dependencies for Library domain."""

from typing import Annotated

from fastapi import Depends

from ..common.dependencies import LLMFactoryDep
from .tag_service import TagService


def get_tag_service(
    factory: LLMFactoryDep,
) -> TagService:
    """Get tag service instance."""
    # Use unified factory for LLM creation
    llm = factory.create_chat_model(temperature=0.3)  # Lower temperature for consistent tags
    
    return TagService(llm)


TagServiceDep = Annotated[TagService, Depends(get_tag_service)]