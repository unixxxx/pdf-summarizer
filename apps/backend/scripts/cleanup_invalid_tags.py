#!/usr/bin/env python3
"""Clean up invalid tags in the database."""

import asyncio
import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config import get_settings
from shared.models import Tag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_invalid_tags():
    """Remove or fix invalid tags."""
    settings = get_settings()
    
    # Create database session
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find tags with invalid names (less than 2 characters)
        result = await session.execute(
            select(Tag).where(Tag.name.in_(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]))
        )
        invalid_tags = result.scalars().all()
        
        if invalid_tags:
            logger.info(f"Found {len(invalid_tags)} invalid tags to remove")
            
            for tag in invalid_tags:
                logger.info(f"Removing invalid tag: '{tag.name}' (id: {tag.id})")
                await session.delete(tag)
            
            await session.commit()
            logger.info("Invalid tags removed")
        else:
            logger.info("No invalid tags found")
        
        # Update any tags with null description to empty string
        await session.execute(
            update(Tag).where(Tag.description.is_(None)).values(description="")
        )
        await session.commit()
        logger.info("Updated null descriptions to empty strings")
        
        # List remaining tags
        result = await session.execute(select(Tag).order_by(Tag.name))
        tags = result.scalars().all()
        
        logger.info(f"\nRemaining tags ({len(tags)}):")
        for tag in tags:
            logger.info(f"  - {tag.name} (slug: {tag.slug})")


if __name__ == "__main__":
    asyncio.run(cleanup_invalid_tags())