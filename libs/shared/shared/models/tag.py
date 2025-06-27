"""Tag model for DocuLearn."""

from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class Tag(Base):
    """Tag model for categorizing documents."""

    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly version
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    embedding = Column(Vector, nullable=True)  # Flexible dimension for any embedding model
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    documents = relationship(
        "Document", secondary="document_tags", back_populates="tags"
    )
    folders = relationship(
        "Folder", secondary="folder_tags", back_populates="tags"
    )