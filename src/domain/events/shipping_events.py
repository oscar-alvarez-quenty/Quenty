from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.events.base_event import DomainEvent


@dataclass
class ShipmentPickedUp(DomainEvent):
    guide_id: str
    pickup_datetime: datetime
    pickup_location: str
    operator_id: str


@dataclass
class ShipmentInTransit(DomainEvent):
    guide_id: str
    current_location: str
    description: str
    timestamp: datetime


@dataclass
class ShipmentDelivered(DomainEvent):
    guide_id: str
    delivery_datetime: datetime
    delivery_address: str
    recipient_name: str
    delivery_attempt: int


@dataclass
class ShipmentFailed(DomainEvent):
    guide_id: str
    failure_reason: str
    final_attempt_date: datetime
    total_attempts: int


@dataclass
class IncidentReported(DomainEvent):
    guide_id: str
    incident_id: str
    incident_type: str
    description: str
    severity: str
    location: str
    reported_by: str


@dataclass
class DeliveryRescheduled(DomainEvent):
    guide_id: str
    attempt_number: int
    reschedule_reason: str
    next_attempt_date: Optional[datetime]


@dataclass
class OperatorAssigned(DomainEvent):
    guide_id: str
    operator_id: str
    operator_name: str
    assigned_at: datetime


@dataclass
class PickupScheduled(DomainEvent):
    guide_id: str
    pickup_date: datetime
    pickup_address: str
    operator_id: str


@dataclass
class ShipmentReturningToOrigin(DomainEvent):
    guide_id: str
    return_reason: str
    return_initiated_at: datetime
    original_destination: str


@dataclass
class DeliveryAttemptFailed(DomainEvent):
    guide_id: str
    attempt_number: int
    failure_reason: str
    attempted_at: datetime
    next_attempt_scheduled: Optional[datetime]


@dataclass
class ShipmentRouteUpdated(DomainEvent):
    guide_id: str
    new_route: str
    estimated_delivery_update: datetime
    reason: str


@dataclass
class CustomsClearanceStarted(DomainEvent):
    guide_id: str
    customs_location: str
    started_at: datetime
    estimated_clearance_time: int  # hours


@dataclass
class CustomsClearanceCompleted(DomainEvent):
    guide_id: str
    customs_location: str
    completed_at: datetime
    clearance_duration_hours: int


@dataclass
class ShipmentDamageReported(DomainEvent):
    guide_id: str
    damage_description: str
    damage_severity: str  # "minor", "major", "total"
    reported_at: datetime
    reported_by: str
    evidence_urls: list


@dataclass
class ShipmentLost(DomainEvent):
    guide_id: str
    last_known_location: str
    reported_lost_at: datetime
    investigation_started: bool


@dataclass
class DeliveryConfirmationReceived(DomainEvent):
    guide_id: str
    confirmation_method: str  # "signature", "photo", "sms", "email"
    confirmed_by: str
    confirmation_data: dict  # signature image, photo URL, etc.


@dataclass
class ShipmentIntercepted(DomainEvent):
    guide_id: str
    interception_reason: str
    intercepted_at: datetime
    intercepted_location: str
    new_instructions: str


@dataclass
class DeliveryTimeSlotChanged(DomainEvent):
    guide_id: str
    old_time_slot: str
    new_time_slot: str
    change_reason: str
    requested_by: str


@dataclass
class ShipmentConsolidated(DomainEvent):
    guide_ids: list  # Multiple shipments consolidated
    consolidation_location: str
    consolidated_at: datetime
    new_estimated_delivery: datetime


@dataclass
class ShipmentSplit(DomainEvent):
    original_guide_id: str
    new_guide_ids: list
    split_reason: str
    split_at: datetime