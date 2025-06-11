"""Tag management module."""

from .dependencies import TagServiceDep
from .router import router
from .schemas import TagGenerationRequest, TagGenerationRequestInternal, TagResponse
from .service import TagService

__all__ = [
    "router",
    "TagGenerationRequest",
    "TagGenerationRequestInternal", 
    "TagResponse",
    "TagService",
    "TagServiceDep"
]