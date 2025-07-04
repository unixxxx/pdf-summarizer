"""Staged progress reporter for multi-stage document processing."""

from typing import Any

from .progress_calculator import ProcessingStages, calculate_global_progress
from .redis_progress_reporter import ProgressStage, RedisProgressReporter


class StagedProgressReporter(RedisProgressReporter):
    """Progress reporter that handles multi-stage processing with cumulative progress."""
    
    def __init__(
        self,
        redis,
        job_id: str,
        document_id: str | None,
        user_id: str,
        current_stage: ProcessingStages
    ):
        """
        Initialize staged progress reporter.
        
        Args:
            redis: Redis connection
            job_id: Unique job identifier
            document_id: Document being processed
            user_id: User who initiated the job
            current_stage: Current processing stage
        """
        super().__init__(redis, job_id, document_id, user_id)
        self.current_stage = current_stage
    
    async def report_progress(
        self, 
        stage: str | ProgressStage, 
        local_progress: float, 
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        """
        Report progress with automatic global progress calculation.
        
        Args:
            stage: Current processing stage
            local_progress: Progress within the current stage (0.0 to 1.0)
            message: Human-readable status message
            details: Additional details about the progress
        """
        # Calculate global progress based on current stage
        global_progress = calculate_global_progress(self.current_stage, local_progress)
        
        # Call parent's report_progress with global progress
        await super().report_progress(stage, global_progress, message, details)