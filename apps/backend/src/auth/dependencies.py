from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..database.session import get_db
from .jwt_service import JWTService
from .oauth_service import OAuthService
from .schemas import TokenData, User
from .user_service import UserService

# Security scheme
security = HTTPBearer(
    scheme_name="JWT Bearer Token", description="JWT token obtained from OAuth2 login"
)


# Create singleton instances
_jwt_service: Optional[JWTService] = None
_oauth_service: Optional[OAuthService] = None


def get_jwt_service(settings: Settings = Depends(get_settings)) -> JWTService:
    """Get JWT service instance."""
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService(settings)
    return _jwt_service


def get_oauth_service(settings: Settings = Depends(get_settings)) -> OAuthService:
    """Get OAuth service instance."""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService(settings)
    return _oauth_service


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance."""
    return UserService(db)


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
    user_service: UserService = Depends(get_user_service),
) -> User:
    """
    Get the current authenticated user.

    Args:
        token_data: Decoded JWT token data
        user_service: User service instance

    Returns:
        Current user

    Raises:
        HTTPException: If user not found
    """
    user = await user_service.get_user(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


async def get_optional_user(
    request: Request,
    jwt_service: JWTService = Depends(get_jwt_service),
    user_service: UserService = Depends(get_user_service),
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.

    This dependency doesn't require authentication and won't raise
    an exception if the user is not authenticated.

    Args:
        request: FastAPI request
        jwt_service: JWT service instance
        user_service: User service instance

    Returns:
        Current user if authenticated, None otherwise
    """
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    # Extract token
    token = auth_header.split(" ")[1]

    # Try to decode token
    token_data = jwt_service.verify_token(token)
    if not token_data:
        return None

    # Get user
    user = await user_service.get_user(token_data.sub)
    return user


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]  # New naming convention
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
