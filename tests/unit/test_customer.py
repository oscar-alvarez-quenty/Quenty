import pytest
from datetime import datetime
from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email
from src.domain.value_objects.customer_type import CustomerType

class TestCustomer:
    
    def test_create_customer_with_valid_data(self):
        # Arrange
        email = Email("test@example.com")
        customer_id = CustomerId.generate()
        
        # Act
        customer = Customer(
            id=customer_id,
            email=email,
            customer_type=CustomerType.SMALL,
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        
        # Assert
        assert customer.id == customer_id
        assert customer.email == email
        assert customer.customer_type == CustomerType.SMALL
        assert customer.business_name == "Test Business"
        assert customer.tax_id == "123456789"
        assert customer.phone == "1234567890"
        assert customer.address == "Test Address"
        assert customer.kyc_validated == False
        assert customer.is_active == True
        assert isinstance(customer.created_at, datetime)
        assert isinstance(customer.updated_at, datetime)
    
    def test_validate_kyc(self):
        # Arrange
        customer = Customer(
            email=Email("test@example.com"),
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        
        # Act
        customer.validate_kyc()
        
        # Assert
        assert customer.kyc_validated == True
    
    def test_deactivate_customer(self):
        # Arrange
        customer = Customer(
            email=Email("test@example.com"),
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        
        # Act
        customer.deactivate()
        
        # Assert
        assert customer.is_active == False
    
    def test_can_create_international_shipment_with_kyc(self):
        # Arrange
        customer = Customer(
            email=Email("test@example.com"),
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        customer.validate_kyc()
        
        # Act & Assert
        assert customer.can_create_international_shipment() == True
    
    def test_cannot_create_international_shipment_without_kyc(self):
        # Arrange
        customer = Customer(
            email=Email("test@example.com"),
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        
        # Act & Assert
        assert customer.can_create_international_shipment() == False
    
    def test_medium_customer_can_use_credit(self):
        # Arrange
        customer = Customer(
            email=Email("test@example.com"),
            customer_type=CustomerType.MEDIUM,
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        
        # Act & Assert
        assert customer.can_use_credit() == True
    
    def test_small_customer_cannot_use_credit(self):
        # Arrange
        customer = Customer(
            email=Email("test@example.com"),
            customer_type=CustomerType.SMALL,
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        
        # Act & Assert
        assert customer.can_use_credit() == False
    
    def test_large_customer_can_request_pickup(self):
        # Arrange
        customer = Customer(
            email=Email("test@example.com"),
            customer_type=CustomerType.LARGE,
            business_name="Test Business",
            tax_id="123456789",
            phone="1234567890",
            address="Test Address"
        )
        
        # Act & Assert
        assert customer.can_request_pickup() == True