from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from ..common.schemas import BaseSchema


class SummaryStyle(str, Enum):
    """Summary style options."""
    DETAILED = "detailed"
    CONCISE = "concise"
    BALANCED = "balanced"
    BULLET_POINTS = "bullet_points"


class CreateSummaryRequest(BaseSchema):
    """Request to create a summary."""
    
    document_id: Optional[UUID] = Field(
        None, 
        description="ID of existing document to summarize"
    )
    text: Optional[str] = Field(
        None, 
        description="Raw text to summarize (creates new document)",
        min_length=1,
        max_length=1000000  # 1MB text limit
    )
    filename: Optional[str] = Field(
        None, 
        description="Filename for text document",
        min_length=1,
        max_length=255
    )
    style: SummaryStyle = Field(
        SummaryStyle.BALANCED, 
        description="Summary style"
    )
    max_length: Optional[int] = Field(
        None, 
        description="Maximum length in words",
        ge=50,
        le=5000
    )
    focus_areas: Optional[str] = Field(
        None, 
        description="Areas to focus on",
        max_length=500
    )
    custom_prompt: Optional[str] = Field(
        None, 
        description="Custom prompt modifier",
        max_length=1000
    )

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean text input."""
        if v:
            return v.strip()
        return v

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean filename."""
        if v:
            return v.strip()
        return v

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "document_id": "123e4567-e89b-12d3-a456-426614174000",
            "style": "balanced",
            "max_length": 500
        }
    }


class TagResponse(BaseSchema):
    """Tag response model."""
    
    id: UUID
    name: str
    slug: str
    color: str


class DocumentInfoResponse(BaseSchema):
    """Document information in summary response."""
    
    id: UUID
    filename: str
    file_size: int
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    created_at: str


class SummaryResponse(BaseSchema):
    """Summary response."""
    
    id: UUID
    document_id: UUID
    content: str
    word_count: int
    processing_time: float
    tags: list[TagResponse]
    document_info: DocumentInfoResponse
    llm_provider: str
    llm_model: str

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "document_id": "123e4567-e89b-12d3-a456-426614174000",
            "content": "This is a summary of the document...",
            "word_count": 150,
            "processing_time": 2.5,
            "tags": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Technology",
                    "slug": "technology",
                    "color": "#3B82F6"
                }
            ],
            "document_info": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "document.pdf",
                "file_size": 1024000,
                "word_count": 5000,
                "page_count": 10,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo"
        }
    }


class TextSummaryRequest(BaseSchema):
    """Request schema for text summarization."""

    text: str = Field(
        ..., description="Text content to summarize", min_length=10, max_length=100000
    )
    max_length: Optional[int] = Field(
        default=500, description="Maximum length of summary in words", ge=50, le=2000
    )
    format: Optional[str] = Field(
        default="paragraph",
        description="Summary format: 'paragraph', 'bullets', or 'keypoints'",
        pattern="^(paragraph|bullets|keypoints)$",
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Additional instructions for summary generation",
        max_length=500,
    )

    @field_validator("text")
    @classmethod
    def validate_text_content(cls, v: str) -> str:
        """Ensure text has meaningful content."""
        if not v.strip():
            raise ValueError("Text content cannot be empty or only whitespace")
        return v

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "text": "Long text content to be summarized...",
            "max_length": 500,
            "format": "paragraph",
            "instructions": "Focus on technical details",
        }
    }


class TextSummaryResponse(BaseSchema):
    """Response schema for text summarization."""

    summary: str = Field(..., description="Generated summary")
    original_length: int = Field(..., description="Original text length in characters")
    summary_length: int = Field(..., description="Summary length in characters")
    original_words: int = Field(..., description="Original text word count")
    summary_words: int = Field(..., description="Summary word count")
    compression_ratio: float = Field(..., description="Compression ratio as percentage")

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "summary": "This is a concise summary of the text...",
            "original_length": 5000,
            "summary_length": 500,
            "original_words": 1000,
            "summary_words": 100,
            "compression_ratio": 10.0,
        }
    }


class TagGenerationResponse(BaseSchema):
    """Schema for structured tag generation from LLM."""
    
    tags: list[str] = Field(
        ...,
        min_items=3,
        max_items=8,
        description=(
            "List of relevant tags for the document. Tags should be lowercase, "
            "use hyphens for multi-word tags (e.g., 'machine-learning'), "
            "and be relevant to the content."
        )
    )
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and clean tags."""
        cleaned_tags = []
        for tag in v:
            # Convert to lowercase and replace spaces with hyphens
            tag = tag.lower().strip().replace(' ', '-')
            # Remove any non-alphanumeric characters except hyphens
            tag = ''.join(c for c in tag if c.isalnum() or c == '-')
            # Remove multiple consecutive hyphens
            while '--' in tag:
                tag = tag.replace('--', '-')
            # Remove leading/trailing hyphens
            tag = tag.strip('-')
            
            # Only add if valid
            if tag and 1 < len(tag) <= 50 and tag not in cleaned_tags:
                cleaned_tags.append(tag)
        
        return cleaned_tags[:8]  # Ensure max 8 tags
    
    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "tags": [
                "machine-learning", "python", "data-science", 
                "tutorial", "neural-networks"
            ]
        }
    }


class SummaryStats(BaseSchema):
    """Statistics about a generated summary."""

    original_length: int = Field(..., description="Original text length")
    summary_length: int = Field(..., description="Summary length")
    original_words: int = Field(..., description="Original word count")
    summary_words: int = Field(..., description="Summary word count")
    compression_ratio: float = Field(..., description="Compression ratio")
    chunk_count: int = Field(..., description="Number of chunks processed")

    model_config = BaseSchema.model_config.copy()
    model_config["json_schema_extra"] = {
        "example": {
            "original_length": 5000,
            "summary_length": 500,
            "original_words": 1000,
            "summary_words": 100,
            "compression_ratio": 10.0,
            "chunk_count": 3,
        }
    }
