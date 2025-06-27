"""Async chat router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..database.session import get_db
from .async_service import AsyncChatService
from .schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatResponse,
    CreateChatRequest,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/document/{document_id}/session",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or get chat session",
    description="Create a new chat session or get existing active session for a document",
)
async def create_or_get_chat_session(
    document_id: UUID,
    session_data: CreateChatRequest,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Create or get chat session for a document."""
    service = AsyncChatService()
    
    # Check for existing active session
    existing_chat = await service.find_active_chat_for_document(
        user_id=current_user.id,
        document_id=document_id,
        db=db,
    )
    
    if existing_chat:
        return ChatResponse(
            id=existing_chat.id,
            document_id=existing_chat.document_id,
            title=existing_chat.title,
            created_at=existing_chat.created_at,
            updated_at=existing_chat.updated_at,
        )
    
    # Create new session
    chat = await service.create_chat_session(
        user_id=current_user.id,
        document_id=document_id,
        title=session_data.title,
        db=db,
    )
    
    return ChatResponse(
        id=chat.id,
        document_id=chat.document_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )


@router.get(
    "/session/{chat_id}/messages",
    response_model=list[ChatMessageResponse],
    summary="Get chat messages",
    description="Get all messages in a chat session",
)
async def get_chat_messages(
    chat_id: UUID,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessageResponse]:
    """Get all messages in a chat session."""
    service = AsyncChatService()
    
    messages = await service.get_chat_messages(
        chat_id=chat_id,
        user_id=current_user.id,
        db=db,
    )
    
    return [
        ChatMessageResponse(
            id=msg.id,
            chat_id=msg.chat_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            metadata=msg.message_metadata,
        )
        for msg in messages
    ]


@router.post(
    "/session/{chat_id}/message",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send message",
    description="Send a message in chat session and queue AI response",
)
async def send_message(
    chat_id: UUID,
    message_data: ChatMessageRequest,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send a message and queue AI response generation."""
    service = AsyncChatService()
    
    try:
        result = await service.enqueue_message(
            chat_id=chat_id,
            user_id=current_user.id,
            message=message_data.message,
            db=db,
        )
        return result
    except Exception as e:
        if "Chat not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        )


@router.delete(
    "/session/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete chat session",
    description="Delete a chat session and all its messages",
)
async def delete_chat_session(
    chat_id: UUID,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a chat session."""
    service = AsyncChatService()
    
    await service.delete_chat(
        chat_id=chat_id,
        user_id=current_user.id,
        db=db,
    )