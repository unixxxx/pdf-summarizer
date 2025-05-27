import io
import time
from typing import Optional, Tuple
from pypdf import PdfReader

from ..common.exceptions import (
    PDFProcessingError,
    PDFTooLargeError,
    PDFTooManyPagesError,
    EmptyContentError
)
from ..config import Settings
from .schemas import PDFMetadata


class PDFService:
    """Service for PDF file operations."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    async def validate_pdf(self, pdf_content: bytes, filename: str) -> None:
        """
        Validate PDF file against configured limits.
        
        Args:
            pdf_content: PDF file content
            filename: Original filename
            
        Raises:
            PDFTooLargeError: If file exceeds size limit
            PDFTooManyPagesError: If file has too many pages
            PDFProcessingError: If validation fails
        """
        # Check file size
        if len(pdf_content) > self.settings.max_pdf_size_bytes:
            raise PDFTooLargeError(self.settings.max_pdf_size_mb)
        
        try:
            # Create reader to check page count
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            # Check page count
            if len(reader.pages) > self.settings.max_pdf_pages:
                raise PDFTooManyPagesError(self.settings.max_pdf_pages)
                
        except (PDFTooLargeError, PDFTooManyPagesError):
            raise
        except Exception as e:
            raise PDFProcessingError(f"Failed to validate PDF: {str(e)}")
    
    async def extract_text(self, pdf_content: bytes) -> Tuple[str, float]:
        """
        Extract text content from PDF.
        
        Args:
            pdf_content: PDF file content
            
        Returns:
            Tuple of (extracted_text, extraction_time_seconds)
            
        Raises:
            PDFProcessingError: If text extraction fails
            EmptyContentError: If no text content found
        """
        start_time = time.time()
        
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n".join(text_parts)
            
            # Check if text was extracted
            if not full_text.strip():
                raise EmptyContentError("PDF file")
            
            extraction_time = time.time() - start_time
            return full_text, extraction_time
            
        except EmptyContentError:
            raise
        except Exception as e:
            raise PDFProcessingError(f"Failed to extract text from PDF: {str(e)}")
    
    async def extract_metadata(
        self, 
        pdf_content: bytes, 
        filename: str
    ) -> PDFMetadata:
        """
        Extract metadata from PDF file.
        
        Args:
            pdf_content: PDF file content
            filename: Original filename
            
        Returns:
            PDFMetadata object
            
        Raises:
            PDFProcessingError: If metadata extraction fails
        """
        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            # Build metadata dict
            metadata_dict = {
                "filename": filename,
                "pages": len(reader.pages),
                "size_bytes": len(pdf_content),
                "encrypted": reader.is_encrypted,
            }
            
            # Add document info if available
            if reader.metadata:
                # Clean metadata values
                metadata_dict.update({
                    "title": self._clean_metadata_value(reader.metadata.get("/Title")),
                    "author": self._clean_metadata_value(reader.metadata.get("/Author")),
                    "subject": self._clean_metadata_value(reader.metadata.get("/Subject")),
                    "creator": self._clean_metadata_value(reader.metadata.get("/Creator")),
                })
            
            return PDFMetadata(**metadata_dict)
            
        except Exception as e:
            raise PDFProcessingError(f"Failed to extract PDF metadata: {str(e)}")
    
    def _clean_metadata_value(self, value: Optional[str]) -> Optional[str]:
        """Clean and normalize metadata values."""
        if not value:
            return None
        
        # Convert to string and strip whitespace
        cleaned = str(value).strip()
        
        # Return None if empty after cleaning
        return cleaned if cleaned else None