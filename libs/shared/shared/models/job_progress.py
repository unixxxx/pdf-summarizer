"""JobProgress model for tracking background job status."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class JobProgress(Base):
    """Job progress tracking."""
    __tablename__ = "job_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Progress tracking
    stage = Column(String(50), nullable=False)
    progress = Column(Float, nullable=False, default=0.0)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=func.now())
    last_update = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    def update_progress(self, stage: str, progress: float, message: str, details: dict = None):
        """Update job progress."""
        self.stage = stage
        self.progress = progress
        self.message = message
        self.details = details
        self.last_update = datetime.now(timezone.utc)
        
        if stage in ["completed", "failed"]:
            self.completed_at = datetime.now(timezone.utc)