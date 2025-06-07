from typing import Optional

from pydantic import Field, field_validator

from ..common.schemas import BaseSchema


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
        description="List of relevant tags for the document. Tags should be lowercase, use hyphens for multi-word tags (e.g., 'machine-learning'), and be relevant to the content."
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
            "tags": ["machine-learning", "python", "data-science", "tutorial", "neural-networks"]
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
