"""Upload service for handling file upload logic."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import StorageError, ValidationError
from ..config import Settings
from ..library.document.service import DocumentService
from ..library.folder.service import FolderService
from ..storage.service import StorageService
from .schemas import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
    UploadMethod,
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
    
    MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, storage_service: StorageService, settings: Settings):
        self.storage_service = storage_service
        self.settings = settings
        self.document_service = DocumentService()
        self.folder_service = FolderService()
    
    async def create_presigned_upload_url(
        self,
        request: PresignedUrlRequest,
        user_id: UUID,
        db: AsyncSession,
    ) -> PresignedUrlResponse:
        """Create presigned URL and document record for upload."""
        # Validate content type
        if request.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                f"Unsupported file type: {request.content_type}. "
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
        document = await self.document_service.create_document_for_upload(
            user_id=user_id,
            filename=request.filename,
            file_size=request.file_size,
            file_hash=request.file_hash,
            storage_path=storage_key,
            folder_id=folder_id,
            db=db,
        )
        
        await db.commit()
        
        # Determine upload method
        use_multipart = (
            request.upload_method == UploadMethod.PRESIGNED_URL or 
            request.file_size > self.MULTIPART_THRESHOLD
        )
        
        if use_multipart:
            return await self._create_multipart_response(
                document=document,
                storage_key=storage_key,
            )
        else:
            return await self._create_presigned_post_response(
                document=document,
                storage_key=storage_key,
                content_type=request.content_type,
                file_size=request.file_size,
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
        
        logger.info(f"Document {document.id} marked as upload complete, status: {document.status}")
        
        # Processing can be triggered via POST /upload/process/{document_id}
        
        return CompleteUploadResponse(
            document_id=str(document.id),
            status="uploaded",
            stage="complete",
            progress=100,
        )
    
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
        from ..database.models import User
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
    
    async def _create_multipart_response(
        self,
        document,
        storage_key: str,
    ) -> PresignedUrlResponse:
        """Create response for multipart upload."""
        if not self.settings.s3_enabled:
            raise StorageError("S3 storage is not configured")
        
        upload_id = str(uuid4())
        
        return PresignedUrlResponse(
            upload_url="",  # Not used for multipart
            fields={},      # Not used for multipart
            upload_id=upload_id,
            document_id=str(document.id),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            method=UploadMethod.PRESIGNED_URL,
            bucket=self.settings.s3_bucket_name,
            key=storage_key,
            credentials={
                "region": self.settings.aws_default_region,
                "endpoint": self.settings.s3_endpoint_url or None,
                # In production, these would be temporary credentials from STS
                # For development, the frontend can use its own credentials
            }
        )
    
    async def _create_presigned_post_response(
        self,
        document,
        storage_key: str,
        content_type: str,
        file_size: int,
    ) -> PresignedUrlResponse:
        """Create response for presigned POST upload."""
        upload_id = str(uuid4())
        
        # Create presigned URL
        presigned_data = await self.storage_service.create_presigned_post(
            key=storage_key,
            content_type=content_type,
            max_size=file_size,
        )
        
        return PresignedUrlResponse(
            upload_url=presigned_data["url"],
            fields=presigned_data["fields"],
            upload_id=upload_id,
            document_id=str(document.id),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            method=UploadMethod.PRESIGNED_POST,
        )