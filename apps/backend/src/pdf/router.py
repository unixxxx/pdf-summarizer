import hashlib
import time
from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUser
from ..database.models import Document, Summary
from ..database.session import get_db
from ..embeddings.dependencies import EmbeddingsServiceDep
from ..storage.dependencies import StorageServiceDep
from ..summarization.dependencies import SummarizerServiceDep
from .dependencies import PDFServiceDep, ValidatedPDFFile
from .schemas import (
    PDFSummaryHistoryItem,
    PDFSummaryResponse,
    PDFTextExtractionResponse,
)

router = APIRouter(
    prefix="/pdf",
    tags=["PDF Operations"],
    responses={
        400: {"description": "Bad request"},
        413: {"description": "File too large"},
        422: {"description": "Unprocessable entity"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/extract-text",
    response_model=PDFTextExtractionResponse,
    summary="Extract text from PDF",
    description="Extract all text content from a PDF file",
)
async def extract_pdf_text(
    file: ValidatedPDFFile,
    pdf_service: PDFServiceDep,
    current_user: CurrentUser,
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
        text=text, metadata=metadata, extraction_time=extraction_time
    )


@router.post(
    "/summarize",
    response_model=PDFSummaryResponse,
    summary="Summarize PDF content",
    description="Upload a PDF file and get an AI-generated summary",
)
async def summarize_pdf(
    file: ValidatedPDFFile,
    pdf_service: PDFServiceDep,
    summarizer: SummarizerServiceDep,
    embeddings_service: EmbeddingsServiceDep,
    storage_service: StorageServiceDep,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    max_length: Annotated[
        Optional[int],
        Query(description="Maximum summary length in words", ge=50, le=2000),
    ] = 500,
    format: Annotated[
        Optional[str],
        Query(
            description="Summary format: 'paragraph', 'bullets', or 'keypoints'",
            pattern="^(paragraph|bullets|keypoints)$"
        ),
    ] = "paragraph",
    instructions: Annotated[
        Optional[str],
        Query(description="Additional instructions for summary generation", max_length=500),
    ] = None,
    include_metadata: Annotated[
        bool, Query(description="Include PDF metadata in response")
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
    summary_result = await summarizer.summarize_pdf(text, max_length, format, instructions)

    # Calculate processing time
    processing_time = time.time() - start_time

    # Calculate file hash
    file_hash = hashlib.sha256(pdf_content).hexdigest()

    # Check if document already exists
    existing_doc = await db.execute(
        select(Document).where(
            Document.user_id == current_user.id, Document.file_hash == file_hash
        )
    )
    document = existing_doc.scalar_one_or_none()

    # Create document if it doesn't exist
    if not document:
        # Store the PDF file
        storage_path = await storage_service.store_file(
            content=pdf_content,
            user_id=str(current_user.id),
            file_type='pdf',
            original_filename=file.filename,
        )
        
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_size=len(pdf_content),
            file_hash=file_hash,
            page_count=metadata.pages if metadata else None,
            storage_path=storage_path,
        )
        db.add(document)
        await db.flush()
        
        # Generate embeddings for the document
        await embeddings_service.create_document_embeddings(
            document_id=str(document.id),
            text=text,
            db=db,
        )

    # Calculate word counts
    original_words = len(text.split())
    summary_words = summary_result["stats"].get(
        "summary_words", len(summary_result["summary"].split())
    )

    # Create summary record
    summary = Summary(
        user_id=current_user.id,
        document_id=document.id,
        summary_text=summary_result["summary"],
        original_word_count=original_words,
        summary_word_count=summary_words,
        compression_ratio=original_words / summary_words if summary_words > 0 else 0,
        processing_time=processing_time,
        llm_provider=summarizer.provider_name,
        llm_model=summarizer.model_name,
    )
    db.add(summary)
    await db.commit()

    return PDFSummaryResponse(
        summary=summary_result["summary"],
        metadata=metadata,
        processing_time=processing_time,
        summary_stats=summary_result["stats"],
    )


@router.get(
    "/history",
    response_model=List[PDFSummaryHistoryItem],
    summary="Get PDF summary history",
    description="Get all PDF summaries for the current user",
)
async def get_pdf_history(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> List[PDFSummaryHistoryItem]:
    """Get user's PDF summary history."""
    # Query summaries with joined document data
    result = await db.execute(
        select(Summary, Document)
        .join(Document, Summary.document_id == Document.id)
        .where(Summary.user_id == current_user.id)
        .order_by(desc(Summary.created_at))
    )

    # Transform results to response schema
    history_items = []
    for summary, document in result:
        history_items.append(
            PDFSummaryHistoryItem(
                id=summary.id,
                document_id=document.id,
                fileName=document.filename,
                fileSize=document.file_size,
                summary=summary.summary_text,
                original_word_count=summary.original_word_count,
                wordCount=summary.summary_word_count,
                compression_ratio=summary.compression_ratio,
                processingTime=summary.processing_time,
                llm_provider=summary.llm_provider,
                llm_model=summary.llm_model,
                createdAt=summary.created_at,
            )
        )

    return history_items


@router.delete(
    "/history/{summary_id}",
    summary="Delete document and all associated data",
    description="Delete a document along with its summary, embeddings, and all chat sessions",
)
async def delete_pdf_summary(
    summary_id: UUID,
    storage_service: StorageServiceDep,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a PDF summary and its associated document from history."""
    # Find the summary with its document
    result = await db.execute(
        select(Summary, Document)
        .join(Document, Summary.document_id == Document.id)
        .where(
            Summary.id == summary_id, 
            Summary.user_id == current_user.id
        )
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    summary, document = row

    # Delete the file from storage if it exists
    if document.storage_path:
        try:
            await storage_service.delete_file(document.storage_path)
        except Exception as e:
            # Log error but don't fail the deletion
            print(f"Failed to delete file from storage: {e}")

    # Delete the document (this will cascade delete summaries, chunks, and chats)
    await db.delete(document)
    await db.commit()

    return {"message": "Document and all associated data deleted successfully"}
