"""Test that models are properly importable."""

import pytest


def test_models_importable():
    """Test that all models can be imported."""
    from shared.models import (
        Base,
        DocumentStatus,
        User,
        Document,
        DocumentChunk,
        Summary,
        Chat,
        ChatMessage,
        Tag,
        Folder,
        JobProgress,
        document_tags,
        folder_tags,
    )
    
    # Basic assertions to ensure imports worked
    assert Base is not None
    assert DocumentStatus.PENDING == "pending"
    assert User.__tablename__ == "users"
    assert Document.__tablename__ == "documents"
    assert DocumentChunk.__tablename__ == "document_chunks"
    assert Summary.__tablename__ == "summaries"
    assert Chat.__tablename__ == "chats"
    assert ChatMessage.__tablename__ == "chat_messages"
    assert Tag.__tablename__ == "tags"
    assert Folder.__tablename__ == "folders"
    assert JobProgress.__tablename__ == "job_progress"
    assert document_tags.name == "document_tags"
    assert folder_tags.name == "folder_tags"