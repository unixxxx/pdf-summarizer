#!/usr/bin/env python3
"""Debug script to check tag generation and database state."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Set up environment
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_summarizer")


async def main():
    # Import after path setup
    from src.config import get_settings
    from src.database.models import Document, Tag, document_tags
    from src.summarization.service import SummarizerService
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.orm import selectinload
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    print("Tag Debugging Script")
    print("=" * 60)
    
    # Test 1: Check database state
    print("\n1. DATABASE STATE CHECK")
    print("-" * 40)
    
    async with AsyncSessionLocal() as session:
        # Count documents
        total_docs = await session.scalar(select(func.count(Document.id)))
        print(f"Total documents: {total_docs}")
        
        # Count tags
        total_tags = await session.scalar(select(func.count(Tag.id)))
        print(f"Total tags: {total_tags}")
        
        # Count document-tag relationships
        total_relations = await session.scalar(
            select(func.count()).select_from(document_tags)
        )
        print(f"Total document-tag relationships: {total_relations}")
        
        # List all tags
        if total_tags > 0:
            print("\nExisting tags:")
            tags = await session.scalars(select(Tag).limit(20))
            for tag in tags:
                print(f"  - {tag.name} (slug: {tag.slug}, color: {tag.color})")
    
    # Test 2: Test tag generation
    print("\n\n2. TAG GENERATION TEST")
    print("-" * 40)
    
    summarizer = SummarizerService(settings)
    
    test_text = """
    Artificial Intelligence and Machine Learning are transforming the technology landscape. 
    Python programming has become essential for data science and AI development. 
    This technical tutorial covers deep learning fundamentals using TensorFlow and PyTorch.
    """
    
    test_summary = "AI and ML guide covering Python programming for deep learning with TensorFlow."
    
    print("Test text preview:", test_text[:100] + "...")
    print("Test summary:", test_summary)
    
    try:
        tags = await summarizer.generate_tags(test_text, test_summary)
        print(f"\nGenerated {len(tags)} tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. '{tag}'")
    except Exception as e:
        print(f"ERROR generating tags: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check recent documents
    print("\n\n3. RECENT DOCUMENTS CHECK")
    print("-" * 40)
    
    async with AsyncSessionLocal() as session:
        recent_docs = await session.scalars(
            select(Document)
            .options(selectinload(Document.tags))
            .order_by(Document.created_at.desc())
            .limit(5)
        )
        
        for doc in recent_docs:
            print(f"\nDocument: {doc.filename}")
            print(f"  Created: {doc.created_at}")
            print(f"  File hash: {doc.file_hash[:20]}...")
            tag_names = [t.name for t in doc.tags]
            print(f"  Tags: {tag_names if tag_names else 'NO TAGS'}")
    
    # Test 4: Full summarization test
    print("\n\n4. FULL SUMMARIZATION TEST")
    print("-" * 40)
    
    try:
        result = await summarizer.summarize_pdf(
            test_text, 
            max_length=100, 
            format="paragraph"
        )
        
        print("Summarization result:")
        print(f"  Summary: {result['summary'][:100]}...")
        print(f"  Tags in result: {result.get('tags', 'NO TAGS KEY')}")
        print(f"  Stats: {result['stats']}")
        
    except Exception as e:
        print(f"ERROR in summarization: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Debug complete!")


if __name__ == "__main__":
    asyncio.run(main())