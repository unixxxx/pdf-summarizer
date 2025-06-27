"""Shared database models for DocuLearn."""

from .base import Base
from .enums import DocumentStatus
from .user import User
from .document import Document, DocumentChunk
from .summary import Summary
from .chat import Chat, ChatMessage
from .tag import Tag
from .folder import Folder
from .associations import document_tags, folder_tags
from .job_progress import JobProgress

__all__ = [
    # Base
    "Base",
    
    # Enums
    "DocumentStatus",
    
    # Models
    "User",
    "Document",
    "DocumentChunk",
    "Summary",
    "Chat",
    "ChatMessage",
    "Tag",
    "Folder",
    "JobProgress",
    
    # Association tables
    "document_tags",
    "folder_tags",
]