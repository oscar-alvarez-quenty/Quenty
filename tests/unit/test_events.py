import pytest
from datetime import datetime
from uuid import uuid4
from src.domain.events.customer_events import CustomerCreated, CustomerKYCValidated
from src.domain.events.order_events import OrderCreated, GuideGenerated
from src.domain.events.payment_events import PaymentProcessed
from src.domain.value_objects.customer_type import CustomerType
from src.domain.entities.order import ServiceType

class TestCustomerEvents:
    
    def test_customer_created_event(self):
        # Arrange
        customer_id = str(uuid4())
        email = "test@example.com"
        
        # Act
        event = CustomerCreated(
            aggregate_id=uuid4(),
            aggregate_type="customer",
            customer_id=customer_id,
            email=email,
            customer_type=CustomerType.SMALL,
            business_name="Test Business"
        )
        
        # Assert
        assert event.get_event_type() == "customer.created"
        assert event.customer_id == customer_id
        assert event.email == email
        assert event.customer_type == CustomerType.SMALL
        assert event.business_name == "Test Business"
        assert event.occurred_at is not None
    
    def test_customer_created_event_to_dict(self):
        # Arrange
        event = CustomerCreated(
            aggregate_id=uuid4(),
            aggregate_type="customer",
            customer_id="123",
            email="test@example.com",
            customer_type=CustomerType.SMALL,
            business_name="Test Business"
        )
        
        # Act
        event_dict = event.to_dict()
        
        # Assert
        assert event_dict["event_type"] == "customer.created"
        assert event_dict["data"]["customer_id"] == "123"
        assert event_dict["data"]["email"] == "test@example.com"
        assert event_dict["data"]["customer_type"] == "pequeño"
        assert event_dict["aggregate_type"] == "customer"
    
    def test_customer_kyc_validated_event(self):
        # Arrange & Act
        event = CustomerKYCValidated(
            aggregate_id=uuid4(),
            aggregate_type="customer",
            customer_id="123",
            validation_method="automated",
            validated_by="system"
        )
        
        # Assert
        assert event.get_event_type() == "customer.kyc_validated"
        assert event.customer_id == "123"
        assert event.validation_method == "automated"
        assert event.validated_by == "system"

class TestOrderEvents:
    
    def test_order_created_event(self):
        # Arrange & Act
        event = OrderCreated(
            aggregate_id=uuid4(),
            aggregate_type="order",
            order_id="ORD_123",
            customer_id="CUST_456",
            service_type=ServiceType.NATIONAL,
            origin_city="Bogotá",
            destination_city="Medellín",
            declared_value="50000"
        )
        
        # Assert
        assert event.get_event_type() == "order.created"
        assert event.order_id == "ORD_123"
        assert event.customer_id == "CUST_456"
        assert event.service_type == ServiceType.NATIONAL
        assert event.origin_city == "Bogotá"
        assert event.destination_city == "Medellín"
    
    def test_guide_generated_event(self):
        # Arrange & Act
        event = GuideGenerated(
            aggregate_id=uuid4(),
            aggregate_type="order",
            guide_id="GDE_789",
            order_id="ORD_123",
            customer_id="CUST_456",
            logistics_operator="Quenty Express",
            pickup_address="Calle 123",
            delivery_address="Carrera 456"
        )
        
        # Assert
        assert event.get_event_type() == "guide.generated"
        assert event.guide_id == "GDE_789"
        assert event.order_id == "ORD_123"
        assert event.customer_id == "CUST_456"
        assert event.logistics_operator == "Quenty Express"

class TestPaymentEvents:
    
    def test_payment_processed_event(self):
        # Arrange & Act
        event = PaymentProcessed(
            aggregate_id=uuid4(),
            aggregate_type="payment",
            payment_id="PAY_123",
            order_id="ORD_456",
            customer_id="CUST_789",
            amount="25000",
            payment_method="credit_card",
            transaction_reference="TXN_ABC123"
        )
        
        # Assert
        assert event.get_event_type() == "payment.processed"
        assert event.payment_id == "PAY_123"
        assert event.order_id == "ORD_456"
        assert event.customer_id == "CUST_789"
        assert event.amount == "25000"
        assert event.payment_method == "credit_card"
        assert event.transaction_reference == "TXN_ABC123"
    
    def test_payment_event_to_dict(self):
        # Arrange
        event = PaymentProcessed(
            aggregate_id=uuid4(),
            aggregate_type="payment",
            payment_id="PAY_123",
            order_id="ORD_456",
            customer_id="CUST_789",
            amount="25000",
            payment_method="credit_card",
            transaction_reference="TXN_ABC123"
        )
        
        # Act
        event_dict = event.to_dict()
        
        # Assert
        assert event_dict["event_type"] == "payment.processed"
        assert event_dict["data"]["payment_id"] == "PAY_123"
        assert event_dict["data"]["amount"] == "25000"
        assert event_dict["data"]["payment_method"] == "credit_card"
        assert "occurred_at" in event_dict
        assert "event_id" in event_dict

class TestEventMetadata:
    
    def test_event_has_required_metadata(self):
        # Arrange & Act
        event = CustomerCreated(
            aggregate_id=uuid4(),
            aggregate_type="customer",
            customer_id="123",
            email="test@example.com",
            customer_type=CustomerType.SMALL,
            business_name="Test Business"
        )
        
        # Assert
        assert event.event_id is not None
        assert event.occurred_at is not None
        assert event.aggregate_id is not None
        assert event.aggregate_type == "customer"
        assert event.event_version == 1
        assert isinstance(event.metadata, dict)
    
    def test_event_with_custom_metadata(self):
        # Arrange
        custom_metadata = {"source": "api", "user_id": "admin123"}
        
        # Act
        event = CustomerCreated(
            aggregate_id=uuid4(),
            aggregate_type="customer",
            customer_id="123",
            email="test@example.com",
            customer_type=CustomerType.SMALL,
            business_name="Test Business",
            metadata=custom_metadata
        )
        
        # Assert
        assert event.metadata["source"] == "api"
        assert event.metadata["user_id"] == "admin123"