"""Document summarization tasks for the worker."""

import time
from typing import Any
from uuid import UUID

from shared.models import Document, DocumentStatus, Summary, Tag, document_tags
from sqlalchemy import select, update

from ..common.config import get_settings
from ..common.database import get_db_session
from ..common.llm_factory import UnifiedLLMFactory
from ..common.logger import logger
from ..common.progress_calculator import ProcessingStages
from ..common.redis_progress_reporter import ProgressStage
from ..common.retry import retry_on_llm_error
from ..common.staged_progress_reporter import (
    StagedProgressReporter as RedisProgressReporter,
)
from .llm_schemas import ComprehensiveDocumentAnalysis

settings = get_settings()


async def summarize_text(ctx: dict, text: str, options: dict = None) -> dict[str, Any]:
    """
    Summarize arbitrary text.
    
    Args:
        ctx: arq context
        text: Text to summarize
        options: Optional summarization options
        
    Returns:
        Summary text
    """
    try:
        # Initialize LLM factory
        llm_factory = UnifiedLLMFactory(settings)
        llm = llm_factory.create_chat_model(temperature=0.3)
        
        # Create prompt
        style = options.get("style", "balanced") if options else "balanced"
        prompt = f"""Summarize the following text in a {style} style:

{text[:8000]}  # Limit to avoid token limits

Provide a clear, well-structured summary."""
        
        # Generate summary
        @retry_on_llm_error(max_attempts=3)
        async def generate_summary() -> str:
            response = await llm.ainvoke(prompt)
            return response.content
        
        summary = await generate_summary()
        
        logger.info(
            "Text summarized", 
            text_length=len(text), 
            summary_length=len(summary)
        )
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary)
        }
        
    except Exception as e:
        logger.error("Text summarization failed", error=str(e), exc_info=True)
        raise


