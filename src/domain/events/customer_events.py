from dataclasses import dataclass
from typing import Dict, Any
from src.domain.events.base_event import DomainEvent
from src.domain.value_objects.customer_type import CustomerType

@dataclass
class CustomerCreated(DomainEvent):
    customer_id: str = ""
    email: str = ""
    customer_type: CustomerType = CustomerType.SMALL
    business_name: str = ""
    
    def get_event_type(self) -> str:
        return "customer.created"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "email": self.email,
            "customer_type": self.customer_type.value,
            "business_name": self.business_name
        }

@dataclass
class CustomerUpdated(DomainEvent):
    customer_id: str = ""
    updated_fields: Dict[str, Any] = None
    
    def get_event_type(self) -> str:
        return "customer.updated"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "updated_fields": self.updated_fields or {}
        }

@dataclass
class CustomerKYCValidated(DomainEvent):
    customer_id: str = ""
    validation_method: str = ""
    validated_by: str = ""
    
    def get_event_type(self) -> str:
        return "customer.kyc_validated"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "validation_method": self.validation_method,
            "validated_by": self.validated_by
        }

@dataclass
class CustomerDeactivated(DomainEvent):
    customer_id: str = ""
    reason: str = ""
    deactivated_by: str = ""
    
    def get_event_type(self) -> str:
        return "customer.deactivated"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "reason": self.reason,
            "deactivated_by": self.deactivated_by
        }

@dataclass
class WalletCredited(DomainEvent):
    wallet_id: str = ""
    customer_id: str = ""
    amount: str = ""
    transaction_type: str = ""
    description: str = ""
    
    def get_event_type(self) -> str:
        return "wallet.credited"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "description": self.description
        }

@dataclass
class WalletDebited(DomainEvent):
    wallet_id: str = ""
    customer_id: str = ""
    amount: str = ""
    transaction_type: str = ""
    description: str = ""
    
    def get_event_type(self) -> str:
        return "wallet.debited"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "description": self.description
        }

@dataclass
class MicrocreditRequested(DomainEvent):
    microcredit_id: str = ""
    customer_id: str = ""
    requested_amount: str = ""
    credit_score: int = 0
    
    def get_event_type(self) -> str:
        return "microcredit.requested"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "microcredit_id": self.microcredit_id,
            "customer_id": self.customer_id,
            "requested_amount": self.requested_amount,
            "credit_score": self.credit_score
        }

@dataclass
class MicrocreditApproved(DomainEvent):
    microcredit_id: str = ""
    customer_id: str = ""
    approved_amount: str = ""
    interest_rate: str = ""
    term_days: int = 0
    
    def get_event_type(self) -> str:
        return "microcredit.approved"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "microcredit_id": self.microcredit_id,
            "customer_id": self.customer_id,
            "approved_amount": self.approved_amount,
            "interest_rate": self.interest_rate,
            "term_days": self.term_days
        }