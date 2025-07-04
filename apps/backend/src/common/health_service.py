"""Shared health check service to avoid duplication."""

import logging

from arq import create_pool
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.cache_service import CacheService
from ..config import Settings

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for performing health checks on various components."""
    
    @staticmethod
    async def check_database(db: AsyncSession) -> tuple[bool, str]:
        """Check database connectivity.
        
        Returns:
            Tuple of (is_healthy, status_message)
        """
        try:
            await db.execute("SELECT 1")
            return True, "ok"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False, f"error: {str(e)}"
    
    @staticmethod
    async def check_redis(settings: Settings) -> tuple[bool, str]:
        """Check Redis connectivity.
        
        Returns:
            Tuple of (is_healthy, status_message)
        """
        try:
            redis = await create_pool(settings.redis_url)
            await redis.ping()
            await redis.close()
            return True, "ok"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False, f"error: {str(e)}"
    
    @staticmethod
    async def check_cache(settings: Settings) -> tuple[bool, str]:
        """Check cache service status.
        
        Returns:
            Tuple of (is_healthy, status_message)
        """
        try:
            if not settings.cache_enabled:
                return True, "disabled"
            
            cache_service = CacheService(settings)
            if await cache_service.ping():
                return True, "ok"
            else:
                return False, "not connected"
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False, f"error: {str(e)}"
    
    @staticmethod
    async def perform_basic_health_check(
        db: AsyncSession,
        settings: Settings
    ) -> dict[str, any]:
        """Perform basic health checks.
        
        Returns:
            Dictionary with health check results
        """
        services = {
            "api": True,
            "database": False,
            "redis": False,
        }
        
        # Check database
        db_healthy, _ = await HealthCheckService.check_database(db)
        services["database"] = db_healthy
        
        # Check Redis
        redis_healthy, _ = await HealthCheckService.check_redis(settings)
        services["redis"] = redis_healthy
        
        # Determine overall health
        all_healthy = all(services.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": services,
        }
    
    @staticmethod
    async def perform_detailed_health_check(
        db: AsyncSession,
        settings: Settings
    ) -> dict[str, any]:
        """Perform detailed health checks with status messages.
        
        Returns:
            Dictionary with detailed health check results
        """
        health_status = {
            "status": "healthy",
            "checks": {
                "api": "ok",
                "database": "unknown",
                "cache": "unknown",
            },
        }
        
        # Check database
        db_healthy, db_status = await HealthCheckService.check_database(db)
        health_status["checks"]["database"] = db_status
        if not db_healthy:
            health_status["status"] = "unhealthy"
        
        # Check cache
        _, cache_status = await HealthCheckService.check_cache(settings)
        health_status["checks"]["cache"] = cache_status
        
        return health_status