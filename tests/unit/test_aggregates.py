import pytest
from decimal import Decimal
from src.domain.aggregates.customer_aggregate import CustomerAggregate
from src.domain.aggregates.order_aggregate import OrderAggregate
from src.domain.entities.order import Recipient, ServiceType
from src.domain.value_objects.package_dimensions import PackageDimensions
from src.domain.value_objects.customer_id import CustomerId
from src.domain.events.customer_events import CustomerCreated, WalletCredited
from src.domain.events.order_events import OrderCreated, GuideGenerated

class TestCustomerAggregate:
    
    def test_create_new_customer_aggregate(self):
        # Act
        aggregate = CustomerAggregate.create_new_customer(
            email="test@example.com",
            business_name="Test Business",
            tax_id="123456789",
            phone="3001234567",
            address="Test Address"
        )
        
        # Assert
        assert aggregate.customer.email.value == "test@example.com"
        assert aggregate.customer.business_name == "Test Business"
        assert aggregate.wallet is not None
        assert aggregate.wallet.customer_id == aggregate.customer.id
        
        # Verify domain event was created
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], CustomerCreated)
        assert events[0].email == "test@example.com"
    
    def test_validate_kyc(self):
        # Arrange
        aggregate = CustomerAggregate.create_new_customer(
            email="test@example.com",
            business_name="Test Business",
            tax_id="123456789",
            phone="3001234567",
            address="Test Address"
        )
        aggregate.clear_domain_events()
        
        # Act
        aggregate.validate_kyc("automated", "system")
        
        # Assert
        assert aggregate.customer.kyc_validated == True
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "customer.kyc_validated"
    
    def test_add_funds_to_wallet(self):
        # Arrange
        aggregate = CustomerAggregate.create_new_customer(
            email="test@example.com",
            business_name="Test Business",
            tax_id="123456789",
            phone="3001234567",
            address="Test Address"
        )
        aggregate.clear_domain_events()
        
        amount = Decimal('100000')
        
        # Act
        aggregate.add_funds_to_wallet(amount, "Test deposit")
        
        # Assert
        assert aggregate.wallet.balance == amount
        assert len(aggregate.wallet.transactions) == 1
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], WalletCredited)
        assert events[0].amount == str(amount)
    
    def test_debit_from_wallet_sufficient_funds(self):
        # Arrange
        aggregate = CustomerAggregate.create_new_customer(
            email="test@example.com",
            business_name="Test Business",
            tax_id="123456789",
            phone="3001234567",
            address="Test Address"
        )
        
        # Add funds first
        aggregate.add_funds_to_wallet(Decimal('100000'), "Initial deposit")
        aggregate.clear_domain_events()
        
        debit_amount = Decimal('50000')
        
        # Act
        aggregate.debit_from_wallet(debit_amount, "Test payment")
        
        # Assert
        assert aggregate.wallet.balance == Decimal('50000')
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "wallet.debited"
    
    def test_request_microcredit(self):
        # Arrange
        aggregate = CustomerAggregate.create_new_customer(
            email="test@example.com",
            business_name="Test Business",
            tax_id="123456789",
            phone="3001234567",
            address="Test Address"
        )
        aggregate.clear_domain_events()
        
        requested_amount = Decimal('500000')
        
        # Act
        microcredit = aggregate.request_microcredit(
            requested_amount, 
            payment_history=[{"on_time": True}], 
            shipment_count=10
        )
        
        # Assert
        assert microcredit.requested_amount == requested_amount
        assert microcredit.customer_id == aggregate.customer.id
        assert microcredit in aggregate.microcredits
        assert microcredit.credit_score > 0
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "microcredit.requested"
    
    def test_can_create_international_shipment_with_kyc(self):
        # Arrange
        aggregate = CustomerAggregate.create_new_customer(
            email="test@example.com",
            business_name="Test Business",
            tax_id="123456789",
            phone="3001234567",
            address="Test Address"
        )
        aggregate.validate_kyc()
        
        # Act & Assert
        assert aggregate.can_create_international_shipment() == True
    
    def test_cannot_create_international_shipment_without_kyc(self):
        # Arrange
        aggregate = CustomerAggregate.create_new_customer(
            email="test@example.com",
            business_name="Test Business",
            tax_id="123456789",
            phone="3001234567",
            address="Test Address"
        )
        
        # Act & Assert
        assert aggregate.can_create_international_shipment() == False

