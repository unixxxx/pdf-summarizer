"""Bulk database operations for performance optimization."""

import numpy as np
from shared.models import DocumentChunk
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.logger import logger


async def bulk_insert_chunks(
    db: AsyncSession,
    document_id: str,
    embeddings: list[dict],
    batch_size: int = 100
) -> int:
    """
    Bulk insert document chunks with embeddings.
    
    Args:
        db: Database session
        document_id: Document ID
        embeddings: List of embedding data dicts
        batch_size: Number of chunks to insert at once
        
    Returns:
        Number of chunks inserted
    """
    # Delete existing chunks
    await db.execute(
        delete(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        )
    )
    
    total_inserted = 0
    
    # Process in batches for optimal performance
    for i in range(0, len(embeddings), batch_size):
        batch = embeddings[i:i + batch_size]
        
        # Prepare bulk insert data
        chunk_data = []
        for emb_data in batch:
            chunk_info = emb_data["chunk"]
            embedding = emb_data["embedding"]
            
            chunk_data.append({
                "document_id": document_id,
                "chunk_text": chunk_info["text"],
                "chunk_index": chunk_info["chunk_index"],
                "embedding": np.array(embedding),  # pgvector expects numpy array
            })
        
        # Bulk insert using PostgreSQL's INSERT
        stmt = insert(DocumentChunk).values(chunk_data)
        await db.execute(stmt)
        
        total_inserted += len(batch)
        
        logger.info(
            f"Bulk inserted batch {i//batch_size + 1}, "
            f"size: {len(batch)}, total: {total_inserted}"
        )
    
    await db.commit()
    
    return total_inserted


async def bulk_upsert_chunks(
    db: AsyncSession,
    document_id: str,
    embeddings: list[dict],
    batch_size: int = 100
) -> int:
    """
    Bulk upsert document chunks with embeddings using ON CONFLICT.
    
    This is useful when you want to update existing chunks without
    deleting and recreating them.
    
    Args:
        db: Database session
        document_id: Document ID
        embeddings: List of embedding data dicts
        batch_size: Number of chunks to upsert at once
        
    Returns:
        Number of chunks upserted
    """
    total_upserted = 0
    
    for i in range(0, len(embeddings), batch_size):
        batch = embeddings[i:i + batch_size]
        
        # Prepare bulk upsert data
        chunk_data = []
        for emb_data in batch:
            chunk_info = emb_data["chunk"]
            embedding = emb_data["embedding"]
            
            chunk_data.append({
                "document_id": document_id,
                "chunk_text": chunk_info["text"],
                "chunk_index": chunk_info["chunk_index"],
                "embedding": np.array(embedding),
            })
        
        # Bulk upsert with ON CONFLICT
        stmt = insert(DocumentChunk).values(chunk_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['document_id', 'chunk_index'],
            set_={
                'chunk_text': stmt.excluded.chunk_text,
                'embedding': stmt.excluded.embedding,
            }
        )
        
        await db.execute(stmt)
        total_upserted += len(batch)
    
    await db.commit()
    
    return total_upserted