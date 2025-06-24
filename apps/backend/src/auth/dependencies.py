from typing import Annotated

from fastapi import Depends, HTTPException, Query, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.cache_dependencies import CacheServiceDep
from ..config import Settings, get_settings
from ..database.session import get_db
from .cached_user_service import CachedUserService
from .jwt_service import JWTService
from .oauth_service import OAuthService
from .schemas import TokenData, User
from .user_service import UserService

# Security scheme
security = HTTPBearer(
    scheme_name="JWT Bearer Token", description="JWT token obtained from OAuth2 login")


def get_jwt_service(settings: Settings = Depends(get_settings)) -> JWTService:
    """Get JWT service instance."""
    return JWTService(settings)


def get_oauth_service(settings: Settings = Depends(get_settings)) -> OAuthService:
    """Get OAuth service instance."""
    return OAuthService(settings)


def get_user_service() -> UserService:
    """Get user service instance."""
    return UserService()


async def get_cached_user_service(
    cache_service: CacheServiceDep = None,
) -> CachedUserService:
    """Get cached user service instance."""
    user_service = UserService()
    return CachedUserService(user_service, cache_service)


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenData:
    """
    Validate JWT token and return token data.

    Args:
        credentials: Bearer token from Authorization header
        jwt_service: JWT service instance

    Returns:
        Decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    return jwt_service.decode_token(token)


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    cached_user_service: CachedUserService = Depends(get_cached_user_service),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user.

    Args:
        token_data: Decoded JWT token data
        cached_user_service: Cached user service instance
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If user not found
    """
    user = await cached_user_service.get_user(db, token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


async def get_current_user_ws(
    websocket: WebSocket,
    token: str = Query(..., alias="token"),
    jwt_service: JWTService = Depends(get_jwt_service),
    cached_user_service: CachedUserService = Depends(get_cached_user_service),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get current user from WebSocket connection.
    
    WebSocket connections can't use Authorization headers, so we use query params.
    
    Args:
        websocket: WebSocket connection
        token: JWT token from query parameter
        jwt_service: JWT service instance
        cached_user_service: Cached user service instance
        db: Database session
        
    Returns:
        Current user if authenticated, None otherwise
    """
    try:
        # Decode token
        token_data = jwt_service.decode_token(token)
        
        # Get user
        user = await cached_user_service.get_user(db, token_data.sub)
        return user
    except HTTPException:
        return None
    except Exception:
        return None


# Type aliases for dependency injection
CurrentUserDep = Annotated[User, Depends(get_current_user)]  # New naming convention
