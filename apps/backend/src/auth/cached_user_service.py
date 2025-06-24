"""Cached user service that wraps the UserService with caching."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..common.cache_service import CacheService
from .schemas import User as UserSchema
from .schemas import UserCreate
from .user_service import UserService

logger = logging.getLogger(__name__)


class CachedUserService:
    """User service wrapper with caching support."""
    
    def __init__(self, user_service: UserService, cache_service: CacheService):
        """Initialize with user service and cache service."""
        self.user_service = user_service
        self.cache_service = cache_service
    
    async def create_or_update_user(self, db: AsyncSession, user_data: UserCreate) -> UserSchema:
        """Create or update user and invalidate cache."""
        result = await self.user_service.create_or_update_user(db, user_data)
        
        # Invalidate user cache
        if result:
            user_key = self.cache_service.user_key(result.provider, result.provider_id)
            await self.cache_service.delete(user_key)
            
            # Also invalidate by ID
            id_key = self.cache_service.cache_key("user", "id", result.id)
            await self.cache_service.delete(id_key)
        
        return result
    
    async def get_user(self, db: AsyncSession, user_id: str) -> UserSchema:
        """Get user by ID with caching."""
        # Try cache first
        cache_key = self.cache_service.cache_key("user", "id", user_id)
        cached = await self.cache_service.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for user ID: {user_id}")
            return UserSchema(**cached)
        
        # Cache miss, fetch from database
        logger.debug(f"Cache miss for user ID: {user_id}")
        user = await self.user_service.get_user(db, user_id)
        
        # Cache the result
        if user:
            await self.cache_service.set(cache_key, user.model_dump(mode='json'), ttl=3600)  # 1 hour
            # Also cache by provider
            provider_key = self.cache_service.user_key(user.provider, user.provider_id)
            await self.cache_service.set(provider_key, user.model_dump(mode='json'), ttl=3600)
        
        return user
    
    async def get_user_by_provider(
        self,
        db: AsyncSession,
        provider: str, 
        provider_id: str
    ) -> UserSchema | None:
        """Get user by provider with caching."""
        # Try cache first
        cache_key = self.cache_service.user_key(provider, provider_id)
        cached = await self.cache_service.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for user {provider}:{provider_id}")
            return UserSchema(**cached)
        
        # Cache miss, fetch from database
        logger.debug(f"Cache miss for user {provider}:{provider_id}")
        user = await self.user_service.get_user_by_provider(db, provider, provider_id)
        
        if user:
            # Cache the result
            await self.cache_service.set(cache_key, user.model_dump(mode='json'), ttl=3600)
            # Also cache by ID
            id_key = self.cache_service.cache_key("user", "id", user.id)
            await self.cache_service.set(id_key, user.model_dump(mode='json'), ttl=3600)
            return user
        
        return None
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> UserSchema | None:
        """Get user by email (no caching for privacy)."""
        # Don't cache email lookups for privacy reasons
        return await self.user_service.get_user_by_email(db, email)
    
    async def delete_user(self, db: AsyncSession, user_id: str) -> None:
        """Delete user and invalidate cache."""
        # Get user first to know provider info
        user = await self.get_user(db, user_id)
        
        # Delete from database
        await self.user_service.delete_user(db, user_id)
        
        # Invalidate cache
        if user:
            user_key = self.cache_service.user_key(user.provider, user.provider_id)
            await self.cache_service.delete(user_key)
            
            id_key = self.cache_service.cache_key("user", "id", user_id)
            await self.cache_service.delete(id_key)
    
    async def get_user_count(self, db: AsyncSession) -> int:
        """Get user count with caching."""
        cache_key = "users:count"
        cached = await self.cache_service.get(cache_key)
        if cached is not None:
            return cached
        
        count = await self.user_service.get_user_count(db)
        await self.cache_service.set(cache_key, count, ttl=300)  # 5 minutes
        return count
    
    async def list_users(
        self,
        db: AsyncSession,
        limit: int = 100, 
        offset: int = 0
    ) -> list[UserSchema]:
        """List users (no caching for dynamic lists)."""
        return await self.user_service.list_users(db, limit, offset)