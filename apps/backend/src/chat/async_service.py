"""Async chat service that delegates to worker."""

import logging
from uuid import UUID

from arq import create_pool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundException
from ..config import get_settings
from shared.models import Chat, ChatMessage, Document

logger = logging.getLogger(__name__)


class AsyncChatService:
    """Service for chat operations - delegates message processing to worker."""
    
    def __init__(self):
        """Initialize service."""
        self.settings = get_settings()
    
    async def find_active_chat_for_document(
        self,
        user_id: UUID,
        document_id: UUID,
        db: AsyncSession,
    ) -> Chat | None:
        """Find an existing active chat session for a document."""
        # Query for the most recent chat session for this document
        result = await db.execute(
            select(Chat)
            .where(
                Chat.user_id == user_id,
                Chat.document_id == document_id,
            )
            .order_by(Chat.updated_at.desc())
            .limit(1)
        )
        chat = result.scalar_one_or_none()
        
        # Only return if it's a recent chat (within last 24 hours)
        if chat:
            from datetime import datetime, timedelta, timezone
            if chat.updated_at and chat.updated_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc) - timedelta(hours=24):
                return chat
        
        return None
    
    async def create_chat_session(
        self,
        user_id: UUID,
        document_id: UUID,
        title: str | None,
        db: AsyncSession,
    ) -> Chat:
        """Create a new chat session for a document."""
        # Verify document exists and belongs to user
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundException("Document not found")
        
        # Create chat session
        chat = Chat(
            user_id=user_id,
            document_id=document_id,
            title=title or f"Chat with {document.filename}",
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        return chat
    
    async def get_chat_messages(
        self,
        chat_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> list[ChatMessage]:
        """Get all messages in a chat session."""
        # Verify chat belongs to user
        result = await db.execute(
            select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == user_id,
            )
        )
        chat = result.scalar_one_or_none()
        
        if not chat:
            raise NotFoundException("Chat not found")
        
        # Get messages
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at)
        )
        return result.scalars().all()
    
    async def enqueue_message(
        self,
        chat_id: UUID,
        user_id: UUID,
        message: str,
        db: AsyncSession,
    ) -> dict:
        """Enqueue message processing to worker."""
        # Verify chat belongs to user
        result = await db.execute(
            select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == user_id,
            )
        )
        chat = result.scalar_one_or_none()
        
        if not chat:
            raise NotFoundException("Chat not found")
        
        # Save user message
        user_message = ChatMessage(
            chat_id=chat_id,
            role="user",
            content=message,
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)
        
        # Enqueue message processing
        redis = await create_pool(self.settings.redis_url)
        
        try:
            job = await redis.enqueue_job(
                "process_chat_message",
                str(chat_id),
                str(user_id),
                str(user_message.id),
                message,
                _job_id=f"chat:{chat_id}:{user_message.id}",
                _queue_name="doculearn:queue",
            )
            
            return {
                "job_id": job.job_id,
                "status": "queued",
                "message": "Message processing has been queued",
                "chat_id": str(chat_id),
                "message_id": str(user_message.id),
            }
        finally:
            await redis.close()
    
    async def delete_chat(
        self,
        chat_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Delete a chat session."""
        # Verify chat belongs to user
        result = await db.execute(
            select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == user_id,
            )
        )
        chat = result.scalar_one_or_none()
        
        if not chat:
            raise NotFoundException("Chat not found")
        
        await db.delete(chat)
        await db.commit()