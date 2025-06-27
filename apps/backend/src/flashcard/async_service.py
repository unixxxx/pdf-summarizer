"""Asynchronous flashcard service that uses arq worker."""

from uuid import UUID
from arq import create_pool
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from .schemas import FlashcardOptions


class AsyncFlashcardService:
    """Service for enqueuing flashcard generation jobs."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def enqueue_flashcard_generation(
        self,
        document_id: UUID,
        user_id: UUID,
        options: FlashcardOptions,
        document_service,
        db: AsyncSession,
    ) -> dict:
        """
        Enqueue flashcard generation job to worker.
        
        Returns:
            Dict with job_id and status
        """
        from ..common.exceptions import BadRequestException
        
        # Get document and validate access
        document = await document_service.get_document(
            document_id=document_id,
            user_id=user_id,
            db=db,
        )
        
        # Validate document has been processed
        if not document.extracted_text:
            raise BadRequestException(
                "Document has not been processed yet. Please wait for processing to complete."
            )
        
        # Create Redis connection
        redis = await create_pool(self.settings.redis_url)
        
        try:
            # Enqueue job
            job = await redis.enqueue_job(
                "generate_flashcards",  # Function name in worker
                str(document_id),
                str(user_id),
                options.num_cards,
                [ct.value for ct in options.card_types],
                options.difficulty.value,
                _job_id=f"flashcards:{document_id}:{user_id}",
                _queue_name="doculearn:queue",
            )
            
            return {
                "job_id": job.job_id,
                "status": "queued",
                "message": "Flashcard generation has been queued",
                "document_id": str(document_id),
            }
            
        finally:
            await redis.close()
    
    async def get_flashcard_status(self, job_id: str) -> dict:
        """
        Get status of flashcard generation job.
        
        Returns:
            Dict with job status and result if completed
        """
        redis = await create_pool(self.settings.redis_url)
        
        try:
            job = await redis._get_job_by_id(job_id)
            
            if not job:
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "message": "Job not found",
                }
            
            if job.status == "complete":
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "result": job.result,
                }
            elif job.status == "failed":
                return {
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(job.error) if job.error else "Unknown error",
                }
            else:
                return {
                    "job_id": job_id,
                    "status": job.status,
                    "message": "Flashcard generation in progress",
                }
                
        finally:
            await redis.close()