"""Schemas for processing module."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProcessingStage(str, Enum):
    """Document processing stages."""
    
    PENDING = "pending"
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    EMBEDDING = "embedding"
    ENRICHING = "enriching"
    READY = "ready"
    ERROR = "error"


class ProcessingStatus(BaseModel):
    """Document processing status."""
    
    document_id: str = Field(..., description="Document ID")
    stage: ProcessingStage = Field(..., description="Current processing stage")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    started_at: datetime = Field(..., description="When processing started")
    completed_at: datetime | None = Field(None, description="When processing completed")
    error: str | None = Field(None, description="Error message if failed")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class ProcessingStatusResponse(ProcessingStatus):
    """Response model for processing status."""
    
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")
    stages_completed: list[str] = Field(default_factory=list, description="Completed stages")
    current_stage_detail: str | None = Field(None, description="Details about current stage")