"""WebSocket authentication service."""

import logging
from typing import Optional

from fastapi import WebSocket, status
from fastapi.exceptions import WebSocketException
from jose import JWTError, jwt

from ..auth.user_service import UserService
from ..config import Settings, get_settings
from ..database.session import get_db

logger = logging.getLogger(__name__)


class WebSocketAuthService:
    """Service for handling WebSocket authentication."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the WebSocket authentication service.
        
        Args:
            settings: Application settings. If not provided, will be fetched.
        """
        self.settings = settings or get_settings()

    async def authenticate_websocket(
        self, 
        websocket: WebSocket
    ) -> dict[str, str]:
        """Authenticate WebSocket connection using JWT token from query parameters.
        
        Args:
            websocket: The WebSocket connection to authenticate.
            
        Returns:
            Dictionary containing user information (id, email, name).
            
        Raises:
            WebSocketException: If authentication fails for any reason.
        """
        # Extract token from query parameters
        token = self._extract_token_from_query(websocket)
        
        if not token:
            await self._close_with_policy_violation(
                websocket, 
                "No authentication token provided"
            )
        
        try:
            # Verify JWT token
            user_id = self._verify_jwt_token(token)
            
            # Get user from database
            user_data = await self._get_user_from_database(websocket, user_id)
            
            return user_data
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            await self._close_with_policy_violation(
                websocket, 
                "Invalid authentication token"
            )
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await self._close_with_internal_error(websocket)

    def _extract_token_from_query(self, websocket: WebSocket) -> Optional[str]:
        """Extract authentication token from WebSocket query parameters.
        
        Args:
            websocket: The WebSocket connection.
            
        Returns:
            The token string if present, None otherwise.
        """
        query_params = dict(websocket.query_params)
        return query_params.get('token')

    def _verify_jwt_token(self, token: str) -> str:
        """Verify JWT token and extract user ID.
        
        Args:
            token: The JWT token to verify.
            
        Returns:
            The user ID extracted from the token.
            
        Raises:
            JWTError: If token verification fails.
            ValueError: If user ID is not present in token.
        """
        payload = jwt.decode(
            token,
            self.settings.jwt_secret_key,
            algorithms=[self.settings.jwt_algorithm]
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("No user ID in token payload")
            
        return user_id

    async def _get_user_from_database(
        self, 
        websocket: WebSocket, 
        user_id: str
    ) -> dict[str, str]:
        """Retrieve user from database.
        
        Args:
            websocket: The WebSocket connection (for error handling).
            user_id: The user ID to look up.
            
        Returns:
            Dictionary containing user information.
            
        Raises:
            WebSocketException: If user is not found.
        """
        async for db in get_db():
            user_service = UserService()
            user = await user_service.get_user(db, user_id)
            if user is None:
                await self._close_with_policy_violation(
                    websocket, 
                    f"User {user_id} not found"
                )
            
            return {
                "id": str(user.id),
                "email": user.email,
                "name": user.name
            }

    async def _close_with_policy_violation(
        self, 
        websocket: WebSocket, 
        reason: str
    ) -> None:
        """Close WebSocket connection with policy violation code.
        
        Args:
            websocket: The WebSocket connection to close.
            reason: The reason for closing (for logging).
            
        Raises:
            WebSocketException: Always raised after closing.
        """
        logger.warning(f"WebSocket auth failed: {reason}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    async def _close_with_internal_error(self, websocket: WebSocket) -> None:
        """Close WebSocket connection with internal error code.
        
        Args:
            websocket: The WebSocket connection to close.
            
        Raises:
            WebSocketException: Always raised after closing.
        """
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR)