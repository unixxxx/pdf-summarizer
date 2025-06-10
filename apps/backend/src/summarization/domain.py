"""Domain models and value objects for summarization."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SummaryResult:
    """Value object representing the result of summarization."""
    content: str
    processing_time: float
    metadata: dict[str, Any]
    
    @property
    def word_count(self) -> int:
        """Calculate word count of the summary."""
        return len(self.content.split())
    
    @property
    def was_fast(self) -> bool:
        """Check if processing was fast (under 5 seconds)."""
        return self.processing_time < 5.0


@dataclass
class SummaryOptions:
    """Value object for summarization options."""
    style: str = "balanced"  # detailed, concise, balanced, bullet_points
    max_length: Optional[int] = None
    focus_areas: Optional[str] = None
    custom_prompt: Optional[str] = None
    
    def to_prompt_modifier(self) -> str:
        """Convert options to prompt modifier."""
        modifiers = []
        
        if self.style == "detailed":
            modifiers.append("Provide a comprehensive and detailed summary")
        elif self.style == "concise":
            modifiers.append("Provide a brief and concise summary")
        elif self.style == "bullet_points":
            modifiers.append("Provide the summary as bullet points")
        
        if self.max_length:
            modifiers.append(f"Limit the summary to approximately {self.max_length} words")
        
        if self.focus_areas:
            modifiers.append(f"Focus particularly on: {self.focus_areas}")
        
        if self.custom_prompt:
            modifiers.append(self.custom_prompt)
        
        return ". ".join(modifiers) if modifiers else ""