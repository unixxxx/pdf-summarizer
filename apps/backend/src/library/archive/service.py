"""Service for managing archive functionality."""

import contextlib
import logging
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...common.exceptions import NotFoundException
from ...database.models import Document, Folder, User
from ...storage.service import StorageService
from .schemas import (
    ArchivedDocument,
    ArchivedFolderWithChildren,
    ArchiveStats,
)

logger = logging.getLogger(__name__)


class ArchiveService:
    """Service for managing archive operations."""

    def __init__(self, storage_service: StorageService | None = None):
        """Initialize archive service."""
        self.storage_service = storage_service

    async def get_archive_stats(self, db: AsyncSession, user: User) -> ArchiveStats:
        """Get statistics about user's archive."""
        # Count archived documents
        doc_count_query = select(func.count(Document.id)).where(
            and_(
                Document.user_id == user.id,
                Document.archived_at.isnot(None)
            )
        )
        doc_count_result = await db.execute(doc_count_query)
        total_documents = doc_count_result.scalar() or 0

        # Count archived folders
        folder_count_query = select(func.count(Folder.id)).where(
            and_(
                Folder.user_id == user.id,
                Folder.archived_at.isnot(None)
            )
        )
        folder_count_result = await db.execute(folder_count_query)
        total_folders = folder_count_result.scalar() or 0

        # Calculate total size
        size_query = select(func.sum(Document.file_size)).where(
            and_(
                Document.user_id == user.id,
                Document.archived_at.isnot(None)
            )
        )
        size_result = await db.execute(size_query)
        total_size = size_result.scalar() or 0

        # Find oldest item
        oldest_doc_query = select(func.min(Document.archived_at)).where(
            and_(
                Document.user_id == user.id,
                Document.archived_at.isnot(None)
            )
        )
        oldest_doc_result = await db.execute(oldest_doc_query)
        oldest_doc = oldest_doc_result.scalar()

        oldest_folder_query = select(func.min(Folder.archived_at)).where(
            and_(
                Folder.user_id == user.id,
                Folder.archived_at.isnot(None)
            )
        )
        oldest_folder_result = await db.execute(oldest_folder_query)
        oldest_folder = oldest_folder_result.scalar()

        oldest_item_date = None
        if oldest_doc and oldest_folder:
            oldest_item_date = min(oldest_doc, oldest_folder)
        elif oldest_doc:
            oldest_item_date = oldest_doc
        elif oldest_folder:
            oldest_item_date = oldest_folder

        return ArchiveStats(
            total_documents=total_documents,
            total_folders=total_folders,
            total_size=total_size,
            oldest_item_date=oldest_item_date
        )

    async def get_archived_documents(self, db: AsyncSession, user: User) -> list[ArchivedDocument]:
        """Get all archived documents that are NOT in archived folders."""
        # First get all document IDs that are in archived folders
        folder_doc_query = (
            select(Document.id)
            .join(Folder, Document.folder_id == Folder.id)
            .where(
                and_(
                    Document.user_id == user.id,
                    Document.archived_at.isnot(None),
                    Folder.archived_at.isnot(None)  # Folder is also archived
                )
            )
        )
        folder_doc_result = await db.execute(folder_doc_query)
        docs_in_archived_folders = {row[0] for row in folder_doc_result}
        
        # Now get all archived documents that either:
        # 1. Have no folder_id (standalone documents)
        # 2. Are in non-archived folders 
        # 3. Are not in the set of documents within archived folders
        conditions = [
            Document.user_id == user.id,
            Document.archived_at.isnot(None)
        ]
        
        if docs_in_archived_folders:
            conditions.append(Document.id.notin_(docs_in_archived_folders))
        
        query = (
            select(Document)
            .where(and_(*conditions))
            .order_by(Document.archived_at.desc())
        )
        result = await db.execute(query)
        documents = result.scalars().all()

        archived_docs = []
        for doc in documents:
            # Get the folder it was in (if any) - should be non-deleted folder
            folder = None
            if doc.folder_id:
                folder_query = (
                    select(Folder)
                    .where(
                        and_(
                            Folder.id == doc.folder_id,
                            Folder.archived_at.is_(None)  # Only non-deleted folders
                        )
                    )
                )
                folder_result = await db.execute(folder_query)
                folder = folder_result.scalar_one_or_none()

            archived_docs.append(ArchivedDocument(
                id=doc.id,
                name=doc.filename,
                archived_at=doc.archived_at,
                user_id=doc.user_id,
                file_size=doc.file_size,
                page_count=doc.page_count,
                folder_id=folder.id if folder else None,
                folder_name=folder.name if folder else None
            ))

        return archived_docs

    async def get_archived_folders(self, db: AsyncSession, user: User) -> list[ArchivedFolderWithChildren]:
        """Get all archived folders in a tree structure."""
        # Get all archived folders first
        query = (
            select(Folder)
            .where(
                and_(
                    Folder.user_id == user.id,
                    Folder.archived_at.isnot(None)
                )
            )
            .options(
                selectinload(Folder.children),
                selectinload(Folder.documents)
            )
            .order_by(Folder.archived_at.desc())
        )
        result = await db.execute(query)
        folders = result.scalars().unique().all()
        
        # Create a map of all folders for easy lookup
        all_folders_map = {f.id: f for f in folders}

        # Build tree structure of archived folders
        folder_map = {}
        roots = []
        
        # First pass: create all folder objects
        for folder in folders:
            # For nested folders, we need to ensure documents are loaded
            # Count only direct documents and children for display
            doc_count = len([d for d in folder.documents if d.archived_at is not None])
            # Count only archived children
            archived_children = [c for c in folder.children if c.archived_at is not None and c.id in all_folders_map]
            children_count = len(archived_children)
            
            # Convert archived documents to ArchivedDocument schema
            archived_docs = []
            for doc in folder.documents:
                if doc.archived_at is not None:
                    archived_docs.append(ArchivedDocument(
                        id=doc.id,
                        name=doc.filename,
                        archived_at=doc.archived_at,
                        user_id=doc.user_id,
                        file_size=doc.file_size,
                        page_count=doc.page_count,
                        folder_id=folder.id,
                        folder_name=folder.name
                    ))
            
            folder_obj = ArchivedFolderWithChildren(
                id=folder.id,
                name=folder.name,
                description=folder.description,
                color=folder.color,
                parent_id=folder.parent_id,
                archived_at=folder.archived_at,
                user_id=folder.user_id,
                document_count=doc_count,
                children_count=children_count,
                children=[],
                documents=archived_docs
            )
            folder_map[folder.id] = folder_obj
            
            # If parent is NOT in the archived folders, this is a root of archived tree
            if folder.parent_id is None or folder.parent_id not in all_folders_map:
                roots.append(folder_obj)
        
        # Second pass: build tree structure only for archived folders
        for folder in folders:
            if folder.parent_id and folder.parent_id in folder_map:
                parent = folder_map[folder.parent_id]
                child = folder_map[folder.id]
                parent.children.append(child)
        
        return roots

    async def restore_document(self, db: AsyncSession, user: User, document_id: UUID) -> None:
        """Restore a document from archive."""
        # Get the document
        query = select(Document).where(
            and_(
                Document.id == document_id,
                Document.user_id == user.id,
                Document.archived_at.isnot(None)
            )
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundException("Document not found in archive")
        
        # If document is in a folder, check if folder is archived
        if document.folder_id:
            folder_query = select(Folder).where(Folder.id == document.folder_id)
            folder_result = await db.execute(folder_query)
            folder = folder_result.scalar_one_or_none()
            
            if folder and folder.archived_at is not None:
                # Remove from archived folder
                document.folder_id = None
        
        # Restore the document
        document.archived_at = None
        await db.commit()
        
        logger.info(f"Restored document {document_id} from archive")

    async def restore_folder(self, db: AsyncSession, user: User, folder_id: UUID) -> None:
        """Restore a folder and all its contents from archive."""
        # Get the folder
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id,
                Folder.archived_at.isnot(None)
            )
        )
        result = await db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise NotFoundException("Folder not found in archive")
        
        # Check if parent folder exists and is not archived
        if folder.parent_id:
            parent_query = select(Folder).where(Folder.id == folder.parent_id)
            parent_result = await db.execute(parent_query)
            parent = parent_result.scalar_one_or_none()
            
            if parent and parent.archived_at is not None:
                # Remove from deleted parent
                folder.parent_id = None
        
        # Get all descendant folders and documents
        descendant_ids = await self._get_all_descendant_folder_ids(db, folder_id)
        
        # Restore all folders in the tree
        folders_query = select(Folder).where(
            and_(
                Folder.id.in_(descendant_ids),
                Folder.archived_at.isnot(None)
            )
        )
        folders_result = await db.execute(folders_query)
        folders_to_restore = folders_result.scalars().all()
        
        for folder_to_restore in folders_to_restore:
            folder_to_restore.archived_at = None
        
        # Restore all documents in these folders
        docs_query = select(Document).where(
            and_(
                Document.folder_id.in_(descendant_ids),
                Document.archived_at.isnot(None)
            )
        )
        docs_result = await db.execute(docs_query)
        documents_to_restore = docs_result.scalars().all()
        
        for doc in documents_to_restore:
            doc.archived_at = None
        
        await db.commit()
        
        logger.info(f"Restored folder {folder_id} and its contents from archive")

    async def permanently_delete_document(
        self, db: AsyncSession, user: User, document_id: UUID
    ) -> None:
        """Permanently delete a document from archive."""
        # Get the document
        query = select(Document).where(
            and_(
                Document.id == document_id,
                Document.user_id == user.id,
                Document.archived_at.isnot(None)
            )
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundException("Document not found in archive")
        
        # Delete the document's storage file if using local storage
        if self.storage_service and document.storage_path:
            with contextlib.suppress(Exception):
                await self.storage_service.delete_file(document.storage_path)
        
        # Delete the document record
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Permanently deleted document {document_id}")

    async def permanently_delete_folder(
        self, db: AsyncSession, user: User, folder_id: UUID
    ) -> None:
        """Permanently delete a folder and all its contents from archive."""
        # Get the folder
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id,
                Folder.archived_at.isnot(None)
            )
        )
        result = await db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise NotFoundException("Folder not found in archive")
        
        # Get all descendant folders
        descendant_ids = await self._get_all_descendant_folder_ids(db, folder_id)
        
        # Get all documents in these folders
        docs_query = select(Document).where(
            and_(
                Document.folder_id.in_(descendant_ids),
                Document.archived_at.isnot(None)
            )
        )
        docs_result = await db.execute(docs_query)
        documents_to_delete = docs_result.scalars().all()
        
        # Delete storage files for all documents
        if self.storage_service:
            for doc in documents_to_delete:
                if doc.storage_path:
                    with contextlib.suppress(Exception):
                        await self.storage_service.delete_file(doc.storage_path)
        
        # Delete all documents
        for doc in documents_to_delete:
            await db.delete(doc)
        
        # Delete all folders in reverse order (children first)
        folders_query = select(Folder).where(Folder.id.in_(descendant_ids))
        folders_result = await db.execute(folders_query)
        folders_to_delete = folders_result.scalars().all()
        
        # Sort folders by depth (deepest first)
        sorted_folders = sorted(
            folders_to_delete,
            key=lambda f: self._get_folder_depth(f, folders_to_delete),
            reverse=True
        )
        
        for folder_to_delete in sorted_folders:
            await db.delete(folder_to_delete)
        
        await db.commit()
        
        logger.info(f"Permanently deleted folder {folder_id} and all its contents")

    async def empty_archive(self, db: AsyncSession, user: User) -> dict:
        """Empty all items from archive permanently."""
        # Get all archived documents not in deleted folders
        docs_in_folders_query = (
            select(Document.id)
            .join(Folder, Document.folder_id == Folder.id)
            .where(
                and_(
                    Document.user_id == user.id,
                    Document.archived_at.isnot(None),
                    Folder.archived_at.isnot(None)
                )
            )
        )
        docs_in_folders_result = await db.execute(docs_in_folders_query)
        docs_in_deleted_folders = {row[0] for row in docs_in_folders_result}
        
        # Get standalone archived documents
        standalone_docs_query = select(Document).where(
            and_(
                Document.user_id == user.id,
                Document.archived_at.isnot(None),
                Document.id.notin_(docs_in_deleted_folders) if docs_in_deleted_folders else True
            )
        )
        standalone_docs_result = await db.execute(standalone_docs_query)
        standalone_docs = standalone_docs_result.scalars().all()
        
        # Get all archived folders
        folders_query = select(Folder).where(
            and_(
                Folder.user_id == user.id,
                Folder.archived_at.isnot(None)
            )
        ).options(selectinload(Folder.documents))
        folders_result = await db.execute(folders_query)
        folders = folders_result.scalars().unique().all()
        
        # Count items for response
        doc_count = len(standalone_docs)
        folder_count = len(folders)
        
        # Delete storage files for standalone documents
        if self.storage_service:
            for doc in standalone_docs:
                if doc.storage_path:
                    with contextlib.suppress(Exception):
                        await self.storage_service.delete_file(doc.storage_path)
        
        # Delete storage files for documents in folders
        if self.storage_service:
            for folder in folders:
                for doc in folder.documents:
                    if doc.archived_at and doc.storage_path:
                        with contextlib.suppress(Exception):
                            await self.storage_service.delete_file(doc.storage_path)
        
        # Delete all standalone documents
        for doc in standalone_docs:
            await db.delete(doc)
        
        # Delete all folders and their documents (cascade will handle documents)
        for folder in folders:
            await db.delete(folder)
        
        await db.commit()
        
        logger.info(f"Emptied archive for user {user.id}: {doc_count} documents, {folder_count} folders")
        
        return {
            "documents_deleted": doc_count,
            "folders_deleted": folder_count
        }


    async def _get_all_descendant_folder_ids(self, db: AsyncSession, folder_id: UUID) -> list[UUID]:
        """Get all descendant folder IDs recursively."""
        from sqlalchemy import text
        
        # Use a recursive CTE for better performance
        cte_query = text("""
            WITH RECURSIVE folder_tree AS (
                -- Base case: start with the given folder
                SELECT id FROM folders WHERE id = :folder_id
                
                UNION ALL
                
                -- Recursive case: find all children
                SELECT f.id 
                FROM folders f
                INNER JOIN folder_tree ft ON f.parent_id = ft.id
            )
            SELECT id FROM folder_tree
        """)
        
        result = await db.execute(cte_query, {"folder_id": str(folder_id)})
        return [row[0] for row in result]

    def _get_folder_depth(self, folder: Folder, all_folders: list[Folder]) -> int:
        """Calculate the depth of a folder in the tree."""
        depth = 0
        current = folder
        folder_map = {f.id: f for f in all_folders}
        
        while current.parent_id and current.parent_id in folder_map:
            depth += 1
            current = folder_map[current.parent_id]
        
        return depth