"""Association tables for many-to-many relationships in DocuLearn."""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Table,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


# Association table for many-to-many relationship between documents and tags
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, nullable=False, default=func.now())
)

# Association table for many-to-many relationship between folders and tags (for smart folders)
folder_tags = Table(
    'folder_tags',
    Base.metadata,
    Column('folder_id', UUID(as_uuid=True), ForeignKey('folders.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, nullable=False, default=func.now())
)