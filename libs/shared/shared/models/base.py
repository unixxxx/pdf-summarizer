"""Base model configuration for SQLAlchemy."""

from sqlalchemy.orm import declarative_base

# Create base model class
Base = declarative_base()

# This will be shared by both backend and worker
# Backend will use it for API models
# Worker will use it for database operations