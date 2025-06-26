"""Processing router for document processing status."""

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep, get_current_user_ws
from ..database.session import get_db
from ..document.dependencies import DocumentServiceDep
from .dependencies import ProcessingServiceDep
from .schemas import ProcessingStatusResponse

router = APIRouter(
    prefix="/processing",
    tags=["Processing"],
    responses={
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "/document/{document_id}/status",
    response_model=ProcessingStatusResponse,
    summary="Get processing status",
    description="Get current processing status for a document",
)
async def get_processing_status(
    document_id: UUID,
    current_user: CurrentUserDep,
    document_service: DocumentServiceDep,
    processing_service: ProcessingServiceDep,
    db: AsyncSession = Depends(get_db),
) -> ProcessingStatusResponse:
    """Get current processing status for a document."""
    # Get document to verify ownership
    document = await document_service.get_document_by_id(document_id, user_id=current_user.id, db=db)
    
    # Delegate status determination to service layer
    return await processing_service.get_processing_status(document, document_id)


@router.websocket("/ws/document/{document_id}/status")
async def document_status_websocket(
    websocket: WebSocket,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time status updates."""
    await websocket.accept()
    
    # Get processing service instance
    from .service import ProcessingService
    processing_service = ProcessingService()
    
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Send initial status using service
        status_update = await processing_service.get_websocket_status_update(document_id)
        await websocket.send_json(status_update)
        
        # Keep connection alive until client disconnects
        while True:
            # Wait for client messages (heartbeat/ping)
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)