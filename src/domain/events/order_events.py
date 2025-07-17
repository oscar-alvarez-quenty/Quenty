from dataclasses import dataclass
from typing import Dict, Any
from src.domain.events.base_event import DomainEvent
from src.domain.entities.order import ServiceType

@dataclass
class OrderCreated(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    service_type: ServiceType = ServiceType.NATIONAL
    origin_city: str = ""
    destination_city: str = ""
    declared_value: str = ""
    
    def get_event_type(self) -> str:
        return "order.created"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "service_type": self.service_type.value,
            "origin_city": self.origin_city,
            "destination_city": self.destination_city,
            "declared_value": self.declared_value
        }

@dataclass
class OrderQuoted(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    quoted_price: str = ""
    estimated_delivery_days: int = 0
    logistics_operator: str = ""
    
    def get_event_type(self) -> str:
        return "order.quoted"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "quoted_price": self.quoted_price,
            "estimated_delivery_days": self.estimated_delivery_days,
            "logistics_operator": self.logistics_operator
        }

@dataclass
class OrderConfirmed(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    confirmed_price: str = ""
    payment_method: str = ""
    
    def get_event_type(self) -> str:
        return "order.confirmed"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "confirmed_price": self.confirmed_price,
            "payment_method": self.payment_method
        }

@dataclass
class OrderCancelled(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    cancellation_reason: str = ""
    cancelled_by: str = ""
    
    def get_event_type(self) -> str:
        return "order.cancelled"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "cancellation_reason": self.cancellation_reason,
            "cancelled_by": self.cancelled_by
        }

@dataclass
class GuideGenerated(DomainEvent):
    guide_id: str = ""
    order_id: str = ""
    customer_id: str = ""
    logistics_operator: str = ""
    pickup_address: str = ""
    delivery_address: str = ""
    
    def get_event_type(self) -> str:
        return "guide.generated"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "guide_id": self.guide_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "logistics_operator": self.logistics_operator,
            "pickup_address": self.pickup_address,
            "delivery_address": self.delivery_address
        }

@dataclass
class PackagePickedUp(DomainEvent):
    guide_id: str = ""
    order_id: str = ""
    pickup_location: str = ""
    messenger_id: str = ""
    pickup_timestamp: str = ""
    
    def get_event_type(self) -> str:
        return "package.picked_up"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "guide_id": self.guide_id,
            "order_id": self.order_id,
            "pickup_location": self.pickup_location,
            "messenger_id": self.messenger_id,
            "pickup_timestamp": self.pickup_timestamp
        }

@dataclass
class PackageInTransit(DomainEvent):
    guide_id: str = ""
    order_id: str = ""
    current_location: str = ""
    next_location: str = ""
    estimated_arrival: str = ""
    
    def get_event_type(self) -> str:
        return "package.in_transit"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "guide_id": self.guide_id,
            "order_id": self.order_id,
            "current_location": self.current_location,
            "next_location": self.next_location,
            "estimated_arrival": self.estimated_arrival
        }

@dataclass
class PackageOutForDelivery(DomainEvent):
    guide_id: str = ""
    order_id: str = ""
    delivery_location: str = ""
    messenger_id: str = ""
    estimated_delivery: str = ""
    
    def get_event_type(self) -> str:
        return "package.out_for_delivery"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "guide_id": self.guide_id,
            "order_id": self.order_id,
            "delivery_location": self.delivery_location,
            "messenger_id": self.messenger_id,
            "estimated_delivery": self.estimated_delivery
        }

@dataclass
class PackageDelivered(DomainEvent):
    guide_id: str = ""
    order_id: str = ""
    delivery_location: str = ""
    recipient_name: str = ""
    delivery_timestamp: str = ""
    delivery_evidence: str = ""
    
    def get_event_type(self) -> str:
        return "package.delivered"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "guide_id": self.guide_id,
            "order_id": self.order_id,
            "delivery_location": self.delivery_location,
            "recipient_name": self.recipient_name,
            "delivery_timestamp": self.delivery_timestamp,
            "delivery_evidence": self.delivery_evidence
        }

@dataclass
class IncidentReported(DomainEvent):
    incident_id: str = ""
    guide_id: str = ""
    order_id: str = ""
    incident_type: str = ""
    description: str = ""
    reported_by: str = ""
    location: str = ""
    
    def get_event_type(self) -> str:
        return "incident.reported"
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "guide_id": self.guide_id,
            "order_id": self.order_id,
            "incident_type": self.incident_type,
            "description": self.description,
            "reported_by": self.reported_by,
            "location": self.location
        }