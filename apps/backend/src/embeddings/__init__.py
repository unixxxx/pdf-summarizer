"""Embeddings module for document vector operations."""

from .dependencies import EmbeddingsServiceDep
from .service import EmbeddingsService

__all__ = ["EmbeddingsService", "EmbeddingsServiceDep"]