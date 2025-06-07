#!/usr/bin/env python3
"""Test script to debug tag generation and saving flow."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Settings
from summarization.service import SummarizerService


async def test_tag_generation():
    """Test tag generation with sample text."""
    settings = Settings()
    summarizer = SummarizerService(settings)
    
    # Sample text about machine learning
    sample_text = """
    Machine learning is a subset of artificial intelligence that focuses on the development of algorithms 
    and statistical models that enable computer systems to improve their performance on a specific task 
    through experience. Deep learning, a subfield of machine learning, uses neural networks with multiple 
    layers to progressively extract higher-level features from raw input. Python has become the dominant 
    programming language for machine learning due to libraries like TensorFlow, PyTorch, and scikit-learn.
    """
    
    sample_summary = """
    Machine learning enables computers to learn from experience using algorithms and statistical models. 
    Deep learning uses multi-layer neural networks for feature extraction. Python dominates ML development 
    with libraries like TensorFlow and PyTorch.
    """
    
    print("Testing tag generation...")
    print(f"Text sample length: {len(sample_text)} chars")
    print(f"Summary length: {len(sample_summary)} chars")
    print("-" * 50)
    
    try:
        tags = await summarizer.generate_tags(sample_text, sample_summary)
        print(f"Generated {len(tags)} tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. '{tag}'")
    except Exception as e:
        print(f"Error generating tags: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_full_summarization():
    """Test full summarization pipeline including tag generation."""
    settings = Settings()
    summarizer = SummarizerService(settings)
    
    # Longer sample text
    sample_pdf_text = """
    Introduction to Cloud Computing
    
    Cloud computing has revolutionized the way businesses operate by providing on-demand access to computing 
    resources over the internet. This technology enables organizations to scale their infrastructure dynamically, 
    reduce capital expenditures, and improve operational efficiency.
    
    The three main service models of cloud computing are:
    
    1. Infrastructure as a Service (IaaS): Provides virtualized computing resources over the internet. 
    Examples include Amazon EC2, Google Compute Engine, and Microsoft Azure Virtual Machines.
    
    2. Platform as a Service (PaaS): Offers a development platform that allows developers to build, test, 
    and deploy applications without managing the underlying infrastructure. Examples include Heroku, 
    Google App Engine, and AWS Elastic Beanstalk.
    
    3. Software as a Service (SaaS): Delivers software applications over the internet on a subscription basis. 
    Examples include Salesforce, Microsoft 365, and Google Workspace.
    
    Security in cloud computing remains a critical concern. Organizations must implement proper access controls, 
    encryption, and compliance measures to protect their data. Multi-factor authentication, regular security 
    audits, and data backup strategies are essential components of a robust cloud security framework.
    
    The future of cloud computing includes emerging technologies such as edge computing, serverless architectures, 
    and artificial intelligence integration. These advancements will continue to transform how businesses 
    leverage technology to drive innovation and competitive advantage.
    """
    
    print("\nTesting full summarization pipeline...")
    print(f"Text length: {len(sample_pdf_text)} chars")
    print("-" * 50)
    
    try:
        result = await summarizer.summarize_pdf(sample_pdf_text, max_length=150, format="paragraph")
        
        print("Summary generated successfully!")
        print(f"Summary: {result['summary'][:200]}..." if len(result['summary']) > 200 else f"Summary: {result['summary']}")
        print(f"\nStats: {result['stats']}")
        print(f"\nGenerated {len(result.get('tags', []))} tags:")
        for i, tag in enumerate(result.get('tags', []), 1):
            print(f"  {i}. '{tag}'")
            
    except Exception as e:
        print(f"Error in summarization: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Tag Generation Test Script")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_tag_generation())
    asyncio.run(test_full_summarization())