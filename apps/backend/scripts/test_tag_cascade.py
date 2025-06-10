#!/usr/bin/env python3
"""Test CASCADE deletion for document_tags association."""

import asyncio
from sqlalchemy import select, func, text
from uuid import uuid4

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.session import async_session
from src.database.models import User, Document, Tag, document_tags


async def test_cascade_deletion():
    """Test that deleting a document properly removes associations."""
    async with async_session() as db:
        try:
            # Create a test user
            test_user = User(
                id=uuid4(),
                email=f"test_{uuid4()}@example.com",
                name="Test User",
                provider="google",
                provider_id=str(uuid4())
            )
            db.add(test_user)
            
            # Create a test document
            test_doc = Document(
                id=uuid4(),
                user_id=test_user.id,
                filename="test.pdf",
                file_hash="test_hash_" + str(uuid4()),
                file_size=1000,
                storage_path="test/path",
                extracted_text="Test content",
                word_count=100
            )
            db.add(test_doc)
            
            # Create a test tag
            test_tag = Tag(
                id=uuid4(),
                name="Test Tag",
                slug="test-tag",
                color="#FF0000"
            )
            db.add(test_tag)
            
            await db.flush()
            
            # Create association
            await db.execute(
                document_tags.insert().values(
                    document_id=test_doc.id,
                    tag_id=test_tag.id
                )
            )
            await db.commit()
            
            print("✓ Created test document and tag with association")
            
            # Verify association exists
            assoc_result = await db.execute(
                select(func.count()).select_from(document_tags).where(
                    document_tags.c.document_id == test_doc.id
                )
            )
            assoc_count = assoc_result.scalar()
            print(f"✓ Association exists: {assoc_count} entries")
            
            # Delete the document
            await db.delete(test_doc)
            await db.commit()
            print("✓ Document deleted")
            
            # Check if association was removed
            assoc_after = await db.execute(
                select(func.count()).select_from(document_tags).where(
                    document_tags.c.document_id == test_doc.id
                )
            )
            assoc_count_after = assoc_after.scalar()
            
            if assoc_count_after == 0:
                print("✅ CASCADE DELETE WORKS: Association was removed")
            else:
                print(f"❌ CASCADE DELETE FAILED: {assoc_count_after} associations remain")
            
            # Check if tag still exists (it should)
            tag_result = await db.execute(
                select(Tag).where(Tag.id == test_tag.id)
            )
            tag_still_exists = tag_result.scalar_one_or_none()
            
            if tag_still_exists:
                print("✓ Tag still exists (as expected)")
            else:
                print("❌ Tag was deleted (unexpected)")
                
            # Clean up
            if tag_still_exists:
                await db.delete(tag_still_exists)
            await db.delete(test_user)
            await db.commit()
            print("✓ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
            await db.rollback()
            raise


async def check_current_state():
    """Check current database state."""
    async with async_session() as db:
        # Raw SQL to check associations without joins
        result = await db.execute(
            text("""
                SELECT 
                    dt.document_id,
                    dt.tag_id,
                    d.id as doc_exists,
                    t.name as tag_name
                FROM document_tags dt
                LEFT JOIN documents d ON dt.document_id = d.id
                LEFT JOIN tags t ON dt.tag_id = t.id
                WHERE d.id IS NULL
                LIMIT 10
            """)
        )
        orphaned = result.all()
        
        if orphaned:
            print(f"\n⚠️  Found {len(orphaned)} orphaned associations (document deleted but association remains):")
            for row in orphaned:
                print(f"  - Document ID: {row.document_id}, Tag: {row.tag_name}")
            print("\nThis indicates CASCADE DELETE is not working properly!")
        else:
            print("\n✅ No orphaned associations found")


if __name__ == "__main__":
    print("Testing CASCADE deletion...")
    asyncio.run(test_cascade_deletion())
    
    print("\nChecking current database state...")
    asyncio.run(check_current_state())