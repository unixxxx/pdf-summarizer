"""Embeddings service for search."""

import logging

from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


_embedding_service = None

async def get_embedding_service():
    """Get configured embedding service."""
    global _embedding_service
    
    # Return cached instance if available
    if _embedding_service is not None:
        return _embedding_service
    
    try:
        if settings.llm_provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            _embedding_service = OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                model="text-embedding-3-small",  # Cheaper and faster
                dimensions=1536,  # Standard dimension for compatibility
            )
        
        elif settings.llm_provider == "ollama":
            # Use gte-qwen2-1.5b-instruct-embed-f16 for 1536 dimensions
            # or configure via settings
            _embedding_service = OllamaEmbeddings(
                model=settings.ollama_embedding_model,
                base_url=settings.ollama_base_url,
            )
        
        else:
            raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
        
        return _embedding_service
            
    except Exception as e:
        logger.error(f"Failed to initialize embeddings: {e}")
        raise