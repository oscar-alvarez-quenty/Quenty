import os
from typing import AsyncGenerator, Dict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from contextlib import asynccontextmanager
import asyncpg
from .config import settings
from .models import Base
import logging

logger = logging.getLogger(__name__)

# Main RAG database with vector support
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database with pgvector extension and create tables"""
    try:
        # Create pgvector extension
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully with pgvector extension")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


class MicroserviceConnector:
    """Manages connections to all microservice databases"""
    
    def __init__(self):
        self.connections: Dict[str, create_async_engine] = {}
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize connections to all microservice databases"""
        services = {
            "auth": settings.auth_db_url,
            "customer": settings.customer_db_url,
            "order": settings.order_db_url,
            "carrier": settings.carrier_db_url,
            "analytics": settings.analytics_db_url,
            "franchise": settings.franchise_db_url,
            "international": settings.international_db_url,
            "microcredit": settings.microcredit_db_url,
            "pickup": settings.pickup_db_url,
            "reverse_logistics": settings.reverse_logistics_db_url,
        }
        
        for service_name, db_url in services.items():
            if db_url:
                # Convert to async URL if needed
                async_url = db_url
                if "postgresql://" in db_url and "+asyncpg" not in db_url:
                    async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
                
                self.connections[service_name] = create_async_engine(
                    async_url,
                    echo=False,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10
                )
                logger.info(f"Initialized connection to {service_name} database")
    
    @asynccontextmanager
    async def get_connection(self, service_name: str):
        """Get a connection to a specific microservice database"""
        if service_name not in self.connections:
            raise ValueError(f"Unknown service: {service_name}")
        
        engine = self.connections[service_name]
        async with engine.connect() as conn:
            yield conn
    
    async def execute_query(self, service_name: str, query: str):
        """Execute a read-only query on a microservice database"""
        async with self.get_connection(service_name) as conn:
            result = await conn.execute(text(query))
            return result.fetchall()
    
    async def close_all(self):
        """Close all database connections"""
        for service_name, engine in self.connections.items():
            await engine.dispose()
            logger.info(f"Closed connection to {service_name} database")


# Global instance
microservice_connector = MicroserviceConnector()