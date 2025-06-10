"""Summarization service following DDD principles."""

import logging
import time
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document as LangchainDocument
from langchain.schema.language_model import BaseLanguageModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import SummarizationError
from ..database.models import Summary
from .domain import SummaryOptions, SummaryResult

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating and managing summaries."""
    
    def __init__(
        self, llm: BaseLanguageModel, chunk_size: int = 3000, chunk_overlap: int = 200
    ):
        self.llm = llm
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    async def summarize_text(
        self,
        text: str,
        options: Optional[dict[str, Any]] = None,
    ) -> SummaryResult:
        """Generate a summary for the given text."""
        start_time = time.time()
        
        # Parse options
        summary_options = self._parse_options(options)
        
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            docs = [LangchainDocument(page_content=chunk) for chunk in chunks]
            
            logger.info(f"Split text into {len(docs)} chunks for summarization")
            
            # Create summarization chain
            chain = self._create_chain(summary_options)
            
            # Generate summary
            # Try the newer ainvoke method first, fall back to arun for compatibility
            try:
                result = await chain.ainvoke({"input_documents": docs})
                if isinstance(result, dict):
                    result = result.get("output_text", "")
            except (AttributeError, TypeError):
                # Fallback for older langchain versions or Ollama compatibility
                result = await chain.arun({"input_documents": docs})
            
            processing_time = time.time() - start_time
            
            # Create metadata
            metadata = {
                "chunks_processed": len(docs),
                "total_chars": len(text),
                "options": options or {},
                "llm_type": getattr(self.llm, "_llm_type", "unknown"),
                "model": getattr(self.llm, "model_name", getattr(self.llm, "model", "unknown")),
            }
            
            return SummaryResult(
                content=result,
                processing_time=processing_time,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise SummarizationError(f"Failed to generate summary: {str(e)}") from e
    
    async def save_summary(
        self,
        document_id: UUID,
        user_id: UUID,
        content: str,
        processing_time: float,
        metadata: dict[str, Any],
        llm_provider: str,
        llm_model: str,
        db: AsyncSession,
    ) -> Summary:
        """Save a summary to the database."""
        # Calculate word counts
        original_word_count = metadata.get("original_words", len(metadata.get("original_text", "").split()))
        summary_word_count = len(content.split())
        compression_ratio = (original_word_count - summary_word_count) / original_word_count if original_word_count > 0 else 0
        
        summary = Summary(
            user_id=user_id,
            document_id=document_id,
            summary_text=content,
            original_word_count=original_word_count,
            summary_word_count=summary_word_count,
            compression_ratio=compression_ratio,
            processing_time=processing_time,
            llm_provider=llm_provider,
            llm_model=llm_model,
            created_at=datetime.utcnow(),
        )
        
        db.add(summary)
        await db.flush()
        await db.refresh(summary)
        
        return summary
    
    async def get_summary_for_document(
        self,
        document_id: UUID,
        db: AsyncSession,
    ) -> Optional[Summary]:
        """Get summary for a document if it exists."""
        result = await db.execute(
            select(Summary).where(Summary.document_id == document_id)
        )
        return result.scalar_one_or_none()
    
    def get_service_info(self) -> dict[str, Any]:
        """Get information about the summarization service configuration."""
        return {
            "llm_type": getattr(self.llm, "_llm_type", "unknown"),
            "chunk_size": self.text_splitter._chunk_size,
            "chunk_overlap": self.text_splitter._chunk_overlap,
            "separators": self.text_splitter._separators,
        }
    
    def _parse_options(self, options: Optional[dict[str, Any]]) -> SummaryOptions:
        """Parse options dictionary into SummaryOptions."""
        if not options:
            return SummaryOptions()
        
        return SummaryOptions(
            style=options.get("style", "balanced"),
            max_length=options.get("max_length"),
            focus_areas=options.get("focus_areas"),
            custom_prompt=options.get("custom_prompt"),
        )
    
    def _create_chain(self, options: SummaryOptions):
        """Create the appropriate summarization chain."""
        # Get prompt modifier from options
        modifier = options.to_prompt_modifier()
        
        # Create custom prompt if modifier exists
        if modifier:
            from langchain.prompts import PromptTemplate
            
            template = f"""Write a summary of the following text.
{modifier}

Text: {{text}}

SUMMARY:"""
            
            prompt = PromptTemplate(template=template, input_variables=["text"])
            
            return load_summarize_chain(
                llm=self.llm,
                chain_type="stuff",
                prompt=prompt,
            )
        
        # Use default chain
        return load_summarize_chain(
            llm=self.llm,
            chain_type="stuff",
        )