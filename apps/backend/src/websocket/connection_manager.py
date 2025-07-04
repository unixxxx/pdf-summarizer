"""WebSocket connection manager for handling real-time updates."""

import asyncio
import contextlib
import json
import logging
from uuid import UUID

import redis.asyncio as redis
from fastapi import WebSocket
from pydantic import ValidationError

from ..config import get_settings
from ..document.schemas import DocumentListItemResponse
from ..tag.schemas import TagResponse
from .schemas import (
    BaseWebSocketMessage,
    ConnectionMessage,
    ConnectionStatus,
    DocumentProcessingMessage,
    ProcessingStage,
    RedisProgressMessage,
)

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
        connection_msg = ConnectionMessage(
            status=ConnectionStatus.CONNECTED,
            message="WebSocket connection established"
        )
        await websocket.send_json(connection_msg.model_dump(mode="json"))
    
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
        progress: float,
        message: str | None = None,
        error: str | None = None,
        document: DocumentListItemResponse | None = None
    ):
        """Send document processing progress update to specific user."""
        # Convert UUID to string for consistent dictionary keys
        user_id_str = str(user_id)
        
        # Create validated message
        try:
            processing_msg = DocumentProcessingMessage(
                document_id=UUID(document_id),
                stage=ProcessingStage(stage),
                progress=progress,
                message=message,
                error=error,
                document=document
            )
        except (ValueError, ValidationError) as e:
            logger.error(f"Invalid processing message data: {e}")
            return
        
        # Send via direct connections
        if user_id_str in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[user_id_str]:
                try:
                    await connection.send_json(processing_msg.model_dump(mode="json"))
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
                redis_message = {
                    "user_id": str(user_id),
                    "data": processing_msg.model_dump(mode="json")
                }
                await self._redis_client.publish("document_progress", json.dumps(redis_message))
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
            stage=ProcessingStage.FAILED.value,
            progress=0.0,
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
                        # Debug log the raw message
                        logger.debug(f"[WEBSOCKET] Raw Redis message: {message['data'][:200]}")
                        
                        # Parse Redis message
                        redis_msg = RedisProgressMessage.model_validate_json(message["data"])
                        user_id_str = redis_msg.user_id
                        raw_data = redis_msg.data
                        
                        # Map worker message to proper WebSocket schema
                        ws_message = await self._map_worker_message_to_schema(raw_data)
                        if not ws_message:
                            logger.warning(f"Could not map worker message: {raw_data}")
                            continue
                        
                        # Only send to connections on this instance
                        if user_id_str in self.active_connections:
                            sent_count = 0
                            for connection in self.active_connections[user_id_str]:
                                try:
                                    await connection.send_json(ws_message.model_dump(mode="json"))
                                    sent_count += 1
                                except Exception as e:
                                    logger.error(f"[WEBSOCKET] Error sending to connection: {e}")
                            
                        else:
                            logger.debug(f"[WEBSOCKET] No active connections for user {user_id_str}")
                    except ValidationError as e:
                        logger.error(f"[WEBSOCKET] Invalid Redis message format: {e}")
                    except Exception as e:
                        logger.error(f"[WEBSOCKET] Error processing Redis message: {e}")
                        logger.error(f"[WEBSOCKET] Message data: {message.get('data', 'N/A')[:500]}")
        except Exception as e:
            logger.error(f"Error in Redis message handler: {e}")
    
    async def _map_worker_message_to_schema(self, raw_data: dict) -> BaseWebSocketMessage | None:
        """Map raw worker message to proper WebSocket schema."""
        try:
            msg_type = raw_data.get("type")
            
            if msg_type == "document_processing":
                stage = ProcessingStage(raw_data["stage"])
                
                # Extract document data if present in details
                document_data = None
                details = raw_data.get("details", {})
                if "document" in details:
                    try:
                        document_data = DocumentListItemResponse.model_validate(details["document"])
                    except ValidationError as e:
                        logger.warning(f"Failed to parse document data from worker message: {e}")
                
                # If stage is completed and no document data, fetch it from database
                if stage == ProcessingStage.COMPLETED and not document_data:
                    logger.info(
                        f"Completion event received without document data. "
                        f"Fetching document {raw_data.get('document_id')} from database"
                    )
                    document_data = await self._fetch_document_data(raw_data["document_id"])
                
                return DocumentProcessingMessage(
                    document_id=UUID(raw_data["document_id"]),
                    stage=stage,
                    progress=float(raw_data["progress"]),
                    message=raw_data.get("message"),
                    error=raw_data.get("error") or details.get("error"),
                    document=document_data
                )
            
            # Add more message type mappings as needed
            
            return None
        except (KeyError, ValueError, ValidationError) as e:
            logger.error(f"Failed to map worker message: {e}")
            return None
    
    async def _fetch_document_data(self, document_id: str) -> DocumentListItemResponse | None:
        """Fetch document data from database."""
        try:
            from shared.models import Document
            from sqlalchemy import select
            from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
            from sqlalchemy.orm import selectinload, sessionmaker
            
            # Create database session
            engine = create_async_engine(self.settings.database_url)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                result = await session.execute(
                    select(Document)
                    .options(selectinload(Document.tags))
                    .where(Document.id == UUID(document_id))
                )
                document = result.scalar_one_or_none()
                
                if not document:
                    logger.error(f"Document {document_id} not found in database")
                    return None
                
                # Convert to DocumentListItemResponse
                return DocumentListItemResponse(
                    id=document.id,
                    document_id=document.id,
                    filename=document.filename,
                    file_size=document.file_size,
                    summary=(
                        document.extracted_text[:200] + "..."
                        if document.extracted_text
                        else ""
                    ),
                    created_at=document.created_at,
                    word_count=document.word_count or 0,
                    tags=[
                        TagResponse(
                            id=tag.id,
                            name=tag.name,
                            slug=tag.slug,
                            color=tag.color,
                        )
                        for tag in document.tags
                    ],
                    status=document.status,
                    folder_id=document.folder_id,
                    error_message=document.error_message,
                )
        except Exception as e:
            logger.error(f"Failed to fetch document data: {e}")
            return None
    
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