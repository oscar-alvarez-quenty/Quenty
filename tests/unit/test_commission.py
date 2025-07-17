import pytest
from decimal import Decimal
from datetime import datetime
from src.domain.entities.commission import Commission, CommissionType, CommissionStatus, Liquidation
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.order_id import OrderId

class TestCommission:
    
    def test_create_commission_with_valid_data(self):
        # Arrange
        recipient_id = CustomerId.generate()
        order_id = OrderId.generate()
        base_amount = Decimal('100000')
        commission_rate = Decimal('0.05')
        
        # Act
        commission = Commission(
            recipient_id=recipient_id,
            order_id=order_id,
            commission_type=CommissionType.SHIPMENT,
            base_amount=base_amount,
            commission_rate=commission_rate
        )
        
        # Assert
        assert commission.recipient_id == recipient_id
        assert commission.order_id == order_id
        assert commission.commission_type == CommissionType.SHIPMENT
        assert commission.base_amount == base_amount
        assert commission.commission_rate == commission_rate
        assert commission.status == CommissionStatus.PENDING
    
    def test_calculate_commission_success(self):
        # Arrange
        commission = Commission(
            recipient_id=CustomerId.generate(),
            order_id=OrderId.generate(),
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05')
        )
        
        # Act
        commission.calculate_commission()
        
        # Assert
        assert commission.commission_amount == Decimal('5000')  # 5% of 100,000
        assert commission.tax_amount == Decimal('950')  # 19% of 5,000
        assert commission.net_amount == Decimal('4050')  # 5,000 - 950
        assert commission.status == CommissionStatus.CALCULATED
        assert commission.calculation_date is not None
    
    def test_cannot_calculate_non_pending_commission(self):
        # Arrange
        commission = Commission(
            recipient_id=CustomerId.generate(),
            order_id=OrderId.generate(),
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05'),
            status=CommissionStatus.CALCULATED
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Only pending commissions can be calculated"):
            commission.calculate_commission()
    
    def test_approve_commission(self):
        # Arrange
        commission = Commission(
            recipient_id=CustomerId.generate(),
            order_id=OrderId.generate(),
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05'),
            status=CommissionStatus.CALCULATED
        )
        
        # Act
        commission.approve()
        
        # Assert
        assert commission.status == CommissionStatus.APPROVED
        assert commission.approval_date is not None
    
    def test_mark_as_paid(self):
        # Arrange
        commission = Commission(
            recipient_id=CustomerId.generate(),
            order_id=OrderId.generate(),
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05'),
            status=CommissionStatus.APPROVED
        )
        
        # Act
        commission.mark_as_paid()
        
        # Assert
        assert commission.status == CommissionStatus.PAID
        assert commission.payment_date is not None
    
    def test_block_commission(self):
        # Arrange
        commission = Commission(
            recipient_id=CustomerId.generate(),
            order_id=OrderId.generate(),
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05'),
            status=CommissionStatus.CALCULATED
        )
        
        reason = "Customer has overdue balance"
        
        # Act
        commission.block(reason)
        
        # Assert
        assert commission.status == CommissionStatus.BLOCKED
        assert "Blocked: " + reason in commission.notes
    
    def test_cannot_block_paid_commission(self):
        # Arrange
        commission = Commission(
            recipient_id=CustomerId.generate(),
            order_id=OrderId.generate(),
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05'),
            status=CommissionStatus.PAID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot block paid commissions"):
            commission.block("Test reason")

class TestLiquidation:
    
    def test_create_liquidation(self):
        # Arrange
        recipient_id = CustomerId.generate()
        period = "2024-01"
        
        # Act
        liquidation = Liquidation(
            recipient_id=recipient_id,
            period=period
        )
        
        # Assert
        assert liquidation.recipient_id == recipient_id
        assert liquidation.period == period
        assert liquidation.total_commissions == Decimal('0.00')
        assert liquidation.status.value == "pending"
    
    def test_add_commission_to_liquidation(self):
        # Arrange
        liquidation = Liquidation(
            recipient_id=CustomerId.generate(),
            period="2024-01"
        )
        
        commission = Commission(
            recipient_id=liquidation.recipient_id,
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05'),
            status=CommissionStatus.APPROVED
        )
        commission.calculate_commission()
        commission.approve()
        
        # Act
        liquidation.add_commission(commission)
        
        # Assert
        assert commission.id in liquidation.commission_ids
        assert liquidation.total_commissions == commission.commission_amount
        assert liquidation.total_taxes == commission.tax_amount
        assert liquidation.net_amount == commission.net_amount
    
    def test_cannot_add_non_approved_commission(self):
        # Arrange
        liquidation = Liquidation(
            recipient_id=CustomerId.generate(),
            period="2024-01"
        )
        
        commission = Commission(
            recipient_id=liquidation.recipient_id,
            commission_type=CommissionType.SHIPMENT,
            base_amount=Decimal('100000'),
            commission_rate=Decimal('0.05'),
            status=CommissionStatus.PENDING
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Only approved commissions can be added to liquidation"):
            liquidation.add_commission(commission)
    
    def test_process_payment(self):
        # Arrange
        liquidation = Liquidation(
            recipient_id=CustomerId.generate(),
            period="2024-01"
        )
        
        transaction_ref = "TXN_123456"
        
        # Act
        liquidation.process_payment(transaction_ref)
        
        # Assert
        assert liquidation.status.value == "processing"
        assert liquidation.transaction_reference == transaction_ref
        assert liquidation.processed_at is not None
    
    def test_complete_payment(self):
        # Arrange
        liquidation = Liquidation(
            recipient_id=CustomerId.generate(),
            period="2024-01"
        )
        liquidation.process_payment("TXN_123456")
        
        # Act
        liquidation.complete_payment()
        
        # Assert
        assert liquidation.status.value == "completed"
        assert liquidation.completed_at is not None