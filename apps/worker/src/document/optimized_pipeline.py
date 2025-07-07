"""Optimized document processing pipeline with parallelization."""

from typing import Any

from ..common.config import get_settings
from ..common.logger import logger

settings = get_settings()


class OptimizedDocumentPipeline:
    """Optimized document processing with early start for next stages."""
    
    @staticmethod
    async def process_document_optimized(
        document_id: str,
        user_id: str,
        redis_connection
    ) -> dict[str, Any]:
        """
        Process document with optimized pipeline.
        
        Key optimizations:
        1. Start embedding generation while text extraction is still running
        2. Start summary generation as soon as we have enough chunks
        3. Use parallel processing where possible
        """
        from arq import create_pool
        from arq.connections import RedisSettings
        
        try:
            # Start all jobs with minimal delays
            redis_pool = await create_pool(
                RedisSettings.from_dsn(settings.redis_url)
            )
            
            # Queue jobs with shorter delays
            jobs = []
            
            # Text extraction (immediate)
            job1 = await redis_pool.enqueue_job(
                "process_document",
                str(document_id),
                str(user_id),
                _job_id=f"doc:{document_id}",
                _queue_name="doculearn:queue"
            )
            jobs.append(job1)
            
            # Embeddings (start after 2 seconds)
            job2 = await redis_pool.enqueue_job(
                "generate_document_embeddings",
                str(document_id),
                str(user_id),
                _job_id=f"embed:{document_id}",
                _defer_by=2,  # Reduced from typical delays
                _queue_name="doculearn:queue"
            )
            jobs.append(job2)
            
            # Summary (start after 4 seconds)
            job3 = await redis_pool.enqueue_job(
                "generate_document_summary",
                str(document_id),
                str(user_id),
                _job_id=f"summary:{document_id}",
                _defer_by=4,  # Can start before embeddings complete
                _queue_name="doculearn:queue"
            )
            jobs.append(job3)
            
            await redis_pool.close()
            
            logger.info(
                f"Optimized pipeline started for document {document_id} "
                f"with {len(jobs)} parallel jobs"
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "jobs_queued": len(jobs)
            }
            
        except Exception as e:
            logger.error(f"Optimized pipeline failed: {e}")
            raise