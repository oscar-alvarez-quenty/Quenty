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

class TestOrderAPI:
    
    def setup_method(self):
        self.client = TestClient(app)
    
    async def create_test_customer(self):
        customer_data = {
            "email": "test@example.com",
            "customer_type": "pequeño",
            "business_name": "Test Business",
            "tax_id": "123456789",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        response = self.client.post("/api/v1/customers/", json=customer_data)
        return response.json()["id"]
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, setup_database):
        # Arrange
        customer_id = await self.create_test_customer()
        
        order_data = {
            "customer_id": customer_id,
            "recipient": {
                "name": "John Doe",
                "phone": "1234567890",
                "email": "john@example.com",
                "address": "123 Destination St",
                "city": "Destination City",
                "country": "Colombia"
            },
            "package_dimensions": {
                "length_cm": 10.5,
                "width_cm": 8.0,
                "height_cm": 5.0,
                "weight_kg": 1.2
            },
            "declared_value": 50000.00,
            "service_type": "national",
            "origin_address": "456 Origin St",
            "origin_city": "Origin City",
            "notes": "Handle with care"
        }
        
        # Act
        response = self.client.post("/api/v1/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["recipient"]["name"] == "John Doe"
        assert data["status"] == "pending"
        assert data["service_type"] == "national"
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_customer(self, setup_database):
        # Arrange
        order_data = {
            "customer_id": "00000000-0000-0000-0000-000000000000",  # Non-existent customer
            "recipient": {
                "name": "John Doe",
                "phone": "1234567890",
                "email": "john@example.com",
                "address": "123 Destination St",
                "city": "Destination City"
            },
            "package_dimensions": {
                "length_cm": 10.5,
                "width_cm": 8.0,
                "height_cm": 5.0,
                "weight_kg": 1.2
            },
            "declared_value": 50000.00,
            "service_type": "national",
            "origin_address": "456 Origin St",
            "origin_city": "Origin City"
        }
        
        # Act
        response = self.client.post("/api/v1/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_order_by_id(self, setup_database):
        # Arrange - First create a customer and order
        customer_id = await self.create_test_customer()
        
        order_data = {
            "customer_id": customer_id,
            "recipient": {
                "name": "John Doe",
                "phone": "1234567890",
                "email": "john@example.com",
                "address": "123 Destination St",
                "city": "Destination City"
            },
            "package_dimensions": {
                "length_cm": 10.5,
                "width_cm": 8.0,
                "height_cm": 5.0,
                "weight_kg": 1.2
            },
            "declared_value": 50000.00,
            "service_type": "national",
            "origin_address": "456 Origin St",
            "origin_city": "Origin City"
        }
        
        create_response = self.client.post("/api/v1/orders/", json=order_data)
        order_id = create_response.json()["id"]
        
        # Act
        response = self.client.get(f"/api/v1/orders/{order_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["customer_id"] == customer_id
    
    @pytest.mark.asyncio
    async def test_calculate_quote(self, setup_database):
        # Arrange
        quote_data = {
            "origin": "Bogotá",
            "destination": "Medellín",
            "package_dimensions": {
                "length_cm": 20.0,
                "width_cm": 15.0,
                "height_cm": 10.0,
                "weight_kg": 2.5
            }
        }
        
        # Act
        response = self.client.post("/api/v1/orders/quote", json=quote_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert "delivery_days" in data
        assert "billable_weight" in data
        assert data["delivery_days"] == 3  # National delivery
    
    @pytest.mark.asyncio
    async def test_quote_order(self, setup_database):
        # Arrange - Create customer and order
        customer_id = await self.create_test_customer()
        
        order_data = {
            "customer_id": customer_id,
            "recipient": {
                "name": "John Doe",
                "phone": "1234567890",
                "email": "john@example.com",
                "address": "123 Destination St",
                "city": "Medellín"
            },
            "package_dimensions": {
                "length_cm": 10.5,
                "width_cm": 8.0,
                "height_cm": 5.0,
                "weight_kg": 1.2
            },
            "declared_value": 50000.00,
            "service_type": "national",
            "origin_address": "456 Origin St",
            "origin_city": "Bogotá"
        }
        
        create_response = self.client.post("/api/v1/orders/", json=order_data)
        order_id = create_response.json()["id"]
        
        # Act
        response = self.client.post(f"/api/v1/orders/{order_id}/quote")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "quoted"
        assert data["quoted_price"] is not None
        assert data["estimated_delivery_days"] is not None
    
    @pytest.mark.asyncio
    async def test_confirm_order(self, setup_database):
        # Arrange - Create customer, order, and quote it
        customer_id = await self.create_test_customer()
        
        order_data = {
            "customer_id": customer_id,
            "recipient": {
                "name": "John Doe",
                "phone": "1234567890",
                "email": "john@example.com",
                "address": "123 Destination St",
                "city": "Medellín"
            },
            "package_dimensions": {
                "length_cm": 10.5,
                "width_cm": 8.0,
                "height_cm": 5.0,
                "weight_kg": 1.2
            },
            "declared_value": 50000.00,
            "service_type": "national",
            "origin_address": "456 Origin St",
            "origin_city": "Bogotá"
        }
        
        create_response = self.client.post("/api/v1/orders/", json=order_data)
        order_id = create_response.json()["id"]
        
        # Quote the order first
        self.client.post(f"/api/v1/orders/{order_id}/quote")
        
        # Act
        response = self.client.post(f"/api/v1/orders/{order_id}/confirm")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, setup_database):
        # Arrange - Create customer and order
        customer_id = await self.create_test_customer()
        
        order_data = {
            "customer_id": customer_id,
            "recipient": {
                "name": "John Doe",
                "phone": "1234567890",
                "email": "john@example.com",
                "address": "123 Destination St",
                "city": "Destination City"
            },
            "package_dimensions": {
                "length_cm": 10.5,
                "width_cm": 8.0,
                "height_cm": 5.0,
                "weight_kg": 1.2
            },
            "declared_value": 50000.00,
            "service_type": "national",
            "origin_address": "456 Origin St",
            "origin_city": "Origin City"
        }
        
        create_response = self.client.post("/api/v1/orders/", json=order_data)
        order_id = create_response.json()["id"]
        
        # Act
        response = self.client.post(f"/api/v1/orders/{order_id}/cancel")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Order cancelled successfully"