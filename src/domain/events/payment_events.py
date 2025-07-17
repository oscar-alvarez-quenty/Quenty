from dataclasses import dataclass
from typing import Dict, Any
from src.domain.events.base_event import DomainEvent

@dataclass
class PaymentProcessed(DomainEvent):
    payment_id: str = ""
    order_id: str = ""
    customer_id: str = ""
    amount: str = ""
    payment_method: str = ""
    transaction_reference: str = ""
    
    def get_event_type(self) -> str:
        return "payment.processed"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference
        }

@dataclass
class PaymentFailed(DomainEvent):
    payment_id: str = ""
    order_id: str = ""
    customer_id: str = ""
    amount: str = ""
    payment_method: str = ""
    failure_reason: str = ""
    error_code: str = ""
    
    def get_event_type(self) -> str:
        return "payment.failed"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "failure_reason": self.failure_reason,
            "error_code": self.error_code
        }

@dataclass
class PaymentRefunded(DomainEvent):
    refund_id: str = ""
    original_payment_id: str = ""
    order_id: str = ""
    customer_id: str = ""
    refund_amount: str = ""
    refund_reason: str = ""
    
    def get_event_type(self) -> str:
        return "payment.refunded"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "refund_id": self.refund_id,
            "original_payment_id": self.original_payment_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "refund_amount": self.refund_amount,
            "refund_reason": self.refund_reason
        }

@dataclass
class CashOnDeliveryCollected(DomainEvent):
    collection_id: str = ""
    guide_id: str = ""
    order_id: str = ""
    customer_id: str = ""
    collected_amount: str = ""
    collection_method: str = ""
    messenger_id: str = ""
    
    def get_event_type(self) -> str:
        return "cod.collected"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "collection_id": self.collection_id,
            "guide_id": self.guide_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "collected_amount": self.collected_amount,
            "collection_method": self.collection_method,
            "messenger_id": self.messenger_id
        }

@dataclass
class CommissionCalculated(DomainEvent):
    commission_id: str = ""
    recipient_id: str = ""
    order_id: str = ""
    commission_type: str = ""
    base_amount: str = ""
    commission_rate: str = ""
    commission_amount: str = ""
    
    def get_event_type(self) -> str:
        return "commission.calculated"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "commission_id": self.commission_id,
            "recipient_id": self.recipient_id,
            "order_id": self.order_id,
            "commission_type": self.commission_type,
            "base_amount": self.base_amount,
            "commission_rate": self.commission_rate,
            "commission_amount": self.commission_amount
        }

@dataclass
class CommissionPaid(DomainEvent):
    commission_id: str = ""
    recipient_id: str = ""
    liquidation_id: str = ""
    net_amount: str = ""
    payment_method: str = ""
    transaction_reference: str = ""
    
    def get_event_type(self) -> str:
        return "commission.paid"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "commission_id": self.commission_id,
            "recipient_id": self.recipient_id,
            "liquidation_id": self.liquidation_id,
            "net_amount": self.net_amount,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference
        }