"""Redis caching service for the application."""

import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from ..config import Settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing Redis cache operations."""

    def __init__(self, settings: Settings):
        """Initialize cache service with Redis connection."""
        self.settings = settings
        self.enabled = settings.cache_enabled
        self._redis: redis.Redis | None = None

        if self.enabled:
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.enabled = False

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self.enabled or not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.enabled or not self._redis:
            return False

        try:
            ttl = ttl or self.settings.cache_ttl
            serialized = json.dumps(value)
            await self._redis.setex(key, ttl, serialized)
            return True
        except (RedisError, json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled or not self._redis:
            return False

        try:
            result = await self._redis.delete(key)
            return bool(result)
        except RedisError as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.enabled or not self._redis:
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self._redis.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.enabled or not self._redis:
            return False

        try:
            return bool(await self._redis.exists(key))
        except RedisError as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False

    async def ping(self) -> bool:
        """Check if Redis is available."""
        if not self.enabled or not self._redis:
            return False

        try:
            return await self._redis.ping()
        except RedisError:
            return False

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    def cache_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments."""
        parts = [prefix]
        for arg in args:
            if arg is not None:
                parts.append(str(arg))
        return ":".join(parts)

    # Cache key generators for different entities
    def user_key(self, provider: str, provider_id: str) -> str:
        """Generate cache key for user lookup."""
        return self.cache_key("user", provider, provider_id)

    def tag_counts_key(self, user_id: str) -> str:
        """Generate cache key for tag counts."""
        return self.cache_key("tags", "counts", user_id)





# Dependency injection
def get_cache_service(settings: Settings) -> CacheService:
    """Get cache service instance for dependency injection."""
    return CacheService(settings)
