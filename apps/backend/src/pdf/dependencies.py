from fastapi import Depends, UploadFile, File
from typing import Annotated

from ..config import get_settings, Settings
from ..common.exceptions import InvalidFileTypeError
from .service import PDFService


def get_pdf_service(settings: Annotated[Settings, Depends(get_settings)]) -> PDFService:
    """Get PDF service instance."""
    return PDFService(settings)


async def validate_pdf_file(file: UploadFile = File(...)) -> UploadFile:
    """
    Validate that uploaded file is a PDF.
    
    Args:
        file: Uploaded file
        
    Returns:
        The validated file
        
    Raises:
        InvalidFileTypeError: If file is not a PDF
    """
    if not file.filename:
        raise InvalidFileTypeError("unknown")
    
    if not file.filename.lower().endswith('.pdf'):
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'unknown'
        raise InvalidFileTypeError(file_ext)
    
    # Check content type
    if file.content_type and file.content_type != 'application/pdf':
        raise InvalidFileTypeError(file.content_type)
    
    return file


# Type aliases for cleaner dependency injection
PDFServiceDep = Annotated[PDFService, Depends(get_pdf_service)]
ValidatedPDFFile = Annotated[UploadFile, Depends(validate_pdf_file)]