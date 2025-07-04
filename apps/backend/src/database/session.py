"""Database session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import get_settings

settings = get_settings()

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    # Connection pool settings
    pool_size=20,  # Number of connections to maintain in pool
    max_overflow=40,  # Maximum overflow connections above pool_size
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Set up monitoring in development
if not settings.is_production:
    try:
        from ..common.monitoring import setup_connection_pool_monitoring, setup_database_monitoring
        setup_database_monitoring(engine.sync_engine)
        setup_connection_pool_monitoring(engine.pool)
    except ImportError:
        # Monitoring module might not be available yet during initial setup
        pass

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base is now imported from shared models


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session() as session:
        try:
            yield session
            # Note: Don't auto-commit here - let the request handler control transactions
        except Exception:
            await session.rollback()
            raise

