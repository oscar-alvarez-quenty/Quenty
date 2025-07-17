import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from main import app
from src.infrastructure.database.database import get_db, Base

# Test database URL - use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

class TestCustomerAPI:
    
    def setup_method(self):
        self.client = TestClient(app)
    
    @pytest.mark.asyncio
    async def test_create_customer_success(self, setup_database):
        # Arrange
        customer_data = {
            "email": "test@example.com",
            "customer_type": "pequeño",
            "business_name": "Test Business",
            "tax_id": "123456789",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        
        # Act
        response = self.client.post("/api/v1/customers/", json=customer_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == customer_data["email"]
        assert data["business_name"] == customer_data["business_name"]
        assert data["kyc_validated"] == False
        assert data["is_active"] == True
    
    @pytest.mark.asyncio
    async def test_create_customer_invalid_email(self, setup_database):
        # Arrange
        customer_data = {
            "email": "invalid-email",
            "customer_type": "pequeño",
            "business_name": "Test Business",
            "tax_id": "123456789",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        
        # Act
        response = self.client.post("/api/v1/customers/", json=customer_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_customer_missing_required_fields(self, setup_database):
        # Arrange
        customer_data = {
            "email": "test@example.com",
            # Missing required fields
        }
        
        # Act
        response = self.client.post("/api/v1/customers/", json=customer_data)
        
        # Assert
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_customer_by_id(self, setup_database):
        # Arrange - First create a customer
        customer_data = {
            "email": "test@example.com",
            "customer_type": "pequeño",
            "business_name": "Test Business",
            "tax_id": "123456789",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        create_response = self.client.post("/api/v1/customers/", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Act
        response = self.client.get(f"/api/v1/customers/{customer_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer_id
        assert data["email"] == customer_data["email"]
    
    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, setup_database):
        # Arrange
        fake_customer_id = "00000000-0000-0000-0000-000000000000"
        
        # Act
        response = self.client.get(f"/api/v1/customers/{fake_customer_id}")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_customer(self, setup_database):
        # Arrange - First create a customer
        customer_data = {
            "email": "test@example.com",
            "customer_type": "pequeño",
            "business_name": "Test Business",
            "tax_id": "123456789",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        create_response = self.client.post("/api/v1/customers/", json=customer_data)
        customer_id = create_response.json()["id"]
        
        update_data = {
            "business_name": "Updated Business Name",
            "customer_type": "mediano"
        }
        
        # Act
        response = self.client.put(f"/api/v1/customers/{customer_id}", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["business_name"] == "Updated Business Name"
        assert data["customer_type"] == "mediano"
    
    @pytest.mark.asyncio
    async def test_validate_kyc(self, setup_database):
        # Arrange - First create a customer
        customer_data = {
            "email": "test@example.com",
            "customer_type": "pequeño",
            "business_name": "Test Business",
            "tax_id": "123456789",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        create_response = self.client.post("/api/v1/customers/", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Act
        response = self.client.post(f"/api/v1/customers/{customer_id}/validate-kyc")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["kyc_validated"] == True
    
    @pytest.mark.asyncio
    async def test_list_customers(self, setup_database):
        # Arrange - Create multiple customers
        customers = []
        for i in range(3):
            customer_data = {
                "email": f"test{i}@example.com",
                "customer_type": "pequeño",
                "business_name": f"Test Business {i}",
                "tax_id": f"12345678{i}",
                "phone": f"123456789{i}",
                "address": f"123 Test Street {i}"
            }
            response = self.client.post("/api/v1/customers/", json=customer_data)
            customers.append(response.json())
        
        # Act
        response = self.client.get("/api/v1/customers/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["customers"]) == 3
        assert data["total"] == 3