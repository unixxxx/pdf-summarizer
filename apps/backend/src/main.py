"""Main application module with DDD structure."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .archive.router import router as archive_router
from .auth.router import router as auth_router
from .chat.async_router import router as chat_router
from .common.cache_service import CacheService
from .common.exceptions import (
    DatabaseError,
    DocuLearnException,
    ExternalAPIError,
    RateLimitError,
    ValidationError,
)
from .common.logging import get_logger, setup_logging
from .common.monitoring import PerformanceMonitoringMiddleware, metrics
from .common.schemas import ErrorResponse
from .config import get_settings
from .document.router import router as document_router

# Import domain routers
from .flashcard.async_router import router as flashcard_router
from .folder.router import router as folder_router
from .monitoring.router import health_router, monitoring_router
from .quiz.async_router import router as quiz_router
from .search import SearchService
from .storage.router import router as storage_router
from .summarization.async_router import router as summarization_router
from .tag.router import router as tag_router
from .upload.router import router as upload_router
from .websocket.connection_manager import manager as ws_manager
from .websocket.router import router as websocket_router

# Configure logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle events."""
    # Startup
    logger.info("Starting DocuLearn API...")
    settings = get_settings()

    # Log configuration
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize WebSocket manager
    await ws_manager.initialize()
    logger.info("WebSocket manager initialized")
    
    # Initialize cache service for testing
    cache_service = None
    if settings.cache_enabled:
        try:
            cache_service = CacheService(settings)
            if await cache_service.ping():
                logger.info("Redis cache connected successfully")
                # Store cache service in app state for cleanup
                app.state.cache_service = cache_service
            else:
                logger.warning("Redis cache ping failed, caching disabled")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {str(e)}, caching disabled")
    else:
        logger.info("Caching is disabled")
    
    # LLM is now handled by the worker service
    logger.info("LLM processing is handled by the worker service")
    
    # Preload ML models for search
    if settings.enable_reranking:
        try:
            logger.info("Preloading sentence transformer model for search reranking...")
            # This will initialize the global reranker instance
            search_service = SearchService()
            logger.info("Sentence transformer model loaded successfully")
            # Store in app state if needed for monitoring
            app.state.search_service = search_service
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            # Continue without reranking rather than failing startup
            logger.warning("Search reranking disabled due to model loading failure")

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
    logger.info("Shutting down DocuLearn API...")
    
    # Close WebSocket manager
    await ws_manager.close()
    logger.info("WebSocket manager closed")
    
    # Cleanup cache service
    if hasattr(app.state, "cache_service") and app.state.cache_service:
        await app.state.cache_service.close()
        logger.info("Redis cache connection closed")


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
    
    # Add GZip compression middleware
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,  # Only compress responses larger than 1KB
        compresslevel=6,    # Compression level (1-9, 6 is a good balance)
    )
    
    # Add performance monitoring middleware
    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        """Wrapper for performance monitoring middleware."""
        middleware = PerformanceMonitoringMiddleware(
            slow_request_threshold=1.0 if settings.is_production else 2.0
        )
        response = await middleware(request, call_next)
        
        # Record metrics
        process_time = float(response.headers.get("X-Process-Time", 0))
        metrics.record_request(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=process_time,
        )
        
        return response

    # Include routers
    app.include_router(health_router)  # Root level health endpoints
    app.include_router(auth_router, prefix="/api/v1")
    
    # Library module routers
    app.include_router(document_router, prefix="/api/v1")
    app.include_router(folder_router, prefix="/api/v1")
    app.include_router(tag_router, prefix="/api/v1")
    app.include_router(archive_router, prefix="/api/v1")
    
    # Learning module routers
    app.include_router(upload_router, prefix="/api/v1")
    app.include_router(quiz_router, prefix="/api/v1")
    app.include_router(flashcard_router, prefix="/api/v1")
    
    # WebSocket router (no prefix for WebSocket endpoints)
    app.include_router(websocket_router)
    
    # Other routers
    app.include_router(summarization_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(storage_router, prefix="/api/v1")
    app.include_router(monitoring_router, prefix="/api/v1")

    # Specific exception handlers
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle validation errors."""
        logger.warning(f"Validation error on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                status_code=exc.status_code,
                path=str(request.url.path),
            ).model_dump(mode='json'),
        )
    
    @app.exception_handler(DatabaseError)
    async def database_exception_handler(
        request: Request, exc: DatabaseError
    ) -> JSONResponse:
        """Handle database errors."""
        logger.error(f"Database error on {request.url.path}: {exc.detail}", exc_info=True)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail="A database error occurred. Please try again later.",
                status_code=exc.status_code,
                path=str(request.url.path),
            ).model_dump(mode='json'),
        )
    
    @app.exception_handler(ExternalAPIError)
    async def external_api_exception_handler(
        request: Request, exc: ExternalAPIError
    ) -> JSONResponse:
        """Handle external API errors."""
        logger.error(f"External API error on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                status_code=exc.status_code,
                path=str(request.url.path),
            ).model_dump(mode='json'),
        )
    
    @app.exception_handler(RateLimitError)
    async def rate_limit_exception_handler(
        request: Request, exc: RateLimitError
    ) -> JSONResponse:
        """Handle rate limit errors."""
        logger.warning(f"Rate limit exceeded on {request.url.path}")
        response = JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                status_code=exc.status_code,
                path=str(request.url.path),
            ).model_dump(mode='json'),
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response
    
    # Global exception handler for other custom exceptions
    @app.exception_handler(DocuLearnException)
    async def doculearn_exception_handler(
        request: Request, exc: DocuLearnException
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.error(f"Application error on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                status_code=exc.status_code,
                path=str(request.url.path),
            ).model_dump(mode='json'),
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
            ).model_dump(mode='json'),
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