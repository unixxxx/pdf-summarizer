"""Service for intelligently organizing documents into folders based on tag similarity."""

import logging
from uuid import UUID

from shared.models import Document, Folder
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..common.embeddings_service import get_embedding_service

logger = logging.getLogger(__name__)


class DocumentOrganizeService:
    """Service for organizing documents into folders based on tag similarity."""
    
    def __init__(self):
        """Initialize the organize service."""
        self.embedding_service = None
        self.similarity_threshold = 0.3  # Minimum similarity score to consider a match
    
    async def get_organization_suggestions(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> dict[str, any]:
        """
        Get suggestions for organizing unfiled documents into folders based on tag similarity.
        
        Args:
            user_id: The user ID
            db: Database session
            
        Returns:
            Dictionary with organization suggestions
        """
        # Initialize embedding service if needed
        if self.embedding_service is None:
            self.embedding_service = await get_embedding_service()
        
        # Get all unfiled documents with their tags
        unfiled_docs_query = (
            select(Document)
            .options(selectinload(Document.tags))
            .where(
                and_(
                    Document.user_id == user_id,
                    Document.folder_id.is_(None),
                    Document.archived_at.is_(None)
                )
            )
        )
        
        result = await db.execute(unfiled_docs_query)
        unfiled_documents = result.scalars().all()
        
        if not unfiled_documents:
            return {
                "message": "No unfiled documents to organize",
                "organized_count": 0,
                "suggestions": []
            }
        
        # Get all folders with their tags
        folders_query = (
            select(Folder)
            .options(selectinload(Folder.tags))
            .where(
                and_(
                    Folder.user_id == user_id,
                    Folder.archived_at.is_(None)
                )
            )
        )
        
        result = await db.execute(folders_query)
        folders = result.scalars().all()
        
        if not folders:
            return {
                "message": "No folders available for organization",
                "organized_count": 0,
                "suggestions": []
            }
        
        # Build folder tag embeddings
        folder_embeddings = await self._build_folder_embeddings(folders, db)
        
        # Find best folder matches for each document
        suggestions = []
        
        for doc in unfiled_documents:
            if not doc.tags:
                continue  # Skip documents without tags
            
            best_match = await self._find_best_folder_match(
                doc, folders, folder_embeddings, db
            )
            
            if best_match:
                suggestions.append({
                    "document_id": str(doc.id),
                    "document_name": doc.filename,
                    "document_tags": [tag.name for tag in doc.tags],
                    "suggested_folder_id": str(best_match["folder"].id),
                    "suggested_folder_name": best_match["folder"].name,
                    "folder_tags": [tag.name for tag in best_match["folder"].tags],
                    "similarity_score": float(best_match["score"]),
                    "matching_tags": best_match["matching_tags"]
                })
        
        return {
            "suggestions": suggestions,
            "total_unfiled": len(unfiled_documents),
            "total_with_tags": len([d for d in unfiled_documents if d.tags])
        }
    
    async def apply_organization(
        self,
        user_id: UUID,
        assignments: list[dict[str, str]],
        db: AsyncSession
    ) -> dict[str, any]:
        """
        Apply document organization by moving documents to assigned folders.
        
        Args:
            user_id: The user ID
            assignments: List of document-folder assignments
            db: Database session
            
        Returns:
            Dictionary with organization results
        """
        if not assignments:
            return {
                "message": "No documents to organize",
                "organized_count": 0
            }
        
        organized_count = 0
        errors = []
        
        for assignment in assignments:
            try:
                document_id = UUID(assignment["document_id"])
                folder_id = UUID(assignment["folder_id"])
                
                # Get document and verify ownership
                doc_result = await db.execute(
                    select(Document).where(
                        and_(
                            Document.id == document_id,
                            Document.user_id == user_id,
                            Document.folder_id.is_(None),
                            Document.archived_at.is_(None)
                        )
                    )
                )
                document = doc_result.scalar_one_or_none()
                
                if not document:
                    errors.append(f"Document {document_id} not found or already organized")
                    continue
                
                # Verify folder exists and user owns it
                folder_result = await db.execute(
                    select(Folder).where(
                        and_(
                            Folder.id == folder_id,
                            Folder.user_id == user_id,
                            Folder.archived_at.is_(None)
                        )
                    )
                )
                folder = folder_result.scalar_one_or_none()
                
                if not folder:
                    errors.append(f"Folder {folder_id} not found")
                    continue
                
                # Move document to folder
                document.folder_id = folder_id
                organized_count += 1
                
            except ValueError as e:
                errors.append(f"Invalid UUID format: {str(e)}")
            except Exception as e:
                errors.append(f"Error processing assignment: {str(e)}")
        
        # Commit all changes
        if organized_count > 0:
            await db.commit()
        
        result = {
            "message": f"Organized {organized_count} documents",
            "organized_count": organized_count
        }
        
        if errors:
            result["errors"] = errors
        
        return result
    
    async def _build_folder_embeddings(
        self,
        folders: list[Folder],
        db: AsyncSession
    ) -> dict[UUID, list[float]]:
        """Build average embeddings for each folder based on its tags."""
        folder_embeddings = {}
        
        for folder in folders:
            if not folder.tags:
                continue
            
            # Get tag embeddings
            tag_embeddings = []
            for tag in folder.tags:
                if tag.embedding is not None:
                    # Convert to list if it's a numpy array
                    embedding = tag.embedding.tolist() if hasattr(tag.embedding, 'tolist') else tag.embedding
                    tag_embeddings.append(embedding)
                else:
                    # Generate embedding for tag if it doesn't have one
                    embedding = await self.embedding_service.aembed_query(tag.name)
                    tag.embedding = embedding
                    tag_embeddings.append(embedding)
            
            if tag_embeddings:
                # Calculate average embedding for the folder
                avg_embedding = [
                    sum(emb[i] for emb in tag_embeddings) / len(tag_embeddings)
                    for i in range(len(tag_embeddings[0]))
                ]
                folder_embeddings[folder.id] = avg_embedding
        
        return folder_embeddings
    
    async def _find_best_folder_match(
        self,
        document: Document,
        folders: list[Folder],
        folder_embeddings: dict[UUID, list[float]],
        db: AsyncSession
    ) -> dict[str, any] | None:
        """Find the best folder match for a document based on tag similarity."""
        if not document.tags:
            return None
        
        # Build document embedding from its tags
        doc_embeddings = []
        for tag in document.tags:
            if tag.embedding is not None:
                # Convert to list if it's a numpy array
                embedding = list(tag.embedding) if hasattr(tag.embedding, 'tolist') else tag.embedding
                doc_embeddings.append(embedding)
            else:
                # Generate embedding for tag if it doesn't have one
                embedding = await self.embedding_service.aembed_query(tag.name)
                tag.embedding = embedding
                doc_embeddings.append(embedding)
        
        if not doc_embeddings:
            return None
        
        # Calculate average embedding for the document
        doc_avg_embedding = [
            sum(emb[i] for emb in doc_embeddings) / len(doc_embeddings)
            for i in range(len(doc_embeddings[0]))
        ]
        
        # Find best matching folder
        best_match = None
        best_score = 0.0
        
        for folder in folders:
            if folder.id not in folder_embeddings:
                continue
            
            # Calculate cosine similarity
            folder_embedding = folder_embeddings[folder.id]
            similarity = self._cosine_similarity(doc_avg_embedding, folder_embedding)
            
            # Also check for exact tag matches
            doc_tag_names = {tag.name.lower() for tag in document.tags}
            folder_tag_names = {tag.name.lower() for tag in folder.tags}
            matching_tags = doc_tag_names.intersection(folder_tag_names)
            
            # Boost score if there are exact tag matches
            if matching_tags:
                similarity = min(1.0, similarity + 0.1 * len(matching_tags))
            
            if similarity > best_score:
                best_score = similarity
                best_match = {
                    "folder": folder,
                    "score": float(similarity),
                    "matching_tags": list(matching_tags)
                }
        
        return best_match if best_score >= self.similarity_threshold else None
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)