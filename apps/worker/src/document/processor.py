"""Document processing tasks for arq worker."""

import asyncio
import io
from typing import Any

import aioboto3
import PyPDF2
from shared.models import Document, DocumentStatus
from sqlalchemy import select

from ..common.config import get_settings
from ..common.cpu_monitor import cpu_monitor
from ..common.database import get_db_session
from ..common.logger import logger
from ..common.progress_calculator import ProcessingStages
from ..common.redis_progress_reporter import ProgressStage
from ..common.staged_progress_reporter import StagedProgressReporter as ProgressReporter

settings = get_settings()


async def extract_pdf_text(file_content: bytes) -> tuple[str, int]:
    """
    Extract text and page count from PDF content.
    
    Returns:
        Tuple of (extracted_text, page_count)
    """
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    page_count = len(pdf_reader.pages)
    
    text_parts = []
    for page_num, page in enumerate(pdf_reader.pages):
        # Check CPU and add delay if needed
        if page_num % 5 == 0 and page_num > 0:  # Every 5 pages
            if cpu_monitor.should_pause():
                await cpu_monitor.wait_for_cpu()
            else:
                # Add small delay to prevent CPU spike
                delay = cpu_monitor.get_throttle_delay(0.05)
                await asyncio.sleep(delay)
        
        text = page.extract_text()
        if text:
            text_parts.append(text)
    
    return "\n\n".join(text_parts), page_count


async def download_file(storage_path: str) -> bytes:
    """Download file from S3 storage."""
    if not settings.s3_bucket_name:
        raise ValueError("S3_BUCKET_NAME not configured")
    
    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_default_region
    )
    
    try:
        async with session.client(
            's3',
            endpoint_url=settings.s3_endpoint_url
        ) as s3_client:
            logger.info(
                "Downloading file from S3",
                bucket=settings.s3_bucket_name,
                key=storage_path
            )
            
            response = await s3_client.get_object(
                Bucket=settings.s3_bucket_name,
                Key=storage_path
            )
            
            content = await response['Body'].read()
            
            logger.info(
                "File downloaded successfully",
                bucket=settings.s3_bucket_name,
                key=storage_path,
                size=len(content)
            )
            
            return content
            
    except Exception as e:
        logger.error(
            "Failed to download file from S3",
            bucket=settings.s3_bucket_name,
            key=storage_path,
            error=str(e)
        )
        raise FileNotFoundError(f"File not found: {storage_path}")


async def process_document(ctx: dict, document_id: str, user_id: str) -> dict[str, Any]:
    """
    Main document processing task.
    
    Args:
        ctx: arq context with job information
        document_id: UUID of the document to process
        user_id: UUID of the user who owns the document
        
    Returns:
        Dict with processing results
    """
    job_id = ctx.get("job_id", f"doc:{document_id}")
    
    # Get Redis connection from context
    redis = ctx.get('redis')
    
    async with ProgressReporter(
        redis=redis,
        job_id=job_id,
        document_id=document_id,
        user_id=user_id,
        current_stage=ProcessingStages.TEXT_EXTRACTION
    ) as reporter:
        
        try:
            # 1. Fetch document from database (5%)
            await reporter.report_progress(
                ProgressStage.DOWNLOADING, 
                0.05, 
                "Fetching document from database"
            )
            
            async with get_db_session() as db:
                result = await db.execute(
                    select(Document).where(Document.id == document_id)
                )
                document = result.scalar_one_or_none()
                
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                # Log for debugging
                logger.info(
                    "Document ownership check",
                    document_id=document_id,
                    document_user_id=str(document.user_id),
                    requested_user_id=str(user_id),
                    match=str(document.user_id) == str(user_id)
                )
                
                if str(document.user_id) != str(user_id):
                    raise ValueError(f"Document {document_id} does not belong to user {user_id}")
                
                # Update status to processing
                document.status = DocumentStatus.PROCESSING
                await db.commit()
            
            # 2. Download file content (15%)
            await reporter.report_progress(
                ProgressStage.DOWNLOADING, 
                0.15, 
                "Downloading file content"
            )
            
            file_content = await download_file(document.storage_path)
            
            # 3. Extract text (35%)
            await reporter.report_progress(
                ProgressStage.EXTRACTING, 
                0.25, 
                "Extracting text from PDF"
            )
            
            # Only extract if not already done
            if not document.extracted_text:
                extracted_text, page_count = await extract_pdf_text(file_content)
                word_count = len(extracted_text.split())
                
                async with get_db_session() as db:
                    # Re-fetch document to avoid stale state
                    result = await db.execute(
                        select(Document).where(Document.id == document_id)
                    )
                    document = result.scalar_one()
                    
                    document.extracted_text = extracted_text
                    document.page_count = page_count
                    document.word_count = word_count
                    await db.commit()
                
                await reporter.report_progress(
                    ProgressStage.EXTRACTING, 
                    0.35, 
                    f"Extracted {word_count} words from {page_count} pages"
                )
            else:
                extracted_text = document.extracted_text
                await reporter.report_progress(
                    ProgressStage.EXTRACTING, 
                    0.35, 
                    "Text already extracted"
                )
            
            # 4. Mark as ready for further processing (40%)
            await reporter.report_progress(
                ProgressStage.STORING, 
                0.40, 
                "Document ready for embedding generation"
            )
            
            # Enqueue embedding generation task
            from arq import create_pool
            from arq.connections import RedisSettings
            redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
            
            await redis.enqueue_job(
                "generate_document_embeddings",
                document_id,
                user_id,
                _job_id=f"embed:{document_id}",
                _defer_by=1,  # Start after 1 second
                _queue_name="doculearn:queue"
            )
            
            await redis.close()
            
            # Update document status
            async with get_db_session() as db:
                result = await db.execute(
                    select(Document).where(Document.id == document_id)
                )
                document = result.scalar_one()
                document.status = DocumentStatus.PROCESSING
                await db.commit()
            
            await reporter.report_progress(
                ProgressStage.STORING, 
                0.40, 
                "Text extraction completed, embedding generation queued"
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "word_count": document.word_count,
                "page_count": document.page_count,
                "next_task": "generate_document_embeddings"
            }
            
        except Exception as e:
            logger.error(
                "Document processing failed",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )
            
            # Update document status to failed
            try:
                async with get_db_session() as db:
                    result = await db.execute(
                        select(Document).where(Document.id == document_id)
                    )
                    document = result.scalar_one_or_none()
                    if document:
                        document.status = DocumentStatus.FAILED
                        document.error_message = str(e)
                        await db.commit()
            except Exception as db_error:
                logger.error(
                    "Failed to update document status",
                    document_id=document_id,
                    error=str(db_error)
                )
            
            await reporter.report_error(str(e))
            raise