class TestOrderAggregate:
    
    def create_test_order_data(self):
        return {
            'customer_id': CustomerId.generate(),
            'recipient': Recipient(
                name="John Doe",
                phone="3001234567",
                email="john@example.com",
                address="123 Test St",
                city="Medellín"
            ),
            'package_dimensions': PackageDimensions(
                length_cm=Decimal('10'),
                width_cm=Decimal('10'),
                height_cm=Decimal('10'),
                weight_kg=Decimal('1')
            ),
            'declared_value': Decimal('50000'),
            'service_type': ServiceType.NATIONAL,
            'origin_address': "456 Origin St",
            'origin_city': "Bogotá"
        }
    
    def test_create_new_order_aggregate(self):
        # Arrange
        order_data = self.create_test_order_data()
        
        # Act
        aggregate = OrderAggregate.create_new_order(order_data)
        
        # Assert
        assert aggregate.order.customer_id == order_data['customer_id']
        assert aggregate.order.recipient.name == "John Doe"
        assert aggregate.order.service_type == ServiceType.NATIONAL
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], OrderCreated)
        assert events[0].destination_city == "Medellín"
    
    def test_quote_order(self):
        # Arrange
        order_data = self.create_test_order_data()
        aggregate = OrderAggregate.create_new_order(order_data)
        aggregate.clear_domain_events()
        
        price = Decimal('25000')
        delivery_days = 3
        
        # Act
        aggregate.quote_order(price, delivery_days, "Quenty Express")
        
        # Assert
        assert aggregate.order.quoted_price == price
        assert aggregate.order.estimated_delivery_days == delivery_days
        assert aggregate.order.status.value == "quoted"
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "order.quoted"
    
    def test_confirm_order(self):
        # Arrange
        order_data = self.create_test_order_data()
        aggregate = OrderAggregate.create_new_order(order_data)
        aggregate.quote_order(Decimal('25000'), 3)
        aggregate.clear_domain_events()
        
        # Act
        aggregate.confirm_order("credit_card")
        
        # Assert
        assert aggregate.order.status.value == "confirmed"
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "order.confirmed"
    
    def test_generate_guide(self):
        # Arrange
        order_data = self.create_test_order_data()
        aggregate = OrderAggregate.create_new_order(order_data)
        aggregate.quote_order(Decimal('25000'), 3)
        aggregate.confirm_order()
        aggregate.clear_domain_events()
        
        # Act
        guide = aggregate.generate_guide("Quenty Express")
        
        # Assert
        assert guide is not None
        assert aggregate.guide == guide
        assert aggregate.tracking is not None
        assert aggregate.order.status.value == "with_guide"
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], GuideGenerated)
    
    def test_pickup_package(self):
        # Arrange
        order_data = self.create_test_order_data()
        aggregate = OrderAggregate.create_new_order(order_data)
        aggregate.quote_order(Decimal('25000'), 3)
        aggregate.confirm_order()
        aggregate.generate_guide()
        aggregate.clear_domain_events()
        
        # Act
        aggregate.pickup_package("Bogotá Centro", "MSG_123")
        
        # Assert
        assert aggregate.guide.status.value == "picked_up"
        assert len(aggregate.tracking.events) >= 2  # Generate + Pickup events
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "package.picked_up"
    
    def test_deliver_package(self):
        # Arrange
        order_data = self.create_test_order_data()
        aggregate = OrderAggregate.create_new_order(order_data)
        aggregate.quote_order(Decimal('25000'), 3)
        aggregate.confirm_order()
        aggregate.generate_guide()
        aggregate.pickup_package("Bogotá", "MSG_123")
        aggregate.guide.mark_in_transit()
        aggregate.guide.mark_out_for_delivery()
        aggregate.clear_domain_events()
        
        # Act
        aggregate.deliver_package("John Doe", "Medellín Centro", "Signature received")
        
        # Assert
        assert aggregate.guide.status.value == "delivered"
        assert aggregate.is_delivered() == True
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "package.delivered"
    
    def test_report_incident(self):
        # Arrange
        order_data = self.create_test_order_data()
        aggregate = OrderAggregate.create_new_order(order_data)
        aggregate.quote_order(Decimal('25000'), 3)
        aggregate.confirm_order()
        aggregate.generate_guide()
        aggregate.clear_domain_events()
        
        # Act
        incident = aggregate.report_incident(
            "delivery_failed", 
            "Recipient not found", 
            "messenger", 
            "Medellín"
        )
        
        # Assert
        assert incident in aggregate.incidents
        assert aggregate.has_active_incidents() == True
        
        # Verify domain event
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert events[0].get_event_type() == "incident.reported"
    
    def test_get_current_location(self):
        # Arrange
        order_data = self.create_test_order_data()
        aggregate = OrderAggregate.create_new_order(order_data)
        aggregate.quote_order(Decimal('25000'), 3)
        aggregate.confirm_order()
        aggregate.generate_guide()
        aggregate.pickup_package("Bogotá Centro", "MSG_123")
        
        # Act
        current_location = aggregate.get_current_location()
        
        # Assert
        assert current_location == "Bogotá Centro"