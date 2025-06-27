from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.schemas import HealthResponse, MessageResponse
from ..config import Settings, get_settings
from ..database.session import get_db

router = APIRouter(
    tags=["Health & Status"], responses={
        200: {"description": "Success"}, 503: {"description": "Service unavailable"}, }, )


@router.get(
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


@router.get(
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
    services = {
        "api": True,
        "database": False,
        "redis": False,
    }

    # Check database connectivity
    try:
        await db.execute("SELECT 1")
        services["database"] = True
    except Exception:
        services["database"] = False

    # Check Redis connectivity
    try:
        from arq import create_pool
        redis = await create_pool(settings.redis_url)
        await redis.ping()
        await redis.close()
        services["redis"] = True
    except Exception:
        services["redis"] = False

    # Determine overall health
    all_healthy = all(services.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=settings.api_version,
        services=services,
    )
