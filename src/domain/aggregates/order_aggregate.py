from typing import List, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from src.domain.entities.order import Order, OrderStatus
from src.domain.entities.guide import Guide, GuideStatus
from src.domain.entities.tracking import Tracking, TrackingEvent, TrackingEventType
from src.domain.entities.incident import Incident, DeliveryAttempt, DeliveryRetry
from src.domain.events.order_events import (
    OrderCreated, OrderQuoted, OrderConfirmed, OrderCancelled,
    GuideGenerated, PackagePickedUp, PackageInTransit, 
    PackageDelivered, IncidentReported
)
from src.domain.events.base_event import DomainEvent
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.guide_id import GuideId

@dataclass
class OrderAggregate:
    """
    Agregado de Orden que encapsula el ciclo completo de vida de un envío
    """
    order: Order
    guide: Optional[Guide] = None
    tracking: Optional[Tracking] = None
    incidents: List[Incident] = field(default_factory=list)
    delivery_attempts: List[DeliveryAttempt] = field(default_factory=list)
    delivery_retry: Optional[DeliveryRetry] = None
    _domain_events: List[DomainEvent] = field(default_factory=list)
    
    @classmethod
    def create_new_order(cls, order_data: dict) -> "OrderAggregate":
        """Factory method para crear una nueva orden"""
        
        order = Order(**order_data)
        aggregate = cls(order=order)
        
        # Registrar evento de creación
        event = OrderCreated(
            aggregate_id=order.id.value,
            aggregate_type="order",
            order_id=str(order.id.value),
            customer_id=str(order.customer_id.value),
            service_type=order.service_type,
            origin_city=order.origin_city,
            destination_city=order.recipient.city,
            declared_value=str(order.declared_value)
        )
        aggregate._add_domain_event(event)
        
        return aggregate
    
    def quote_order(self, price: Decimal, delivery_days: int, operator: str = "") -> None:
        """Cotiza la orden"""
        if self.order.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be quoted")
        
        self.order.set_quote(price, delivery_days)
        
        event = OrderQuoted(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            order_id=str(self.order.id.value),
            customer_id=str(self.order.customer_id.value),
            quoted_price=str(price),
            estimated_delivery_days=delivery_days,
            logistics_operator=operator
        )
        self._add_domain_event(event)
    
    def confirm_order(self, payment_method: str = "") -> None:
        """Confirma la orden"""
        if self.order.status != OrderStatus.QUOTED:
            raise ValueError("Only quoted orders can be confirmed")
        
        self.order.confirm()
        
        event = OrderConfirmed(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            order_id=str(self.order.id.value),
            customer_id=str(self.order.customer_id.value),
            confirmed_price=str(self.order.quoted_price or 0),
            payment_method=payment_method
        )
        self._add_domain_event(event)
    
    def cancel_order(self, reason: str = "", cancelled_by: str = "customer") -> None:
        """Cancela la orden"""
        self.order.cancel()
        
        event = OrderCancelled(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            order_id=str(self.order.id.value),
            customer_id=str(self.order.customer_id.value),
            cancellation_reason=reason,
            cancelled_by=cancelled_by
        )
        self._add_domain_event(event)
    
    def generate_guide(self, logistics_operator: str = "Quenty Express") -> Guide:
        """Genera la guía de envío"""
        if self.order.status != OrderStatus.CONFIRMED:
            raise ValueError("Can only generate guide for confirmed orders")
        
        # Crear la guía
        self.guide = Guide(
            order_id=self.order.id,
            customer_id=self.order.customer_id,
            logistics_operator=logistics_operator
        )
        
        # Crear tracking
        self.tracking = Tracking(guide_id=self.guide.id)
        self.tracking.add_event(
            TrackingEventType.GUIDE_GENERATED,
            "Guía de envío generada",
            location=self.order.origin_city,
            operator=logistics_operator
        )
        
        # Actualizar estado de la orden
        self.order.mark_with_guide()
        
        event = GuideGenerated(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            guide_id=str(self.guide.id.value),
            order_id=str(self.order.id.value),
            customer_id=str(self.order.customer_id.value),
            logistics_operator=logistics_operator,
            pickup_address=self.order.origin_address,
            delivery_address=self.order.recipient.address
        )
        self._add_domain_event(event)
        
        return self.guide
    
    def pickup_package(self, location: str, messenger_id: str = "") -> None:
        """Marca el paquete como recolectado"""
        if not self.guide:
            raise ValueError("Guide must be generated before pickup")
        
        self.guide.mark_picked_up()
        
        if self.tracking:
            self.tracking.add_event(
                TrackingEventType.PACKAGE_PICKED_UP,
                "Paquete recolectado",
                location=location,
                operator=messenger_id
            )
        
        event = PackagePickedUp(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            guide_id=str(self.guide.id.value),
            order_id=str(self.order.id.value),
            pickup_location=location,
            messenger_id=messenger_id,
            pickup_timestamp=datetime.utcnow().isoformat()
        )
        self._add_domain_event(event)
    
    def update_transit_status(self, current_location: str, next_location: str = "") -> None:
        """Actualiza el estado en tránsito"""
        if not self.guide:
            raise ValueError("Guide must exist to update transit status")
        
        self.guide.mark_in_transit()
        
        if self.tracking:
            self.tracking.add_event(
                TrackingEventType.IN_TRANSIT,
                f"En tránsito hacia {next_location}" if next_location else "En tránsito",
                location=current_location
            )
        
        event = PackageInTransit(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            guide_id=str(self.guide.id.value),
            order_id=str(self.order.id.value),
            current_location=current_location,
            next_location=next_location,
            estimated_arrival=""
        )
        self._add_domain_event(event)
    
    def deliver_package(self, recipient_name: str, location: str, evidence: str = "") -> None:
        """Entrega el paquete"""
        if not self.guide:
            raise ValueError("Guide must exist to deliver package")
        
        self.guide.mark_delivered()
        
        if self.tracking:
            self.tracking.add_event(
                TrackingEventType.DELIVERED,
                f"Entregado a {recipient_name}",
                location=location,
                notes=evidence
            )
        
        event = PackageDelivered(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            guide_id=str(self.guide.id.value),
            order_id=str(self.order.id.value),
            delivery_location=location,
            recipient_name=recipient_name,
            delivery_timestamp=datetime.utcnow().isoformat(),
            delivery_evidence=evidence
        )
        self._add_domain_event(event)
    
    def report_incident(self, incident_type: str, description: str, 
                       reported_by: str = "", location: str = "") -> Incident:
        """Reporta un incidente"""
        if not self.guide:
            raise ValueError("Guide must exist to report incident")
        
        from src.domain.entities.incident import IncidentType
        
        incident = Incident(
            guide_id=self.guide.id,
            incident_type=IncidentType(incident_type),
            description=description,
            location=location,
            reported_by=reported_by
        )
        
        self.incidents.append(incident)
        
        if self.tracking:
            self.tracking.add_event(
                TrackingEventType.INCIDENT_REPORTED,
                f"Incidente reportado: {description}",
                location=location,
                operator=reported_by
            )
        
        event = IncidentReported(
            aggregate_id=self.order.id.value,
            aggregate_type="order",
            incident_id=str(incident.id),
            guide_id=str(self.guide.id.value),
            order_id=str(self.order.id.value),
            incident_type=incident_type,
            description=description,
            reported_by=reported_by,
            location=location
        )
        self._add_domain_event(event)
        
        return incident
    
    def add_delivery_attempt(self, status: str, notes: str = "", failure_reason: str = "") -> DeliveryAttempt:
        """Agrega un intento de entrega"""
        if not self.guide:
            raise ValueError("Guide must exist to add delivery attempt")
        
        from src.domain.entities.incident import IncidentType
        
        attempt = DeliveryAttempt(
            guide_id=self.guide.id,
            attempt_number=len(self.delivery_attempts) + 1,
            status=status,
            notes=notes
        )
        
        if failure_reason:
            attempt.mark_failed(IncidentType(failure_reason), notes)
        elif status == "successful":
            attempt.mark_successful(notes)
        
        self.delivery_attempts.append(attempt)
        return attempt
    
    def is_delivered(self) -> bool:
        """Verifica si el paquete fue entregado"""
        return self.guide and self.guide.status == GuideStatus.DELIVERED
    
    def has_active_incidents(self) -> bool:
        """Verifica si tiene incidentes activos"""
        from src.domain.entities.incident import IncidentStatus
        return any(inc.status in [IncidentStatus.REPORTED, IncidentStatus.IN_REVIEW, IncidentStatus.ESCALATED] 
                  for inc in self.incidents)
    
    def get_current_location(self) -> str:
        """Obtiene la ubicación actual del paquete"""
        if self.tracking:
            return self.tracking.current_location
        return ""
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Agrega un evento de dominio"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Obtiene los eventos de dominio"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Limpia los eventos de dominio"""
        self._domain_events.clear()