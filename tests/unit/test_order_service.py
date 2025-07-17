import pytest
from unittest.mock import AsyncMock, Mock
from decimal import Decimal
from src.domain.services.order_service import OrderService
from src.domain.entities.order import Order, OrderStatus, ServiceType, Recipient
from src.domain.entities.customer import Customer
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email
from src.domain.value_objects.package_dimensions import PackageDimensions

class TestOrderService:
    
    def setup_method(self):
        self.order_repository = AsyncMock()
        self.customer_repository = AsyncMock()
        self.order_service = OrderService(self.order_repository, self.customer_repository)
    
    def create_test_customer(self):
        return Customer(
            id=CustomerId.generate(),
            email=Email("test@example.com"),
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address",
            kyc_validated=True
        )
    
    def create_order_data(self):
        customer_id = CustomerId.generate()
        recipient = Recipient(
            name="John Doe",
            phone="1234567890",
            email="john@example.com",
            address="123 Test St",
            city="Test City"
        )
        package_dimensions = PackageDimensions(
            length_cm=Decimal('10'),
            width_cm=Decimal('10'),
            height_cm=Decimal('10'),
            weight_kg=Decimal('1')
        )
        
        return {
            'customer_id': customer_id,
            'recipient': recipient,
            'package_dimensions': package_dimensions,
            'declared_value': Decimal('50000'),
            'service_type': ServiceType.NATIONAL,
            'origin_address': "456 Origin St",
            'origin_city': "Origin City",
            'notes': "Test order"
        }
    
    @pytest.mark.asyncio
    async def test_create_order_success(self):
        # Arrange
        customer = self.create_test_customer()
        order_data = self.create_order_data()
        order_data['customer_id'] = customer.id
        
        expected_order = Order(**order_data)
        
        self.customer_repository.find_by_id.return_value = customer
        self.order_repository.save.return_value = expected_order
        
        # Act
        result = await self.order_service.create_order(order_data)
        
        # Assert
        assert result == expected_order
        self.customer_repository.find_by_id.assert_called_once_with(customer.id)
        self.order_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_order_customer_not_found(self):
        # Arrange
        order_data = self.create_order_data()
        self.customer_repository.find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Customer not found"):
            await self.order_service.create_order(order_data)
    
    @pytest.mark.asyncio
    async def test_create_international_order_without_kyc(self):
        # Arrange
        customer = self.create_test_customer()
        customer.kyc_validated = False
        
        order_data = self.create_order_data()
        order_data['customer_id'] = customer.id
        order_data['service_type'] = ServiceType.INTERNATIONAL
        
        self.customer_repository.find_by_id.return_value = customer
        
        # Act & Assert
        with pytest.raises(ValueError, match="Customer must complete KYC for international shipments"):
            await self.order_service.create_order(order_data)
    
    def test_calculate_shipping_national(self):
        # Arrange
        package_dimensions = PackageDimensions(
            length_cm=Decimal('20'),
            width_cm=Decimal('15'),
            height_cm=Decimal('10'),
            weight_kg=Decimal('2')
        )
        
        # Act
        result = self.order_service.calculate_shipping(
            "Bogotá", "Medellín", package_dimensions
        )
        
        # Assert
        assert 'price' in result
        assert 'delivery_days' in result
        assert 'billable_weight' in result
        assert result['delivery_days'] == 3
        assert isinstance(result['price'], Decimal)
    
    def test_calculate_shipping_international(self):
        # Arrange
        package_dimensions = PackageDimensions(
            length_cm=Decimal('20'),
            width_cm=Decimal('15'),
            height_cm=Decimal('10'),
            weight_kg=Decimal('2')
        )
        
        # Act
        result = self.order_service.calculate_shipping(
            "Bogotá", "international Miami", package_dimensions
        )
        
        # Assert
        assert result['delivery_days'] == 5
        assert result['price'] > Decimal('10000')  # Should be more expensive
    
    @pytest.mark.asyncio
    async def test_generate_guide_success(self):
        # Arrange
        customer = self.create_test_customer()
        order = Order(
            customer_id=customer.id,
            recipient=Recipient(
                name="John Doe",
                phone="1234567890",
                email="john@example.com",
                address="123 Test St",
                city="Test City"
            ),
            package_dimensions=PackageDimensions(
                length_cm=Decimal('10'),
                width_cm=Decimal('10'),
                height_cm=Decimal('10'),
                weight_kg=Decimal('1')
            ),
            status=OrderStatus.CONFIRMED,
            origin_address="456 Origin St",
            origin_city="Origin City"
        )
        
        self.order_repository.find_by_id.return_value = order
        self.customer_repository.find_by_id.return_value = customer
        self.order_repository.save.return_value = order
        
        # Act
        guide = await self.order_service.generate_guide(order.id)
        
        # Assert
        assert guide.order_id == order.id
        assert guide.customer_id == customer.id
        assert guide.logistics_operator == "Quenty Express"
        assert order.status == OrderStatus.WITH_GUIDE
    
    @pytest.mark.asyncio
    async def test_generate_guide_order_not_found(self):
        # Arrange
        order_id = OrderId.generate()
        self.order_repository.find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Order not found"):
            await self.order_service.generate_guide(order_id)
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self):
        # Arrange
        order = Order(
            customer_id=CustomerId.generate(),
            recipient=Recipient(
                name="John Doe",
                phone="1234567890", 
                email="john@example.com",
                address="123 Test St",
                city="Test City"
            ),
            package_dimensions=PackageDimensions(
                length_cm=Decimal('10'),
                width_cm=Decimal('10'),
                height_cm=Decimal('10'),
                weight_kg=Decimal('1')
            ),
            status=OrderStatus.PENDING,
            origin_address="456 Origin St",
            origin_city="Origin City"
        )
        
        self.order_repository.find_by_id.return_value = order
        self.order_repository.save.return_value = order
        
        # Act
        result = await self.order_service.cancel_order(order.id)
        
        # Assert
        assert result == True
        assert order.status == OrderStatus.CANCELLED