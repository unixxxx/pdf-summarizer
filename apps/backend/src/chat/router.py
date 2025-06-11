"""Chat API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..database.models import Chat, ChatMessage, Document
from ..database.session import get_db
from .dependencies import ChatServiceDep
from .schemas import (
    ChatListItem,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatResponse,
    ChatWithMessages,
    CreateChatRequest,
)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={
        400: {"description": "Bad request"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


@router.post(
    "/sessions",
    response_model=ChatResponse,
    summary="Create a new chat session",
    description="Create a new chat session for a document",
)
async def create_chat_session(
    request: CreateChatRequest,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Create a new chat session."""
    chat = await chat_service.create_chat_session(
        user_id=current_user.id,
        document_id=request.document_id,
        title=request.title,
        db=db,
    )
    return ChatResponse.model_validate(chat)


@router.post(
    "/sessions/find-or-create",
    response_model=ChatResponse,
    summary="Find existing chat or create new one",
    description="Returns existing active chat session for a document or creates a new one",
)
async def find_or_create_chat_session(
    request: CreateChatRequest,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Find an existing chat session or create a new one."""
    # Check for existing active chat sessions for this document
    existing_chat = await chat_service.find_active_chat_for_document(
        user_id=current_user.id,
        document_id=request.document_id,
        db=db,
    )
    
    if existing_chat:
        return ChatResponse.model_validate(existing_chat)
    
    # No existing chat, create a new one
    chat = await chat_service.create_chat_session(
        user_id=current_user.id,
        document_id=request.document_id,
        title=request.title,
        db=db,
    )
    return ChatResponse.model_validate(chat)


@router.get(
    "/sessions",
    response_model=list[ChatListItem],
    summary="Get user's chat sessions",
    description="Get all chat sessions for the current user",
)
async def get_chat_sessions(
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> list[ChatListItem]:
    """Get user's chat sessions with last message and message count."""
    # Query to get chats with document info and message stats
    stmt = (
        select(
            Chat,
            Document.filename,
            func.count(ChatMessage.id).label("message_count"),
            func.max(ChatMessage.content).label("last_message"),
        )
        .join(Document, Chat.document_id == Document.id)
        .outerjoin(ChatMessage, Chat.id == ChatMessage.chat_id)
        .where(Chat.user_id == current_user.id)
        .group_by(Chat.id, Document.filename)
        .order_by(Chat.updated_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    chat_items = []
    for row in rows:
        chat = row[0]
        chat_items.append(
            ChatListItem(
                id=chat.id,
                document_id=chat.document_id,
                document_filename=row[1],
                title=chat.title,
                message_count=row[2] or 0,
                last_message=row[3],
                created_at=chat.created_at,
                updated_at=chat.updated_at,
            )
        )
    
    return chat_items


@router.get(
    "/sessions/{chat_id}",
    response_model=ChatWithMessages,
    summary="Get chat session with messages",
    description="Get a specific chat session with all its messages",
)
async def get_chat_session(
    chat_id: UUID,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> ChatWithMessages:
    """Get a chat session with all messages."""
    # Verify chat belongs to user
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
        )
    )
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get messages
    messages = await chat_service.get_chat_messages(
        chat_id=chat_id,
        user_id=current_user.id,
        db=db,
    )
    
    return ChatWithMessages(
        chat=ChatResponse.model_validate(chat),
        messages=[ChatMessageResponse.model_validate(msg) for msg in messages],
    )


@router.post(
    "/sessions/{chat_id}/messages",
    response_model=list[ChatMessageResponse],
    summary="Send a message",
    description="Send a message in a chat session and get both user and AI response",
)
async def send_message(
    chat_id: UUID,
    request: ChatMessageRequest,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessageResponse]:
    """Send a message and get AI response."""
    user_message, ai_response = await chat_service.send_message(
        chat_id=chat_id,
        user_id=current_user.id,
        message=request.message,
        db=db,
    )
    return [
        ChatMessageResponse.model_validate(user_message),
        ChatMessageResponse.model_validate(ai_response)
    ]


@router.delete(
    "/sessions/{chat_id}",
    summary="Delete a chat session",
    description="Delete a chat session and all its messages",
)
async def delete_chat_session(
    chat_id: UUID,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a chat session."""
    await chat_service.delete_chat(
        chat_id=chat_id,
        user_id=current_user.id,
        db=db,
    )
    return {"message": "Chat deleted successfully"}