async def generate_document_summary(
    ctx: dict, document_id: str, user_id: str
) -> dict[str, Any]:
    """
    Generate summary for a document as part of the processing pipeline.
    
    Args:
        ctx: arq context
        document_id: Document to summarize
        user_id: User who owns the document
        
    Returns:
        Processing results
    """
    job_id = ctx.get("job_id", f"summary:{document_id}")
    
    logger.info(
        "Starting document summary generation",
        document_id=document_id,
        user_id=user_id,
        job_id=job_id
    )
    
    # Get Redis connection from context
    redis = ctx.get("redis")
    
    async with RedisProgressReporter(
        redis=redis, 
        job_id=job_id, 
        document_id=document_id, 
        user_id=user_id,
        current_stage=ProcessingStages.SUMMARY_GENERATION
    ) as reporter:
        
        try:
            start_time = time.time()
            
            # 1. Fetch document from database
            await reporter.report_progress(
                ProgressStage.DOWNLOADING,
                0.05,
                "Loading document for summary generation",
            )
            
            async with get_db_session() as db:
                result = await db.execute(
                    select(Document).where(Document.id == UUID(document_id))
                )
                document = result.scalar_one_or_none()
                
                if not document:
                    raise ValueError(
                        f"Document {document_id} not found"
                    )
                
                if str(document.user_id) != str(user_id):
                    raise ValueError(
                        f"Document {document_id} does not belong to user {user_id}"
                    )
                
                if not document.extracted_text:
                    raise ValueError(f"Document {document_id} has no extracted text")
                    
                text = document.extracted_text
                original_word_count = document.word_count or len(text.split())
            
            # 2. Initialize LLM
            await reporter.report_progress(
                ProgressStage.EXTRACTING,
                0.20,
                "Initializing language model",
            )
            
            llm_factory = UnifiedLLMFactory(settings)
            llm = llm_factory.create_chat_model(temperature=0.3)
            
            # 3. Generate summary
            await reporter.report_progress(
                ProgressStage.EXTRACTING,
                0.30,
                "Generating document summary",
            )
            
            # Create a more sophisticated prompt for structured output
            prompt = (
                f"""Analyze the following document and provide a comprehensive analysis.

Document content:
{text[:10000]}  # Limit to avoid token limits

Provide a JSON response with:
1. A comprehensive summary (50-2000 characters) capturing main topics and key points
2. A meaningful title (3-50 characters) based on the content
3. 3-8 relevant tags for categorization

Tag requirements:
- Each tag must be at least 2 characters long
- Use lowercase letters only
- Use spaces for multi-word tags (e.g., "machine learning")
- Be specific and descriptive (avoid single letters or numbers)
- Focus on the document's main topics, technologies, or concepts

Focus on:
- Main topics and key points
- Important findings or conclusions
- The document's primary subject matter
- Technical concepts or methodologies mentioned

Example format:
{{
    "summary": "A comprehensive summary of the document...",
    "title": "Document Title",
    "tags": ["machine learning", "python", "neural networks", "tutorial", "deep learning"]
}}"""
            )
            
            @retry_on_llm_error(max_attempts=3)
            async def generate_analysis() -> ComprehensiveDocumentAnalysis:
                await reporter.report_progress(
                    ProgressStage.EXTRACTING,
                    0.50,
                    "Processing with language model",
                )
                
                # Use structured output if available
                try:
                    # Try to use structured output
                    response = await llm.with_structured_output(
                        ComprehensiveDocumentAnalysis
                    ).ainvoke(prompt)
                    return response
                except Exception as e:
                    logger.warning(
                        f"Structured output failed, parsing JSON manually: {e}"
                    )
                    # Fallback to manual parsing
                    response = await llm.ainvoke(prompt)
                    import json
                    data = json.loads(response.content)
                    return ComprehensiveDocumentAnalysis.model_validate(data)
            
            analysis = await generate_analysis()
            summary_text = analysis.summary
            summary_word_count = len(summary_text.split())
            compression_ratio = (
                summary_word_count / original_word_count 
                if original_word_count > 0 
                else 0
            )
            
            # 4. Create or find tags based on LLM suggestions
            await reporter.report_progress(
                ProgressStage.STORING,
                0.70,
                "Processing tags",
            )
            
            # Helper function to create slug
            def create_slug(name: str) -> str:
                import re
                slug = name.lower()
                slug = re.sub(r'[^\w\s-]', '', slug)
                slug = re.sub(r'[-\s]+', '-', slug)
                return slug.strip('-')
            
            # Tag colors (cycling through them)
            TAG_COLORS = [
                "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
                "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
            ]
            
            # 5. Store summary and tags in database
            await reporter.report_progress(
                ProgressStage.STORING,
                0.80,
                "Storing summary and tags in database",
            )
            
            async with get_db_session() as db:
                # Check if summary already exists
                result = await db.execute(
                    select(Summary).where(Summary.document_id == UUID(document_id))
                )
                existing_summary = result.scalar_one_or_none()
                
                if existing_summary:
                    # Update existing summary
                    existing_summary.summary_text = summary_text
                    existing_summary.original_word_count = original_word_count
                    existing_summary.summary_word_count = summary_word_count
                    existing_summary.compression_ratio = compression_ratio
                    existing_summary.processing_time = time.time() - start_time
                    existing_summary.llm_provider = settings.llm_provider
                    existing_summary.llm_model = (
                        settings.openai_model if settings.llm_provider == "openai" 
                        else settings.ollama_model
                    )
                else:
                    # Create new summary
                    summary = Summary(
                        user_id=UUID(user_id),
                        document_id=UUID(document_id),
                        summary_text=summary_text,
                        original_word_count=original_word_count,
                        summary_word_count=summary_word_count,
                        compression_ratio=compression_ratio,
                        processing_time=time.time() - start_time,
                        llm_provider=settings.llm_provider,
                        llm_model=(
                            settings.openai_model if settings.llm_provider == "openai" 
                            else settings.ollama_model
                        ),
                    )
                    db.add(summary)
                
                # Update document status to completed
                await db.execute(
                    update(Document)
                    .where(Document.id == UUID(document_id))
                    .values(status=DocumentStatus.COMPLETED)
                )
                
                # Create or find tags
                tag_ids = []
                new_tag_ids = []
                new_tag_names = []
                
                for idx, tag_name in enumerate(analysis.tags):
                    # Skip invalid tags
                    if not tag_name or len(tag_name) < 2:
                        logger.warning(
                            f"Skipping invalid tag: '{tag_name}'"
                        )
                        continue
                        
                    slug = create_slug(tag_name)
                    
                    # Validate slug
                    if not slug or len(slug) < 2:
                        logger.warning(
                            f"Skipping tag with invalid slug: '{tag_name}' -> '{slug}'"
                        )
                        continue
                    
                    # Check if tag exists
                    result = await db.execute(
                        select(Tag).where(Tag.slug == slug)
                    )
                    existing_tag = result.scalar_one_or_none()
                    
                    if existing_tag:
                        tag_ids.append(existing_tag.id)
                    else:
                        # Create new tag without embedding (will be generated by separate job)
                        new_tag = Tag(
                            name=tag_name,
                            slug=slug,
                            color=TAG_COLORS[idx % len(TAG_COLORS)],
                        )
                        
                        db.add(new_tag)
                        await db.flush()
                        tag_ids.append(new_tag.id)
                        
                        # Collect new tag info for batch embedding generation
                        new_tag_ids.append(str(new_tag.id))
                        new_tag_names.append(new_tag.name)
                
                # Enqueue job to generate embeddings for all new tags at once
                if new_tag_ids:
                    try:
                        from arq import create_pool
                        from arq.connections import RedisSettings
                        
                        redis_pool = await create_pool(
                            RedisSettings.from_dsn(settings.redis_url)
                        )
                        
                        await redis_pool.enqueue_job(
                            "generate_tag_embeddings",
                            new_tag_ids,  # Pass all new tag IDs at once
                            _queue_name="doculearn:queue"
                        )
                        await redis_pool.close()
                        
                        logger.info(
                            f"Enqueued embedding generation for {len(new_tag_ids)} tags: "
                            f"{', '.join(new_tag_names)}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to enqueue embedding generation for tags: {e}"
                        )
                
                # Associate tags with document
                if tag_ids:
                    # Remove existing associations
                    await db.execute(
                        document_tags.delete().where(
                            document_tags.c.document_id == UUID(document_id)
                        )
                    )
                    
                    # Create new associations
                    await db.execute(
                        document_tags.insert(),
                        [{"document_id": UUID(document_id), "tag_id": tag_id} 
                         for tag_id in tag_ids]
                    )
                
                await db.commit()
            
            # 6. Report completion
            await reporter.report_completion(
                "Document summary and tags generated successfully"
            )
            
            logger.info(
                "Document summary and tags generated",
                document_id=document_id,
                original_words=original_word_count,
                summary_words=summary_word_count,
                compression_ratio=f"{compression_ratio:.2%}",
                tags=analysis.tags,
                tag_count=len(analysis.tags),
                processing_time=f"{time.time() - start_time:.2f}s",
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "summary_length": summary_word_count,
                "compression_ratio": compression_ratio,
                "tags": analysis.tags,
                "processing_time": time.time() - start_time,
            }
            
        except Exception as e:
            logger.error(
                "Document summarization failed",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )
            
            # Update document status to failed
            try:
                async with get_db_session() as db:
                    await db.execute(
                        update(Document)
                        .where(Document.id == UUID(document_id))
                        .values(
                            status=DocumentStatus.FAILED,
                            error_message=f"Summary and tag generation failed: {str(e)}",
                        )
                    )
                    await db.commit()
            except Exception as db_error:
                logger.error(
                    "Failed to update document status",
                    document_id=document_id,
                    error=str(db_error),
                )
            
            await reporter.report_error(str(e))
            raise