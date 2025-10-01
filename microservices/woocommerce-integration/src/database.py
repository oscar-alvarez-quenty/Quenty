"""
Database Configuration for WooCommerce Integration Service
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os
from typing import AsyncGenerator

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://woocommerce_user:woocommerce_pass@localhost:5432/woocommerce_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True if os.getenv("SQL_ECHO", "false").lower() == "true" else False,
    poolclass=NullPool,
    future=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models (imported from models/entities.py)
from models.entities import Base


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Usage in FastAPI:
    ```python
    @app.get("/stores")
    async def list_stores(db: AsyncSession = Depends(get_db)):
        ...
    ```
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """
    Create all tables defined in models.
    Only for development - in production use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """
    Drop all tables. Use with caution!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def init_db():
    """
    Initialize database with tables.
    """
    await create_tables()
    print("✅ WooCommerce database tables created successfully")
