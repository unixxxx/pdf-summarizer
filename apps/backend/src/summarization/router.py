"""Summarization router following FastAPI best practices."""

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..common.exceptions import NotFoundError, SummarizationError
from ..database.session import get_db
from ..document.dependencies import DocumentServiceDep
from ..document.pdf_utils import extract_text_from_pdf
from ..storage.dependencies import StorageServiceDep
from .dependencies import (
    LLMFactoryDep,
    SummarizationOrchestratorDep,
    SummaryServiceDep,
)
from .schemas import (
    CreateSummaryRequest,
    DocumentInfoResponse,
    SummaryResponse,
    SummaryStyle,
    TagResponse,
)

router = APIRouter(
    prefix="/summarization",
    tags=["Summarization"],
    responses={
        400: {"description": "Bad request"},
        404: {"description": "Resource not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable"},
    },
)


@router.post(
    "",
    response_model=SummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a summary",
    description="Create a summary for an existing document or raw text",
    responses={
        201: {"description": "Summary created successfully"},
        400: {"description": "Invalid request parameters"},
        404: {"description": "Document not found"},
    },
)
async def create_summary(
    request: CreateSummaryRequest,
    current_user: CurrentUserDep,
    orchestrator: SummarizationOrchestratorDep,
    llm_factory: LLMFactoryDep,
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """
    Create a summary for a document or text.
    
    Either `document_id` or `text` must be provided:
    - If `document_id` is provided, summarize an existing document
    - If `text` is provided, create a new document and summarize it (requires `filename`)
    """
    # Validate request
    if not request.document_id and not request.text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either document_id or text must be provided",
        )
    
    if request.text and not request.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required when providing raw text",
        )
    
    # Prepare options
    options = {
        "style": request.style.value,
        "max_length": request.max_length,
        "focus_areas": request.focus_areas,
        "custom_prompt": request.custom_prompt,
    }
    # Remove None values
    options = {k: v for k, v in options.items() if v is not None}
    
    try:
        # Summarize based on input type
        if request.document_id:
            summary = await orchestrator.summarize_document(
                document_id=request.document_id,
                user_id=current_user.id,
                options=options,
                db=db,
            )
            # Get document for response
            document = await orchestrator.document_service.get_document(
                document_id=request.document_id,
                user_id=current_user.id,
                db=db,
            )
        else:
            # Summarize text (creates new document)
            summary = await orchestrator.summarize_text(
                text=request.text,
                filename=request.filename,
                user_id=current_user.id,
                options=options,
                db=db,
            )
            # Get created document
            document = await orchestrator.document_service.get_document(
                document_id=summary.document_id,
                user_id=current_user.id,
                db=db,
            )
        
        # Refresh document to get tags before commit
        await db.refresh(document, ["tags"])
        
        await db.commit()
        
        # Get LLM info
        llm_info = llm_factory.get_provider_info()
        
        # Prepare response
        return SummaryResponse(
            id=summary.id,
            document_id=summary.document_id,
            content=summary.summary_text,
            word_count=summary.summary_word_count,
            processing_time=summary.processing_time,
            tags=[
                TagResponse(
                    id=tag.id,
                    name=tag.name,
                    slug=tag.slug,
                    color=tag.color,
                )
                for tag in (document.tags or [])
            ],
            document_info=DocumentInfoResponse(
                id=document.id,
                filename=document.filename,
                file_size=document.file_size,
                word_count=document.word_count,
                page_count=document.page_count,
                created_at=document.created_at.isoformat(),
            ),
            llm_provider=llm_info["provider"],
            llm_model=llm_info["model"],
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    except SummarizationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}",
        )


