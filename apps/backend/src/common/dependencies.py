"""Common dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from .llm_factory import UnifiedLLMFactory, get_llm_factory


def get_unified_llm_factory(
    settings: Annotated[Settings, Depends(get_settings)]
) -> UnifiedLLMFactory:
    """Get unified LLM factory instance for dependency injection."""
    return get_llm_factory(settings)


# Type alias for dependency injection
LLMFactoryDep = Annotated[UnifiedLLMFactory, Depends(get_unified_llm_factory)]