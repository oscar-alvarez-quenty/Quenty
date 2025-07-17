from dataclasses import dataclass
from typing import Dict, Any
from src.domain.events.base_event import DomainEvent

@dataclass
class FranchiseRegistered(DomainEvent):
    franchise_id: str = ""
    franchisee_id: str = ""
    zone_id: str = ""
    business_name: str = ""
    investment_amount: str = ""
    
    def get_event_type(self) -> str:
        return "franchise.registered"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "franchise_id": self.franchise_id,
            "franchisee_id": self.franchisee_id,
            "zone_id": self.zone_id,
            "business_name": self.business_name,
            "investment_amount": self.investment_amount
        }

@dataclass
class FranchiseApproved(DomainEvent):
    franchise_id: str = ""
    franchisee_id: str = ""
    zone_id: str = ""
    contract_start_date: str = ""
    contract_end_date: str = ""
    approved_by: str = ""
    
    def get_event_type(self) -> str:
        return "franchise.approved"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "franchise_id": self.franchise_id,
            "franchisee_id": self.franchisee_id,
            "zone_id": self.zone_id,
            "contract_start_date": self.contract_start_date,
            "contract_end_date": self.contract_end_date,
            "approved_by": self.approved_by
        }

@dataclass
class FranchiseSuspended(DomainEvent):
    franchise_id: str = ""
    franchisee_id: str = ""
    suspension_reason: str = ""
    suspended_by: str = ""
    suspension_until: str = ""
    
    def get_event_type(self) -> str:
        return "franchise.suspended"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "franchise_id": self.franchise_id,
            "franchisee_id": self.franchisee_id,
            "suspension_reason": self.suspension_reason,
            "suspended_by": self.suspended_by,
            "suspension_until": self.suspension_until
        }

@dataclass
class LogisticPointCreated(DomainEvent):
    point_id: str = ""
    franchise_id: str = ""
    zone_id: str = ""
    point_name: str = ""
    point_type: str = ""
    address: str = ""
    
    def get_event_type(self) -> str:
        return "logistic_point.created"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "franchise_id": self.franchise_id,
            "zone_id": self.zone_id,
            "point_name": self.point_name,
            "point_type": self.point_type,
            "address": self.address
        }

@dataclass
class TokensIssued(DomainEvent):
    token_id: str = ""
    city_code: str = ""
    franchise_id: str = ""
    issued_amount: str = ""
    total_supply: str = ""
    issue_reason: str = ""
    
    def get_event_type(self) -> str:
        return "tokens.issued"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "city_code": self.city_code,
            "franchise_id": self.franchise_id,
            "issued_amount": self.issued_amount,
            "total_supply": self.total_supply,
            "issue_reason": self.issue_reason
        }

@dataclass
class UtilityDistributionProcessed(DomainEvent):
    distribution_id: str = ""
    city_token_id: str = ""
    period: str = ""
    total_utility_amount: str = ""
    participating_holders: int = 0
    distribution_rate: str = ""
    
    def get_event_type(self) -> str:
        return "utility_distribution.processed"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "distribution_id": self.distribution_id,
            "city_token_id": self.city_token_id,
            "period": self.period,
            "total_utility_amount": self.total_utility_amount,
            "participating_holders": self.participating_holders,
            "distribution_rate": self.distribution_rate
        }