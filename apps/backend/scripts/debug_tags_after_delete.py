#!/usr/bin/env python3
"""Debug script to check tags after deleting all documents."""

import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.session import async_session
from src.database.models import Tag, Document, document_tags


async def check_tags_and_associations():
    """Check tags and their associations after document deletion."""
    async with async_session() as db:
        # Count total documents
        doc_count_result = await db.execute(select(func.count(Document.id)))
        doc_count = doc_count_result.scalar()
        print(f"\nTotal documents in database: {doc_count}")
        
        # Count total tags
        tag_count_result = await db.execute(select(func.count(Tag.id)))
        tag_count = tag_count_result.scalar()
        print(f"Total tags in database: {tag_count}")
        
        # Count associations in document_tags
        assoc_count_result = await db.execute(
            select(func.count()).select_from(document_tags)
        )
        assoc_count = assoc_count_result.scalar()
        print(f"Total associations in document_tags: {assoc_count}")
        
        # Get all tags with their document counts using the same query as the service
        result = await db.execute(
            select(
                Tag,
                func.count(document_tags.c.document_id).label("document_count")
            )
            .join(document_tags, Tag.id == document_tags.c.tag_id)
            .group_by(Tag.id)
            .having(func.count(document_tags.c.document_id) > 0)
            .order_by(func.count(document_tags.c.document_id).desc())
        )
        
        tags_with_docs = result.all()
        print(f"\nTags with at least one document (using JOIN): {len(tags_with_docs)}")
        
        for tag, count in tags_with_docs[:5]:  # Show first 5
            print(f"  - {tag.name}: {count} documents")
        
        # Also check with LEFT JOIN to see all tags
        result_all = await db.execute(
            select(
                Tag,
                func.count(document_tags.c.document_id).label("document_count")
            )
            .outerjoin(document_tags, Tag.id == document_tags.c.tag_id)
            .group_by(Tag.id)
            .order_by(func.count(document_tags.c.document_id).desc())
        )
        
        all_tags = result_all.all()
        print(f"\nAll tags (using LEFT JOIN): {len(all_tags)}")
        
        # Show tags with 0 documents
        orphan_tags = [tag for tag, count in all_tags if count == 0]
        if orphan_tags:
            print(f"\nOrphan tags (0 documents): {len(orphan_tags)}")
            for tag in orphan_tags[:5]:  # Show first 5
                print(f"  - {tag.name}")
        
        # Check if there are any dangling associations
        dangling_result = await db.execute(
            select(document_tags.c.document_id, document_tags.c.tag_id)
            .outerjoin(Document, Document.id == document_tags.c.document_id)
            .where(Document.id.is_(None))
        )
        dangling = dangling_result.all()
        if dangling:
            print(f"\nWARNING: Found {len(dangling)} dangling associations (document deleted but association remains)")


if __name__ == "__main__":
    asyncio.run(check_tags_and_associations())