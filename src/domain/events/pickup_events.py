from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.events.base_event import DomainEvent


@dataclass
class PickupRequested(DomainEvent):
    pickup_id: str
    guide_id: str
    customer_id: str
    pickup_type: str
    pickup_address: str
    preferred_date: Optional[datetime]
    priority: str


@dataclass
class PickupScheduled(DomainEvent):
    pickup_id: str
    scheduled_date: datetime
    assigned_operator_id: str
    time_slot_start: datetime
    time_slot_end: datetime


@dataclass
class PickupCompleted(DomainEvent):
    pickup_id: str
    guide_id: str
    operator_id: str
    completed_at: datetime
    packages_collected: int
    completion_notes: str


@dataclass
class PickupFailed(DomainEvent):
    pickup_id: str
    guide_id: str
    operator_id: str
    failure_reason: str
    attempt_number: int
    auto_reschedule: bool


@dataclass
class PickupRescheduled(DomainEvent):
    pickup_id: str
    old_date: Optional[datetime]
    new_date: datetime
    reschedule_reason: str
    new_operator_id: str


@dataclass
class PickupCancelled(DomainEvent):
    pickup_id: str
    guide_id: str
    cancellation_reason: str
    cancelled_by: str
    cancelled_at: datetime


@dataclass
class PickupRouteCreated(DomainEvent):
    route_id: str
    operator_id: str
    scheduled_date: datetime
    pickup_count: int
    estimated_duration_hours: Optional[float]


@dataclass
class RouteOptimized(DomainEvent):
    route_id: str
    operator_id: str
    pickup_count: int
    scheduled_date: datetime
    estimated_duration_hours: Optional[float]


@dataclass
class PickupRouteStarted(DomainEvent):
    route_id: str
    operator_id: str
    started_at: datetime
    first_pickup_id: str


@dataclass
class PickupRouteCompleted(DomainEvent):
    route_id: str
    operator_id: str
    completed_at: datetime
    successful_pickups: int
    failed_pickups: int
    total_distance_km: Optional[float]


@dataclass
class LogisticPointAssigned(DomainEvent):
    pickup_id: str
    guide_id: str
    point_id: str
    point_name: str
    customer_notified: bool


@dataclass
class PickupTimeSlotReserved(DomainEvent):
    pickup_id: str
    operator_id: str
    time_slot_start: datetime
    time_slot_end: datetime
    slot_type: str  # "morning", "afternoon", "evening"


@dataclass
class PickupCapacityExceeded(DomainEvent):
    operator_id: str
    date: datetime
    requested_pickups: int
    max_capacity: int
    overflow_count: int


@dataclass
class PickupDelayed(DomainEvent):
    pickup_id: str
    scheduled_time: datetime
    current_time: datetime
    delay_minutes: int
    delay_reason: str


@dataclass
class CustomerNotified(DomainEvent):
    pickup_id: str
    customer_id: str
    notification_type: str  # "scheduled", "en_route", "completed", "failed"
    notification_channel: str  # "sms", "email", "whatsapp", "push"
    sent_at: datetime