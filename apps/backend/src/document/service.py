"""Document domain service following DDD principles."""

import hashlib
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..database.models import Document


class DocumentService:
    """Service for managing document lifecycle."""
    
    async def create_document(
        self,
        user_id: UUID,
        filename: str,
        content: bytes,
        file_size: int,
        storage_path: Optional[str],
        db: AsyncSession,
    ) -> tuple[Document, bool]:
        """
        Create a new document or return existing one.
        
        Returns:
            Tuple of (document, is_new) where is_new indicates if document was created
        """
        # Calculate content hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Check for existing document with same hash (excluding trashed)
        result = await db.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.file_hash == file_hash,
                Document.deleted_at.is_(None),
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
                Document.deleted_at.is_(None),
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Document")
        
        return document
    
    async def update_document_content(
        self,
        document_id: UUID,
        extracted_text: str,
        word_count: int,
        db: AsyncSession,
    ) -> Document:
        """Update document with extracted content."""
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Document")
        
        document.extracted_text = extracted_text
        document.word_count = word_count
        
        await db.flush()
        return document
    
    async def delete_document(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Soft delete a document."""
        document = await self.get_document(document_id, user_id, db)
        document.deleted_at = func.now()
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
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()