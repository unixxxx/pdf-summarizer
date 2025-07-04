"""LLM-specific schemas for summarization module."""

from pydantic import BaseModel, Field, field_validator


class ComprehensiveDocumentAnalysis(BaseModel):
    """Comprehensive analysis of a document including summary, filename, and tags.
    
    This model is used for structured output from LLM when analyzing documents.
    """
    
    summary: str = Field(
        ..., 
        description="A comprehensive summary of the document's content",
        min_length=50,
        max_length=2000
    )
    
    title: str = Field(
        ..., 
        description="A meaningful title based on the content",
        min_length=3,
        max_length=50
    )
    
    tags: list[str] = Field(
        ...,
        description="Relevant tags for categorizing the document (lowercase, use hyphens for multi-word tags)",
        min_items=3,
        max_items=8
    )
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are properly formatted."""
        import re
        cleaned_tags = []
        for tag in v:
            # Convert to lowercase and use hyphens
            tag = tag.lower().strip()
            tag = re.sub(r'[^a-z0-9\s-]', '', tag)
            tag = re.sub(r'\s+', '-', tag)
            tag = re.sub(r'-+', '-', tag).strip('-')
            
            # Ensure tag is at least 2 characters and not just numbers
            if tag and len(tag) >= 2 and not tag.isdigit() and tag not in cleaned_tags:
                cleaned_tags.append(tag)
        
        # Ensure we have at least 3 valid tags
        if len(cleaned_tags) < 3:
            raise ValueError(
                f"At least 3 valid tags required (got {len(cleaned_tags)}). "
                f"Tags must be at least 2 characters long and descriptive."
            )
        
        return cleaned_tags[:8]  # Ensure max 8 tags
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "This document provides a comprehensive guide to implementing neural networks using Python and TensorFlow. It covers the fundamental concepts of deep learning, network architectures, training procedures, and optimization techniques.",
                "title": "Neural Networks Implementation Guide",
                "tags": ["machine-learning", "neural-networks", "python", "tensorflow", "deep-learning", "tutorial"]
            }
        }