"""Dependencies for Chat domain."""

from typing import Annotated

from fastapi import Depends

from .async_service import AsyncChatService


def get_async_chat_service() -> AsyncChatService:
    """Get async chat service instance."""
    return AsyncChatService()


AsyncChatServiceDep = Annotated[AsyncChatService, Depends(get_async_chat_service)]