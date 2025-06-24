"""Schemas for chat operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateChatRequest(BaseModel):
    """Request to create a new chat session."""
    
    document_id: UUID = Field(description="ID of the document to chat with")
    title: str | None = Field(
        default=None,
        description="Optional title for the chat session",
        max_length=255,
    )


class ChatResponse(BaseModel):
    """Response for a chat session."""
    
    id: UUID
    user_id: UUID
    document_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageRequest(BaseModel):
    """Request to send a message in a chat."""
    
    message: str = Field(
        description="The message to send",
        min_length=1,
        max_length=5000,
    )


class ChatMessageResponse(BaseModel):
    """Response for a chat message."""
    
    id: UUID
    chat_id: UUID
    role: str
    content: str
    message_metadata: dict[str, Any] | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @field_validator("message_metadata", mode="before")
    @classmethod
    def parse_json_metadata(cls, v):
        """Parse JSON metadata if it's a string."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class ChatListItem(BaseModel):
    """Item in chat list."""
    
    id: UUID
    document_id: UUID
    document_filename: str
    title: str
    last_message: str | None = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class ChatWithMessages(BaseModel):
    """Chat session with messages."""
    
    chat: ChatResponse
    messages: list[ChatMessageResponse]