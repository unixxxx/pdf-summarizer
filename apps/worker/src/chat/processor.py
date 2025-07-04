"""Chat message processor task."""

import logging
from typing import Any
from uuid import UUID

from arq import ArqRedis
from shared.models import Chat, ChatMessage, Document
from sqlalchemy import select

from ..common.database import get_db_session
from ..common.llm_factory import UnifiedLLMFactory
from ..common.redis_progress_reporter import ProgressStage
from ..common.redis_progress_reporter import RedisProgressReporter as ProgressReporter

logger = logging.getLogger(__name__)


async def process_chat_message(
    ctx: dict,
    chat_id: str,
    user_id: str,
    message_id: str,
    message_text: str,
) -> dict[str, Any]:
    """
    Process a chat message and generate AI response.
    
    Args:
        ctx: Worker context
        chat_id: Chat session ID
        user_id: User ID
        message_id: User message ID
        message_text: Message content
        
    Returns:
        Dict with AI response
    """
    redis: ArqRedis = ctx["redis"]
    job_id = ctx.get("job_id", f"chat:{message_id}")
    
    async with ProgressReporter(
        redis=redis,
        job_id=job_id,
        document_id=chat_id,  # Using chat_id as document_id for progress tracking
        user_id=user_id
    ) as reporter:
        
        try:
            await reporter.report_progress(
                ProgressStage.PROCESSING, 
                0.10, 
                "Processing message"
            )
            
            async with get_db_session() as db:
                # Get chat and document
                result = await db.execute(
                    select(Chat).where(Chat.id == UUID(chat_id))
                )
                chat = result.scalar_one_or_none()
                
                if not chat:
                    raise ValueError(f"Chat {chat_id} not found")
                
                # Get document
                result = await db.execute(
                    select(Document).where(Document.id == chat.document_id)
                )
                document = result.scalar_one()
                
                await reporter.report_progress(
                    ProgressStage.PROCESSING,
                    0.20,
                    "Retrieving relevant context"
                )
                
                # Initialize LLM factory
                factory = UnifiedLLMFactory(ctx["settings"])
                embeddings_model, _ = factory.create_embeddings_model()
                
                # Generate embedding for the query
                query_embedding = await embeddings_model.aembed_query(message_text)
                
                # Search for similar chunks using pgvector
                import json

                from sqlalchemy import text
                
                query_embedding_str = json.dumps(query_embedding)
                
                # Use raw SQL for vector similarity search
                sql = text("""
                    SELECT 
                        dc.*,
                        1 - (dc.embedding <=> CAST(:query_embedding AS vector)) as similarity
                    FROM document_chunks dc
                    WHERE 
                        dc.embedding IS NOT NULL
                        AND dc.document_id = :document_id
                        AND dc.embedding <=> CAST(:query_embedding AS vector) <= 0.5
                    ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
                    LIMIT 8
                """)
                
                result = await db.execute(sql, {
                    "query_embedding": query_embedding_str,
                    "document_id": str(document.id)
                })
                
                chunks = result.mappings().all()
                relevant_chunks = [(chunk, chunk['similarity']) for chunk in chunks]
                
                await reporter.report_progress(
                    ProgressStage.PROCESSING,
                    0.40,
                    "Generating response"
                )
                
                # Build context
                context_texts = []
                chunk_metadata = []
                
                if relevant_chunks:
                    for chunk, similarity in relevant_chunks:
                        context_texts.append(chunk['chunk_text'])
                        chunk_metadata.append({
                            "chunk_id": str(chunk['id']),
                            "similarity": similarity,
                            "chunk_index": chunk['chunk_index'],
                        })
                elif document.extracted_text:
                    # Fallback to document text
                    max_chars = 8000
                    text = document.extracted_text[:max_chars]
                    if len(document.extracted_text) > max_chars:
                        text += "\n\n[Note: Document truncated for processing]"
                    context_texts.append(text)
                
                context = "\n\n".join(context_texts)
                
                # Get chat history
                result = await db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.chat_id == UUID(chat_id))
                    .order_by(ChatMessage.created_at.desc())
                    .limit(20)
                )
                history = list(reversed(result.scalars().all()))
                
                await reporter.report_progress(
                    ProgressStage.PROCESSING,
                    0.60,
                    "Creating AI response"
                )
                
                # Build prompt
                system_prompt = (
                    f"You are an intelligent assistant specialized in answering questions about the document '{document.filename}'. "
                    "Provide accurate, helpful, and contextual answers based on the document's content.\n\n"
                )
                
                if context:
                    system_prompt += f"Relevant excerpts from '{document.filename}':\n"
                    system_prompt += "=" * 50 + "\n"
                    for i, chunk_text in enumerate(context_texts, 1):
                        system_prompt += f"\n[Excerpt {i}]\n{chunk_text}\n"
                    system_prompt += "=" * 50 + "\n\n"
                
                # Create messages
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add history
                for msg in history[-10:]:  # Last 10 messages
                    if msg.id != UUID(message_id):  # Skip the current message we're processing
                        messages.append({
                            "role": msg.role,
                            "content": msg.content,
                        })
                
                # Add current message
                messages.append({
                    "role": "user",
                    "content": message_text,
                })
                
                # Generate response
                llm = factory.create_chat_model()
                response = await llm.ainvoke(messages)
                
                await reporter.report_progress(
                    ProgressStage.STORING,
                    0.80,
                    "Saving response"
                )
                
                # Save AI response
                ai_message = ChatMessage(
                    chat_id=UUID(chat_id),
                    role="assistant",
                    content=response.content,
                    context_metadata=json.dumps({
                        "chunks_used": chunk_metadata,
                        "model": factory.get_provider_info()["model"],
                    }),
                )
                db.add(ai_message)
                
                # Update chat timestamp
                from sqlalchemy import func
                chat.updated_at = func.now()
                
                await db.commit()
                await db.refresh(ai_message)
                
                await reporter.report_progress(
                    ProgressStage.COMPLETED,
                    1.0,
                    "Response generated"
                )
                
                return {
                    "message_id": str(ai_message.id),
                    "content": ai_message.content,
                    "role": ai_message.role,
                    "created_at": ai_message.created_at.isoformat(),
                    "metadata": {
                        "chunks_used": chunk_metadata,
                        "model": factory.get_provider_info()["model"],
                    },
                }
                
        except Exception as e:
            logger.error(f"Failed to process chat message: {str(e)}")
            await reporter.report_error(str(e))
            raise