@router.post(
    "/upload",
    response_model=SummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and summarize a document",
    description="Upload a PDF or text file and get a summary in one operation",
    responses={
        201: {"description": "Document uploaded and summarized successfully"},
        400: {"description": "Invalid file type"},
        413: {"description": "File too large"},
    },
)
async def upload_and_summarize(
    current_user: CurrentUserDep,
    orchestrator: SummarizationOrchestratorDep,
    document_service: DocumentServiceDep,
    storage_service: StorageServiceDep,
    llm_factory: LLMFactoryDep,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(..., description="PDF or text file to summarize"),
    style: SummaryStyle = Form(
        SummaryStyle.BALANCED,
        description="Summary style"
    ),
    max_length: Optional[int] = Form(
        None,
        description="Maximum length in words",
        ge=50,
        le=5000
    ),
    focus_areas: Optional[str] = Form(
        None,
        description="Areas to focus on",
        max_length=500
    ),
    custom_prompt: Optional[str] = Form(
        None,
        description="Custom prompt modifier",
        max_length=1000
    ),
) -> SummaryResponse:
    """
    Upload a file and summarize it in one operation.
    
    Supported file types:
    - PDF files (application/pdf)
    - Text files (text/plain)
    """
    # Validate file type
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type: {file.content_type}. "
                "Only PDF and text files are supported."
            ),
        )
    
    # Validate file size (50MB limit)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit",
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.content_type == "application/pdf":
            # Extract text from PDF
            pdf_data = await extract_text_from_pdf(content)
            text = pdf_data["text"]
            metadata = pdf_data["metadata"]
        else:
            # Plain text file
            text = content.decode("utf-8")
            metadata = {}
        
        # Store file
        file_type = 'pdf' if file.content_type == 'application/pdf' else 'txt'
        storage_path = await storage_service.store_file(
            content=content,
            user_id=str(current_user.id),
            file_type=file_type,
            original_filename=file.filename,
        )
        
        # Create document
        document, _ = await document_service.create_document(
            user_id=current_user.id,
            filename=file.filename,
            content=content,
            file_size=len(content),
            storage_path=storage_path,
            db=db,
        )
        
        # Update with extracted text
        word_count = len(text.split())
        document = await document_service.update_document_content(
            document_id=document.id,
            extracted_text=text,
            word_count=word_count,
            db=db,
        )
        
        # Update page count if available
        if metadata.get("page_count"):
            document.page_count = metadata["page_count"]
            await db.flush()
        
        # Prepare summarization options
        options = {
            "style": style.value,
            "max_length": max_length,
            "focus_areas": focus_areas,
            "custom_prompt": custom_prompt,
        }
        options = {k: v for k, v in options.items() if v is not None}
        
        # Create summary
        summary = await orchestrator.summarize_document(
            document_id=document.id,
            user_id=current_user.id,
            options=options,
            db=db,
        )
        
        # Refresh document to get tags before commit
        await db.refresh(document, ["tags"])
        
        await db.commit()
        
        # Get LLM info
        llm_info = llm_factory.get_provider_info()
        
        return SummaryResponse(
            id=summary.id,
            document_id=summary.document_id,
            content=summary.summary_text,
            word_count=summary.summary_word_count,
            processing_time=summary.processing_time,
            tags=[
                TagResponse(
                    id=tag.id,
                    name=tag.name,
                    slug=tag.slug,
                    color=tag.color,
                )
                for tag in (document.tags or [])
            ],
            document_info=DocumentInfoResponse(
                id=document.id,
                filename=document.filename,
                file_size=document.file_size,
                word_count=document.word_count,
                page_count=document.page_count,
                created_at=document.created_at.isoformat(),
            ),
            llm_provider=llm_info["provider"],
            llm_model=llm_info["model"],
        )
        
    except Exception as e:
        # Clean up on error
        if 'document' in locals():
            await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}",
        )


@router.delete(
    "/{summary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete summary",
    description="Delete a summary (keeps the document)",
)
async def delete_summary(
    summary_id: UUID,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a summary while keeping the document."""
    # Import locally to avoid circular imports
    from sqlalchemy import select

    from ..database.models import Document, Summary
    
    # Verify ownership
    result = await db.execute(
        select(Summary)
        .join(Document, Summary.document_id == Document.id)
        .where(
            Summary.id == summary_id,
            Document.user_id == current_user.id,
        )
    )
    summary = result.scalar_one_or_none()
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found",
        )
    
    await db.delete(summary)
    await db.commit()


@router.get(
    "/info",
    summary="Get summarization service info",
    description="Get information about the summarization service configuration",
    responses={
        200: {"description": "Service information"},
    },
)
async def get_service_info(
    current_user: CurrentUserDep,  # noqa: ARG001 - Required for authentication
    summary_service: SummaryServiceDep,
    llm_factory: LLMFactoryDep,
) -> dict:
    """Get information about the summarization service."""
    service_info = summary_service.get_service_info()
    llm_info = llm_factory.get_provider_info()
    
    return {
        **service_info,
        "llm": llm_info,
        "supported_styles": [style.value for style in SummaryStyle],
        "max_file_size_mb": 50,
        "supported_file_types": ["application/pdf", "text/plain"],
    }