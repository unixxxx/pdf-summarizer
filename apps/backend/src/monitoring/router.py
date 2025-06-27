"""Monitoring API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user
from ..common.monitoring import metrics
from .progress_tracker import progress_tracker
from shared.models import User
from ..database.session import get_db

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get application performance metrics.
    
    Note: In production, this should be restricted to admin users only.
    """
    return {
        "status": "ok",
        "metrics": metrics.get_metrics(),
    }


@router.get("/health/detailed")
async def get_detailed_health(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed health status including database connectivity."""
    health_status = {
        "status": "healthy",
        "checks": {
            "api": "ok",
            "database": "unknown",
            "cache": "unknown",
        },
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Check cache
    try:
        from ..common.cache_service import CacheService
        from ..config import get_settings
        
        settings = get_settings()
        if settings.cache_enabled:
            cache_service = CacheService(settings)
            if await cache_service.ping():
                health_status["checks"]["cache"] = "ok"
            else:
                health_status["checks"]["cache"] = "not connected"
        else:
            health_status["checks"]["cache"] = "disabled"
    except Exception as e:
        health_status["checks"]["cache"] = f"error: {str(e)}"
    
    # Add metrics summary
    current_metrics = metrics.get_metrics()
    health_status["metrics_summary"] = {
        "total_requests": current_metrics["total_requests"],
        "error_rate": f"{current_metrics['error_rate']:.2%}",
        "avg_response_time": f"{current_metrics['avg_response_time']:.3f}s",
        "p95_response_time": f"{current_metrics['p95_response_time']:.3f}s",
    }
    
    return health_status


@router.get("/progress/{task_type}/{task_id}")
async def get_task_progress(
    task_type: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any] | None:
    """Get progress for a specific task."""
    progress = await progress_tracker.get_progress(task_type, task_id)
    
    # Verify user has access to this task
    if progress and progress.get("metadata", {}).get("user_id") == str(current_user.id):
        return progress
    return None


@router.get("/progress")
async def get_all_progress(
    task_type: str | None = Query(None, description="Filter by task type"),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Get all progress for the current user."""
    all_progress = await progress_tracker.get_all_progress(task_type)
    
    # Filter to only show user's own progress
    user_progress = [
        p for p in all_progress
        if p.get("metadata", {}).get("user_id") == str(current_user.id)
    ]
    
    return user_progress