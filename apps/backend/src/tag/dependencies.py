"""Dependencies for Tag module."""

from typing import Annotated

from fastapi import Depends

from ..common.cache_dependencies import CacheServiceDep
from .cached_service import CachedTagService
from .service import TagService


def get_tag_service() -> TagService:
    """Get tag service instance."""
    return TagService()


def get_cached_tag_service(
    cache_service: CacheServiceDep,
) -> CachedTagService:
    """Get cached tag service instance."""
    tag_service = TagService()
    return CachedTagService(tag_service, cache_service)


TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
CachedTagServiceDep = Annotated[CachedTagService, Depends(get_cached_tag_service)]