"""Health and Monitoring API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from shared.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user
from ..common.health_service import HealthCheckService
from ..common.monitoring import metrics
from ..common.schemas import HealthResponse, MessageResponse
from ..config import Settings, get_settings
from ..database.session import get_db

# Create two routers - one for root level health endpoints, one for monitoring
health_router = APIRouter(tags=["Health & Status"])
monitoring_router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# Root level endpoints
@health_router.get(
    "/",
    response_model=MessageResponse,
    summary="Root endpoint",
    description="Welcome message for the API",
)
async def root() -> MessageResponse:
    """API root endpoint."""
    return MessageResponse(
        message="DocuLearn API is running. Visit /docs for API documentation."
    )


@health_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and its dependencies",
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """Check API health and dependent services."""
    health_result = await HealthCheckService.perform_basic_health_check(db, settings)
    
    return HealthResponse(
        status=health_result["status"],
        version=settings.api_version,
        services=health_result["services"],
    )


# Monitoring endpoints
@monitoring_router.get("/metrics")
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


@monitoring_router.get("/health/detailed")
async def get_detailed_health(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed health status including database connectivity."""
    settings = get_settings()
    
    # Use shared health check service
    health_status = await HealthCheckService.perform_detailed_health_check(db, settings)
    
    # Add metrics summary
    current_metrics = metrics.get_metrics()
    health_status["metrics_summary"] = {
        "total_requests": current_metrics["total_requests"],
        "error_rate": f"{current_metrics['error_rate']:.2%}",
        "avg_response_time": f"{current_metrics['avg_response_time']:.3f}s",
        "p95_response_time": f"{current_metrics['p95_response_time']:.3f}s",
    }
    
    return health_status