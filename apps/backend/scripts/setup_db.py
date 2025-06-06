#!/usr/bin/env python3
"""Setup database with pgvector extension."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import get_settings


async def setup_database():
    """Create database and enable pgvector extension."""
    settings = get_settings()
    
    # Parse database URL to get database name
    db_url_parts = settings.database_url.split("/")
    db_name = db_url_parts[-1]
    base_url = "/".join(db_url_parts[:-1])
    
    # Connect to postgres database to create our database
    engine = create_async_engine(f"{base_url}/postgres")
    
    async with engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": db_name}
        )
        exists = result.scalar() is not None
        
        if not exists:
            # Create database
            await conn.execute(text("COMMIT"))  # Exit transaction
            await conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"Created database: {db_name}")
        else:
            print(f"Database already exists: {db_name}")
    
    await engine.dispose()
    
    # Connect to our database and create pgvector extension
    engine = create_async_engine(settings.database_url)
    
    async with engine.connect() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.commit()
        print("Enabled pgvector extension")
    
    await engine.dispose()
    print("Database setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_database())