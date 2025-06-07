#!/usr/bin/env python3
"""Test PDF upload with tag generation."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Create a simple test PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile


def create_test_pdf():
    """Create a test PDF file."""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        c = canvas.Canvas(f.name, pagesize=letter)
        
        # Add content about machine learning
        c.drawString(100, 750, "Introduction to Machine Learning")
        c.drawString(100, 700, "This document covers the fundamentals of machine learning,")
        c.drawString(100, 680, "including supervised learning, unsupervised learning,")
        c.drawString(100, 660, "and deep neural networks. We'll explore Python libraries")
        c.drawString(100, 640, "like TensorFlow, PyTorch, and scikit-learn.")
        c.drawString(100, 600, "Topics covered:")
        c.drawString(120, 580, "- Classification algorithms")
        c.drawString(120, 560, "- Regression techniques")
        c.drawString(120, 540, "- Neural network architectures")
        c.drawString(120, 520, "- Data preprocessing")
        c.drawString(120, 500, "- Model evaluation metrics")
        
        c.save()
        return f.name


async def test_upload():
    """Test PDF upload through the API."""
    import httpx
    import json
    
    # Create test PDF
    pdf_path = create_test_pdf()
    print(f"Created test PDF: {pdf_path}")
    
    # You'll need to get a valid JWT token first
    # For testing, you can get one by logging in through the frontend
    token = os.environ.get("TEST_JWT_TOKEN")
    if not token:
        print("ERROR: Please set TEST_JWT_TOKEN environment variable")
        print("You can get a token by logging in through the frontend and")
        print("checking the localStorage or network requests")
        return
    
    async with httpx.AsyncClient() as client:
        # Upload and summarize PDF
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test_ml_document.pdf', f, 'application/pdf')}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = await client.post(
                'http://localhost:8000/api/v1/pdf/summarize',
                files=files,
                headers=headers,
                params={
                    'max_length': 200,
                    'format': 'paragraph'
                }
            )
        
        if response.status_code == 200:
            result = response.json()
            print("\nUpload successful!")
            print(f"Summary: {result['summary'][:200]}...")
            print(f"Processing time: {result['processing_time']:.2f}s")
            print(f"Stats: {result['summary_stats']}")
        else:
            print(f"\nUpload failed with status {response.status_code}")
            print(f"Response: {response.text}")
    
    # Clean up
    os.unlink(pdf_path)
    
    # Check tags in database
    from src.config import get_settings
    from src.database.models import Document, Tag
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.orm import selectinload
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    print("\n\nChecking database for new tags...")
    async with AsyncSessionLocal() as session:
        # Get the most recent document
        result = await session.execute(
            select(Document)
            .options(selectinload(Document.tags))
            .order_by(Document.created_at.desc())
            .limit(1)
        )
        latest_doc = result.scalar_one_or_none()
        
        if latest_doc:
            print(f"Latest document: {latest_doc.filename}")
            print(f"Tags: {[tag.name for tag in latest_doc.tags]}")
        
        # Check total tags
        tag_count = await session.scalar(select(func.count(Tag.id)))
        print(f"\nTotal tags in database: {tag_count}")


if __name__ == "__main__":
    print("PDF Upload Test")
    print("=" * 60)
    
    # Check if reportlab is installed
    try:
        import reportlab
    except ImportError:
        print("Installing reportlab for PDF generation...")
        os.system("uv pip install reportlab")
    
    asyncio.run(test_upload())