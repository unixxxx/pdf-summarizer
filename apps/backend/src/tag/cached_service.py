"""Cached tag service for improved performance."""

import logging
from typing import Any
from uuid import UUID

from shared.models import Tag
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.cache_service import CacheService
from .schemas import TagResponse
from .service import TagService

logger = logging.getLogger(__name__)


class CachedTagService:
    """Tag service with caching support."""
    
    def __init__(self, tag_service: TagService, cache_service: CacheService):
        """Initialize with tag service and cache service."""
        self.tag_service = tag_service
        self.cache_service = cache_service
    
    async def get_all_tags(
        self,
        db: AsyncSession,
    ) -> list[TagResponse]:
        """Get all tags (cached)."""
        # Use global cache key since tags are shared across users
        cache_key = self.cache_service.cache_key("tags", "all")
        
        # Try cache first
        cached = await self.cache_service.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for tags")
            return cached
        
        # Cache miss, fetch from database
        logger.debug("Cache miss for tags")
        result = await self.tag_service.get_all_tags(db)
        
        # Cache for 5 minutes
        await self.cache_service.set(cache_key, result, ttl=300)
        
        return result
    
    async def find_or_create_tags(
        self,
        tag_data_list: list[dict[str, Any]],
        db: AsyncSession,
    ) -> list[Tag]:
        """Find or create tags and invalidate cache."""
        result = await self.tag_service.find_or_create_tags(tag_data_list, db)
        
        # Invalidate tags cache
        await self._invalidate_tag_cache()
        
        return result
    
    async def associate_tags_with_document(
        self,
        document_id: UUID,
        tag_ids: list[UUID],
        db: AsyncSession,
    ) -> None:
        """Associate tags with document and invalidate cache."""
        await self.tag_service.associate_tags_with_document(document_id, tag_ids, db)
        
        # Invalidate tags cache
        await self._invalidate_tag_cache()
    
    async def _invalidate_tag_cache(self):
        """Invalidate all tag-related caches."""
        # Delete tags cache
        tags_key = self.cache_service.cache_key("tags", "all")
        await self.cache_service.delete(tags_key)