"""Optimized embedding processor with parallel processing."""

import asyncio
from typing import Any

from ..common.config import get_settings
from ..common.logger import logger
from ..common.parallel_processor import process_in_parallel
from ..common.retry import retry_on_llm_error

settings = get_settings()


class OptimizedEmbeddingProcessor:
    """Optimized embedding processor with batching and parallelization."""
    
    def __init__(self, embeddings_model):
        self.embeddings_model = embeddings_model
        self.batch_size = settings.batch_size * 2  # Double the batch size
        self.max_concurrent = settings.embedding_concurrency
    
    @retry_on_llm_error(max_attempts=3)
    async def generate_batch_embeddings(
        self, texts: list[str]
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            # Try batch processing first
            embeddings = await self.embeddings_model.aembed_documents(texts)
            return embeddings
        except AttributeError:
            # Fallback to parallel individual processing
            return await process_in_parallel(
                texts,
                self.embeddings_model.aembed_query,
                self.max_concurrent,
                "Generating embeddings"
            )
    
    async def process_all_chunks(
        self, chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process all chunks with optimized batching."""
        results = []
        
        # Process in larger batches
        for i in range(0, len(chunks), self.batch_size):
            batch_chunks = chunks[i:i + self.batch_size]
            batch_texts = [chunk["text"] for chunk in batch_chunks]
            
            logger.info(
                f"Processing batch {i//self.batch_size + 1}, "
                f"size: {len(batch_texts)}"
            )
            
            # Generate embeddings for the batch
            embeddings = await self.generate_batch_embeddings(batch_texts)
            
            # Combine results
            for j, embedding in enumerate(embeddings):
                results.append({
                    "chunk": batch_chunks[j],
                    "embedding": embedding
                })
            
            # Minimal delay between batches
            if i + self.batch_size < len(chunks):
                await asyncio.sleep(0.01)  # 10ms delay
        
        return results