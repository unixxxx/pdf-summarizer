from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ..common.schemas import BaseSchema


class SummaryStyle(str, Enum):
    """Summary style options."""
    DETAILED = "detailed"
    CONCISE = "concise"
    BALANCED = "balanced"
    BULLET_POINTS = "bullet_points"


class SummaryOptions(BaseSchema):
    """Options for summarization."""
    style: SummaryStyle = Field(default=SummaryStyle.BALANCED, description="Summary style")
    max_length: int | None = Field(default=None, description="Maximum length in words", ge=1)
    focus_areas: str | None = Field(default=None, description="Areas to focus on", max_length=500)
    custom_prompt: str | None = Field(default=None, description="Custom prompt modifier", max_length=1000)
    
    @property
    def prompt_modifier(self) -> str:
        """Build prompt modifier from options."""
        modifiers = []
        
        if self.style == SummaryStyle.DETAILED:
            modifiers.append("Provide a comprehensive and detailed summary")
        elif self.style == SummaryStyle.CONCISE:
            modifiers.append("Provide a brief and concise summary")
        elif self.style == SummaryStyle.BULLET_POINTS:
            modifiers.append("Provide the summary as bullet points")
        
        if self.max_length:
            modifiers.append(f"Limit the summary to approximately {self.max_length} words")
        
        if self.focus_areas:
            modifiers.append(f"Focus particularly on: {self.focus_areas}")
        
        if self.custom_prompt:
            modifiers.append(self.custom_prompt)
        
        return ". ".join(modifiers) if modifiers else ""


class SummaryResult(BaseSchema):
    """Result of summarization."""
    content: str = Field(..., description="Summary content")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def word_count(self) -> int:
        """Calculate word count of the summary."""
        return len(self.content.split())
    
    @property
    def was_fast(self) -> bool:
        """Check if processing was fast (under 5 seconds)."""
        return self.processing_time < 5.0


class CreateSummaryRequest(SummaryOptions):
    """Request to create a summary."""
    
    document_id: UUID | None = Field(
        None, 
        description="ID of existing document to summarize"
    )
    text: str | None = Field(
        None, 
        description="Raw text to summarize (creates new document)",
        min_length=1,
        max_length=1000000  # 1MB text limit
    )
    filename: str | None = Field(
        None, 
        description="Filename for text document",
        min_length=1,
        max_length=255
    )
    
    def get_summary_options(self) -> SummaryOptions:
        """Return SummaryOptions"""
        return SummaryOptions(
            focus_areas=self.focus_areas,
            custom_prompt=self.custom_prompt,
            max_length=self.max_length,
            style=self.style
        )

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str | None) -> str | None:
        """Validate and clean text input."""
        if v:
            return v.strip()
        return v

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str | None) -> str | None:
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
    word_count: int | None = None
    page_count: int | None = None
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



