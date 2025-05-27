from fastapi import Depends
from typing import Annotated

from ..config import get_settings, Settings
from .service import SummarizerService
from ..common.exceptions import ServiceUnavailableError


def get_summarizer_service(
    settings: Annotated[Settings, Depends(get_settings)]
) -> SummarizerService:
    """
    Get summarizer service instance.
    
    Returns:
        SummarizerService instance
        
    Raises:
        ServiceUnavailableError: If service cannot be initialized
    """
    try:
        return SummarizerService(settings)
    except Exception as e:
        raise ServiceUnavailableError("Summarization")


# Type alias for cleaner dependency injection
SummarizerServiceDep = Annotated[SummarizerService, Depends(get_summarizer_service)]