"""Folder model for DocuLearn."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship

from .base import Base


class Folder(Base):
    """Folder model for organizing documents."""

    __tablename__ = "folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    parent_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    archived_at = Column(DateTime, nullable=True, index=True)  # Soft delete timestamp

    # Relationships
    user = relationship("User", back_populates="folders")
    documents = relationship("Document", back_populates="folder")
    parent = relationship(
        "Folder", 
        remote_side=[id], 
        backref=backref("children", cascade="all, delete-orphan")
    )
    tags = relationship(
        "Tag", secondary="folder_tags", back_populates="folders"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", "parent_id", name="_user_folder_name_uc"),
    )