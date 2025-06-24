"""Dependencies for Tag module."""

from typing import Annotated

from fastapi import Depends

from ...common.cache_dependencies import CacheServiceDep
from .cached_service import CachedTagService
from .service import TagService


def get_tag_service() -> TagService:
    """Get tag service instance."""
    # Don't inject embeddings service - it's optional for tags
    return TagService(None)


def get_cached_tag_service(
    cache_service: CacheServiceDep,
) -> CachedTagService:
    """Get cached tag service instance."""
    tag_service = TagService(None)
    return CachedTagService(tag_service, cache_service)


TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
CachedTagServiceDep = Annotated[CachedTagService, Depends(get_cached_tag_service)]