"""Maintenance tasks for the worker."""

from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import select, and_, or_

from ..common.database import get_db_session
from shared.models import Document
from ..common.logger import logger
from ..common.config import get_settings

settings = get_settings()


async def cleanup_orphaned_files(ctx: dict) -> Dict[str, Any]:
    """
    Clean up orphaned files from storage that no longer have database records.
    
    This task is typically run on a schedule (e.g., daily at 2 AM).
    
    Returns:
        Cleanup statistics
    """
    try:
        cleaned_files = 0
        errors = 0
        total_size_freed = 0
        
        # Get storage directory (assuming local storage for now)
        # In production, this would check S3 or other storage backends
        storage_base = Path("/tmp/doculearn/uploads")  # Update with actual path
        
        if not storage_base.exists():
            logger.warning("Storage directory does not exist", path=str(storage_base))
            return {
                "success": True,
                "message": "Storage directory does not exist",
                "cleaned_files": 0
            }
        
        # Get all file paths from database
        async with get_db_session() as db:
            result = await db.execute(
                select(Document.storage_path).where(
                    Document.storage_path.isnot(None)
                )
            )
            db_file_paths = {row[0] for row in result}
        
        # Scan storage directory
        for file_path in storage_base.rglob("*"):
            if file_path.is_file():
                try:
                    # Check if file is in database
                    if str(file_path) not in db_file_paths:
                        # Check file age (only delete files older than 24 hours)
                        file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_age > timedelta(hours=24):
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_files += 1
                            total_size_freed += file_size
                            
                            logger.info(
                                "Deleted orphaned file",
                                file=str(file_path),
                                size=file_size,
                                age_hours=file_age.total_seconds() / 3600
                            )
                except Exception as e:
                    errors += 1
                    logger.error(
                        "Failed to delete orphaned file",
                        file=str(file_path),
                        error=str(e)
                    )
        
        # Clean up failed documents older than 7 days
        async with get_db_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            result = await db.execute(
                select(Document).where(
                    and_(
                        Document.status == "failed",
                        Document.created_at < cutoff_date
                    )
                )
            )
            failed_docs = result.scalars().all()
            
            for doc in failed_docs:
                # Delete associated file if exists
                if doc.storage_path:
                    try:
                        file_path = Path(doc.storage_path)
                        if file_path.exists():
                            file_path.unlink()
                            logger.info(
                                "Deleted file for failed document",
                                document_id=str(doc.id),
                                file=doc.storage_path
                            )
                    except Exception as e:
                        logger.error(
                            "Failed to delete file for failed document",
                            document_id=str(doc.id),
                            error=str(e)
                        )
                
                # Delete document record
                db.delete(doc)
            
            await db.commit()
            
            if failed_docs:
                logger.info(
                    "Cleaned up failed documents",
                    count=len(failed_docs)
                )
        
        # Log summary
        logger.info(
            "Orphaned file cleanup completed",
            cleaned_files=cleaned_files,
            errors=errors,
            size_freed_mb=total_size_freed / (1024 * 1024)
        )
        
        return {
            "success": True,
            "cleaned_files": cleaned_files,
            "errors": errors,
            "size_freed_bytes": total_size_freed,
            "failed_documents_cleaned": len(failed_docs) if 'failed_docs' in locals() else 0
        }
        
    except Exception as e:
        logger.error(
            "Orphaned file cleanup failed",
            error=str(e),
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e)
        }