"""Document processing orchestrator."""

import logging
from typing import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..library.document.service import DocumentService
from ..storage.service import StorageService

logger = logging.getLogger(__name__)


class DocumentProcessingOrchestrator:
    """Orchestrates document processing pipeline."""
    
    def __init__(
        self,
        document_service: DocumentService,
        storage_service: StorageService,
    ):
        self.document_service = document_service
        self.storage_service = storage_service
        # TODO: Initialize embeddings service with proper config
        # self.embedding_service = EmbeddingsService(settings, factory)
    
    async def process_uploaded_document(
        self,
        document_id: UUID,
        file_content: bytes,
        user_id: UUID,
        db: AsyncSession,
        progress_callback: Callable | None = None,
    ) -> None:
        """Process an uploaded document through the full pipeline."""
        logger.info(f"[ORCHESTRATOR] Starting document processing for {document_id}")
        
        try:
            # Progress: Extracting text
            if progress_callback:
                await progress_callback("extracting_text", 30)
            
            logger.info(f"[ORCHESTRATOR] Extracting text from PDF for document {document_id}")
            # Extract text from PDF
            from ..common.pdf_utils import extract_text_from_pdf
            extracted_text = await extract_text_from_pdf(file_content)
            
            # Calculate word count
            word_count = len(extracted_text.split())
            
            # Get page count from PDF
            import io

            import PyPDF2
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            page_count = len(pdf_reader.pages)
            
            # Update document with extracted text
            await self.document_service.update_document_content(
                document_id=document_id,
                extracted_text=extracted_text,
                word_count=word_count,
                page_count=page_count,
                db=db,
            )
            
            # TODO: Generate embeddings when service is ready
            # Progress: Generating embeddings
            # if progress_callback:
            #     await progress_callback("generating_embeddings", 60)
            
            # Generate embeddings
            # await self.embedding_service.create_document_embeddings(
            #     document_id=document_id,
            #     text=extracted_text,
            #     db=db,
            # )
            
            # TODO: Generate summary when service is ready
            # Progress: Generating summary
            # if progress_callback:
            #     await progress_callback("generating_summary", 80)
            
            # Progress: Complete
            if progress_callback:
                await progress_callback("completed", 90)
            
            logger.info(f"[ORCHESTRATOR] Document processing completed for {document_id}")
            
        except Exception as e:
            # Log error and re-raise
            logger.error(f"[ORCHESTRATOR] Error processing document {document_id}: {str(e)}")
            raise