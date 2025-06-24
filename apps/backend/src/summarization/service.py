"""Summarization service following DDD principles."""

import logging
from typing import Any
from uuid import UUID

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema.language_model import BaseLanguageModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import LLMError
from ..common.retry import retry_on_llm_error
from ..database.models import Summary
from .llm_schemas import ComprehensiveDocumentAnalysis
from .schemas import SummaryOptions

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating and managing summaries."""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
    
    
    async def analyze_document(
        self,
        text: str,
        options: SummaryOptions | None = None,
    ) -> ComprehensiveDocumentAnalysis:
        """Analyze document to generate summary, filename, and tags in a single LLM call."""
        parser = PydanticOutputParser(pydantic_object=ComprehensiveDocumentAnalysis)
        
        # Create comprehensive prompt
        template = f"""Analyze the following document and provide a JSON response.

{options.prompt_modifier}

Document: {{text}}

IMPORTANT: You MUST respond with a valid JSON object that includes:
- summary: A comprehensive summary of the document
- title: A descriptive title using only letters and numbers (e.g., 'Neural network guide')
- tags: An array of 3-8 relevant tags using only lowercase letters, numbers, and hyphens (e.g., 'machine-learning')

Example response format:
{{{{
    "summary": "This document discusses...",
    "title": "Example Title",
    "tags": ["tag-one", "tag-two", "tag-three"]
}}}}
"""     
        prompt = PromptTemplate(
            template=template,
            input_variables=["text"],
            output_parser=parser
        )
        
        # Create chain with structured output
        chain = prompt | self.llm.with_structured_output(ComprehensiveDocumentAnalysis, method="json_schema")
        
        @retry_on_llm_error(max_attempts=3)
        async def _invoke_llm():
            try:
                return await chain.ainvoke({"text": text})
            except Exception as e:
                logger.error(f"LLM invocation failed: {str(e)}")
                raise LLMError(f"Failed to analyze document: {str(e)}")
        
        try:
            # Generate comprehensive analysis with retry
            return await _invoke_llm()
        except (LLMError, Exception) as e:
            logger.error(f"Structured analysis failed after retries: {str(e)}")
            # Ultimate fallback
            return ComprehensiveDocumentAnalysis(
                summary="Failed to analyze document. Please try again.",
                title="document",
                tags=["unprocessed", "error", "retry"]
            )
    
    
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
        )
        
        db.add(summary)
        await db.flush()
        await db.refresh(summary)
        
        return summary
    
    
    async def get_summary_for_document(
        self,
        document_id: UUID,
        db: AsyncSession,
    ) -> Summary | None:
        """Get summary for a document if it exists."""
        result = await db.execute(
            select(Summary).where(Summary.document_id == document_id)
        )
        return result.scalar_one_or_none()
    
    def get_service_info(self) -> dict[str, str]:
        """Get service information."""
        return {
            "service": "SummaryService",
            "version": "1.0",
            "llm_type": type(self.llm).__name__
        }
    
    
