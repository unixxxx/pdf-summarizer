#!/usr/bin/env python3
"""Script to check document tags in the database."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload

from src.database.models import Document, Tag, Summary
from src.config import get_settings


async def check_tags():
    """Check tags in the database."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Count total tags
        tag_count = await session.execute(select(func.count(Tag.id)))
        total_tags = tag_count.scalar()
        print(f"\nTotal tags in database: {total_tags}")
        
        # List all tags
        if total_tags > 0:
            tags_result = await session.execute(select(Tag).order_by(Tag.name))
            tags = tags_result.scalars().all()
            print("\nExisting tags:")
            for tag in tags:
                print(f"  - {tag.name} (slug: {tag.slug}, color: {tag.color})")
        
        # Count documents
        doc_count = await session.execute(select(func.count(Document.id)))
        total_docs = doc_count.scalar()
        print(f"\nTotal documents: {total_docs}")
        
        # Check documents with tags
        docs_with_tags = await session.execute(
            select(Document)
            .options(selectinload(Document.tags))
            .order_by(Document.created_at.desc())
            .limit(10)
        )
        documents = docs_with_tags.scalars().all()
        
        print("\nRecent documents and their tags:")
        for doc in documents:
            tag_names = [tag.name for tag in doc.tags]
            print(f"  - {doc.filename[:50]}... Tags: {tag_names if tag_names else 'None'}")
        
        # Check recent summaries to see if tag generation was attempted
        summaries_result = await session.execute(
            select(Summary)
            .order_by(Summary.created_at.desc())
            .limit(5)
        )
        summaries = summaries_result.scalars().all()
        
        print("\nRecent summaries:")
        for summary in summaries:
            print(f"  - Created: {summary.created_at}, Model: {summary.llm_model}")


async def test_tag_generation():
    """Test tag generation logic."""
    print("\n" + "="*50)
    print("Testing tag generation logic")
    print("="*50)
    
    from src.summarization.service import SummarizerService
    from src.config import get_settings
    
    settings = get_settings()
    summarizer = SummarizerService(settings)
    
    # Test text
    test_text = """
    Machine learning is a subset of artificial intelligence that enables 
    computers to learn from data. Python is widely used for machine learning
    due to its extensive libraries like scikit-learn, TensorFlow, and PyTorch.
    This tutorial covers the basics of neural networks and deep learning.
    """
    
    test_summary = """
    This document explains machine learning concepts and Python libraries
    for AI development, focusing on neural networks and deep learning basics.
    """
    
    try:
        tags = await summarizer.generate_tags(test_text, test_summary)
        print(f"\nGenerated tags: {tags}")
    except Exception as e:
        print(f"\nError generating tags: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Checking document tags in database...")
    asyncio.run(check_tags())
    
    print("\n" + "="*50)
    asyncio.run(test_tag_generation())