import pytest
from decimal import Decimal
from datetime import datetime
from src.domain.entities.franchise import Franchise, FranchiseStatus, LogisticPoint, LogisticPointType
from src.domain.value_objects.customer_id import CustomerId
from uuid import uuid4

class TestFranchise:
    
    def test_create_franchise_with_valid_data(self):
        # Arrange
        franchisee_id = CustomerId.generate()
        zone_id = uuid4()
        investment_amount = Decimal('5000000')
        
        # Act
        franchise = Franchise(
            franchisee_id=franchisee_id,
            zone_id=zone_id,
            business_name="Quenty Bogotá Norte",
            investment_amount=investment_amount,
            franchise_fee=Decimal('750000'),
            monthly_fee=Decimal('500000')
        )
        
        # Assert
        assert franchise.franchisee_id == franchisee_id
        assert franchise.zone_id == zone_id
        assert franchise.business_name == "Quenty Bogotá Norte"
        assert franchise.investment_amount == investment_amount
        assert franchise.status == FranchiseStatus.PENDING
    
    def test_approve_franchise_success(self):
        # Arrange
        franchise = Franchise(
            franchisee_id=CustomerId.generate(),
            zone_id=uuid4(),
            business_name="Test Franchise",
            investment_amount=Decimal('5000000'),
            minimum_capital_required=Decimal('5000000')
        )
        
        start_date = datetime.utcnow()
        end_date = datetime(2025, 12, 31)
        
        # Act
        franchise.approve_franchise(start_date, end_date)
        
        # Assert
        assert franchise.status == FranchiseStatus.ACTIVE
        assert franchise.contract_start_date == start_date
        assert franchise.contract_end_date == end_date
    
    def test_approve_franchise_insufficient_capital(self):
        # Arrange
        franchise = Franchise(
            franchisee_id=CustomerId.generate(),
            zone_id=uuid4(),
            business_name="Test Franchise",
            investment_amount=Decimal('3000000'),  # Below minimum
            minimum_capital_required=Decimal('5000000')
        )
        
        start_date = datetime.utcnow()
        end_date = datetime(2025, 12, 31)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Investment amount must be at least"):
            franchise.approve_franchise(start_date, end_date)
    
    def test_cannot_approve_non_pending_franchise(self):
        # Arrange
        franchise = Franchise(
            franchisee_id=CustomerId.generate(),
            zone_id=uuid4(),
            business_name="Test Franchise",
            investment_amount=Decimal('5000000'),
            status=FranchiseStatus.ACTIVE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Only pending franchises can be approved"):
            franchise.approve_franchise(datetime.utcnow(), datetime(2025, 12, 31))
    
    def test_suspend_franchise(self):
        # Arrange
        franchise = Franchise(
            franchisee_id=CustomerId.generate(),
            zone_id=uuid4(),
            business_name="Test Franchise",
            investment_amount=Decimal('5000000'),
            status=FranchiseStatus.ACTIVE
        )
        
        # Act
        franchise.suspend_franchise("Non-compliance")
        
        # Assert
        assert franchise.status == FranchiseStatus.SUSPENDED
    
    def test_calculate_monthly_revenue_share(self):
        # Arrange
        franchise = Franchise(
            franchisee_id=CustomerId.generate(),
            zone_id=uuid4(),
            business_name="Test Franchise",
            investment_amount=Decimal('5000000'),
            monthly_fee=Decimal('500000'),
            commission_rate=Decimal('0.15')
        )
        
        gross_revenue = Decimal('10000000')
        
        # Act
        revenue_share = franchise.calculate_monthly_revenue_share(gross_revenue)
        
        # Assert
        expected = Decimal('500000') + (Decimal('10000000') * Decimal('0.15'))
        assert revenue_share == expected
    
    def test_can_allocate_tokens_active_franchise(self):
        # Arrange
        franchise = Franchise(
            franchisee_id=CustomerId.generate(),
            zone_id=uuid4(),
            business_name="Test Franchise",
            investment_amount=Decimal('5000000'),
            status=FranchiseStatus.ACTIVE,
            contract_start_date=datetime(2024, 1, 1),
            contract_end_date=datetime(2025, 12, 31),
            token_allocation=Decimal('1000')
        )
        
        # Act & Assert
        assert franchise.can_allocate_tokens() == True
    
    def test_cannot_allocate_tokens_inactive_franchise(self):
        # Arrange
        franchise = Franchise(
            franchisee_id=CustomerId.generate(),
            zone_id=uuid4(),
            business_name="Test Franchise",
            investment_amount=Decimal('5000000'),
            status=FranchiseStatus.SUSPENDED,
            token_allocation=Decimal('1000')
        )
        
        # Act & Assert
        assert franchise.can_allocate_tokens() == False

class TestLogisticPoint:
    
    def test_create_logistic_point(self):
        # Arrange & Act
        point = LogisticPoint(
            name="Punto Norte",
            address="Calle 123 #45-67",
            city="Bogotá",
            phone="3001234567",
            email="norte@quenty.com",
            point_type=LogisticPointType.FRANCHISE,
            operating_hours="8:00-18:00"
        )
        
        # Assert
        assert point.name == "Punto Norte"
        assert point.point_type == LogisticPointType.FRANCHISE
        assert point.is_active == True
    
    def test_can_receive_packages_franchise_point(self):
        # Arrange
        point = LogisticPoint(
            name="Test Point",
            address="Test Address",
            city="Test City",
            phone="1234567890",
            email="test@test.com",
            point_type=LogisticPointType.FRANCHISE,
            is_active=True
        )
        
        # Act & Assert
        assert point.can_receive_packages() == True
    
    def test_cannot_receive_packages_inactive_point(self):
        # Arrange
        point = LogisticPoint(
            name="Test Point",
            address="Test Address",
            city="Test City",
            phone="1234567890",
            email="test@test.com",
            point_type=LogisticPointType.FRANCHISE,
            is_active=False
        )
        
        # Act & Assert
        assert point.can_receive_packages() == False