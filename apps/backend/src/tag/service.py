"""Simplified tag management service without LLM dependency."""

import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Tag, document_tags
from ..embeddings.service import EmbeddingsService
from .schemas import TagResponse

logger = logging.getLogger(__name__)


class TagService:
    """Service for managing document tags."""
    
    # Predefined colors for tags (cycling through them)
    TAG_COLORS = [
        "#3B82F6",  # Blue
        "#10B981",  # Emerald
        "#F59E0B",  # Amber
        "#EF4444",  # Red
        "#8B5CF6",  # Violet
        "#EC4899",  # Pink
        "#14B8A6",  # Teal
        "#F97316",  # Orange
        "#6366F1",  # Indigo
        "#84CC16",  # Lime
    ]
    
    def __init__(self, embedding_service: EmbeddingsService | None = None):
        """Initialize with optional embedding service."""
        self.embedding_service = embedding_service
    
    async def find_or_create_tags(
        self,
        tag_data_list: list[dict[str, Any]],
        db: AsyncSession,
    ) -> list[Tag]:
        """Find existing tags or create new ones with similarity matching."""
        tags = []
        
        for tag_data in tag_data_list:
            # First, check for exact match by slug
            result = await db.execute(
                select(Tag).where(Tag.slug == tag_data["slug"])
            )
            existing_tag = result.scalar_one_or_none()
            
            if existing_tag:
                tags.append(existing_tag)
                continue
            
            # If no exact match and embedding service is available, check for similar tags
            similar_tag = None
            if self.embedding_service:
                try:
                    similar_tag = await self.embedding_service.find_or_create_similar_tag(
                        tag_name=tag_data["name"],
                        db=db,
                        similarity_threshold=0.9  # High threshold to avoid false matches
                    )
                except Exception as e:
                    logger.warning(f"Failed to check tag similarity: {str(e)}")
            
            if similar_tag:
                logger.info(f"Using existing similar tag '{similar_tag.name}' instead of creating '{tag_data['name']}'")
                tags.append(similar_tag)
            else:
                # Create new tag
                new_tag = Tag(
                    name=tag_data["name"],
                    slug=tag_data["slug"],
                    color=tag_data.get("color") or self.TAG_COLORS[len(tags) % len(self.TAG_COLORS)],
                )
                db.add(new_tag)
                await db.flush()
                
                # Generate embedding for the new tag
                if self.embedding_service:
                    # Generate embeddings synchronously
                    try:
                        await self.embedding_service.update_tag_embedding(
                            tag_id=new_tag.id,
                            tag_name=new_tag.name,
                            db=db
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for tag '{new_tag.name}': {str(e)}")
                
                tags.append(new_tag)
        
        return tags
    
    async def associate_tags_with_document(
        self,
        document_id: UUID,
        tag_ids: list[UUID],
        db: AsyncSession,
    ) -> None:
        """Associate tags with a document."""
        # Remove existing associations
        await db.execute(
            document_tags.delete().where(
                document_tags.c.document_id == document_id
            )
        )
        
        # Create new associations using bulk insert
        if tag_ids:
            await db.execute(
                document_tags.insert(),
                [{"document_id": document_id, "tag_id": tag_id} 
                 for tag_id in tag_ids]
            )
    
    async def get_all_tags(
        self,
        db: AsyncSession,
    ) -> list[TagResponse]:
        """Get all tags for suggestions."""
        result = await db.execute(
            select(Tag).order_by(Tag.name)
        )
        tags = result.scalars().all()
        
        return [
            TagResponse(
                id=tag.id,
                name=tag.name,
                slug=tag.slug,
                color=tag.color,
            )
            for tag in tags
        ]
    
    def _create_slug(self, name: str) -> str:
        """Create a URL-friendly slug from tag name."""
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')