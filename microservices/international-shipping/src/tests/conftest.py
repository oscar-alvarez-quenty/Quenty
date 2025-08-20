import os
import tempfile
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import delete

from src.main import app
from src.database import get_db
from src.models.models import Base, ClientRatebook
from src.core.auth import get_current_user  # Asegúrate de que este import apunta al correcto

# Base de datos SQLite temporal
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

# Cliente sin autenticación (si lo necesitas)
@pytest.fixture()
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

# Cliente con autenticación simulada
@pytest.fixture()
async def client_with_auth(db_session):
    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return {
            "id": 1,
            "unique_id": "test-uuid",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "full_name": "Test User",
            "avatar_url": None,
            "role": "superuser",
            "company_id": "COMP-TECH0001",
            "permissions": ["*"],
            "is_superuser": True  # <- importante si usas permisos
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

# Limpiar tabla después de cada test
@pytest.fixture(autouse=True)
async def clean_client_ratebook(db_session):
    yield
    await db_session.execute(delete(ClientRatebook))
    await db_session.commit()
