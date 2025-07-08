"""Redis connection pool manager for better performance."""

from typing import Optional

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from .config import get_settings
from .logger import logger

settings = get_settings()


class RedisPoolManager:
    """Manages a shared Redis connection pool."""
    
    _instance: Optional['RedisPoolManager'] = None
    _pool: Optional[ArqRedis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_pool(self) -> ArqRedis:
        """Get or create the Redis connection pool."""
        if self._pool is None:
            logger.info("Creating Redis connection pool")
            self._pool = await create_pool(
                RedisSettings.from_dsn(settings.redis_url),
                max_jobs=10,  # Connection pool size
            )
        return self._pool
    
    async def close(self):
        """Close the Redis connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Redis connection pool closed")


# Global instance
redis_pool_manager = RedisPoolManager()


async def get_redis_pool() -> ArqRedis:
    """Get the shared Redis connection pool."""
    return await redis_pool_manager.get_pool()