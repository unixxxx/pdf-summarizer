"""Summarization orchestrator service following DDD principles."""

import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Document, Summary
from ..document.document_service import DocumentService
from ..library.tag_service import TagGenerationRequest, TagService
from .summary_service import SummaryService

logger = logging.getLogger(__name__)


class SummarizationOrchestrator:
    """Orchestrates the summarization process across multiple services."""
    
    def __init__(
        self,
        document_service: DocumentService,
        summarizer_service: SummaryService,
        tag_service: TagService,
    ):
        self.document_service = document_service
        self.summarizer_service = summarizer_service
        self.tag_service = tag_service
    
    async def summarize_document(
        self,
        document_id: UUID,
        user_id: UUID,
        options: Optional[dict[str, Any]],
        db: AsyncSession,
    ) -> Summary:
        """Summarize an existing document."""
        # Get document
        document = await self.document_service.get_document(
            document_id=document_id,
            user_id=user_id,
            db=db,
        )
        
        if not document.extracted_text:
            raise ValueError("Document has no extracted text to summarize")
        
        # Generate summary
        summary = await self._generate_summary(
            document=document,
            text=document.extracted_text,
            options=options,
            db=db,
        )
        
        return summary
    
    async def summarize_text(
        self,
        text: str,
        filename: str,
        user_id: UUID,
        options: Optional[dict[str, Any]],
        db: AsyncSession,
    ) -> Summary:
        """Summarize raw text by creating a document first."""
        # Calculate word count
        word_count = len(text.split())
        
        # Create document for text
        document, is_new = await self.document_service.create_document(
            user_id=user_id,
            filename=filename,
            content=text.encode('utf-8'),
            file_size=len(text.encode('utf-8')),
            storage_path=None,  # Text documents don't need file storage
            db=db,
        )
        
        # Update with extracted text
        if is_new:
            document = await self.document_service.update_document_content(
                document_id=document.id,
                extracted_text=text,
                word_count=word_count,
                db=db,
            )
        
        # Generate summary
        summary = await self._generate_summary(
            document=document,
            text=text,
            options=options,
            db=db,
        )
        
        return summary
    
    async def _generate_summary(
        self,
        document: Document,
        text: str,
        options: Optional[dict[str, Any]],
        db: AsyncSession,
    ) -> Summary:
        """Generate summary and tags for a document."""
        # Check if summary already exists
        existing_summary = await self.summarizer_service.get_summary_for_document(
            document_id=document.id,
            db=db,
        )
        
        if existing_summary:
            logger.info(f"Summary already exists for document {document.id}")
            return existing_summary
        
        # Generate summary
        summary_result = await self.summarizer_service.summarize_text(
            text=text,
            options=options,
        )
        
        # Get LLM info from metadata
        llm_type = summary_result.metadata.get("llm_type", "unknown")
        llm_provider = "ollama" if "ollama" in llm_type else "openai"
        llm_model = summary_result.metadata.get("model", llm_type)
        
        # Add original text to metadata for word count calculation
        summary_result.metadata["original_text"] = text
        summary_result.metadata["original_words"] = len(text.split())
        
        # Save summary
        summary = await self.summarizer_service.save_summary(
            document_id=document.id,
            user_id=document.user_id,
            content=summary_result.content,
            processing_time=summary_result.processing_time,
            metadata=summary_result.metadata,
            llm_provider=llm_provider,
            llm_model=llm_model,
            db=db,
        )
        
        # Generate and assign tags
        tag_request = TagGenerationRequest(
            content=text,
            filename=document.filename,
            max_tags=5,
        )
        
        tag_data = await self.tag_service.generate_tags_for_document(tag_request)
        tags = await self.tag_service.find_or_create_tags(tag_data, db)
        
        # Associate tags with document
        await self.tag_service.associate_tags_with_document(
            document_id=document.id,
            tag_ids=[tag.id for tag in tags],
            db=db,
        )
        
        # Add tags to summary object for response
        summary.tags = tags
        
        await db.flush()
        
        return summary