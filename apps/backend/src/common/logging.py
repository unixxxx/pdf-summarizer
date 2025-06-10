"""Logging configuration for the application."""

import logging
import sys

from ..config import get_settings


def setup_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()
    
    # Determine log level based on environment
    log_level = logging.DEBUG if settings.environment == "development" else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Set application logger
    app_logger = logging.getLogger("src")
    app_logger.setLevel(log_level)
    
    app_logger.info(f"Logging configured for {settings.environment} environment")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)