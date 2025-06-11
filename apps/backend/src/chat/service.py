"""Chat service for document Q&A."""

import json
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..common.llm_factory import UnifiedLLMFactory
from ..config import Settings
from ..database.models import Chat, ChatMessage, Document
from ..embeddings.service import EmbeddingsService


class ChatService:
    """Service for managing chat sessions and Q&A with documents."""

    def __init__(self, settings: Settings, embeddings_service: EmbeddingsService, factory: UnifiedLLMFactory):
        self.settings = settings
        self.embeddings_service = embeddings_service
        self.factory = factory
        
        # Use unified factory for LLM creation
        self.llm = self.factory.create_chat_model()
    
    async def find_active_chat_for_document(
        self,
        user_id: UUID,
        document_id: UUID,
        db: AsyncSession,
    ) -> Optional[Chat]:
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
        title: Optional[str],
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
            raise NotFoundError("Document")
        
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
    
    async def get_user_chats(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> list[Chat]:
        """Get all chat sessions for a user."""
        result = await db.execute(
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
        )
        return result.scalars().all()
    
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
            raise NotFoundError("Chat")
        
        # Get messages
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at)
        )
        return result.scalars().all()
    
    async def send_message(
        self,
        chat_id: UUID,
        user_id: UUID,
        message: str,
        db: AsyncSession,
    ) -> ChatMessage:
        """Send a message in a chat session and get AI response."""
        # Verify chat belongs to user
        result = await db.execute(
            select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == user_id,
            )
        )
        chat = result.scalar_one_or_none()
        
        if not chat:
            raise NotFoundError("Chat")
        
        # Save user message
        user_message = ChatMessage(
            chat_id=chat_id,
            role="user",
            content=message,
        )
        db.add(user_message)
        
        # Get relevant document chunks (increased from 5 to 8 for better context)
        relevant_chunks = await self.embeddings_service.search_similar_chunks(
            query=message,
            document_id=str(chat.document_id),
            db=db,
            limit=8,
        )
        
        # Build context from relevant chunks
        context_texts = []
        chunk_metadata = []
        for chunk, similarity in relevant_chunks:
            context_texts.append(chunk.chunk_text)
            chunk_metadata.append({
                "chunk_id": str(chunk.id),
                "similarity": similarity,
                "chunk_index": chunk.chunk_index,
            })
        
        context = "\n\n".join(context_texts)
        
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Found {len(relevant_chunks)} chunks for document {chat.document_id}")
        logger.info(f"Context length: {len(context)} characters")
        
        # Get chat history
        history_messages = await self._get_chat_history(chat_id, db)
        
        # Get document info for context
        result = await db.execute(
            select(Document).where(Document.id == chat.document_id)
        )
        document = result.scalar_one()
        
        # Build prompt with context
        system_prompt = (
            f"You are an intelligent assistant specialized in answering questions about the document '{document.filename}'. "
            "Your role is to provide accurate, helpful, and contextual answers based on the document's content.\n\n"
            "Guidelines:\n"
            "1. Use the provided context excerpts to answer questions accurately\n"
            "2. If the context doesn't contain enough information, acknowledge this and provide what you can\n"
            "3. Be specific and cite relevant parts of the context when answering\n"
            "4. For questions about the document's structure or overview, synthesize information from multiple chunks\n"
            "5. Maintain a helpful and professional tone\n"
            "6. If asked about something not in the context, clearly state that the information isn't available in the provided excerpts\n\n"
            "7. Provide short answers\n\n"
        )
        
        if context:
            system_prompt += f"Relevant excerpts from '{document.filename}':\n"
            system_prompt += "=" * 50 + "\n"
            for i, chunk_text in enumerate(context_texts, 1):
                system_prompt += f"\n[Excerpt {i}]\n{chunk_text}\n"
            system_prompt += "=" * 50 + "\n\n"
            system_prompt += "Use these excerpts to answer the user's question. If the answer spans multiple excerpts, synthesize the information coherently."
        else:
            system_prompt += (
                f"Note: No relevant excerpts were found in '{document.filename}' for this specific question. "
                "This might mean:\n"
                "- The document doesn't contain information about this topic\n"
                "- The question needs to be rephrased to match the document's terminology\n"
                "- The document might discuss this topic using different terms\n\n"
                "Please let the user know and suggest how they might rephrase their question."
            )
        
        # Generate response
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add history
        for msg in history_messages[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message,
        })
        
        # Get AI response
        response = await self.llm.ainvoke(messages)
        
        # Save AI response
        ai_message = ChatMessage(
            chat_id=chat_id,
            role="assistant",
            content=response.content,
            message_metadata=json.dumps({
                "chunks_used": chunk_metadata,
                "model": self.factory.get_provider_info()["model"],
            }),
        )
        db.add(ai_message)
        
        # Update chat's updated_at
        chat.updated_at = func.now()
        
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(ai_message)
        
        return user_message, ai_message
    
    async def _get_chat_history(
        self,
        chat_id: UUID,
        db: AsyncSession,
        limit: int = 20,
    ) -> list[ChatMessage]:
        """Get recent chat history for context."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        # Return in chronological order
        return list(reversed(messages))
    
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
            raise NotFoundError("Chat")
        
        await db.delete(chat)
        await db.commit()