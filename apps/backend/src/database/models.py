"""Database models for PDF Summarizer."""

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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .session import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    picture = Column(String(500), nullable=True)
    provider = Column(String(50), nullable=False)  # google, github
    provider_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    documents = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    summaries = relationship(
        "Summary", back_populates="user", cascade="all, delete-orphan"
    )
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("provider", "provider_id", name="_provider_user_uc"),
    )


class Document(Base):
    """Document model for storing uploaded PDFs."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_hash = Column(String(64), nullable=False)  # SHA256 hash
    page_count = Column(Integer, nullable=True)
    storage_path = Column(String(500), nullable=False)  # S3 key or local path
    created_at = Column(DateTime, nullable=False, default=func.now())

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
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    user = relationship("User", back_populates="summaries")
    document = relationship("Document", back_populates="summaries")


class DocumentChunk(Base):
    """Document chunks for vector search and RAG."""

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # Default for OpenAI embeddings
    chunk_metadata = Column(Text, nullable=True)  # JSON metadata
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")


class Chat(Base):
    """Chat session for document Q&A."""

    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="chats")
    document = relationship("Document", back_populates="chats")
    messages = relationship(
        "ChatMessage", back_populates="chat", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    """Individual messages in a chat session."""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_metadata = Column(
        Text, nullable=True
    )  # JSON for storing retrieved chunks, etc.
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    chat = relationship("Chat", back_populates="messages")
