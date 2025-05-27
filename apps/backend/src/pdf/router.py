from fastapi import APIRouter, Depends, Query
from typing import Annotated, Optional
import time

from ..config import get_settings, Settings
from .dependencies import PDFServiceDep, ValidatedPDFFile
from .schemas import PDFTextExtractionResponse, PDFSummaryResponse, PDFSummaryRequest
from .service import PDFService
from ..summarization.dependencies import SummarizerServiceDep
from ..summarization.service import SummarizerService

router = APIRouter(
    prefix="/pdf",
    tags=["PDF Operations"],
    responses={
        400: {"description": "Bad request"},
        413: {"description": "File too large"},
        422: {"description": "Unprocessable entity"},
        500: {"description": "Internal server error"},
    }
)


@router.post(
    "/extract-text",
    response_model=PDFTextExtractionResponse,
    summary="Extract text from PDF",
    description="Extract all text content from a PDF file"
)
async def extract_pdf_text(
    file: ValidatedPDFFile,
    pdf_service: PDFServiceDep,
) -> PDFTextExtractionResponse:
    """Extract text content from uploaded PDF file."""
    # Read file content
    pdf_content = await file.read()
    
    # Validate PDF
    await pdf_service.validate_pdf(pdf_content, file.filename)
    
    # Extract text
    text, extraction_time = await pdf_service.extract_text(pdf_content)
    
    # Extract metadata
    metadata = await pdf_service.extract_metadata(pdf_content, file.filename)
    
    return PDFTextExtractionResponse(
        text=text,
        metadata=metadata,
        extraction_time=extraction_time
    )


@router.post(
    "/summarize",
    response_model=PDFSummaryResponse,
    summary="Summarize PDF content",
    description="Upload a PDF file and get an AI-generated summary"
)
async def summarize_pdf(
    file: ValidatedPDFFile,
    pdf_service: PDFServiceDep,
    summarizer: SummarizerServiceDep,
    max_length: Annotated[
        Optional[int], 
        Query(
            description="Maximum summary length in words",
            ge=50,
            le=2000
        )
    ] = 500,
    include_metadata: Annotated[
        bool,
        Query(description="Include PDF metadata in response")
    ] = True,
) -> PDFSummaryResponse:
    """Generate a summary of uploaded PDF content."""
    start_time = time.time()
    
    # Read file content
    pdf_content = await file.read()
    
    # Validate PDF
    await pdf_service.validate_pdf(pdf_content, file.filename)
    
    # Extract text
    text, _ = await pdf_service.extract_text(pdf_content)
    
    # Extract metadata if requested
    metadata = None
    if include_metadata:
        metadata = await pdf_service.extract_metadata(pdf_content, file.filename)
    
    # Generate summary
    summary_result = await summarizer.summarize_pdf(text, max_length)
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    return PDFSummaryResponse(
        summary=summary_result["summary"],
        metadata=metadata,
        processing_time=processing_time,
        summary_stats=summary_result["stats"]
    )