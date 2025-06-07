#!/usr/bin/env python3
"""Script to check summary content in the database."""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload

from src.database.models import Document, Summary, User
from src.config import get_settings


async def check_summaries():
    """Check summaries in the database."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get recent summaries
        result = await session.execute(
            select(Summary, Document)
            .join(Document, Summary.document_id == Document.id)
            .order_by(Summary.created_at.desc())
            .limit(10)
        )
        
        print("\nRecent summaries:")
        print("=" * 80)
        
        for summary, document in result:
            print(f"\nDocument: {document.filename}")
            print(f"Summary ID: {summary.id}")
            print(f"Created: {summary.created_at}")
            print(f"Summary text (first 200 chars):")
            print(f"  {summary.summary_text[:200]}...")
            
            # Check if summary text looks like a file path
            if summary.summary_text.startswith('/') and len(summary.summary_text) < 200:
                print("  ⚠️  WARNING: Summary text looks like a file path!")
            
            print(f"Word count: {summary.summary_word_count}")
            print(f"Model: {summary.llm_provider} - {summary.llm_model}")
            print("-" * 80)


async def fix_summary_if_needed(summary_id: str):
    """Check and potentially fix a specific summary."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get the summary
        result = await session.execute(
            select(Summary, Document)
            .join(Document, Summary.document_id == Document.id)
            .where(Summary.id == UUID(summary_id))
        )
        
        row = result.one_or_none()
        if not row:
            print(f"Summary {summary_id} not found")
            return
            
        summary, document = row
        
        print(f"\nChecking summary {summary_id}")
        print(f"Document: {document.filename}")
        print(f"Current summary text: {summary.summary_text}")
        
        # Check if it looks like a file path
        if summary.summary_text.startswith('/') and 'TemporaryItems' in summary.summary_text:
            print("\n⚠️  This appears to be a file path, not summary content!")
            print("The summary was likely corrupted during processing.")
            print("\nTo fix this, you would need to:")
            print("1. Re-process the original document")
            print("2. Or manually update the summary text in the database")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        if len(sys.argv) < 3:
            print("Usage: python check_summary_content.py --fix <summary_id>")
            sys.exit(1)
        
        summary_id = sys.argv[2]
        asyncio.run(fix_summary_if_needed(summary_id))
    else:
        print("Checking summary content in database...")
        asyncio.run(check_summaries())
        print("\nTo check a specific summary, run:")
        print("  python check_summary_content.py --fix <summary_id>")