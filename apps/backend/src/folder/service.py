"""Folder service for managing document folders."""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..common.exceptions import BadRequestException, ConflictException, NotFoundException
from ..database.models import Document, Folder, User, document_folders
from ..storage.service import StorageService
from .schemas import FolderCreate, FolderResponse, FolderUpdate, FolderWithChildren


class FolderService:
    """Service for managing folders."""

    def __init__(self, db: AsyncSession, storage_service: Optional[StorageService] = None):
        """Initialize folder service."""
        self.db = db
        self.storage_service = storage_service

    async def create_folder(
        self, user: User, folder_data: FolderCreate
    ) -> FolderResponse:
        """Create a new folder."""
        # Check if parent folder exists and belongs to user
        if folder_data.parent_id:
            parent_query = select(Folder).where(
                and_(
                    Folder.id == folder_data.parent_id,
                    Folder.user_id == user.id
                )
            )
            parent_result = await self.db.execute(parent_query)
            parent = parent_result.scalar_one_or_none()
            
            if not parent:
                raise NotFoundException("Parent folder not found")

        # Check for duplicate folder name at the same level
        existing_query = select(Folder).where(
            and_(
                Folder.user_id == user.id,
                Folder.name == folder_data.name,
                Folder.parent_id == folder_data.parent_id
            )
        )
        existing = await self.db.execute(existing_query)
        if existing.scalar_one_or_none():
            raise ConflictException("A folder with this name already exists at this level")

        # Create folder
        folder = Folder(
            user_id=user.id,
            name=folder_data.name,
            description=folder_data.description,
            color=folder_data.color,
            parent_id=folder_data.parent_id,
        )
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)

        return await self._to_folder_response(folder)

    async def get_folders_tree(self, user: User) -> list[FolderWithChildren]:
        """Get all folders for a user in a tree structure."""
        # Get all non-deleted folders with their relationships
        query = (
            select(Folder)
            .where(
                and_(
                    Folder.user_id == user.id,
                    Folder.deleted_at.is_(None)
                )
            )
            .options(selectinload(Folder.children), selectinload(Folder.documents))
            .order_by(Folder.name)
        )
        result = await self.db.execute(query)
        folders = result.scalars().all()

        # Build tree structure
        folder_map = {folder.id: folder for folder in folders}
        roots = []

        for folder in folders:
            if folder.parent_id is None:
                roots.append(await self._to_folder_with_children(folder, folder_map))

        return roots

    async def get_folder(self, user: User, folder_id: UUID) -> FolderResponse:
        """Get a specific folder."""
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id,
                Folder.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise NotFoundException("Folder not found")

        return await self._to_folder_response(folder)

    async def update_folder(
        self, user: User, folder_id: UUID, folder_data: FolderUpdate
    ) -> FolderResponse:
        """Update a folder."""
        # Get folder with proper query
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id
            )
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise NotFoundException("Folder not found")

        # Check if we're moving to a new parent (including moving to root by setting parent_id to None)
        if "parent_id" in folder_data.model_fields_set and folder_data.parent_id != folder.parent_id and folder_data.parent_id is not None:
            # Prevent moving folder to itself
            if folder_data.parent_id == folder_id:
                raise BadRequestException("Cannot move folder to itself")

            # Check if new parent exists and belongs to user
            parent_query = select(Folder).where(
                and_(
                    Folder.id == folder_data.parent_id,
                    Folder.user_id == user.id
                )
            )
            parent_result = await self.db.execute(parent_query)
            new_parent = parent_result.scalar_one_or_none()
            
            if not new_parent:
                raise NotFoundException("Parent folder not found")

            # Check for circular reference
            if await self._is_descendant(folder_data.parent_id, folder_id):
                raise BadRequestException("Cannot move folder to its own descendant")

        # Check for duplicate name at the new level
        if folder_data.name and folder_data.name != folder.name:
            # Determine the parent_id to check against
            if "parent_id" in folder_data.model_fields_set:
                parent_id = folder_data.parent_id
            else:
                parent_id = folder.parent_id
            existing_query = select(Folder).where(
                and_(
                    Folder.user_id == user.id,
                    Folder.name == folder_data.name,
                    Folder.parent_id == parent_id,
                    Folder.id != folder_id
                )
            )
            existing = await self.db.execute(existing_query)
            if existing.scalar_one_or_none():
                raise ConflictException("A folder with this name already exists at this level")

        # Update folder
        for key, value in folder_data.model_dump(exclude_unset=True).items():
            setattr(folder, key, value)

        await self.db.commit()
        await self.db.refresh(folder)

        return await self._to_folder_response(folder)

    async def delete_folder(self, user: User, folder_id: UUID) -> None:
        """Soft delete a folder and all its descendants."""
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id,
                Folder.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise NotFoundException("Folder not found")

        # Get all descendant folder IDs (including this folder)
        all_folder_ids = await self._get_all_descendant_folder_ids(folder_id)
        
        # Set deletion timestamp
        deleted_at = func.now()
        
        # Soft delete all folders in the tree
        folders_query = select(Folder).where(
            and_(
                Folder.id.in_(all_folder_ids),
                Folder.deleted_at.is_(None)
            )
        )
        folders_result = await self.db.execute(folders_query)
        folders_to_delete = folders_result.scalars().all()
        
        for folder_to_delete in folders_to_delete:
            folder_to_delete.deleted_at = deleted_at
        
        # Soft delete all documents in these folders
        docs_query = (
            select(Document)
            .join(document_folders)
            .where(
                and_(
                    document_folders.c.folder_id.in_(all_folder_ids),
                    Document.deleted_at.is_(None)
                )
            )
        )
        docs_result = await self.db.execute(docs_query)
        documents_to_delete = docs_result.scalars().all()
        
        for doc in documents_to_delete:
            doc.deleted_at = deleted_at

        await self.db.commit()

    async def add_documents_to_folder(
        self, user: User, folder_id: UUID, document_ids: list[UUID]
    ) -> FolderResponse:
        """Add documents to a folder (removes from other folders first)."""
        # Get folder with documents relationship loaded
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id
            )
        ).options(selectinload(Folder.documents))
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise NotFoundException("Folder not found")

        # Verify all documents exist and belong to user
        docs_query = select(Document).where(
            and_(
                Document.id.in_(document_ids),
                Document.user_id == user.id
            )
        )
        result = await self.db.execute(docs_query)
        documents = result.scalars().all()

        if len(documents) != len(document_ids):
            raise NotFoundException("One or more documents not found")

        # First, remove documents from ALL folders (ensuring one-to-one relationship)
        delete_stmt = delete(document_folders).where(
            document_folders.c.document_id.in_(document_ids)
        )
        await self.db.execute(delete_stmt)

        # Then add documents to the target folder
        for doc in documents:
            folder.documents.append(doc)

        await self.db.commit()
        await self.db.refresh(folder)

        return await self._to_folder_response(folder)

    async def remove_documents_from_folder(
        self, user: User, folder_id: UUID, document_ids: list[UUID]
    ) -> FolderResponse:
        """Remove documents from a folder."""
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id
            )
        )
        result = await self.db.execute(query)
        folder = result.scalar_one_or_none()
        
        if not folder:
            raise NotFoundException("Folder not found")

        # Remove documents from folder
        stmt = delete(document_folders).where(
            and_(
                document_folders.c.folder_id == folder_id,
                document_folders.c.document_id.in_(document_ids)
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        await self.db.refresh(folder)

        return await self._to_folder_response(folder)

    async def get_folder_documents(
        self, user: User, folder_id: Optional[UUID] = None
    ) -> list[Document]:
        """Get documents in a folder or unfiled documents."""
        if folder_id:
            # Get documents in specific folder
            query = select(Folder).where(
                and_(
                    Folder.id == folder_id,
                    Folder.user_id == user.id
                )
            )
            result = await self.db.execute(query)
            folder = result.scalar_one_or_none()
            
            if not folder:
                raise NotFoundException("Folder not found")

            query = (
                select(Document)
                .join(document_folders)
                .where(
                    document_folders.c.folder_id == folder_id,
                    Document.deleted_at.is_(None)
                )
                .options(selectinload(Document.folders))
                .order_by(Document.created_at.desc())
            )
        else:
            # Get unfiled documents (not in any folder)
            query = (
                select(Document)
                .where(
                    and_(
                        Document.user_id == user.id,
                        Document.deleted_at.is_(None),
                        ~Document.id.in_(
                            select(document_folders.c.document_id)
                        )
                    )
                )
                .options(selectinload(Document.folders))
                .order_by(Document.created_at.desc())
            )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_unfiled_document_count(self, user: User) -> int:
        """Get count of unfiled documents for a user."""
        query = (
            select(func.count(Document.id))
            .where(
                and_(
                    Document.user_id == user.id,
                    Document.deleted_at.is_(None),
                    ~Document.id.in_(
                        select(document_folders.c.document_id)
                    )
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_total_document_count(self, user: User) -> int:
        """Get total count of all documents for a user."""
        query = (
            select(func.count(Document.id))
            .where(
                Document.user_id == user.id,
                Document.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _is_descendant(self, parent_id: UUID, child_id: UUID) -> bool:
        """Check if parent_id is a descendant of child_id."""
        current_id = parent_id
        visited = set()

        while current_id:
            if current_id in visited:
                break
            if current_id == child_id:
                return True

            visited.add(current_id)
            folder_query = select(Folder).where(Folder.id == current_id)
            folder_result = await self.db.execute(folder_query)
            folder = folder_result.scalar_one_or_none()
            
            if not folder:
                break
            current_id = folder.parent_id

        return False

    async def _get_all_descendant_folder_ids(self, folder_id: UUID) -> list[UUID]:
        """Get all descendant folder IDs recursively using CTE."""
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
        
        result = await self.db.execute(cte_query, {"folder_id": str(folder_id)})
        return [row[0] for row in result]

    async def _to_folder_response(self, folder: Folder) -> FolderResponse:
        """Convert folder model to response schema."""
        # Get all descendant folder IDs (including this folder)
        all_folder_ids = await self._get_all_descendant_folder_ids(folder.id)
        
        # Count documents in this folder and all descendants
        doc_count_query = (
            select(func.count())
            .select_from(document_folders)
            .join(Document, Document.id == document_folders.c.document_id)
            .where(
                document_folders.c.folder_id.in_(all_folder_ids),
                Document.deleted_at.is_(None)
            )
        )
        doc_count_result = await self.db.execute(doc_count_query)
        doc_count = doc_count_result.scalar() or 0

        # Count children
        children_count_query = select(func.count()).select_from(Folder).where(
            and_(
                Folder.parent_id == folder.id,
                Folder.deleted_at.is_(None)
            )
        )
        children_count_result = await self.db.execute(children_count_query)
        children_count = children_count_result.scalar() or 0

        return FolderResponse(
            id=folder.id,
            user_id=folder.user_id,
            name=folder.name,
            description=folder.description,
            color=folder.color,
            parent_id=folder.parent_id,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            document_count=doc_count,
            children_count=children_count,
        )

    async def _to_folder_with_children(
        self, folder: Folder, folder_map: dict[UUID, Folder]
    ) -> FolderWithChildren:
        """Convert folder model to response with children."""
        base_response = await self._to_folder_response(folder)
        
        children = []
        for child in folder.children:
            if child.id in folder_map:
                children.append(await self._to_folder_with_children(child, folder_map))

        return FolderWithChildren(
            **base_response.model_dump(),
            children=sorted(children, key=lambda x: x.name)
        )