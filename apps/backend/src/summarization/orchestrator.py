"""Summarization orchestrator service following DDD principles."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Document, Summary
from ..embeddings.service import EmbeddingsService
from ..library.document.service import DocumentService
from ..library.folder.service import FolderService
from ..library.tag.service import TagService
from .schemas import SummaryOptions
from .service import SummaryService

logger = logging.getLogger(__name__)


class SummarizationOrchestrator:
    """Orchestrates the summarization process across multiple services."""
    
    def __init__(
        self,
        document_service: DocumentService,
        summarizer_service: SummaryService,
        tag_service: TagService,
        folder_service: FolderService,
        embeddings_service: EmbeddingsService | None = None,
    ):
        self.document_service = document_service
        self.summarizer_service = summarizer_service
        self.tag_service = tag_service
        self.folder_service = folder_service
        self.embeddings_service = embeddings_service
    
    async def summarize_document(
        self,
        document_id: UUID,
        user_id: UUID,
        options: SummaryOptions | None,
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
        filename: str,  # Original filename is kept for API compatibility but not used
        user_id: UUID,
        options: SummaryOptions | None,
        db: AsyncSession,
    ) -> Summary:
        """Summarize raw text by creating a document first."""
        # Calculate word count
        word_count = len(text.split())
        
        # Analyze document to get summary, filename, and tags in one call
        analysis = await self.summarizer_service.analyze_document(
            text=text,
            options=options,
        )
        
        # Extract the summary result and filename
        from .schemas import SummaryResult
        summary_result = SummaryResult(
            content=analysis.summary,
            processing_time=0,  # Will be calculated later
            metadata={
                "suggested_filename": analysis.title,
                "tags": analysis.tags,
            }
        )
        
        actual_filename = f"{analysis.title}.txt"
        
        # Create document for text
        document, is_new = await self.document_service.create_document(
            user_id=user_id,
            filename=actual_filename,
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
            
            # Process the summary with tags from the analysis
            summary = await self._process_summary(
                document=document,
                summary_result=summary_result,
                db=db,
                tags_from_analysis=analysis.tags,
            )
        else:
            # Document already exists, check if it has a summary
            existing_summary = await self.summarizer_service.get_summary_for_document(
                document_id=document.id,
                db=db,
            )
            
            if existing_summary:
                logger.info(f"Using existing summary for duplicate document {document.id}")
                summary = existing_summary
            else:
                # Document exists but no summary, create one
                summary = await self._process_summary(
                    document=document,
                    summary_result=summary_result,
                    db=db,
                    tags_from_analysis=analysis.tags,
                )
        
        return summary
    
    async def _generate_summary(
        self,
        document: Document,
        text: str,
        options: SummaryOptions | None,
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
        
        # Analyze document to get summary, filename, and tags
        analysis = await self.summarizer_service.analyze_document(
            text=text,
            options=options,
        )
        
        # Create summary result
        from .schemas import SummaryResult
        summary_result = SummaryResult(
            content=analysis.summary,
            processing_time=0,  # Will be set when saving
            metadata={
                "suggested_filename": analysis.title,
                "tags": analysis.tags,
            }
        )
        
        # Add suggested filename to metadata if document doesn't have a meaningful name
        if document.filename and document.filename.lower() in ['document.txt', 'summary.txt', 'text.txt']:
            summary_result.metadata["suggested_filename"] = analysis.title
        
        # Process the summary with tags
        return await self._process_summary(document, summary_result, db, tags_from_analysis=analysis.tags)
    
    async def _process_summary(
        self,
        document: Document,
        summary_result: Any,
        db: AsyncSession,
        tags_from_analysis: list[str] | None = None,
    ) -> Summary:
        """Process summary result - save it and generate tags, folders, embeddings."""
        
        # Get LLM info from metadata
        llm_type = summary_result.metadata.get("llm_type", "unknown")
        llm_provider = "ollama" if "ollama" in llm_type else "openai"
        llm_model = summary_result.metadata.get("model", llm_type)
        
        # Get document text
        text = document.extracted_text or ""
        
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
        
        # Use tags from analysis
        if tags_from_analysis:
            # Convert tag strings to tag data format
            tag_data = [
                {
                    "name": tag.replace('-', ' ').title(),
                    "slug": tag,
                    "color": self.tag_service.TAG_COLORS[i % len(self.tag_service.TAG_COLORS)]
                }
                for i, tag in enumerate(tags_from_analysis[:8])  # Max 8 tags
            ]
            tags = await self.tag_service.find_or_create_tags(tag_data, db)
        else:
            # No tags provided
            tags = []
        
        # Associate tags with document
        await self.tag_service.associate_tags_with_document(
            document_id=document.id,
            tag_ids=[tag.id for tag in tags],
            db=db,
        )
        
        # Sync smart folders based on new tags
        await self.folder_service.sync_document_folders(db, document)
        
        # Create embeddings for RAG/chat functionality
        if self.embeddings_service:
            # Generate embeddings synchronously
            try:
                # Get the document's text
                text = document.extracted_text or ""
                chunks = await self.embeddings_service.create_document_embeddings(
                    document_id=str(document.id),
                    text=text,
                    db=db,
                )
                logger.info(f"Created {len(chunks)} embeddings for document {document.id}")
            except Exception as e:
                logger.warning(f"Failed to create embeddings for document {document.id}: {str(e)}")
                # Don't fail the whole operation if embeddings fail
        
        # Add tags to summary object for response
        summary.tags = tags
        
        await db.flush()
        
        return summary