from typing import Annotated

from fastapi import APIRouter, Depends

from ..common.dependencies import LLMFactoryDep
from ..common.schemas import HealthResponse, MessageResponse
from ..config import Settings, get_settings

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
        message="PDF Summarizer API is running. Visit /docs for API documentation."
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and its dependencies",
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    factory: LLMFactoryDep,
) -> HealthResponse:
    """Check API health and dependent services."""
    services = {
        "pdf_processor": True,  # PDF service is always available
    }

    # Check if LLM service is configured
    try:
        factory.create_chat_model()
        services["llm"] = True
    except Exception:
        services["llm"] = False

    # Determine overall health
    all_healthy = all(services.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=settings.api_version,
        services=services,
    )
