"""In-memory storage for PDF summaries."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PDFSummaryRecord:
    """Record of a PDF summary."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str = ""
    file_name: str = ""
    file_size: int = 0
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    processing_time: float = 0.0
    word_count: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "fileName": self.file_name,
            "fileSize": self.file_size,
            "summary": self.summary,
            "createdAt": self.created_at.isoformat(),
            "processingTime": self.processing_time,
            "wordCount": self.word_count,
        }


class PDFSummaryStorage:
    """In-memory storage for PDF summaries."""

    def __init__(self):
        self._summaries: Dict[str, List[PDFSummaryRecord]] = {}

    def add_summary(
        self,
        user_email: str,
        file_name: str,
        file_size: int,
        summary: str,
        processing_time: float,
        word_count: Optional[int] = None,
    ) -> PDFSummaryRecord:
        """Add a new summary record."""
        record = PDFSummaryRecord(
            user_email=user_email,
            file_name=file_name,
            file_size=file_size,
            summary=summary,
            processing_time=processing_time,
            word_count=word_count,
        )

        if user_email not in self._summaries:
            self._summaries[user_email] = []

        self._summaries[user_email].append(record)
        return record

    def get_user_summaries(self, user_email: str) -> List[PDFSummaryRecord]:
        """Get all summaries for a user."""
        return self._summaries.get(user_email, [])

    def delete_summary(self, user_email: str, summary_id: str) -> bool:
        """Delete a summary by ID."""
        if user_email not in self._summaries:
            return False

        summaries = self._summaries[user_email]
        original_length = len(summaries)
        self._summaries[user_email] = [s for s in summaries if s.id != summary_id]

        return len(self._summaries[user_email]) < original_length

    def get_summary_by_id(
        self, user_email: str, summary_id: str
    ) -> Optional[PDFSummaryRecord]:
        """Get a specific summary by ID."""
        summaries = self.get_user_summaries(user_email)
        for summary in summaries:
            if summary.id == summary_id:
                return summary
        return None


# Global storage instance
pdf_summary_storage = PDFSummaryStorage()
