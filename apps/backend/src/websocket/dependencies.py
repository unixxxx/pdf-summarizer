"""Dependencies for WebSocket domain."""

from typing import Annotated

from fastapi import Depends

from ..config import Settings, get_settings
from .auth_service import WebSocketAuthService


def get_websocket_auth_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> WebSocketAuthService:
    """Get WebSocket auth service instance."""
    return WebSocketAuthService(settings)


WebSocketAuthServiceDep = Annotated[WebSocketAuthService, Depends(get_websocket_auth_service)]