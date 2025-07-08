"""Document and DocumentChunk models for DocuLearn."""

from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
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
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import relationship

from .base import Base
from .enums import DocumentStatus


class Document(Base):
    """Document model for storing uploaded PDFs."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash with index
    page_count = Column(Integer, nullable=True)
    storage_path = Column(String(500), nullable=True)  # S3 key or local path
    extracted_text = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True, index=True)  # Direct folder relationship
    status = Column(
        SQLEnum(DocumentStatus, name='documentstatus', values_callable=lambda x: [e.value for e in x]), 
        nullable=False, 
        default=DocumentStatus.PENDING
    )
    processed_at = Column(DateTime, nullable=True)  # When processing was completed
    error_message = Column(Text, nullable=True)  # Error message if processing failed
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)  # Index for sorting
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime, nullable=True, index=True)  # Soft delete timestamp
    search_vector = Column(TSVECTOR, nullable=True)  # Full-text search vector

    # Relationships
    user = relationship("User", back_populates="documents")
    summaries = relationship(
        "Summary", back_populates="document", cascade="all, delete-orphan"
    )
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    chats = relationship(
        "Chat", back_populates="document", cascade="all, delete-orphan"
    )
    tags = relationship(
        "Tag", secondary="document_tags", back_populates="documents"
    )
    folder = relationship("Folder", back_populates="documents")


class DocumentChunk(Base):
    """Document chunks for vector search and RAG."""

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector, nullable=True)  # Flexible dimension for any embedding model
    chunk_metadata = Column(Text, nullable=True)  # JSON metadata
    created_at = Column(DateTime, nullable=False, default=func.now())
    search_vector = Column(TSVECTOR, nullable=True)  # Full-text search vector

    # Relationships
    document = relationship("Document", back_populates="chunks")