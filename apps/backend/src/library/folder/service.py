"""Folder service for managing document folders."""

import logging
import re
from uuid import UUID

from sqlalchemy import and_, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...common.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from ...database.models import Document, Folder, Tag, User, folder_tags
from ..tag.service import TagService
from .schemas import (
    FolderCreate,
    FolderResponse,
    FolderUpdate,
    FolderWithChildren,
    TagInfo,
)

logger = logging.getLogger(__name__)


class FolderService:
    """Service for managing folders."""

    def __init__(self, tag_service: TagService | None = None):
        """Initialize folder service."""
        self.tag_service = tag_service

    async def create_folder(
        self, db: AsyncSession, user: User, folder_data: FolderCreate
    ) -> FolderResponse:
        """Create a new folder."""
        # Check if parent folder exists and belongs to user
        if folder_data.parent_id:
            parent_query = select(Folder).where(
                and_(Folder.id == folder_data.parent_id, Folder.user_id == user.id)
            )
            parent_result = await db.execute(parent_query)
            parent = parent_result.scalar_one_or_none()

            if not parent:
                raise NotFoundException("Parent folder not found")

        # Check for duplicate folder name at the same level (excluding archived folders)
        existing_query = select(Folder).where(
            and_(
                Folder.user_id == user.id,
                Folder.name == folder_data.name,
                Folder.parent_id == folder_data.parent_id,
                Folder.archived_at.is_(None),
            )
        )
        existing = await db.execute(existing_query)
        if existing.scalar_one_or_none():
            raise ConflictException(
                "A folder with this name already exists at this level"
            )

        # Create folder
        folder = Folder(
            user_id=user.id,
            name=folder_data.name,
            description=folder_data.description,
            color=folder_data.color,
            parent_id=folder_data.parent_id,
        )
        db.add(folder)

        # Collect all tags (existing + new)
        all_tags = []
        existing_tag_ids = [tag.id for tag in folder_data.tags if tag.id]
        tags_to_create = [tag for tag in folder_data.tags if not tag.id]

        # Get existing tags by ID
        if existing_tag_ids:
            tag_query = select(Tag).where(Tag.id.in_(existing_tag_ids))
            tag_result = await db.execute(tag_query)
            existing_tags = tag_result.scalars().all()

            if len(existing_tags) != len(existing_tag_ids):
                raise NotFoundException("One or more tags not found")

            all_tags.extend(existing_tags)

        # Create new tags if any
        if tags_to_create:
            # Convert tag create data to the format expected by tag service
            tag_data_list = []
            for tag_data in tags_to_create:
                # Generate slug from name
                slug = re.sub(
                    r"[^a-z0-9-]", "", tag_data.name.lower().replace(" ", "-")
                )
                tag_data_list.append(
                    {
                        "name": tag_data.name,
                        "slug": slug,
                        "color": tag_data.color,
                        "description": None,
                    }
                )

            # Create tags using tag service
            new_tags = await self.tag_service.find_or_create_tags(tag_data_list, db)
            all_tags.extend(new_tags)

        # Flush to get ID and timestamps
        await db.flush()

        # Store folder id for later use
        folder_id = folder.id

        # Now associate tags if we have them - use bulk insert for efficiency
        if all_tags:
            await db.execute(
                folder_tags.insert(),
                [{"folder_id": folder_id, "tag_id": tag.id} for tag in all_tags],
            )

        # Commit the transaction
        await db.commit()

        # Now reload the folder with all relationships in a new transaction
        query = (
            select(Folder)
            .where(Folder.id == folder_id)
            .options(selectinload(Folder.tags))
        )
        result = await db.execute(query)
        folder_with_tags = result.scalar_one()

        # Sync documents if folder has tags
        if all_tags:
            await self._sync_folder_documents(db, folder_with_tags)
            await db.commit()

        # Return the response using the reloaded folder
        return await self._to_folder_response(db, folder_with_tags)

    async def get_folders_tree(
        self, db: AsyncSession, user: User
    ) -> list[FolderWithChildren]:
        """Get all folders for a user in a tree structure."""
        # Get all non-deleted folders with their relationships
        query = (
            select(Folder)
            .where(and_(Folder.user_id == user.id, Folder.archived_at.is_(None)))
            .options(selectinload(Folder.children), selectinload(Folder.tags))
            .order_by(Folder.name)
        )
        result = await db.execute(query)
        folders = result.scalars().all()

        # Build tree structure
        folder_map = {folder.id: folder for folder in folders}
        roots = []

        for folder in folders:
            if folder.parent_id is None:
                roots.append(
                    await self._to_folder_with_children(db, folder, folder_map)
                )

        return roots

    async def get_folder(
        self, db: AsyncSession, user: User, folder_id: UUID
    ) -> FolderResponse:
        """Get a specific folder."""
        query = (
            select(Folder)
            .where(
                and_(
                    Folder.id == folder_id,
                    Folder.user_id == user.id,
                    Folder.archived_at.is_(None),
                )
            )
            .options(selectinload(Folder.tags))
        )
        result = await db.execute(query)
        folder = result.scalar_one_or_none()

        if not folder:
            raise NotFoundException("Folder not found")

        return await self._to_folder_response(db, folder)

    async def update_folder(
        self, db: AsyncSession, user: User, folder_id: UUID, folder_data: FolderUpdate
    ) -> FolderResponse:
        """Update a folder."""
        # Get folder with proper query
        query = (
            select(Folder)
            .where(and_(Folder.id == folder_id, Folder.user_id == user.id))
            .options(selectinload(Folder.tags))
        )
        result = await db.execute(query)
        folder = result.scalar_one_or_none()

        if not folder:
            raise NotFoundException("Folder not found")

        # Check if we're moving to a new parent (including moving to root by setting parent_id to None)
        if (
            "parent_id" in folder_data.model_fields_set
            and folder_data.parent_id != folder.parent_id
            and folder_data.parent_id is not None
        ):
            # Prevent moving folder to itself
            if folder_data.parent_id == folder_id:
                raise BadRequestException("Cannot move folder to itself")

            # Check if new parent exists and belongs to user
            parent_query = select(Folder).where(
                and_(Folder.id == folder_data.parent_id, Folder.user_id == user.id)
            )
            parent_result = await db.execute(parent_query)
            new_parent = parent_result.scalar_one_or_none()

            if not new_parent:
                raise NotFoundException("Parent folder not found")

            # Check for circular reference
            if await self._is_descendant(db, folder_data.parent_id, folder_id):
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
                    Folder.id != folder_id,
                    Folder.archived_at.is_(None),
                )
            )
            existing = await db.execute(existing_query)
            if existing.scalar_one_or_none():
                raise ConflictException(
                    "A folder with this name already exists at this level"
                )

        # Handle tag updates
        tags_updated = False
        if folder_data.tags is not None:
            all_tags = []
            existing_tag_ids = [tag.id for tag in folder_data.tags if tag.id]
            tags_to_create = [tag for tag in folder_data.tags if not tag.id]

            # Get existing tags by ID
            if existing_tag_ids:
                logger.info(
                    f"Updating folder '{folder.name}' with existing tag IDs: {existing_tag_ids}"
                )
                tag_query = select(Tag).where(Tag.id.in_(existing_tag_ids))
                tag_result = await db.execute(tag_query)
                existing_tags = tag_result.scalars().all()

                if len(existing_tags) != len(existing_tag_ids):
                    raise NotFoundException("One or more tags not found")

                all_tags.extend(existing_tags)

            # Create new tags if any
            if tags_to_create:
                logger.info(
                    f"Creating new tags for folder '{folder.name}': {[t.name for t in tags_to_create]}"
                )
                # Convert tag create data to the format expected by tag service
                tag_data_list = []
                for tag_data in tags_to_create:
                    # Generate slug from name
                    slug = re.sub(
                        r"[^a-z0-9-]", "", tag_data.name.lower().replace(" ", "-")
                    )
                    tag_data_list.append(
                        {
                            "name": tag_data.name,
                            "slug": slug,
                            "color": tag_data.color,
                            "description": None,
                        }
                    )

                # Create tags using tag service
                new_tags = await self.tag_service.find_or_create_tags(tag_data_list, db)
                all_tags.extend(new_tags)

            # Update folder tags
            folder.tags = all_tags
            tags_updated = True
            logger.info(f"Updated folder tags: {[tag.name for tag in all_tags]}")

        # Update other folder attributes
        update_data = folder_data.model_dump(exclude_unset=True, exclude={"tags"})
        for key, value in update_data.items():
            setattr(folder, key, value)

        # Commit changes first
        await db.commit()

        # Sync documents based on tags if tags were updated
        if tags_updated:
            # Reload folder with tags relationship
            query = (
                select(Folder)
                .where(Folder.id == folder.id)
                .options(selectinload(Folder.tags))
            )
            result = await db.execute(query)
            folder = result.scalar_one()

            await self._sync_folder_documents(db, folder)
            await db.commit()
        else:
            # Just reload folder with tags
            query = (
                select(Folder)
                .where(Folder.id == folder.id)
                .options(selectinload(Folder.tags))
            )
            result = await db.execute(query)
            folder = result.scalar_one()

        return await self._to_folder_response(db, folder)

    async def delete_folder(
        self, db: AsyncSession, user: User, folder_id: UUID
    ) -> None:
        """Soft delete a folder and all its descendants."""
        query = select(Folder).where(
            and_(
                Folder.id == folder_id,
                Folder.user_id == user.id,
                Folder.archived_at.is_(None),
            )
        )
        result = await db.execute(query)
        folder = result.scalar_one_or_none()

        if not folder:
            raise NotFoundException("Folder not found")

        # Get all descendant folder IDs (including this folder)
        all_folder_ids = await self._get_all_descendant_folder_ids(db, folder_id)

        # Set deletion timestamp
        archived_at = func.now()

        # Soft delete all folders in the tree
        folders_query = select(Folder).where(
            and_(Folder.id.in_(all_folder_ids), Folder.archived_at.is_(None))
        )
        folders_result = await db.execute(folders_query)
        folders_to_delete = folders_result.scalars().all()

        for folder_to_delete in folders_to_delete:
            folder_to_delete.archived_at = archived_at

        # Soft delete all documents in these folders
        docs_query = select(Document).where(
            and_(Document.folder_id.in_(all_folder_ids), Document.archived_at.is_(None))
        )
        docs_result = await db.execute(docs_query)
        documents_to_delete = docs_result.scalars().all()

        for doc in documents_to_delete:
            doc.archived_at = archived_at

        await db.commit()

    async def add_documents_to_folder(
        self, db: AsyncSession, user: User, folder_id: UUID, document_ids: list[UUID]
    ) -> FolderResponse:
        """Add documents to a folder (removes from other folders first)."""
        # Get folder with documents and tags relationship loaded
        query = (
            select(Folder)
            .where(and_(Folder.id == folder_id, Folder.user_id == user.id))
            .options(selectinload(Folder.documents), selectinload(Folder.tags))
        )
        result = await db.execute(query)
        folder = result.scalar_one_or_none()

        if not folder:
            raise NotFoundException("Folder not found")

        # Verify all documents exist and belong to user
        docs_query = select(Document).where(
            and_(Document.id.in_(document_ids), Document.user_id == user.id)
        )
        result = await db.execute(docs_query)
        documents = result.scalars().all()

        if len(documents) != len(document_ids):
            raise NotFoundException("One or more documents not found")

        # Update documents to belong to this folder
        for doc in documents:
            doc.folder_id = folder_id

        await db.commit()
        await db.refresh(folder)

        return await self._to_folder_response(db, folder)

    async def remove_documents_from_folder(
        self, db: AsyncSession, user: User, folder_id: UUID, document_ids: list[UUID]
    ) -> FolderResponse:
        """Remove documents from a folder."""
        query = (
            select(Folder)
            .where(and_(Folder.id == folder_id, Folder.user_id == user.id))
            .options(selectinload(Folder.tags))
        )
        result = await db.execute(query)
        folder = result.scalar_one_or_none()

        if not folder:
            raise NotFoundException("Folder not found")

        # Remove documents from folder
        update_stmt = (
            update(Document)
            .where(and_(Document.folder_id == folder_id, Document.id.in_(document_ids)))
            .values(folder_id=None)
        )
        await db.execute(update_stmt)
        await db.commit()
        await db.refresh(folder)

        return await self._to_folder_response(db, folder)

    async def get_unfiled_document_count(self, db: AsyncSession, user: User) -> int:
        """Get count of unfiled documents for a user."""
        query = select(func.count(Document.id)).where(
            and_(
                Document.user_id == user.id,
                Document.archived_at.is_(None),
                Document.folder_id.is_(None),
            )
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def get_total_document_count(self, db: AsyncSession, user: User) -> int:
        """Get total count of all documents for a user."""
        query = select(func.count(Document.id)).where(
            Document.user_id == user.id, Document.archived_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def _is_descendant(
        self, db: AsyncSession, parent_id: UUID, child_id: UUID
    ) -> bool:
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
            folder_result = await db.execute(folder_query)
            folder = folder_result.scalar_one_or_none()

            if not folder:
                break
            current_id = folder.parent_id

        return False

    async def _get_all_descendant_folder_ids(
        self, db: AsyncSession, folder_id: UUID
    ) -> list[UUID]:
        """Get all descendant folder IDs recursively using CTE."""
        # Use a recursive CTE for better performance
        cte_query = text(
            """
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
        """
        )

        result = await db.execute(cte_query, {"folder_id": str(folder_id)})
        return [row[0] for row in result]

    async def _to_folder_response(
        self, db: AsyncSession, folder: Folder
    ) -> FolderResponse:
        """Convert folder model to response schema."""
        # Get all descendant folder IDs (including this folder)
        all_folder_ids = await self._get_all_descendant_folder_ids(db, folder.id)

        # Count documents in this folder and all descendants
        doc_count_query = (
            select(func.count())
            .select_from(Document)
            .where(
                Document.folder_id.in_(all_folder_ids), Document.archived_at.is_(None)
            )
        )
        doc_count_result = await db.execute(doc_count_query)
        doc_count = doc_count_result.scalar() or 0

        # Count children
        children_count_query = (
            select(func.count())
            .select_from(Folder)
            .where(and_(Folder.parent_id == folder.id, Folder.archived_at.is_(None)))
        )
        children_count_result = await db.execute(children_count_query)
        children_count = children_count_result.scalar() or 0

        # Load tags if folder has them
        tags = []
        try:
            # Check if tags are loaded
            if hasattr(folder, "tags") and folder.tags is not None:
                tags = [
                    TagInfo(id=tag.id, name=tag.name, color=tag.color)
                    for tag in folder.tags
                ]
        except Exception:
            # Tags not loaded, skip
            pass

        return FolderResponse(
            id=folder.id,
            name=folder.name,
            description=folder.description,
            color=folder.color,
            parent_id=folder.parent_id,
            tags=tags,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            document_count=doc_count,
            children_count=children_count,
        )

    async def _to_folder_with_children(
        self, db: AsyncSession, folder: Folder, folder_map: dict[UUID, Folder]
    ) -> FolderWithChildren:
        """Convert folder model to response with children."""
        base_response = await self._to_folder_response(db, folder)

        children = []
        for child in folder.children:
            if child.id in folder_map:
                children.append(
                    await self._to_folder_with_children(db, child, folder_map)
                )

        return FolderWithChildren(
            **base_response.model_dump(),
            children=sorted(children, key=lambda x: x.name),
        )

    async def _sync_folder_documents(self, db: AsyncSession, folder: Folder) -> None:
        """Sync documents in a folder based on its tags using SQL-side similarity."""
        logger.info(f"Syncing documents for folder '{folder.name}' (ID: {folder.id})")

        if not folder.tags:
            logger.info("Folder has no tags, removing all documents from folder")
            # Remove all documents from folder if no tags
            update_stmt = (
                update(Document)
                .where(Document.folder_id == folder.id)
                .values(folder_id=None)
            )
            await db.execute(update_stmt)
            return

        logger.info(
            f"Folder has {len(folder.tags)} tags: {[tag.name for tag in folder.tags]}"
        )
        logger.info("Using SQL-side similarity matching to find documents for folder")

        # Get folder tag IDs for the query
        folder_tag_ids = [tag.id for tag in folder.tags]

        # Find documents without folders that have similar tags
        # Using pgvector's cosine similarity operator <->
        similarity_threshold = (
            0.3  # Cosine distance threshold (1 - similarity = 0.7 = 70%)
        )

        # Query to find matching documents using similarity or text matching
        matching_docs_query = text(
            """
            WITH folder_tag_info AS (
                SELECT id, embedding, name, LOWER(name) as lower_name
                FROM tags
                WHERE id = ANY(:folder_tag_ids)
            ),
            document_matches AS (
                SELECT DISTINCT d.id, d.filename,
                       MIN(CASE 
                           WHEN t1.embedding IS NOT NULL AND t2.embedding IS NOT NULL 
                           THEN t1.embedding <-> t2.embedding 
                           ELSE 1.0 
                       END) as min_distance
                FROM documents d
                INNER JOIN document_tags dt ON d.id = dt.document_id
                INNER JOIN tags t1 ON dt.tag_id = t1.id
                CROSS JOIN folder_tag_info t2
                WHERE d.user_id = :user_id
                  AND d.archived_at IS NULL
                  AND d.folder_id IS NULL
                  AND (
                    -- Embedding similarity match
                    (t1.embedding IS NOT NULL 
                     AND t2.embedding IS NOT NULL
                     AND t1.embedding <-> t2.embedding < :threshold)
                    OR
                    -- Text-based matching for related terms
                    (
                      -- Exact match (case insensitive)
                      LOWER(t1.name) = t2.lower_name
                      OR
                      -- Country/demonym pairs (Georgia/Georgian, Armenia/Armenian, etc.)
                      (LENGTH(t1.name) > 3 AND LENGTH(t2.name) > 3 AND (
                        (LOWER(t1.name) LIKE t2.lower_name || '%' AND LENGTH(t1.name) - LENGTH(t2.name) <= 3)
                        OR
                        (t2.lower_name LIKE LOWER(t1.name) || '%' AND LENGTH(t2.name) - LENGTH(t1.name) <= 3)
                      ))
                    )
                  )
                GROUP BY d.id, d.filename
            )
            UPDATE documents
            SET folder_id = :folder_id
            FROM document_matches
            WHERE documents.id = document_matches.id
            RETURNING documents.id, document_matches.filename, document_matches.min_distance
        """
        )

        result = await db.execute(
            matching_docs_query,
            {
                "folder_tag_ids": folder_tag_ids,
                "user_id": str(folder.user_id),
                "folder_id": str(folder.id),
                "threshold": similarity_threshold,
            },
        )

        added_docs = result.fetchall()
        for doc_id, filename, distance in added_docs:
            similarity = 1 - distance  # Convert distance to similarity
            logger.info(
                f"Added document '{filename}' (ID: {doc_id}) to folder based on similarity: {similarity:.2f}"
            )

        # Remove documents that no longer match the folder tags
        remove_docs_query = text(
            """
            WITH folder_tag_info AS (
                SELECT id, embedding, name, LOWER(name) as lower_name
                FROM tags
                WHERE id = ANY(:folder_tag_ids)
            ),
            document_matches AS (
                SELECT d.id, d.filename,
                       BOOL_OR(
                         -- Embedding similarity match
                         (t1.embedding IS NOT NULL 
                          AND t2.embedding IS NOT NULL
                          AND t1.embedding <-> t2.embedding < :threshold)
                         OR
                         -- Text-based matching
                         (
                           -- Exact match (case insensitive)
                           LOWER(t1.name) = t2.lower_name
                           OR
                           -- Country/demonym pairs
                           (LENGTH(t1.name) > 3 AND LENGTH(t2.name) > 3 AND (
                             (LOWER(t1.name) LIKE t2.lower_name || '%' AND LENGTH(t1.name) - LENGTH(t2.name) <= 3)
                             OR
                             (t2.lower_name LIKE LOWER(t1.name) || '%' AND LENGTH(t2.name) - LENGTH(t1.name) <= 3)
                           ))
                         )
                       ) as has_match
                FROM documents d
                INNER JOIN document_tags dt ON d.id = dt.document_id
                INNER JOIN tags t1 ON dt.tag_id = t1.id
                CROSS JOIN folder_tag_info t2
                WHERE d.folder_id = :folder_id
                  AND d.archived_at IS NULL
                GROUP BY d.id, d.filename
            )
            UPDATE documents
            SET folder_id = NULL
            WHERE folder_id = :folder_id
              AND archived_at IS NULL
              AND (
                -- Remove if no tags
                NOT EXISTS (
                    SELECT 1 FROM document_tags 
                    WHERE document_id = documents.id
                )
                OR
                -- Remove if no matching tags
                id IN (
                    SELECT id FROM document_matches
                    WHERE NOT has_match
                )
                OR
                -- Remove if document has tags but they're not in the matches
                (EXISTS (
                    SELECT 1 FROM document_tags dt
                    WHERE dt.document_id = documents.id
                ) AND id NOT IN (
                    SELECT id FROM document_matches
                ))
              )
            RETURNING id, filename
        """
        )

        result = await db.execute(
            remove_docs_query,
            {
                "folder_tag_ids": folder_tag_ids,
                "folder_id": str(folder.id),
                "threshold": similarity_threshold,
            },
        )

        removed_docs = result.fetchall()
        for doc_id, filename in removed_docs:
            logger.info(
                f"Removed document '{filename}' (ID: {doc_id}) from folder - no matching tags by similarity"
            )

    async def sync_document_folders(self, db: AsyncSession, document: Document) -> None:
        """Update folder when a document's tags change using SQL-side similarity matching."""
        # Load document tags
        await db.refresh(document, ["tags"])

        # If no tags on document, remove from any folder
        if not document.tags:
            document.folder_id = None
            return

        logger.info(
            f"Using SQL-side similarity for folder matching. Document has {len(document.tags)} tags"
        )

        # Get document tag IDs
        doc_tag_ids = [tag.id for tag in document.tags]

        # Query to find the best matching folder using similarity
        similarity_threshold = (
            0.3  # Cosine distance threshold (1 - similarity = 0.7 = 70%)
        )
        min_match_score = 0.5  # Minimum weighted score to assign to folder

        best_folder_query = text(
            """
            WITH document_tag_info AS (
                SELECT id, embedding, name, LOWER(name) as lower_name
                FROM tags
                WHERE id = ANY(:doc_tag_ids)
            ),
            folder_matches AS (
                SELECT f.id, f.name,
                       COUNT(DISTINCT CASE 
                           WHEN (
                             -- Embedding similarity match
                             (dt.embedding IS NOT NULL AND t.embedding IS NOT NULL 
                              AND dt.embedding <-> t.embedding < :threshold)
                             OR
                             -- Text-based matching
                             (
                               -- Exact match
                               dt.lower_name = LOWER(t.name)
                               OR
                               -- Country/demonym pairs
                               (LENGTH(dt.name) > 3 AND LENGTH(t.name) > 3 AND (
                                 (dt.lower_name LIKE LOWER(t.name) || '%' AND LENGTH(dt.name) - LENGTH(t.name) <= 3)
                                 OR
                                 (LOWER(t.name) LIKE dt.lower_name || '%' AND LENGTH(t.name) - LENGTH(dt.name) <= 3)
                               ))
                             )
                           ) THEN dt.id 
                       END) as match_count,
                       COUNT(DISTINCT ft.tag_id) as folder_tag_count,
                       AVG(CASE 
                           WHEN dt.embedding IS NOT NULL AND t.embedding IS NOT NULL 
                           THEN 1 - (dt.embedding <-> t.embedding)
                           ELSE 0.7  -- Default similarity for text matches
                       END) as avg_similarity,
                       -- Calculate weighted score
                       (CAST(COUNT(DISTINCT CASE 
                           WHEN (
                             (dt.embedding IS NOT NULL AND t.embedding IS NOT NULL 
                              AND dt.embedding <-> t.embedding < :threshold)
                             OR
                             (
                               dt.lower_name = LOWER(t.name)
                               OR
                               (LENGTH(dt.name) > 3 AND LENGTH(t.name) > 3 AND (
                                 (dt.lower_name LIKE LOWER(t.name) || '%' AND LENGTH(dt.name) - LENGTH(t.name) <= 3)
                                 OR
                                 (LOWER(t.name) LIKE dt.lower_name || '%' AND LENGTH(t.name) - LENGTH(dt.name) <= 3)
                               ))
                             )
                           ) THEN dt.id 
                       END) AS FLOAT) / CAST(COUNT(DISTINCT dta.id) AS FLOAT)) as weighted_score
                FROM folders f
                INNER JOIN folder_tags ft ON f.id = ft.folder_id
                INNER JOIN tags t ON ft.tag_id = t.id
                CROSS JOIN document_tag_info dt
                -- Get total document tags for weighting
                CROSS JOIN LATERAL (
                    SELECT COUNT(*) as id FROM document_tag_info
                ) dta
                WHERE f.user_id = :user_id
                  AND f.archived_at IS NULL
                GROUP BY f.id, f.name, dta.id
                HAVING COUNT(DISTINCT CASE 
                    WHEN (
                      -- Embedding similarity match
                      (dt.embedding IS NOT NULL AND t.embedding IS NOT NULL 
                       AND dt.embedding <-> t.embedding < :threshold)
                      OR
                      -- Text-based matching
                      (
                        dt.lower_name = LOWER(t.name)
                        OR
                        (LENGTH(dt.name) > 3 AND LENGTH(t.name) > 3 AND (
                          (dt.lower_name LIKE LOWER(t.name) || '%' AND LENGTH(dt.name) - LENGTH(t.name) <= 3)
                          OR
                          (LOWER(t.name) LIKE dt.lower_name || '%' AND LENGTH(t.name) - LENGTH(dt.name) <= 3)
                        ))
                      )
                    ) THEN dt.id 
                END) > 0
                ORDER BY weighted_score DESC
                LIMIT 1
            )
            SELECT id, name, match_count, folder_tag_count, avg_similarity, weighted_score
            FROM folder_matches
        """
        )

        result = await db.execute(
            best_folder_query,
            {
                "doc_tag_ids": doc_tag_ids,
                "user_id": str(document.user_id),
                "threshold": similarity_threshold,
                "min_score": min_match_score,
            },
        )

        best_match = result.fetchone()
        if best_match:
            folder_id, folder_name, match_count, _, avg_similarity, weighted_score = (
                best_match
            )
            logger.info(
                f"Found best matching folder '{folder_name}' (ID: {folder_id}) "
                f"with {match_count} tag matches, avg similarity: {avg_similarity:.2f}, "
                f"weighted score: {weighted_score:.2f}"
            )
            document.folder_id = folder_id
        else:
            logger.info("No folder matches document tags with sufficient similarity")
            document.folder_id = None
