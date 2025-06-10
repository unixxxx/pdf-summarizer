#!/usr/bin/env python3
"""Clean up orphaned tags that have no associated documents."""

import asyncio
from sqlalchemy import select, func, delete

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.session import async_session
from src.database.models import Tag, document_tags


async def cleanup_orphaned_tags():
    """Remove tags that have no associated documents."""
    async with async_session() as db:
        # Find orphaned tags using a subquery
        tags_with_docs = select(document_tags.c.tag_id).distinct()
        
        # Find tags NOT in the subquery
        orphaned_tags_query = select(Tag).where(~Tag.id.in_(tags_with_docs))
        
        result = await db.execute(orphaned_tags_query)
        orphaned_tags = result.scalars().all()
        
        if not orphaned_tags:
            print("✅ No orphaned tags found!")
            return
        
        print(f"Found {len(orphaned_tags)} orphaned tags:")
        for tag in orphaned_tags:
            print(f"  - {tag.name} ({tag.slug})")
        
        # Auto-delete in non-interactive mode
        print("\nDeleting orphaned tags...")
        
        if True:  # Always delete in this context
            # Delete orphaned tags
            delete_query = delete(Tag).where(~Tag.id.in_(tags_with_docs))
            result = await db.execute(delete_query)
            await db.commit()
            
            print(f"\n✅ Deleted {result.rowcount} orphaned tags")
        else:
            print("\n❌ Cancelled - no tags were deleted")


if __name__ == "__main__":
    print("Checking for orphaned tags...\n")
    asyncio.run(cleanup_orphaned_tags())