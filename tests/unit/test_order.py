import pytest
from decimal import Decimal
from datetime import datetime
from src.domain.entities.order import Order, OrderStatus, ServiceType, Recipient
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.package_dimensions import PackageDimensions

class TestOrder:
    
    def create_test_order(self):
        recipient = Recipient(
            name="John Doe",
            phone="1234567890",
            email="john@example.com",
            address="123 Test St",
            city="Test City",
            country="Colombia"
        )
        
        package_dimensions = PackageDimensions(
            length_cm=Decimal('10'),
            width_cm=Decimal('10'),
            height_cm=Decimal('10'),
            weight_kg=Decimal('1')
        )
        
        return Order(
            customer_id=CustomerId.generate(),
            recipient=recipient,
            package_dimensions=package_dimensions,
            declared_value=Decimal('50000'),
            service_type=ServiceType.NATIONAL,
            origin_address="456 Origin St",
            origin_city="Origin City"
        )
    
    def test_create_order_with_valid_data(self):
        # Act
        order = self.create_test_order()
        
        # Assert
        assert isinstance(order.id, OrderId)
        assert isinstance(order.customer_id, CustomerId)
        assert order.recipient.name == "John Doe"
        assert order.package_dimensions.weight_kg == Decimal('1')
        assert order.declared_value == Decimal('50000')
        assert order.service_type == ServiceType.NATIONAL
        assert order.status == OrderStatus.PENDING
        assert isinstance(order.created_at, datetime)
    
    def test_set_quote(self):
        # Arrange
        order = self.create_test_order()
        price = Decimal('25000')
        delivery_days = 3
        
        # Act
        order.set_quote(price, delivery_days)
        
        # Assert
        assert order.quoted_price == price
        assert order.estimated_delivery_days == delivery_days
        assert order.status == OrderStatus.QUOTED
    
    def test_confirm_quoted_order(self):
        # Arrange
        order = self.create_test_order()
        order.set_quote(Decimal('25000'), 3)
        
        # Act
        order.confirm()
        
        # Assert
        assert order.status == OrderStatus.CONFIRMED
    
    def test_cannot_confirm_pending_order(self):
        # Arrange
        order = self.create_test_order()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Can only confirm quoted orders"):
            order.confirm()
    
    def test_cancel_pending_order(self):
        # Arrange
        order = self.create_test_order()
        
        # Act
        order.cancel()
        
        # Assert
        assert order.status == OrderStatus.CANCELLED
    
    def test_cannot_cancel_order_with_guide(self):
        # Arrange
        order = self.create_test_order()
        order.set_quote(Decimal('25000'), 3)
        order.confirm()
        order.mark_with_guide()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot cancel order with guide already generated"):
            order.cancel()
    
    def test_mark_with_guide(self):
        # Arrange
        order = self.create_test_order()
        order.set_quote(Decimal('25000'), 3)
        order.confirm()
        
        # Act
        order.mark_with_guide()
        
        # Assert
        assert order.status == OrderStatus.WITH_GUIDE
    
    def test_cannot_generate_guide_for_pending_order(self):
        # Arrange
        order = self.create_test_order()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Can only generate guide for confirmed orders"):
            order.mark_with_guide()
    
    def test_is_international(self):
        # Arrange
        order = self.create_test_order()
        order.service_type = ServiceType.INTERNATIONAL
        
        # Act & Assert
        assert order.is_international() == True
    
    def test_is_not_international(self):
        # Arrange
        order = self.create_test_order()
        
        # Act & Assert
        assert order.is_international() == False