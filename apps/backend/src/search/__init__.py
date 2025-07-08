"""Intelligent search module for DocuLearn."""

from .schemas import SearchQuery, SearchResult
from .service import SearchService

__all__ = ["SearchService", "SearchQuery", "SearchResult"]