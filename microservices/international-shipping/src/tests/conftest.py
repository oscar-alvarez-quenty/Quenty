import os
import tempfile
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from fastapi import FastAPI
from src.main import app
from src.database import get_db
from src.models.models import Base, Rate, Catalog, CatalogRate, ClientRatebook, DocumentType, Document
from sqlalchemy import delete

# Crea una base de datos SQLite temporal basada en archivo
db_fd, db_path = tempfile.mkstemp()
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

engine_test = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture()
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture()
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
async def clean_client_ratebook(db_session):
    yield
    await db_session.execute(delete(ClientRatebook))
    await db_session.commit()