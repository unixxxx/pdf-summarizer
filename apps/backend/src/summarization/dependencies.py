from typing import Annotated

from fastapi import Depends

from ..common.exceptions import ServiceUnavailableError
from ..config import Settings, get_settings
from .service import SummarizerService


def get_summarizer_service(
    settings: Annotated[Settings, Depends(get_settings)],
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
    except Exception:
        raise ServiceUnavailableError("Summarization")


# Type alias for cleaner dependency injection
SummarizerServiceDep = Annotated[SummarizerService, Depends(get_summarizer_service)]
