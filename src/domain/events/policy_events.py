from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.events.base_event import DomainEvent


@dataclass
class PolicyCreated(DomainEvent):
    policy_id: str
    name: str
    policy_type: str
    scope: str
    scope_value: str
    created_by: str


@dataclass
class PolicyActivated(DomainEvent):
    policy_id: str
    approved_by: str
    activated_at: datetime
    scope: str
    scope_value: str


@dataclass
class PolicyDeactivated(DomainEvent):
    policy_id: str
    deactivated_at: datetime
    scope: str
    scope_value: str
    deactivated_by: Optional[str] = None


@dataclass
class PolicyRuleAdded(DomainEvent):
    policy_id: str
    rule_id: str
    rule_condition: str
    rule_action: str
    added_by: str


@dataclass
class PolicyRuleRemoved(DomainEvent):
    policy_id: str
    rule_id: str
    removed_by: str
    removal_reason: str


@dataclass
class PolicyExceptionAdded(DomainEvent):
    policy_id: str
    exception_id: str
    entity_type: str
    entity_id: str
    valid_from: datetime
    valid_until: Optional[datetime]


@dataclass
class PolicyExceptionRemoved(DomainEvent):
    policy_id: str
    exception_id: str
    removed_by: str
    removal_reason: str


@dataclass
class PricingUpdated(DomainEvent):
    policy_id: str
    service_type: str
    old_rate: float
    new_rate: float
    updated_by: str
    updated_at: datetime


@dataclass
class ServiceCatalogUpdated(DomainEvent):
    catalog_id: str
    name: str
    services_count: int
    updated_at: datetime
    updated_by: Optional[str] = None


@dataclass
class ServiceAddedToCatalog(DomainEvent):
    catalog_id: str
    service_id: str
    service_name: str
    service_config: dict
    added_by: str


@dataclass
class ServiceRemovedFromCatalog(DomainEvent):
    catalog_id: str
    service_id: str
    removed_by: str
    removal_reason: str


@dataclass
class PolicyVersionCreated(DomainEvent):
    original_policy_id: str
    new_policy_id: str
    version_number: int
    created_by: str
    changes_summary: str


@dataclass
class PolicyApplied(DomainEvent):
    policy_id: str
    entity_type: str
    entity_id: str
    applied_rules: list
    application_result: dict
    applied_at: datetime


@dataclass
class PolicyViolationDetected(DomainEvent):
    policy_id: str
    entity_type: str
    entity_id: str
    violation_details: str
    severity: str  # "low", "medium", "high", "critical"
    detected_at: datetime


@dataclass
class PolicyAuditStarted(DomainEvent):
    audit_id: str
    policy_ids: list
    audit_scope: str
    started_by: str
    started_at: datetime


@dataclass
class PolicyAuditCompleted(DomainEvent):
    audit_id: str
    findings_count: int
    violations_found: int
    recommendations: list
    completed_at: datetime


@dataclass
class PolicyPerformanceReported(DomainEvent):
    policy_id: str
    period_start: datetime
    period_end: datetime
    applications_count: int
    violations_count: int
    effectiveness_score: float