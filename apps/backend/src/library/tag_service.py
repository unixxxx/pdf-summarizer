"""Tag management service following DDD principles."""

import json
import logging
import re
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Tag, document_tags

logger = logging.getLogger(__name__)


class TagGenerationRequest(BaseModel):
    """Schema for tag generation requests."""
    content: str
    filename: str
    max_tags: int = 5


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
    
    def __init__(self, llm_service):
        """Initialize with LLM service for tag generation."""
        self.llm_service = llm_service
    
    async def generate_tags_for_document(
        self,
        request: TagGenerationRequest,
    ) -> list[dict[str, Any]]:
        """Generate tags for a document using LLM."""
        # Truncate content for tag generation
        max_content_length = 4000
        content_for_tags = request.content[:max_content_length]
        
        prompt = f"""Analyze this document and generate between 3 to {request.max_tags} relevant tags.

Document: {request.filename}
Content: {content_for_tags}

Generate tags that capture:
1. Main topics and themes
2. Document type or category
3. Key concepts or technologies mentioned
4. Industry or domain relevance

Return ONLY a JSON object, nothing else. No explanation, no additional text.
{{"tags": ["machine-learning", "python", "data-science", "tutorial", "neural-networks"]}}

Rules:
- Output ONLY the JSON object
- Use lowercase letters
- Use hyphens instead of spaces (e.g., "machine-learning" NOT "machine learning")
- Keep tags concise (1-3 words)
- No explanation or additional text
"""
        
        try:
            # Call the LLM
            response = await self.llm_service.ainvoke(prompt)
            
            # Extract content from response
            content = response.content.strip()
            
            # Try to parse JSON response
            # Remove any markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON - first try to find JSON object in response
            json_str = content
            
            # Extract JSON object if there's extra text
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
            
            try:
                data = json.loads(json_str)
                if isinstance(data, dict) and "tags" in data:
                    tags_list = data["tags"]
                else:
                    logger.warning(f"Invalid JSON structure: {data}")
                    tags_list = []
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from LLM response: {e}\nContent: {json_str[:200]}")
                tags_list = []
            
            # Validate and clean tags
            if not isinstance(tags_list, list) or not tags_list:
                logger.warning("No valid tags in response")
                return []
            
            # Convert to tag format
            generated_tags = []
            for i, tag in enumerate(tags_list[:request.max_tags]):
                if isinstance(tag, str) and tag.strip():
                    # Clean the tag
                    tag = tag.lower().strip()
                    # Ensure it uses hyphens instead of spaces
                    tag = tag.replace(' ', '-')
                    # Remove any invalid characters
                    tag = ''.join(c for c in tag if c.isalnum() or c == '-')
                    # Remove multiple consecutive hyphens
                    while '--' in tag:
                        tag = tag.replace('--', '-')
                    tag = tag.strip('-')
                    
                    if tag and len(tag) > 1:
                        generated_tags.append({
                            "name": tag.replace('-', ' ').title(),  # Convert back to title case for display
                            "slug": tag,  # Keep the hyphenated version as slug
                            "color": self.TAG_COLORS[i % len(self.TAG_COLORS)]
                        })
            
            if generated_tags:
                logger.info(f"Generated {len(generated_tags)} tags for document")
                return generated_tags
            else:
                logger.warning("No valid tags generated after processing")
                return []
                
        except Exception as e:
            logger.warning(f"Tag generation failed: {e}. Returning empty tags.")
            return []
    
    async def find_or_create_tags(
        self,
        tag_data_list: list[dict[str, Any]],
        db: AsyncSession,
    ) -> list[Tag]:
        """Find existing tags or create new ones."""
        tags = []
        
        for tag_data in tag_data_list:
            # Check if tag exists
            result = await db.execute(
                select(Tag).where(Tag.slug == tag_data["slug"])
            )
            existing_tag = result.scalar_one_or_none()
            
            if existing_tag:
                tags.append(existing_tag)
            else:
                # Create new tag
                new_tag = Tag(
                    name=tag_data["name"],
                    slug=tag_data["slug"],
                    color=tag_data.get("color"),
                )
                db.add(new_tag)
                await db.flush()
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
        
        # Create new associations
        for tag_id in tag_ids:
            await db.execute(
                document_tags.insert().values(
                    document_id=document_id,
                    tag_id=tag_id,
                )
            )
    
    async def get_all_tags_with_counts(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Get all tags with their document counts (only tags with at least one document)."""
        result = await db.execute(
            select(
                Tag,
                func.count(document_tags.c.document_id).label("document_count")
            )
            .join(document_tags, Tag.id == document_tags.c.tag_id)  # Using join instead of outerjoin
            .group_by(Tag.id)
            .having(func.count(document_tags.c.document_id) > 0)  # Filter at SQL level
            .order_by(func.count(document_tags.c.document_id).desc())
        )
        
        return [
            {
                "id": str(tag.id),
                "name": tag.name,
                "slug": tag.slug,
                "color": tag.color,
                "document_count": count,
            }
            for tag, count in result.all()
        ]
    
    def _create_slug(self, name: str) -> str:
        """Create a URL-friendly slug from tag name."""
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
