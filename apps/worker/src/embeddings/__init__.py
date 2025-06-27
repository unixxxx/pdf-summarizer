"""Embeddings module for document vector operations."""

from .processor import (
    generate_document_embeddings,
    generate_tag_embeddings,
    update_all_tag_embeddings,
)

__all__ = [
    "generate_document_embeddings",
    "generate_tag_embeddings",
    "update_all_tag_embeddings",
]