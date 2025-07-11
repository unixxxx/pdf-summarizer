"""Upload service for handling file upload logic."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import (
    BadRequestException,
    NotFoundException,
    StorageError,
    ValidationError,
)
from ..config import Settings
from ..document.service import DocumentService
from ..folder.service import FolderService
from ..storage.service import StorageService
from .schemas import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
)

logger = logging.getLogger(__name__)


class UploadService:
    """Service for handling file uploads."""

    ALLOWED_CONTENT_TYPES = [
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

    def __init__(
        self,
        storage_service: StorageService,
        document_service: DocumentService,
        folder_service: FolderService,
        settings: Settings,
    ):
        self.storage_service = storage_service
        self.document_service = document_service
        self.folder_service = folder_service
        self.settings = settings

    async def create_presigned_upload_url(
        self,
        request: PresignedUrlRequest,
        user_id: UUID,
        db: AsyncSession,
    ) -> PresignedUrlResponse:
        """Create presigned URL and document record for upload."""
        # Validate file size
        if request.file_size > self.MAX_FILE_SIZE:
            raise ValidationError(
                field="file_size",
                detail=f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE // (1024 * 1024)}MB. "
                f"Your file is {request.file_size // (1024 * 1024)}MB."
            )
        
        # Validate content type
        if request.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                field="content_type",
                detail=f"Unsupported file type: {request.content_type}. "
                f"Allowed types: {', '.join(self.ALLOWED_CONTENT_TYPES)}"
            )

        # Get folder name
        folder_name = await self._get_folder_name(request.folder_id, user_id, db)

        # Generate storage key
        storage_key = self._generate_storage_key(
            user_id=user_id,
            folder_name=folder_name,
            filename=request.filename,
        )

        # Create document record
        folder_id = UUID(request.folder_id) if request.folder_id else None
        try:
            document = await self.document_service.create_document_for_upload(
                user_id=user_id,
                filename=request.filename,
                file_size=request.file_size,
                file_hash=request.file_hash,
                storage_path=storage_key,
                folder_id=folder_id,
                db=db,
            )
        except ValueError as e:
            # Convert ValueError from document service to BadRequestException
            raise BadRequestException(detail=str(e))

        await db.commit()

        return await self._create_presigned_post_response(
            document=document,
            storage_key=storage_key,
        )

    async def complete_upload(
        self,
        request: CompleteUploadRequest,
        user_id: UUID,
        db: AsyncSession,
    ) -> CompleteUploadResponse:
        """Complete upload and queue processing tasks."""
        # Verify document ownership
        document = await self.document_service.get_document(
            document_id=UUID(request.document_id),
            user_id=user_id,
            db=db,
        )

        # Update document status
        document = await self.document_service.update_document_upload_complete(
            document_id=UUID(request.document_id),
            db=db,
        )

        await db.commit()

        logger.info(
            f"Document {document.id} marked as upload complete, status: {document.status}"
        )

        # Automatically enqueue document processing
        redis_settings = RedisSettings.from_dsn(self.settings.redis_url)
        redis = await create_pool(redis_settings)
        
        try:
            job = await redis.enqueue_job(
                "process_document",  # Function name in worker
                str(document.id),
                str(user_id),
                _job_id=f"doc:{document.id}",
                _queue_name="doculearn:queue",
            )
            
            logger.info(
                f"Document processing job queued for document {document.id}, job_id: {job.job_id}"
            )
            
            return CompleteUploadResponse(
                document_id=str(document.id),
                status="processing",
                stage="queued",
                progress=0,
            )
        finally:
            await redis.close()

    async def _get_folder_name(
        self,
        folder_id: str | None,
        user_id: UUID,
        db: AsyncSession,
    ) -> str:
        """Get folder name or return 'unfiled'."""
        if not folder_id:
            return "unfiled"

        # Get user object first
        from shared.models import User

        user = await db.get(User, user_id)
        if not user:
            return "unfiled"

        try:
            folder = await self.folder_service.get_folder(
                db=db,
                user=user,
                folder_id=UUID(folder_id),
            )
            return folder.name
        except Exception:
            # If folder not found or any error, use unfiled
            return "unfiled"

    def _generate_storage_key(
        self,
        user_id: UUID,
        folder_name: str,
        filename: str,
    ) -> str:
        """Generate S3 storage key."""
        # Sanitize folder name for S3 key
        safe_folder_name = folder_name.replace("/", "-").replace("\\", "-")
        return f"{user_id}/{safe_folder_name}/{filename}"

    async def _create_presigned_post_response(
        self,
        document,
        storage_key: str,
    ) -> PresignedUrlResponse:
        """Create response for presigned POST upload."""
        if not self.settings.s3_enabled:
            raise StorageError("S3 storage is not configured")

        upload_id = str(uuid4())
        
        # Generate presigned POST data
        presigned_post = await self.storage_service.create_presigned_post(
            key=storage_key,
            expires_in=3600,  # 1 hour
            max_size=self.MAX_FILE_SIZE,
        )

        return PresignedUrlResponse(
            upload_id=upload_id,
            document_id=str(document.id),
            upload_url=presigned_post["url"],
            fields=presigned_post["fields"],
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    async def trigger_document_processing(
        self,
        document_id: UUID,
        user_id: UUID,
        orchestrator,  # Optional, for backward compatibility
        db: AsyncSession,
    ) -> dict:
        """Trigger document processing for an uploaded document."""
        try:
            # Get document to verify ownership
            document = await self.document_service.get_document(
                document_id=document_id,
                user_id=user_id,
                db=db,
            )
            
            # Check if document needs processing
            if document.status == "completed":
                return {
                    "document_id": str(document_id),
                    "status": "already_processed",
                    "message": "Document has already been processed"
                }
            
            # Update status to processing
            await self.document_service.update_document_status(
                document_id=document_id,
                status="processing",
                db=db,
            )
            
            # Enqueue document processing job
            redis_settings = RedisSettings.from_dsn(self.settings.redis_url)
            redis = await create_pool(redis_settings)
            
            try:
                job = await redis.enqueue_job(
                    "process_document",  # Function name in worker
                    str(document_id),
                    str(user_id),
                    _job_id=f"doc:{document_id}",
                    _queue_name="doculearn:queue",
                )
                
                await db.commit()
                
                return {
                    "document_id": str(document_id),
                    "job_id": job.job_id,
                    "status": "processing_queued",
                    "message": "Document processing has been queued"
                }
            finally:
                await redis.close()
            
        except NotFoundException:
            raise NotFoundException("Document not found or access denied")
        except Exception as e:
            # Update status to failed
            await self.document_service.update_document_status(
                document_id=document_id,
                status="failed",
                db=db,
            )
            await db.commit()
            
            logger.error(f"Failed to process document {document_id}: {str(e)}")
            raise
