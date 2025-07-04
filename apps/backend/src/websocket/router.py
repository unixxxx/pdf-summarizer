"""WebSocket router for real-time communication."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import WebSocketException
from pydantic import ValidationError

from .connection_manager import manager
from .schemas import PingMessage, PongMessage, WebSocketMessageType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint."""
    from ..config import get_settings
    from .auth_service import WebSocketAuthService
    
    user = None
    user_id = None
    auth_service = WebSocketAuthService(get_settings())
    
    try:
        # Authenticate user
        user = await auth_service.authenticate_websocket(websocket)
        user_id = user["id"]
        
        # Connect user
        await manager.connect(websocket, user_id)
        
        # Keep connection alive and handle messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            msg_type = data.get("type")
            
            if msg_type == WebSocketMessageType.PING:
                # Respond to ping with pong
                try:
                    # Validate ping message format
                    PingMessage.model_validate(data)
                    pong_msg = PongMessage()
                    await websocket.send_json(pong_msg.model_dump(mode="json"))
                except ValidationError:
                    logger.warning("Invalid ping message format")
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