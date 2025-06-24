"""WebSocket router for real-time communication."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import WebSocketException
from jose import JWTError, jwt

from ..auth.user_service import UserService
from ..config import get_settings
from ..database.session import get_db
from .connection_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_current_user_ws(
    websocket: WebSocket,
) -> dict | None:
    """Authenticate WebSocket connections."""
    # Extract token from query parameters
    query_params = dict(websocket.query_params)
    token = query_params.get('token')
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    
    settings = get_settings()
    
    try:
        # Verify JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        
        # Get user from database
        async for db in get_db():
            user_service = UserService()
            user = await user_service.get_user(db, user_id)
            if user is None:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
            
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
            
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint."""
    user = None
    user_id = None
    
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket)
        user_id = user["id"]
        
        # Connect user
        await manager.connect(websocket, user_id)
        
        # Keep connection alive and handle messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                # Respond to ping with pong
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                })
            elif data.get("type") == "subscribe":
                # Handle subscription requests
                document_id = data.get("document_id")
                if document_id:
                    await websocket.send_json({
                        "type": "subscribed",
                        "document_id": document_id,
                        "message": f"Subscribed to updates for document {document_id}"
                    })
            else:
                # Echo unknown messages back for debugging
                await websocket.send_json({
                    "type": "echo",
                    "original": data
                })
                
    except WebSocketDisconnect:
        if user_id:
            await manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
    except WebSocketException:
        # Already handled in authentication
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user_id:
            await manager.disconnect(websocket, user_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.websocket("/ws/health")
async def websocket_health_check(websocket: WebSocket):
    """WebSocket health check endpoint (no auth required)."""
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "health",
            "status": "healthy",
            "message": "WebSocket server is running"
        })
        await websocket.close()
    except Exception as e:
        logger.error(f"Health check error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)