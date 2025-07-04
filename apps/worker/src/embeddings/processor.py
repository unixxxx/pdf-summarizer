"""Embedding generation tasks for documents and tags."""

import asyncio
from typing import Any
from uuid import UUID

import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from shared.models import Document, DocumentChunk, DocumentStatus, Tag
from sqlalchemy import delete, select, update

from ..common.config import get_settings
from ..common.cpu_monitor import cpu_monitor
from ..common.database import get_db_session
from ..common.llm_factory import UnifiedLLMFactory
from ..common.logger import logger
from ..common.progress_calculator import ProcessingStages
from ..common.redis_progress_reporter import ProgressStage
from ..common.retry import retry_on_llm_error
from ..common.staged_progress_reporter import StagedProgressReporter as ProgressReporter

settings = get_settings()


class ChunkingStrategy:
    """Document chunking configuration."""

    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_document(text: str) -> list[dict[str, Any]]:
    """
    Split document text into chunks for embedding.

    Returns:
        List of chunk dictionaries with text and metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=ChunkingStrategy.CHUNK_SIZE,
        chunk_overlap=ChunkingStrategy.CHUNK_OVERLAP,
        separators=ChunkingStrategy.SEPARATORS,
        length_function=len,
    )

    chunks = text_splitter.split_text(text)

    return [
        {
            "text": chunk,
            "chunk_index": i,
            "start_char": sum(len(c) + 1 for c in chunks[:i]),  # Approximate
        }
        for i, chunk in enumerate(chunks)
    ]


@retry_on_llm_error(max_attempts=3)
async def generate_embedding(text: str, embeddings_model) -> list[float]:
    """Generate embedding for a text chunk with retry logic."""
    embedding = await embeddings_model.aembed_query(text)
    return embedding


@retry_on_llm_error(max_attempts=3)
async def generate_batch_embeddings(
    texts: list[str], embeddings_model
) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call."""
    # Most embedding models support batch operations via aembed_documents
    try:
        embeddings = await embeddings_model.aembed_documents(texts)
        return embeddings
    except AttributeError:
        # Fallback to individual calls if batch not supported
        logger.warning(
            "Batch embedding not supported, falling back to individual calls"
        )
        embeddings = []
        for text in texts:
            embedding = await embeddings_model.aembed_query(text)
            embeddings.append(embedding)
        return embeddings


