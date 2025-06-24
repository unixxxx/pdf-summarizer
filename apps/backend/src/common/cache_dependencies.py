"""Dependencies for cache service."""

from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from .cache_service import CacheService, get_cache_service


def get_cache(settings: Annotated[Settings, Depends(get_settings)]) -> CacheService:
    """Get cache service instance."""
    return get_cache_service(settings)


CacheServiceDep = Annotated[CacheService, Depends(get_cache)]