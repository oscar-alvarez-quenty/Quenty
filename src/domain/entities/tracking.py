from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from src.domain.value_objects.guide_id import GuideId

class TrackingEventType(Enum):
    ORDER_CREATED = "order_created"
    GUIDE_GENERATED = "guide_generated"
    PACKAGE_PICKED_UP = "package_picked_up"
    IN_TRANSIT = "in_transit"
    ARRIVED_AT_HUB = "arrived_at_hub"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERY_ATTEMPTED = "delivery_attempted"
    DELIVERED = "delivered"
    INCIDENT_REPORTED = "incident_reported"
    RETURNED_TO_SENDER = "returned_to_sender"

@dataclass
class TrackingEvent:
    id: UUID = field(default_factory=uuid4)
    event_type: TrackingEventType = None
    description: str = ""
    location: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    operator: str = ""
    notes: str = ""

@dataclass
class Tracking:
    id: UUID = field(default_factory=uuid4)
    guide_id: GuideId = None
    events: List[TrackingEvent] = field(default_factory=list)
    current_location: str = ""
    estimated_delivery: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_event(self, event_type: TrackingEventType, description: str, 
                  location: str = "", operator: str = "", notes: str = "") -> None:
        event = TrackingEvent(
            event_type=event_type,
            description=description,
            location=location,
            operator=operator,
            notes=notes
        )
        self.events.append(event)
        self.current_location = location
        self.updated_at = datetime.utcnow()
    
    def get_latest_event(self) -> Optional[TrackingEvent]:
        if not self.events:
            return None
        return max(self.events, key=lambda e: e.timestamp)
    
    def get_events_by_type(self, event_type: TrackingEventType) -> List[TrackingEvent]:
        return [event for event in self.events if event.event_type == event_type]
    
    def is_delivered(self) -> bool:
        return any(event.event_type == TrackingEventType.DELIVERED for event in self.events)
    
    def has_incidents(self) -> bool:
        return any(event.event_type == TrackingEventType.INCIDENT_REPORTED for event in self.events)