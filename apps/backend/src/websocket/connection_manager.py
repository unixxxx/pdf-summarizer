"""WebSocket connection manager for handling real-time updates."""

import asyncio
import contextlib
import json
import logging
from uuid import UUID

import redis.asyncio as redis
from fastapi import WebSocket

from ..config import get_settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates."""
    
    def __init__(self):
        # Map user_id (as string) to set of active connections
        # Using string keys to ensure consistent lookups
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.settings = get_settings()
        self._redis_client = None
        self._pubsub = None
        self._redis_task = None
    
    async def initialize(self):
        """Initialize Redis connection for pub/sub."""
        if self.settings.redis_url:
            try:
                self._redis_client = redis.from_url(
                    self.settings.redis_url,
                    decode_responses=True
                )
                self._pubsub = self._redis_client.pubsub()
                await self._pubsub.subscribe("document_progress")
                logger.info("Redis pub/sub initialized for WebSocket broadcasting")
                
                # Start Redis message handler task
                self._redis_task = asyncio.create_task(self.handle_redis_messages())
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")
                self._redis_client = None
                self._pubsub = None
    
    async def connect(self, websocket: WebSocket, user_id: UUID):
        """Accept new WebSocket connection."""
        await websocket.accept()
        
        # Convert UUID to string for consistent dictionary keys
        user_id_str = str(user_id)
        
        if user_id_str not in self.active_connections:
            self.active_connections[user_id_str] = set()
        
        self.active_connections[user_id_str].add(websocket)
        
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established"
        })
    
    async def disconnect(self, websocket: WebSocket, user_id: UUID):
        """Remove WebSocket connection."""
        # Convert UUID to string for consistent dictionary keys
        user_id_str = str(user_id)
        
        if user_id_str in self.active_connections:
            self.active_connections[user_id_str].discard(websocket)
            if not self.active_connections[user_id_str]:
                del self.active_connections[user_id_str]
    
    async def send_document_processing_progress(
        self,
        user_id: UUID,
        document_id: str,
        stage: str,
        progress: int,
        **kwargs
    ):
        """Send document processing progress update to specific user."""
        # Convert UUID to string for consistent dictionary keys
        user_id_str = str(user_id)
        
        data = {
            "type": "document_processing",
            "document_id": document_id,
            "stage": stage,
            "progress": progress,
            **kwargs
        }
        
        # Send via direct connections
        if user_id_str in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[user_id_str]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                await self.disconnect(conn, user_id)
        else:
            logger.warning(f"No active WebSocket connections for user {user_id_str}")
        
        # Also publish to Redis for multi-instance support
        if self._redis_client:
            try:
                message = json.dumps({
                    "user_id": str(user_id),
                    "data": data
                })
                await self._redis_client.publish("document_progress", message)
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")
        else:
            logger.warning("Redis client not available for publishing")
    
    async def send_error(
        self,
        user_id: UUID,
        document_id: str,
        error: str
    ):
        """Send error message to specific user."""
        await self.send_document_processing_progress(
            user_id=user_id,
            document_id=document_id,
            stage="error",
            progress=0,
            error=error
        )
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users."""
        dead_connections = []
        
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")
                    dead_connections.append((user_id, connection))
        
        # Clean up dead connections
        for user_id, conn in dead_connections:
            await self.disconnect(conn, user_id)
    
    async def handle_redis_messages(self):
        """Handle messages from Redis pub/sub."""
        if not self._pubsub:
            return
        
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        # Keep user_id as string for consistent dictionary lookups
                        user_id_str = data["user_id"]
                        ws_data = data["data"]
                        
                        
                        # Only send to connections on this instance
                        if user_id_str in self.active_connections:
                            sent_count = 0
                            for connection in self.active_connections[user_id_str]:
                                try:
                                    await connection.send_json(ws_data)
                                    sent_count += 1
                                except Exception as e:
                                    logger.error(f"[WEBSOCKET] Error sending to connection: {e}")
                            
                        else:
                            logger.warning(f"[WEBSOCKET] No active connections for user {user_id_str}")
                    except Exception as e:
                        logger.error(f"[WEBSOCKET] Error processing Redis message: {e}")
        except Exception as e:
            logger.error(f"Error in Redis message handler: {e}")
    
    async def close(self):
        """Clean up connections."""
        # Cancel Redis message handler task
        if self._redis_task:
            self._redis_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._redis_task
        
        if self._pubsub:
            await self._pubsub.unsubscribe("document_progress")
            await self._pubsub.close()
        
        if self._redis_client:
            await self._redis_client.close()


# Global connection manager instance
manager = ConnectionManager()