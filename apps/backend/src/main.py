"""Main application module with DDD structure."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth.router import router as auth_router
from .chat.router import router as chat_router
from .common.exceptions import PDFSummarizerException
from .common.llm_factory import UnifiedLLMFactory
from .common.logging import get_logger, setup_logging
from .common.schemas import ErrorResponse
from .config import get_settings

# Import domain routers
from .document.router import router as document_router
from .health.router import router as health_router
from .library.router import router as library_router
from .storage.router import router as storage_router
from .summarization.router import router as summarization_router

# Configure logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle events."""
    # Startup
    logger.info("Starting PDF Summarizer API...")
    settings = get_settings()

    # Log configuration
    logger.info(f"Environment: {settings.environment}")
    
    # Check LLM configuration using factory
    try:
        llm_factory = UnifiedLLMFactory(settings)
        provider_info = llm_factory.get_provider_info()
        logger.info(f"LLM Provider: {provider_info['provider']}")
        logger.info(f"LLM Model: {provider_info.get('model', 'N/A')}")
        
        if provider_info.get('base_url'):
            logger.info(f"LLM Base URL: {provider_info['base_url']}")
        if provider_info.get('embedding_model'):
            logger.info(f"Embedding Model: {provider_info['embedding_model']}")
            
    except Exception as e:
        logger.warning(f"LLM configuration error: {str(e)}")

    # Check OAuth configuration
    if settings.google_oauth_enabled:
        logger.info("Google OAuth configured successfully")
    else:
        logger.warning("Google OAuth not configured")

    if settings.github_oauth_enabled:
        logger.info("GitHub OAuth configured successfully")
    else:
        logger.warning("GitHub OAuth not configured")
    
    # Check storage configuration
    if settings.s3_enabled:
        logger.info(f"S3 storage enabled with bucket: {settings.s3_bucket_name}")
    else:
        logger.info(f"Local file storage enabled at: {settings.storage_local_path}")

    yield

    # Shutdown
    logger.info("Shutting down PDF Summarizer API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(document_router, prefix="/api/v1")
    app.include_router(library_router, prefix="/api/v1")
    app.include_router(summarization_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(storage_router, prefix="/api/v1")

    # Global exception handler
    @app.exception_handler(PDFSummarizerException)
    async def pdf_summarizer_exception_handler(
        request: Request, exc: PDFSummarizerException
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                status_code=exc.status_code,
                path=str(request.url.path),
            ).model_dump(),
        )

    # Generic exception handler
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail="An unexpected error occurred",
                status_code=500,
                path=str(request.url.path),
            ).model_dump(),
        )

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info",
    )