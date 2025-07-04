"""Redis-based progress reporting for worker tasks."""

import json
from enum import Enum
from typing import Any

from redis.asyncio import Redis

from .logger import logger


class ProgressStage(str, Enum):
    """Progress stages for document processing."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class RedisProgressReporter:
    """Report task progress via Redis pub/sub."""
    
    def __init__(
        self, 
        redis: Redis,
        job_id: str, 
        document_id: str | None, 
        user_id: str
    ):
        """
        Initialize Redis progress reporter.
        
        Args:
            redis: Redis connection
            job_id: Unique job identifier
            document_id: Document being processed (optional for batch jobs)
            user_id: User who initiated the job
        """
        self.redis = redis
        self.job_id = job_id
        self.document_id = document_id
        self.user_id = user_id
        self.channel = "document_progress"  # Same channel as backend uses
    
    async def report_progress(
        self, 
        stage: str | ProgressStage, 
        progress: float, 
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        """
        Report progress via Redis pub/sub.
        
        Args:
            stage: Current processing stage
            progress: Progress percentage (0.0 to 1.0)
            message: Human-readable status message
            details: Additional details about the progress
        """
        try:
            # Format message to match backend's WebSocket format
            ws_message = {
                "user_id": self.user_id,
                "data": {
                    "type": "document_processing",
                    "document_id": self.document_id,
                    "job_id": self.job_id,
                    "stage": stage if isinstance(stage, str) else stage.value,
                    "progress": progress,
                    "message": message,
                    "details": details or {}
                }
            }
            
            # Publish to Redis channel
            await self.redis.publish(self.channel, json.dumps(ws_message))
            
            logger.info(
                "Progress reported via Redis",
                job_id=self.job_id,
                stage=stage if isinstance(stage, str) else stage.value,
                progress=progress,
                message=message,
                channel=self.channel,
                has_details="document" in (details or {})
            )
        except Exception as e:
            logger.error(
                "Failed to report progress via Redis",
                job_id=self.job_id,
                error=str(e),
                stage=stage,
                progress=progress
            )
    
    async def report_error(self, error: str, details: dict[str, Any] | None = None) -> None:
        """Report an error via Redis."""
        await self.report_progress(
            ProgressStage.FAILED,
            0.0,
            f"Processing failed: {error}",
            {"error": error, **(details or {})}
        )
    
    async def report_completion(self, message: str = "Processing completed successfully", document_data: dict[str, Any] | None = None) -> None:
        """Report successful completion with optional document data."""
        details = document_data or {}
        await self.report_progress(
            ProgressStage.COMPLETED,
            1.0,
            message,
            details
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is not None:
            # Report error if exception occurred
            await self.report_error(str(exc_val))