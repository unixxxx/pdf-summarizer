"""Async summarization service that delegates to worker."""

import logging
from uuid import UUID

from arq import create_pool
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import BadRequestException
from ..config import get_settings
from .schemas import SummaryOptions

logger = logging.getLogger(__name__)


class AsyncSummarizationService:
    """Service for summarization operations - delegates to worker."""
    
    def __init__(self):
        """Initialize service."""
        self.settings = get_settings()
    
    async def enqueue_summarization(
        self,
        document_id: UUID,
        user_id: UUID,
        document_service,
        db: AsyncSession,
        options: SummaryOptions | None = None,
    ) -> dict:
        """
        Enqueue summarization job to worker.
        
        Returns:
            Dict with job_id and status
        """
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
            # Convert options to dict for serialization
            options_dict = None
            if options:
                options_dict = {
                    "style": options.style,
                    "max_length": options.max_length,
                    "focus_areas": options.focus_areas,
                    "custom_prompt": options.custom_prompt,
                }
            
            # Enqueue job
            job = await redis.enqueue_job(
                "generate_document_summary",  # Function name in worker
                str(document_id),
                str(user_id),
                options_dict,
                _job_id=f"summary:{document_id}:{user_id}",
                _queue_name="doculearn:queue",
            )
            
            return {
                "job_id": job.job_id,
                "status": "queued",
                "message": "Summarization has been queued",
                "document_id": str(document_id),
            }
            
        finally:
            await redis.close()
    
    async def enqueue_text_summarization(
        self,
        text: str,
        filename: str,
        user_id: UUID,
        options: SummaryOptions | None = None,
        db: AsyncSession | None = None,
    ) -> dict:
        """
        Enqueue text summarization job to worker.
        
        Returns:
            Dict with job_id and status
        """
        if not text:
            raise BadRequestException("Text is required for summarization")
        
        if not filename:
            raise BadRequestException("Filename is required when providing raw text")
        
        # Create Redis connection
        redis = await create_pool(self.settings.redis_url)
        
        try:
            # Convert options to dict for serialization
            options_dict = None
            if options:
                options_dict = {
                    "style": options.style,
                    "max_length": options.max_length,
                    "focus_areas": options.focus_areas,
                    "custom_prompt": options.custom_prompt,
                }
            
            # Enqueue job
            job = await redis.enqueue_job(
                "summarize_text",  # Function name in worker
                text,
                filename,
                str(user_id),
                options_dict,
                _job_id=f"text_summary:{user_id}:{filename}",
                _queue_name="doculearn:queue",
            )
            
            return {
                "job_id": job.job_id,
                "status": "queued",
                "message": "Text summarization has been queued",
            }
            
        finally:
            await redis.close()
    
    async def get_summarization_status(self, job_id: str) -> dict:
        """
        Get status of summarization job.
        
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
                    "message": "Summarization in progress",
                }
                
        finally:
            await redis.close()