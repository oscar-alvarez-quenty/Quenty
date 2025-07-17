from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.order_id import OrderId

class CommissionType(Enum):
    SHIPMENT = "shipment"
    FRANCHISE_FEE = "franchise_fee"
    REFERRAL = "referral"
    VOLUME_BONUS = "volume_bonus"
    TOKEN_DISTRIBUTION = "token_distribution"

class CommissionStatus(Enum):
    PENDING = "pending"
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class LiquidationStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Commission:
    id: UUID = field(default_factory=uuid4)
    recipient_id: CustomerId = None
    order_id: Optional[OrderId] = None
    franchise_id: Optional[UUID] = None
    commission_type: CommissionType = CommissionType.SHIPMENT
    base_amount: Decimal = Decimal('0.00')
    commission_rate: Decimal = Decimal('0.00')
    commission_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    net_amount: Decimal = Decimal('0.00')
    status: CommissionStatus = CommissionStatus.PENDING
    calculation_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    reference_period: str = ""  # YYYY-MM for monthly commissions
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_commission(self, tax_rate: Decimal = Decimal('0.19')) -> None:
        """Calcula la comisión aplicando impuestos"""
        if self.status != CommissionStatus.PENDING:
            raise ValueError("Only pending commissions can be calculated")
        
        self.commission_amount = self.base_amount * self.commission_rate
        self.tax_amount = self.commission_amount * tax_rate
        self.net_amount = self.commission_amount - self.tax_amount
        self.status = CommissionStatus.CALCULATED
        self.calculation_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def approve(self) -> None:
        """Aprueba la comisión para pago"""
        if self.status != CommissionStatus.CALCULATED:
            raise ValueError("Only calculated commissions can be approved")
        
        self.status = CommissionStatus.APPROVED
        self.approval_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_paid(self) -> None:
        """Marca la comisión como pagada"""
        if self.status != CommissionStatus.APPROVED:
            raise ValueError("Only approved commissions can be marked as paid")
        
        self.status = CommissionStatus.PAID
        self.payment_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def block(self, reason: str = "") -> None:
        """Bloquea la comisión"""
        if self.status == CommissionStatus.PAID:
            raise ValueError("Cannot block paid commissions")
        
        self.status = CommissionStatus.BLOCKED
        self.notes = f"Blocked: {reason}"
        self.updated_at = datetime.utcnow()
    
    def cancel(self, reason: str = "") -> None:
        """Cancela la comisión"""
        if self.status == CommissionStatus.PAID:
            raise ValueError("Cannot cancel paid commissions")
        
        self.status = CommissionStatus.CANCELLED
        self.notes = f"Cancelled: {reason}"
        self.updated_at = datetime.utcnow()

@dataclass
class CommissionRule:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    commission_type: CommissionType = CommissionType.SHIPMENT
    customer_type: str = ""  # small, medium, large, franchise, ally
    service_type: str = ""   # national, international
    minimum_amount: Decimal = Decimal('0.00')
    maximum_amount: Optional[Decimal] = None
    commission_rate: Decimal = Decimal('0.00')
    is_active: bool = True
    effective_from: datetime = field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_applicable(self, amount: Decimal, customer_type: str, service_type: str) -> bool:
        """Verifica si la regla es aplicable"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if now < self.effective_from:
            return False
        
        if self.effective_until and now > self.effective_until:
            return False
        
        if self.customer_type and self.customer_type != customer_type:
            return False
        
        if self.service_type and self.service_type != service_type:
            return False
        
        if amount < self.minimum_amount:
            return False
        
        if self.maximum_amount and amount > self.maximum_amount:
            return False
        
        return True

@dataclass
class Liquidation:
    id: UUID = field(default_factory=uuid4)
    recipient_id: CustomerId = None
    period: str = ""  # YYYY-MM
    commission_ids: List[UUID] = field(default_factory=list)
    total_commissions: Decimal = Decimal('0.00')
    total_taxes: Decimal = Decimal('0.00')
    net_amount: Decimal = Decimal('0.00')
    payment_method: str = ""  # bank_transfer, wallet, check
    bank_account: str = ""
    status: LiquidationStatus = LiquidationStatus.PENDING
    generated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    transaction_reference: str = ""
    notes: str = ""
    
    def add_commission(self, commission: Commission) -> None:
        """Agrega una comisión a la liquidación"""
        if commission.status != CommissionStatus.APPROVED:
            raise ValueError("Only approved commissions can be added to liquidation")
        
        self.commission_ids.append(commission.id)
        self.total_commissions += commission.commission_amount
        self.total_taxes += commission.tax_amount
        self.net_amount += commission.net_amount
    
    def process_payment(self, transaction_reference: str) -> None:
        """Procesa el pago de la liquidación"""
        if self.status != LiquidationStatus.PENDING:
            raise ValueError("Only pending liquidations can be processed")
        
        self.status = LiquidationStatus.PROCESSING
        self.transaction_reference = transaction_reference
        self.processed_at = datetime.utcnow()
    
    def complete_payment(self) -> None:
        """Completa el pago de la liquidación"""
        if self.status != LiquidationStatus.PROCESSING:
            raise ValueError("Only processing liquidations can be completed")
        
        self.status = LiquidationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def fail_payment(self, reason: str = "") -> None:
        """Marca el pago como fallido"""
        if self.status != LiquidationStatus.PROCESSING:
            raise ValueError("Only processing liquidations can be marked as failed")
        
        self.status = LiquidationStatus.FAILED
        self.notes = f"Payment failed: {reason}"