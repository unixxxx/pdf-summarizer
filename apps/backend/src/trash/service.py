"""Service for managing trash functionality."""

import contextlib
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..common.exceptions import BadRequestException, NotFoundException
from ..database.models import Document, Folder, User, document_folders
from ..storage.service import StorageService
from .schemas import (
    EmptyTrashRequest,
    RestoreDocumentRequest,
    RestoreFolderRequest,
    TrashedDocument,
    TrashedFolderWithChildren,
    TrashStats,
)


class TrashService:
    """Service for managing trash operations."""

    def __init__(self, db: AsyncSession, storage_service: Optional[StorageService] = None):
        """Initialize trash service."""
        self.db = db
        self.storage_service = storage_service

    async def get_trash_stats(self, user: User) -> TrashStats:
        """Get statistics about user's trash."""
        # Count trashed documents
        doc_count_query = select(func.count(Document.id)).where(
            and_(
                Document.user_id == user.id,
                Document.deleted_at.isnot(None)
            )
        )
        doc_count_result = await self.db.execute(doc_count_query)
        total_documents = doc_count_result.scalar() or 0

        # Count trashed folders
        folder_count_query = select(func.count(Folder.id)).where(
            and_(
                Folder.user_id == user.id,
                Folder.deleted_at.isnot(None)
            )
        )
        folder_count_result = await self.db.execute(folder_count_query)
        total_folders = folder_count_result.scalar() or 0

        # Calculate total size
        size_query = select(func.sum(Document.file_size)).where(
            and_(
                Document.user_id == user.id,
                Document.deleted_at.isnot(None)
            )
        )
        size_result = await self.db.execute(size_query)
        total_size = size_result.scalar() or 0

        # Find oldest item
        oldest_doc_query = select(func.min(Document.deleted_at)).where(
            and_(
                Document.user_id == user.id,
                Document.deleted_at.isnot(None)
            )
        )
        oldest_doc_result = await self.db.execute(oldest_doc_query)
        oldest_doc = oldest_doc_result.scalar()

        oldest_folder_query = select(func.min(Folder.deleted_at)).where(
            and_(
                Folder.user_id == user.id,
                Folder.deleted_at.isnot(None)
            )
        )
        oldest_folder_result = await self.db.execute(oldest_folder_query)
        oldest_folder = oldest_folder_result.scalar()

        oldest_item_date = None
        if oldest_doc and oldest_folder:
            oldest_item_date = min(oldest_doc, oldest_folder)
        elif oldest_doc:
            oldest_item_date = oldest_doc
        elif oldest_folder:
            oldest_item_date = oldest_folder

        return TrashStats(
            total_documents=total_documents,
            total_folders=total_folders,
            total_size=total_size,
            oldest_item_date=oldest_item_date
        )

    async def get_trashed_documents(self, user: User) -> list[TrashedDocument]:
        """Get all trashed documents for a user."""
        query = (
            select(Document)
            .where(
                and_(
                    Document.user_id == user.id,
                    Document.deleted_at.isnot(None)
                )
            )
            .order_by(Document.deleted_at.desc())
        )
        result = await self.db.execute(query)
        documents = result.scalars().all()

        trashed_docs = []
        for doc in documents:
            # Get the folder it was in (if any)
            folder_query = (
                select(Folder)
                .join(document_folders)
                .where(
                    and_(
                        document_folders.c.document_id == doc.id,
                        Folder.deleted_at.is_(None)  # Only non-deleted folders
                    )
                )
            )
            folder_result = await self.db.execute(folder_query)
            folder = folder_result.scalar_one_or_none()

            trashed_docs.append(TrashedDocument(
                id=doc.id,
                name=doc.filename,
                deleted_at=doc.deleted_at,
                user_id=doc.user_id,
                file_size=doc.file_size,
                page_count=doc.page_count,
                folder_id=folder.id if folder else None,
                folder_name=folder.name if folder else None
            ))

        return trashed_docs

    async def get_trashed_folders(self, user: User) -> list[TrashedFolderWithChildren]:
        """Get all trashed folders in a tree structure."""
        # Get all trashed folders
        query = (
            select(Folder)
            .where(
                and_(
                    Folder.user_id == user.id,
                    Folder.deleted_at.isnot(None)
                )
            )
            .options(selectinload(Folder.children), selectinload(Folder.documents))
            .order_by(Folder.deleted_at.desc())
        )
        result = await self.db.execute(query)
        folders = result.scalars().all()

        # Build tree structure of trashed folders
        folder_map = {}
        roots = []

        for folder in folders:
            # Count documents and children
            doc_count = len([d for d in folder.documents if d.deleted_at == folder.deleted_at])
            children_count = len([c for c in folder.children if c.deleted_at == folder.deleted_at])

            # Get parent name if parent exists and is not deleted
            parent_name = None
            if folder.parent_id:
                parent_query = select(Folder.name).where(
                    and_(
                        Folder.id == folder.parent_id,
                        Folder.user_id == user.id,
                        Folder.deleted_at.is_(None)
                    )
                )
                parent_result = await self.db.execute(parent_query)
                parent_name = parent_result.scalar_one_or_none()

            trashed_folder = TrashedFolderWithChildren(
                id=folder.id,
                name=folder.name,
                deleted_at=folder.deleted_at,
                user_id=folder.user_id,
                description=folder.description,
                color=folder.color,
                parent_id=folder.parent_id,
                parent_name=parent_name,
                document_count=doc_count,
                children_count=children_count,
                children=[],
                documents=[]
            )

            folder_map[folder.id] = (folder, trashed_folder)

            # If parent is not in trash or doesn't exist, it's a root
            if not folder.parent_id or folder.parent_id not in folder_map:
                roots.append(trashed_folder)

        # Build hierarchy
        for _folder_id, (folder, trashed_folder) in folder_map.items():
            if folder.parent_id and folder.parent_id in folder_map:
                parent_trashed = folder_map[folder.parent_id][1]
                parent_trashed.children.append(trashed_folder)
                # Remove from roots if it was added there
                if trashed_folder in roots:
                    roots.remove(trashed_folder)

            # Add documents that were deleted with this folder
            for doc in folder.documents:
                if doc.deleted_at == folder.deleted_at:
                    trashed_folder.documents.append(TrashedDocument(
                        id=doc.id,
                        name=doc.filename,
                        deleted_at=doc.deleted_at,
                        user_id=doc.user_id,
                        file_size=doc.file_size,
                        page_count=doc.page_count
                    ))

        return roots

    async def restore_folder(self, user: User, request: RestoreFolderRequest) -> None:
        """Restore a folder from trash."""
        # Get the folder
        query = select(Folder).where(
            and_(
                Folder.id == request.folder_id,
                Folder.user_id == user.id,
                Folder.deleted_at.isnot(None)
            )
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()

        if not folder:
            raise NotFoundException("Folder not found in trash")

        # Check if new parent is valid
        if request.new_parent_id:
            parent_query = select(Folder).where(
                and_(
                    Folder.id == request.new_parent_id,
                    Folder.user_id == user.id,
                    Folder.deleted_at.is_(None)
                )
            )
            parent_result = await self.db.execute(parent_query)
            if not parent_result.scalar_one_or_none():
                raise NotFoundException("Parent folder not found")
            folder.parent_id = request.new_parent_id
        else:
            # If no new parent specified, check if original parent still exists and is not deleted
            if folder.parent_id:
                parent_query = select(Folder).where(
                    and_(
                        Folder.id == folder.parent_id,
                        Folder.user_id == user.id,
                        Folder.deleted_at.is_(None)
                    )
                )
                parent_result = await self.db.execute(parent_query)
                parent_exists = parent_result.scalar_one_or_none()
                
                # If original parent doesn't exist or is deleted, set to root level
                if not parent_exists:
                    folder.parent_id = None
                # Otherwise keep the original parent_id (no change needed)

        # Restore the folder
        deleted_at = folder.deleted_at
        folder.deleted_at = None

        if request.restore_children:
            # Restore all descendants
            await self._restore_folder_descendants(folder.id, deleted_at)

        await self.db.commit()

    async def restore_documents(self, user: User, request: RestoreDocumentRequest) -> None:
        """Restore documents from trash."""
        # Get documents
        query = select(Document).where(
            and_(
                Document.id.in_(request.document_ids),
                Document.user_id == user.id,
                Document.deleted_at.isnot(None)
            )
        )
        result = await self.db.execute(query)
        documents = result.scalars().all()

        if len(documents) != len(request.document_ids):
            raise NotFoundException("One or more documents not found in trash")

        # Restore documents
        for doc in documents:
            doc.deleted_at = None

        # Add to folder if specified
        if request.folder_id:
            folder_query = select(Folder).where(
                and_(
                    Folder.id == request.folder_id,
                    Folder.user_id == user.id,
                    Folder.deleted_at.is_(None)
                )
            )
            folder_result = await self.db.execute(folder_query)
            folder = folder_result.scalar_one_or_none()

            if not folder:
                raise NotFoundException("Target folder not found")

            # Remove documents from all folders first
            delete_stmt = document_folders.delete().where(
                document_folders.c.document_id.in_(request.document_ids)
            )
            await self.db.execute(delete_stmt)

            # Add to target folder
            for doc in documents:
                folder.documents.append(doc)

        await self.db.commit()

    async def empty_trash(self, user: User, request: EmptyTrashRequest) -> None:
        """Empty the trash, permanently deleting items."""
        if not request.confirm:
            raise BadRequestException("Confirmation required to empty trash")

        # Build base queries
        doc_where = and_(
            Document.user_id == user.id,
            Document.deleted_at.isnot(None)
        )
        folder_where = and_(
            Folder.user_id == user.id,
            Folder.deleted_at.isnot(None)
        )

        # Add age filter if not deleting all
        if not request.delete_all:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            doc_where = and_(doc_where, Document.deleted_at < cutoff_date)
            folder_where = and_(folder_where, Folder.deleted_at < cutoff_date)

        # Get documents to delete
        doc_query = select(Document).where(doc_where)
        doc_result = await self.db.execute(doc_query)
        documents = doc_result.scalars().all()

        # Delete physical files and documents
        for doc in documents:
            if self.storage_service and doc.storage_path:
                with contextlib.suppress(Exception):
                    await self.storage_service.delete_file(doc.storage_path)
            await self.db.delete(doc)

        # Get folders to delete (order by depth to delete children first)
        folder_query = (
            select(Folder)
            .where(folder_where)
            .order_by(Folder.created_at.desc())  # Rough approximation of depth
        )
        folder_result = await self.db.execute(folder_query)
        folders = folder_result.scalars().all()

        # Delete folders
        for folder in folders:
            await self.db.delete(folder)

        await self.db.commit()

    async def _restore_folder_descendants(self, folder_id: UUID, deleted_at: datetime) -> None:
        """Recursively restore folder descendants."""
        # Restore child folders
        child_query = select(Folder).where(
            and_(
                Folder.parent_id == folder_id,
                Folder.deleted_at == deleted_at
            )
        )
        child_result = await self.db.execute(child_query)
        children = child_result.scalars().all()

        for child in children:
            child.deleted_at = None
            await self._restore_folder_descendants(child.id, deleted_at)

        # Restore documents in this folder
        doc_query = (
            select(Document)
            .join(document_folders)
            .where(
                and_(
                    document_folders.c.folder_id == folder_id,
                    Document.deleted_at == deleted_at
                )
            )
        )
        doc_result = await self.db.execute(doc_query)
        documents = doc_result.scalars().all()

        for doc in documents:
            doc.deleted_at = None