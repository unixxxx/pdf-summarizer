"""Processing service for document processing status."""

from uuid import UUID

from shared.models import Document
from .schemas import ProcessingStatusResponse


class ProcessingService:
    """Service for handling document processing status."""
    
    async def get_processing_status(
        self,
        document: Document,
        document_id: UUID,
    ) -> ProcessingStatusResponse:
        """
        Get current processing status for a document.
        
        Args:
            document: The document model instance
            document_id: The document ID
            
        Returns:
            ProcessingStatusResponse with current status details
        """
        # Determine processing status based on document state
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
    
    async def get_websocket_status_update(
        self,
        document_id: UUID,
    ) -> dict:
        """
        Get status update for WebSocket communication.
        
        Args:
            document_id: The document ID
            
        Returns:
            Dictionary with status update information
        """
        return {
            "type": "status_update",
            "document_id": str(document_id),
            "stage": "ready",
            "progress": 100,
            "message": "Document processing complete"
        }