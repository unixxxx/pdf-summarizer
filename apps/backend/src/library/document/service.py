"""Document domain service following DDD principles."""

import hashlib
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...common.exceptions import NotFoundException
from ...database.models import Document, DocumentStatus, Folder


class DocumentService:
    """Service for managing document lifecycle."""

    async def create_document(
        self,
        user_id: UUID,
        filename: str,
        content: bytes,
        file_size: int,
        storage_path: str | None,
        db: AsyncSession,
    ) -> tuple[Document, bool]:
        """
        Create a new document or return existing one.

        Returns:
            Tuple of (document, is_new) where is_new indicates if document was created
        """
        # Calculate content hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()

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
            return existing_doc, False

        # Create new document
        document = Document(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            file_hash=file_hash,
            storage_path=storage_path,
        )

        db.add(document)
        await db.flush()  # Get the ID without committing

        return document, True

    async def get_document(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> Document:
        """Get a document by ID, ensuring user ownership."""
        from sqlalchemy.orm import selectinload

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

        return document

    async def get_document_by_id(
        self,
        document_id: UUID,
        db: AsyncSession,
    ) -> Document | None:
        """Get a document by ID without user check (for internal use)."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def update_document_content(
        self,
        document_id: UUID,
        extracted_text: str,
        word_count: int,
        db: AsyncSession,
    ) -> Document:
        """Update document with extracted content."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException("Document not found")

        document.extracted_text = extracted_text
        document.word_count = word_count

        await db.flush()
        return document

    # Note: This method is deprecated in favor of using the presigned URL upload flow
    # async def create_text_document(
    #     self,
    #     user_id: UUID,
    #     data: TextDocumentCreate,
    #     db: AsyncSession,
    # ) -> Document:
    #     """Create a document from text content."""
    #     # Generate a unique filename
    #     filename = f"{data.title}.txt"

    #     # Calculate file size and hash
    #     content_bytes = data.content.encode("utf-8")
    #     file_size = len(content_bytes)
    #     file_hash = hashlib.sha256(content_bytes).hexdigest()

    #     # Check for duplicate
    #     result = await db.execute(
    #         select(Document).where(
    #             Document.user_id == user_id,
    #             Document.file_hash == file_hash,
    #             Document.archived_at.is_(None),
    #         )
    #     )
    #     if result.scalar_one_or_none():
    #         raise ValueError("Document with this content already exists")

    #     # Store text file in S3/storage
    #     storage_key, stored_size = await self.storage_service.store_text_as_file(
    #         text=data.content,
    #         user_id=str(user_id),
    #         title=data.title,
    #     )

    #     # Count words
    #     word_count = len(data.content.split())

    #     # Create document
    #     document = Document(
    #         user_id=user_id,
    #         filename=filename,
    #         file_size=file_size,
    #         file_hash=file_hash,
    #         folder_id=data.folder_id,
    #         storage_path=storage_key,
    #         extracted_text=data.content,
    #         word_count=word_count,
    #         status=DocumentStatus.COMPLETED,
    #     )

    #     db.add(document)
    #     await db.flush()
    #     return document

    async def delete_document(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Soft delete a document."""
        document = await self.get_document(document_id, user_id, db)
        document.archived_at = func.now()
        await db.flush()

    async def list_user_documents(
        self,
        user_id: UUID,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        """List documents for a user with pagination."""
        result = await db.execute(
            select(Document)
            .where(
                Document.user_id == user_id,
                Document.archived_at.is_(None),
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

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
                (existing_doc.folder_id == folder_id) if folder_id 
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

    async def update_document_processing_complete(
        self,
        document_id: UUID,
        extracted_text: str,
        word_count: int,
        page_count: int | None,
        db: AsyncSession,
    ) -> Document:
        """Update document when processing is complete."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException("Document not found")

        document.extracted_text = extracted_text
        document.word_count = word_count
        document.page_count = page_count
        document.status = DocumentStatus.COMPLETED

        await db.flush()
        return document

    async def update_document_status(
        self,
        document_id: UUID,
        status: str,
        db: AsyncSession,
    ) -> Document:
        """Update document status."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException("Document not found")

        # Map string status to enum
        status_map = {
            "uploading": DocumentStatus.UPLOADING,
            "processing": DocumentStatus.PROCESSING,
            "completed": DocumentStatus.COMPLETED,
            "failed": DocumentStatus.FAILED,
        }
        
        if status not in status_map:
            raise ValueError(f"Invalid status: {status}")
            
        document.status = status_map[status]
        await db.flush()
        return document

    async def update_document_failed(
        self,
        document_id: UUID,
        db: AsyncSession,
    ) -> Document:
        """Mark document as failed."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise NotFoundException("Document not found")

        document.status = DocumentStatus.FAILED

        await db.flush()
        return document
