"""Embedding generation tasks for documents and tags."""

from typing import List, Dict, Any
import numpy as np
import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import select, update, delete, func

from ..common.database import get_db_session
from shared.models import Document, DocumentChunk, Tag, DocumentStatus
from ..common.logger import logger
from ..common.redis_progress_reporter import (
    RedisProgressReporter as ProgressReporter,
    ProgressStage,
)
from ..common.config import get_settings
from ..common.llm_factory import UnifiedLLMFactory
from ..common.retry import retry_on_llm_error
from ..common.cpu_monitor import cpu_monitor

settings = get_settings()


class ChunkingStrategy:
    """Document chunking configuration."""

    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_document(text: str) -> List[Dict[str, Any]]:
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
async def generate_embedding(text: str, embeddings_model) -> List[float]:
    """Generate embedding for a text chunk with retry logic."""
    embedding = await embeddings_model.aembed_query(text)
    return embedding


@retry_on_llm_error(max_attempts=3)
async def generate_batch_embeddings(
    texts: List[str], embeddings_model
) -> List[List[float]]:
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
) -> Dict[str, Any]:
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
        redis=redis, job_id=job_id, document_id=document_id, user_id=user_id
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

                # Update document status to completed
                await db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(status=DocumentStatus.COMPLETED, processed_at=func.now())
                )

                await db.commit()

            # 5. Complete
            await reporter.report_progress(
                ProgressStage.COMPLETED,
                1.0,
                "Embedding generation completed successfully",
            )

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


async def generate_tag_embeddings(ctx: dict, tag_names: List[str]) -> Dict[str, Any]:
    """
    Generate embeddings for tags.

    Args:
        ctx: arq context
        tag_names: List of tag names to generate embeddings for

    Returns:
        Processing results
    """
    try:
        # Initialize LLM factory
        llm_factory = UnifiedLLMFactory(settings)
        embeddings_model, embedding_dimension = llm_factory.create_embeddings_model()

        results = []

        async with get_db_session() as db:
            for tag_name in tag_names:
                # Check if tag exists
                result = await db.execute(select(Tag).where(Tag.name == tag_name))
                tag = result.scalar_one_or_none()

                if not tag:
                    # Create new tag
                    tag = Tag(name=tag_name)
                    db.add(tag)

                # Generate embedding
                embedding = await generate_embedding(tag_name, embeddings_model)
                tag.embedding = np.array(embedding)

                results.append({"tag": tag_name, "embedding_generated": True})

            await db.commit()

        logger.info("Tag embeddings generated", tags=tag_names, count=len(tag_names))

        return {"success": True, "tags_processed": len(tag_names), "results": results}

    except Exception as e:
        logger.error(
            "Tag embedding generation failed",
            tags=tag_names,
            error=str(e),
            exc_info=True,
        )
        raise


async def update_all_tag_embeddings(ctx: dict) -> Dict[str, Any]:
    """
    Update embeddings for all tags in the system.

    Returns:
        Processing results
    """
    try:
        async with get_db_session() as db:
            # Get all tag names
            result = await db.execute(select(Tag.name))
            tag_names = [row[0] for row in result]

        if not tag_names:
            return {"success": True, "message": "No tags to update"}

        # Process tags
        result = await generate_tag_embeddings(ctx, tag_names)

        return {"success": True, "total_tags": len(tag_names), **result}

    except Exception as e:
        logger.error("Update all tag embeddings failed", error=str(e), exc_info=True)
        raise
