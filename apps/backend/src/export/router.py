from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import CurrentUserDep
from ..database.models import Document, Summary
from ..database.session import get_db
from .schemas import ExportFormat
from .service import PDFExporter

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{summary_id}")
async def export_summary(
    summary_id: UUID,
    current_user: CurrentUserDep,
    db: AsyncSession = Depends(get_db),
    format: ExportFormat = Query(ExportFormat.MARKDOWN),
) -> Response:
    """
    Export a summary in the specified format.
    
    Supported formats:
    - pdf: Export as PDF document
    - markdown: Export as Markdown text
    - text: Export as plain text
    """
    # Get summary with document info
    result = await db.execute(
        select(Summary, Document)
        .join(Document, Summary.document_id == Document.id)
        .where(
            Summary.id == summary_id,
            Document.user_id == current_user.id,
        )
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found",
        )
    
    summary, document = row
    
    # Export based on format
    if format == ExportFormat.MARKDOWN:
        content = f"""# {document.filename}

## Summary

{summary.summary_text}

---
*Generated on {summary.created_at.strftime('%Y-%m-%d %H:%M:%S')}*
*Processing time: {summary.processing_time:.2f} seconds*
"""
        filename = f"{document.filename.rsplit('.', 1)[0]}_summary.md"
        media_type = "text/markdown"
    
    elif format == ExportFormat.TEXT:
        content = f"""{document.filename}

Summary:
{summary.summary_text}

Generated on {summary.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Processing time: {summary.processing_time:.2f} seconds
"""
        filename = f"{document.filename.rsplit('.', 1)[0]}_summary.txt"
        media_type = "text/plain"
    
    elif format == ExportFormat.PDF:
        # For PDF export, we'll use the PDF export functionality
        exporter = PDFExporter()
        
        pdf_content = await exporter.export_summary_as_pdf(
            summary_text=summary.summary_text,
            metadata={
                "filename": document.filename,
                "created_at": summary.created_at.isoformat(),
                "processing_time": summary.processing_time,
            }
        )
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{document.filename.rsplit(".", 1)[0]}_summary.pdf"'
            }
        )
    
    # Return text-based formats
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )