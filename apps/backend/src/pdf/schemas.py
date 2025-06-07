from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from ..common.schemas import BaseSchema


class PDFMetadata(BaseSchema):
    """PDF file metadata schema."""

    filename: str = Field(..., description="Original filename")
    pages: int = Field(..., description="Number of pages", ge=1)
    size_bytes: int = Field(..., description="File size in bytes", ge=1)
    title: Optional[str] = Field(None, description="PDF title from metadata")
    author: Optional[str] = Field(None, description="PDF author from metadata")
    subject: Optional[str] = Field(None, description="PDF subject from metadata")
    creator: Optional[str] = Field(None, description="PDF creator application")
    encrypted: bool = Field(False, description="Whether PDF is encrypted")

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return round(self.size_bytes / (1024 * 1024), 2)

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "filename": "document.pdf",
            "pages": 10,
            "size_bytes": 1048576,
            "title": "Sample Document",
            "author": "John Doe",
            "encrypted": False,
        }
    }


class PDFSummaryRequest(BaseSchema):
    """Request schema for PDF summarization."""

    max_length: Optional[int] = Field(
        default=500, description="Maximum length of summary in words", ge=50, le=2000
    )
    include_metadata: bool = Field(
        default=True, description="Include PDF metadata in response"
    )

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {"max_length": 500, "include_metadata": True}
    }


class PDFSummaryResponse(BaseSchema):
    """Response schema for PDF summarization."""

    summary: str = Field(..., description="Generated summary text")
    metadata: Optional[PDFMetadata] = Field(None, description="PDF metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    summary_stats: dict = Field(..., description="Summary statistics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "summary": "This document discusses...",
            "metadata": {
                "filename": "document.pdf",
                "pages": 10,
                "size_bytes": 1048576,
            },
            "processing_time": 2.5,
            "summary_stats": {
                "original_length": 5000,
                "summary_length": 500,
                "original_words": 1000,
                "summary_words": 100,
                "compression_ratio": 10.0,
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }
    }


class PDFTextExtractionResponse(BaseSchema):
    """Response schema for PDF text extraction."""

    text: str = Field(..., description="Extracted text content")
    metadata: PDFMetadata = Field(..., description="PDF metadata")
    extraction_time: float = Field(..., description="Extraction time in seconds")

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "text": "Extracted text content...",
            "metadata": {
                "filename": "document.pdf",
                "pages": 10,
                "size_bytes": 1048576,
            },
            "extraction_time": 0.5,
        }
    }


class TagSchema(BaseSchema):
    """Tag schema for documents."""
    
    id: UUID = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="URL-friendly tag slug")
    color: Optional[str] = Field(None, description="Tag color (hex)")
    
    model_config = BaseSchema.model_config.copy()
    model_config["from_attributes"] = True


class PDFSummaryHistoryItem(BaseSchema):
    """Schema for a single PDF summary history item."""

    id: UUID = Field(..., description="Summary ID")
    document_id: UUID = Field(..., description="Document ID")
    fileName: str = Field(..., description="Original filename")
    fileSize: int = Field(..., description="File size in bytes")
    summary: str = Field(..., description="Generated summary")
    createdAt: datetime = Field(..., description="Creation timestamp")
    processingTime: float = Field(..., description="Processing time in seconds")
    wordCount: int = Field(..., description="Summary word count")
    tags: list[TagSchema] = Field(default_factory=list, description="Document tags")

    model_config = BaseSchema.model_config.copy()
    model_config["from_attributes"] = True
