"""Shared enums for DocuLearn models."""

from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"  # Initial state when document record is created
    UPLOADING = "uploading"  # File is being uploaded
    PROCESSING = "processing"  # File is being processed (text extraction, embeddings)
    COMPLETED = "completed"  # Processing complete, ready for use
    FAILED = "failed"  # Processing failed