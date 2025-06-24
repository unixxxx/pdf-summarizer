"""Processing router for document processing status."""

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep, get_current_user_ws
from ..database.session import get_db
from ..library.document.dependencies import DocumentServiceDep
from .dependencies import ProcessingOrchestratorDep
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
    orchestrator: ProcessingOrchestratorDep,
    db: AsyncSession = Depends(get_db),
) -> ProcessingStatusResponse:
    """Get current processing status for a document."""
    # Get document to verify ownership
    document = await document_service.get_document_by_id(document_id, user_id=current_user.id, db=db)
    
    # Return processing status based on document state
    if document.status == "completed":
        return ProcessingStatusResponse(
            document_id=str(document_id),
            stage="ready",
            progress=100,
            started_at=document.created_at.isoformat() if document.created_at else None,
            completed_at=document.updated_at.isoformat() if document.updated_at else None,
            stages_completed=["uploading", "extracting", "embedding", "enriching"],
            current_stage_detail="Document processing complete",
        )
    elif document.status == "processing":
        return ProcessingStatusResponse(
            document_id=str(document_id),
            stage="processing",
            progress=50,
            started_at=document.created_at.isoformat() if document.created_at else None,
            completed_at=None,
            stages_completed=["uploading"],
            current_stage_detail="Processing document...",
        )
    else:
        return ProcessingStatusResponse(
            document_id=str(document_id),
            stage="pending",
            progress=0,
            started_at=None,
            completed_at=None,
            stages_completed=[],
            current_stage_detail="Waiting to process",
        )


@router.websocket("/ws/document/{document_id}/status")
async def document_status_websocket(
    websocket: WebSocket,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time status updates."""
    await websocket.accept()
    
    try:
        # Authenticate user
        user = await get_current_user_ws(websocket, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Send initial status
        await websocket.send_json({
            "type": "status_update",
            "document_id": str(document_id),
            "stage": "ready",
            "progress": 100,
            "message": "Document processing complete"
        })
        
        # Keep connection alive until client disconnects
        while True:
            # Wait for client messages (heartbeat/ping)
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)