async def generate_document_embeddings(
    ctx: dict, document_id: str, user_id: str
) -> dict[str, Any]:
    """
    Generate embeddings for all document chunks.

    Args:
        ctx: arq context
        document_id: Document to process
        user_id: User who owns the document

    Returns:
        Processing results
    """
    job_id = ctx.get("job_id", f"embed:{document_id}")

    # Get Redis connection from context
    redis = ctx.get("redis")

    async with ProgressReporter(
        redis=redis, 
        job_id=job_id, 
        document_id=document_id, 
        user_id=user_id,
        current_stage=ProcessingStages.EMBEDDING_GENERATION
    ) as reporter:

        try:
            # Initialize LLM factory
            llm_factory = UnifiedLLMFactory(settings)
            embeddings_model, embedding_dimension = (
                llm_factory.create_embeddings_model()
            )

            # 1. Fetch document
            await reporter.report_progress(
                ProgressStage.DOWNLOADING,
                0.05,
                "Loading document for embedding generation",
            )

            async with get_db_session() as db:
                result = await db.execute(
                    select(Document).where(Document.id == document_id)
                )
                document = result.scalar_one_or_none()

                if not document:
                    raise ValueError(f"Document {document_id} not found")

                if not document.extracted_text:
                    raise ValueError(f"Document {document_id} has no extracted text")

            # 2. Chunk document
            await reporter.report_progress(
                ProgressStage.CHUNKING, 0.15, "Splitting document into chunks"
            )

            chunks = chunk_document(document.extracted_text)
            total_chunks = len(chunks)

            await reporter.report_progress(
                ProgressStage.CHUNKING,
                0.20,
                f"Created {total_chunks} chunks",
                {"chunk_count": total_chunks},
            )

            # 3. Generate embeddings for each chunk
            await reporter.report_progress(
                ProgressStage.EMBEDDING, 0.20, "Starting embedding generation"
            )

            embeddings = []
            batch_size = settings.batch_size
            base_delay = settings.cpu_throttle_delay

            # Process chunks in batches to reduce CPU load
            for batch_start in range(0, total_chunks, batch_size):
                batch_end = min(batch_start + batch_size, total_chunks)
                batch_chunks = chunks[batch_start:batch_end]

                # Check if we should pause for high CPU
                if cpu_monitor.should_pause():
                    await reporter.report_progress(
                        ProgressStage.EMBEDDING,
                        0.20 + (0.65 * (batch_start / total_chunks)),
                        "Pausing for CPU cooldown",
                    )
                    await cpu_monitor.wait_for_cpu()

                # Calculate progress (20% to 85%)
                batch_progress = 0.20 + (0.65 * (batch_start / total_chunks))

                await reporter.report_progress(
                    ProgressStage.EMBEDDING,
                    batch_progress,
                    f"Processing batch {batch_start//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size}",
                )

                # Extract texts from chunks for batch processing
                batch_texts = [chunk["text"] for chunk in batch_chunks]

                # Generate embeddings for the entire batch in one API call
                logger.info(
                    "Generating batch embeddings",
                    batch_size=len(batch_texts),
                    batch_num=batch_start // batch_size + 1,
                )

                # Use batch embedding to reduce API calls
                batch_embeddings = await generate_batch_embeddings(
                    batch_texts, embeddings_model
                )

                # Add adaptive CPU throttle delay after batch processing
                throttle_delay = cpu_monitor.get_throttle_delay(base_delay)
                await asyncio.sleep(throttle_delay)

                # Combine results
                for i, embedding in enumerate(batch_embeddings):
                    embeddings.append(
                        {"chunk": batch_chunks[i], "embedding": embedding}
                    )

                # Add adaptive delay between batches to cool down CPU
                if batch_end < total_chunks:
                    throttle_delay = cpu_monitor.get_throttle_delay(base_delay * 2)
                    await asyncio.sleep(throttle_delay)

            # 4. Store embeddings in database
            await reporter.report_progress(
                ProgressStage.STORING, 0.85, "Storing embeddings in database"
            )
            
            logger.info("Starting to store embeddings in database", document_id=document_id)

            async with get_db_session() as db:
                # Delete existing chunks
                await db.execute(
                    delete(DocumentChunk).where(
                        DocumentChunk.document_id == document_id
                    )
                )

                # Create new chunks
                for emb_data in embeddings:
                    chunk_data = emb_data["chunk"]
                    embedding = emb_data["embedding"]

                    chunk = DocumentChunk(
                        document_id=document_id,
                        chunk_text=chunk_data["text"],
                        chunk_index=chunk_data["chunk_index"],
                        embedding=np.array(embedding),  # pgvector expects numpy array
                    )
                    db.add(chunk)

                # Keep document status as PROCESSING (summary generation is next)
                await db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(status=DocumentStatus.PROCESSING)
                )

                await db.commit()
                logger.info("Embeddings stored successfully", document_id=document_id)

            # 5. Enqueue summary generation task
            logger.info("Enqueuing summary generation", document_id=document_id)
            
            from arq import create_pool
            from arq.connections import RedisSettings
            redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            
            try:
                job = await redis_pool.enqueue_job(
                    "generate_document_summary",
                    str(document_id),
                    str(user_id),
                    _job_id=f"summary:{document_id}",
                    _defer_by=1,  # Start after 1 second
                    _queue_name="doculearn:queue"
                )
                
                logger.info(
                    "Summary generation job enqueued",
                    document_id=document_id,
                    job_id=f"summary:{document_id}",
                    job_result=job is not None
                )
            finally:
                await redis_pool.close()
            
            # Report progress (not completion yet)
            await reporter.report_progress(
                ProgressStage.STORING,
                0.70,
                "Embeddings stored, summary generation queued"
            )
            logger.info("Summary generation queued", document_id=document_id)
            
            # Small delay to ensure message is sent before function returns
            await asyncio.sleep(0.1)

            logger.info(
                "Document embeddings generated",
                document_id=document_id,
                chunks=total_chunks,
                embedding_dimension=embedding_dimension,
            )

            return {
                "success": True,
                "document_id": document_id,
                "chunks_created": total_chunks,
                "embedding_dimension": embedding_dimension,
            }

        except Exception as e:
            logger.error(
                "Embedding generation failed",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )

            # Update document status
            try:
                async with get_db_session() as db:
                    await db.execute(
                        update(Document)
                        .where(Document.id == document_id)
                        .values(
                            status=DocumentStatus.FAILED,
                            error_message=f"Embedding generation failed: {str(e)}",
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


async def generate_tag_embeddings(ctx: dict, tag_ids: list[str]) -> dict[str, Any]:
    """
    Generate embeddings for tags by their IDs.

    Args:
        ctx: arq context
        tag_ids: List of tag IDs to generate embeddings for

    Returns:
        Processing results
    """
    try:
        # Initialize LLM factory
        llm_factory = UnifiedLLMFactory(settings)
        embeddings_model, embedding_dimension = llm_factory.create_embeddings_model()

        results = []

        async with get_db_session() as db:
            # Fetch all tags in a single query
            tag_uuids = [UUID(tag_id) for tag_id in tag_ids]
            result = await db.execute(
                select(Tag).where(Tag.id.in_(tag_uuids))
            )
            tags = result.scalars().all()
            
            # Create a mapping for quick lookup
            tag_map = {str(tag.id): tag for tag in tags}
            
            # Process each tag
            for tag_id in tag_ids:
                try:
                    tag = tag_map.get(tag_id)
                    
                    if not tag:
                        logger.warning(f"Tag not found with ID: {tag_id}")
                        results.append({
                            "tag_id": tag_id,
                            "error": "Tag not found"
                        })
                        continue
                    
                    # Skip if tag already has embedding
                    if tag.embedding is not None:
                        logger.info(f"Tag '{tag.name}' already has an embedding")
                        results.append({
                            "tag_id": tag_id,
                            "tag_name": tag.name,
                            "embedding_existed": True
                        })
                        continue

                    # Generate embedding using tag name
                    embedding = await generate_embedding(tag.name, embeddings_model)
                    tag.embedding = np.array(embedding)
                    
                    logger.info(f"Generated embedding for tag '{tag.name}' (ID: {tag_id})")
                    results.append({
                        "tag_id": tag_id,
                        "tag_name": tag.name,
                        "embedding_generated": True
                    })
                    
                except Exception as e:
                    logger.error(
                        f"Failed to generate embedding for tag ID {tag_id}: {e}"
                    )
                    results.append({
                        "tag_id": tag_id,
                        "error": str(e)
                    })

            await db.commit()

        logger.info(
            "Tag embeddings generation completed",
            total_tags=len(tag_ids),
            successful=len([r for r in results if r.get("embedding_generated")])
        )

        return {
            "success": True,
            "tags_processed": len(tag_ids),
            "results": results
        }

    except Exception as e:
        logger.error(
            "Tag embedding generation failed",
            tag_ids=tag_ids,
            error=str(e),
            exc_info=True,
        )
        raise


async def update_all_tag_embeddings(ctx: dict) -> dict[str, Any]:
    """
    Update embeddings for all tags in the system.

    Returns:
        Processing results
    """
    try:
        async with get_db_session() as db:
            # Get all tag IDs that don't have embeddings
            result = await db.execute(
                select(Tag.id).where(Tag.embedding.is_(None))
            )
            tag_ids = [str(row[0]) for row in result]

        if not tag_ids:
            return {"success": True, "message": "All tags already have embeddings"}

        # Process tags
        result = await generate_tag_embeddings(ctx, tag_ids)

        return {"success": True, "total_tags": len(tag_ids), **result}

    except Exception as e:
        logger.error("Update all tag embeddings failed", error=str(e), exc_info=True)
        raise
