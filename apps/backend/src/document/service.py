"""Document domain service following DDD principles."""

from uuid import UUID

from fastapi.responses import Response
from shared.models import Document, DocumentStatus, Folder, Summary
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundException
from ..tag.schemas import TagResponse
from .export_service import DocumentExporter
from .schemas import (
    DocumentDetailResponse,
    DocumentListItemResponse,
    DocumentsListResponse,
    ExportFormat,
)


class DocumentService:
    """Service for managing document lifecycle."""

    async def get_document(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> DocumentDetailResponse:
        """Get a document by ID, ensuring user ownership."""
        from sqlalchemy.orm import selectinload

        from ..tag.schemas import TagResponse

        result = await db.execute(
            select(Document)
            .options(selectinload(Document.tags))
            .where(
                Document.id == document_id,
                Document.user_id == user_id,
                Document.archived_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException("Document not found")

        # Map tags to TagResponse
        tag_responses = [TagResponse.model_validate(tag) for tag in document.tags]

        return DocumentDetailResponse(
            id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            file_hash=document.file_hash,
            status=document.status,
            created_at=document.created_at,
            storage_path=document.storage_path,
            extracted_text=document.extracted_text,
            word_count=document.word_count,
            folder_id=document.folder_id,
            error_message=document.error_message,
            tags=tag_responses,
        )

    async def get_document_by_id(
        self,
        document_id: UUID,
        db: AsyncSession,
    ) -> Document | None:
        """Get a document by ID without user check (for internal use)."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def delete_document(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Soft delete a document."""
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
                Document.archived_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException("Document not found")

        document.archived_at = func.now()
        await db.flush()

    async def create_document_for_upload(
        self,
        user_id: UUID,
        filename: str,
        file_size: int,
        file_hash: str,
        storage_path: str,
        folder_id: UUID | None,
        db: AsyncSession,
    ) -> Document:
        """Create a document record for an upload in progress."""
        # Check for existing document with same hash (excluding archived)
        result = await db.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.file_hash == file_hash,
                Document.archived_at.is_(None),
            )
        )
        existing_doc = result.scalar_one_or_none()

        if existing_doc:
            # Check if it's in the same folder or both are unfiled
            same_location = (
                (existing_doc.folder_id == folder_id)
                if folder_id
                else (existing_doc.folder_id is None)
            )

            if same_location:
                # Document with same content exists in the same location
                folder_name = "unfiled"
                if folder_id and existing_doc.folder_id:
                    # Get folder name for better error message
                    folder_result = await db.execute(
                        select(Folder).where(Folder.id == folder_id)
                    )
                    folder = folder_result.scalar_one_or_none()
                    if folder:
                        folder_name = folder.name

                raise ValueError(
                    f"A file with the same content already exists in {folder_name}: {existing_doc.filename}"
                )

            # If document exists in a different location, allow the upload
            # This enables users to have the same file in multiple folders

        # Create new document with uploading status
        document = Document(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            file_hash=file_hash,
            storage_path=storage_path,
            folder_id=folder_id,
            status=DocumentStatus.UPLOADING,
        )

        db.add(document)
        await db.flush()

        return document

    async def update_document_upload_complete(
        self,
        document_id: UUID,
        db: AsyncSession,
    ) -> Document:
        """Update document when upload is complete."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException("Document not found")

        # Storage path was already set during creation
        document.status = DocumentStatus.PROCESSING

        await db.flush()
        return document

    async def get_documents(
        self,
        user_id: UUID,
        db: AsyncSession,
        folder_id: UUID | None = None,
        unfiled: bool = False,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DocumentsListResponse:
        """
        Get documents with filters and pagination.

        Returns:
            DocumentsListResponse with paginated documents
        """
        from sqlalchemy.orm import selectinload

        # Build base query
        query = (
            select(Document)
            .options(selectinload(Document.tags))
            .where(
                Document.user_id == user_id,
                Document.archived_at.is_(None),  # Exclude archived documents
            )
        )

        # Apply folder filter
        if folder_id:
            query = query.where(Document.folder_id == folder_id)
        elif unfiled:
            # Get documents not in any folder
            query = query.where(Document.folder_id.is_(None))

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Document.filename.ilike(search_term))
                | (Document.extracted_text.ilike(search_term))
            )

        # Order by creation date
        query = query.order_by(Document.created_at.desc())

        # Get total count before pagination
        count_query = (
            select(func.count(Document.id))
            .select_from(Document)
            .where(Document.user_id == user_id, Document.archived_at.is_(None))
        )

        # Apply same filters to count query
        if folder_id:
            count_query = count_query.where(Document.folder_id == folder_id)
        elif unfiled:
            count_query = count_query.where(Document.folder_id.is_(None))

        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                (Document.filename.ilike(search_term))
                | (Document.extracted_text.ilike(search_term))
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        documents = result.scalars().all()

        # Transform to response
        items = []
        for document in documents:
            items.append(
                DocumentListItemResponse(
                    id=document.id,
                    document_id=document.id,
                    filename=document.filename,
                    file_size=document.file_size,
                    summary=(
                        document.extracted_text[:200] + "..."
                        if document.extracted_text
                        else ""
                    ),
                    created_at=document.created_at,
                    word_count=document.word_count or 0,
                    tags=[
                        TagResponse(
                            id=tag.id,
                            name=tag.name,
                            slug=tag.slug,
                            color=tag.color,
                        )
                        for tag in document.tags
                    ],
                    status=document.status,
                    folder_id=document.folder_id,
                    error_message=document.error_message,
                )
            )

        return DocumentsListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    async def export_document(
        self,
        document_id: UUID,
        user_id: UUID,
        format: ExportFormat,
        db: AsyncSession,
    ) -> Response:
        """Export a document in the specified format."""
        # Get document with optional summary
        query = (
            select(Document, Summary)
            .outerjoin(Summary, Document.id == Summary.document_id)
            .where(
                Document.id == document_id,
                Document.user_id == user_id,
                Document.archived_at.is_(None),
            )
        )

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise NotFoundException("Document not found")

        document, summary = row

        # Get document content
        content = document.extracted_text or "No content available"

        # Prepare metadata
        metadata = {
            "filename": document.filename,
            "file_size": document.file_size,
            "created_at": document.created_at,
        }

        # Get summary text if available
        summary_text = summary.summary_text if summary else None

        # Export based on format
        exporter = DocumentExporter()

        if format == ExportFormat.MARKDOWN:
            content_str = exporter.export_document_as_markdown(
                content=content,
                metadata=metadata,
                summary=summary_text,
            )
            filename = f"{document.filename.rsplit('.', 1)[0]}.md"
            media_type = "text/markdown"

        elif format == ExportFormat.TEXT:
            content_str = exporter.export_document_as_text(
                content=content,
                metadata=metadata,
                summary=summary_text,
            )
            filename = f"{document.filename.rsplit('.', 1)[0]}.txt"
            media_type = "text/plain"

        elif format == ExportFormat.PDF:
            pdf_content = await exporter.export_document_as_pdf(
                content=content,
                metadata=metadata,
                summary=summary_text,
            )

            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{document.filename.rsplit(".", 1)[0]}.pdf"'
                },
            )

        # Return text-based formats
        return Response(
            content=content_str,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    async def retry_document_processing(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> dict:
        """Retry processing for a failed document."""
        from arq import create_pool
        from arq.connections import RedisSettings

        from ..config import get_settings
        
        settings = get_settings()
        
        # Get document and verify ownership
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
                Document.archived_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundException("Document not found")
        
        # Check if document is in failed state
        if document.status != DocumentStatus.FAILED:
            raise ValueError(f"Document is not in failed state. Current status: {document.status}")
        
        # Reset document status and clear error message
        document.status = DocumentStatus.PROCESSING
        document.error_message = None
        document.processed_at = None
        
        await db.commit()
        
        # Enqueue document processing job
        redis_settings = RedisSettings.from_dsn(settings.redis_url)
        redis = await create_pool(redis_settings)
        
        try:
            # Generate a unique job ID for retry attempts
            import time
            retry_job_id = f"doc:{document_id}:retry:{int(time.time())}"
            
            job = await redis.enqueue_job(
                "process_document",  # Function name in worker
                str(document_id),
                str(user_id),
                _job_id=retry_job_id,
                _queue_name="doculearn:queue",
            )
            
            # If job is None, it means a job with this ID already exists
            if job is None:
                # Try again with a more unique ID
                retry_job_id = f"doc:{document_id}:retry:{int(time.time()*1000)}"
                job = await redis.enqueue_job(
                    "process_document",
                    str(document_id),
                    str(user_id),
                    _job_id=retry_job_id,
                    _queue_name="doculearn:queue",
                )
            
            return {
                "document_id": str(document_id),
                "job_id": retry_job_id if job else "retry_queued",
                "status": "processing_queued",
                "message": "Document processing retry has been queued"
            }
        finally:
            await redis.close()
