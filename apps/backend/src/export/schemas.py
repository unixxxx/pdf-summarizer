"""Export schemas for document generation."""

from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"