"""PDF text extraction utilities."""

import io
import logging
from typing import Any

import PyPDF2

from ..common.exceptions import PDFProcessingError

logger = logging.getLogger(__name__)


async def extract_text_from_pdf(pdf_content: bytes) -> dict[str, Any]:
    """
    Extract text and metadata from PDF content.
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Dictionary with 'text' and 'metadata'
        
    Raises:
        PDFProcessingError: If PDF cannot be processed
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract metadata
        metadata = {
            "page_count": len(pdf_reader.pages),
        }
        
        # Try to extract additional metadata
        if pdf_reader.metadata:
            if pdf_reader.metadata.title:
                metadata["title"] = pdf_reader.metadata.title
            if pdf_reader.metadata.author:
                metadata["author"] = pdf_reader.metadata.author
            if pdf_reader.metadata.subject:
                metadata["subject"] = pdf_reader.metadata.subject
        
        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(page_text)
            except Exception as e:
                # Log but continue with other pages
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
        
        if not text_parts:
            raise PDFProcessingError("No text content could be extracted from the PDF")
        
        text = "\n\n".join(text_parts)
        
        return {
            "text": text,
            "metadata": metadata,
        }
        
    except PyPDF2.errors.PdfReadError as e:
        raise PDFProcessingError(f"Invalid PDF file: {str(e)}")
    except Exception as e:
        raise PDFProcessingError(f"Failed to process PDF: {str(e)}")