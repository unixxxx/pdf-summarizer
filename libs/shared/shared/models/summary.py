"""Summary model for DocuLearn."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class Summary(Base):
    """Summary model for storing document summaries."""

    __tablename__ = "summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    original_word_count = Column(Integer, nullable=False)
    summary_word_count = Column(Integer, nullable=False)
    compression_ratio = Column(Float, nullable=False)
    processing_time = Column(Float, nullable=False)  # in seconds
    llm_provider = Column(String(50), nullable=False)  # openai, ollama
    llm_model = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)  # Index for sorting

    # Relationships
    user = relationship("User", back_populates="summaries")
    document = relationship("Document", back_populates="summaries")