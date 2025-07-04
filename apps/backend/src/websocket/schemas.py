"""WebSocket message schemas."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ..document.schemas import DocumentListItemResponse


class WebSocketMessageType(str, Enum):
    """WebSocket message types."""
    CONNECTION = "connection"
    DOCUMENT_PROCESSING = "document_processing"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class ConnectionStatus(str, Enum):
    """Connection status types."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ProcessingStage(str, Enum):
    """Document processing stages."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseWebSocketMessage(BaseModel):
    """Base WebSocket message."""
    type: WebSocketMessageType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConnectionMessage(BaseWebSocketMessage):
    """Connection status message."""
    type: WebSocketMessageType = WebSocketMessageType.CONNECTION
    status: ConnectionStatus
    message: str | None = None


class DocumentProcessingMessage(BaseWebSocketMessage):
    """Document processing progress message."""
    type: WebSocketMessageType = WebSocketMessageType.DOCUMENT_PROCESSING
    document_id: UUID
    stage: ProcessingStage
    progress: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    message: str | None = None
    error: str | None = None
    document: DocumentListItemResponse | None = None  # Full document data on completion


class PingMessage(BaseWebSocketMessage):
    """Ping message for keeping connection alive."""
    type: WebSocketMessageType = WebSocketMessageType.PING


class PongMessage(BaseWebSocketMessage):
    """Pong response message."""
    type: WebSocketMessageType = WebSocketMessageType.PONG


class ErrorMessage(BaseWebSocketMessage):
    """Error message."""
    type: WebSocketMessageType = WebSocketMessageType.ERROR
    error: str
    details: dict[str, Any] | None = None


# Redis message schema for worker->backend communication
class RedisProgressMessage(BaseModel):
    """Message format from worker via Redis pub/sub."""
    user_id: str
    data: dict[str, Any]