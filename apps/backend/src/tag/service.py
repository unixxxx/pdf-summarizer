"""Simplified tag management service without LLM dependency."""

import logging
import re
from typing import Any
from uuid import UUID

from shared.models import Tag, document_tags
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Embeddings service moved to worker - will be refactored
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
    
    def __init__(self):
        """Initialize tag service."""
        pass
    
    async def find_or_create_tags(
        self,
        tag_data_list: list[dict[str, Any]],
        db: AsyncSession,
    ) -> list[Tag]:
        """Find existing tags or create new ones with similarity matching."""
        tags = []
        new_tag_ids = []
        new_tag_names = []
        
        for tag_data in tag_data_list:
            # First, check for exact match by slug
            result = await db.execute(
                select(Tag).where(Tag.slug == tag_data["slug"])
            )
            existing_tag = result.scalar_one_or_none()
            
            if existing_tag:
                tags.append(existing_tag)
                continue
            
            # Create new tag without similarity check (handled by worker now)
            # Create new tag
            new_tag = Tag(
                name=tag_data["name"],
                slug=tag_data["slug"],
                color=tag_data.get("color") or self.TAG_COLORS[len(tags) % len(self.TAG_COLORS)],
            )
            
            db.add(new_tag)
            await db.flush()
            
            # Collect new tag info for batch embedding generation
            new_tag_ids.append(str(new_tag.id))
            new_tag_names.append(new_tag.name)
            tags.append(new_tag)
        
        # Enqueue job to generate embeddings for all new tags at once
        if new_tag_ids:
            from arq import create_pool
            from arq.connections import RedisSettings
            
            from ..config import get_settings
            
            settings = get_settings()
            if settings.redis_url:
                try:
                    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
                    await redis.enqueue_job(
                        "generate_tag_embeddings",
                        new_tag_ids,  # Pass all new tag IDs at once
                        _queue_name="doculearn:queue"
                    )
                    await redis.close()
                    logger.info(
                        f"Enqueued embedding generation for {len(new_tag_ids)} tags: "
                        f"{', '.join(new_tag_names)}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to enqueue embedding generation for tags: {e}"
                    )
        
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