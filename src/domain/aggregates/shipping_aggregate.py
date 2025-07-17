from typing import List, Optional
from datetime import datetime

from src.domain.entities.guide import Guide
from src.domain.entities.tracking import TrackingEvent, TrackingInfo
from src.domain.entities.incident import Incident, DeliveryAttempt
from src.domain.entities.logistics_operator import LogisticsOperator
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.operator_id import OperatorId
from src.domain.events.shipping_events import (
    ShipmentPickedUp, ShipmentInTransit, ShipmentDelivered, 
    ShipmentFailed, IncidentReported, DeliveryRescheduled
)


class ShippingAggregate:
    def __init__(self, guide: Guide, tracking_info: TrackingInfo):
        self.guide = guide
        self.tracking_info = tracking_info
        self.incidents: List[Incident] = []
        self.delivery_attempts: List[DeliveryAttempt] = []
        self.assigned_operator: Optional[LogisticsOperator] = None
        self._domain_events: List = []

    @classmethod
    def create_shipment(
        cls,
        guide: Guide,
        origin_address: str,
        destination_address: str,
        estimated_delivery_date: datetime
    ) -> "ShippingAggregate":
        """Crear nuevo envío"""
        tracking_info = TrackingInfo(
            guide_id=guide.guide_id,
            current_status="created",
            origin_address=origin_address,
            destination_address=destination_address,
            estimated_delivery_date=estimated_delivery_date
        )
        
        aggregate = cls(guide, tracking_info)
        aggregate._add_domain_event(
            ShipmentCreated(
                guide_id=guide.guide_id.value,
                order_id=guide.order_id.value,
                origin=origin_address,
                destination=destination_address,
                estimated_delivery=estimated_delivery_date
            )
        )
        
        return aggregate

    def assign_operator(self, operator: LogisticsOperator) -> None:
        """Asignar operador logístico al envío"""
        if not operator.is_active:
            raise ValueError("No se puede asignar un operador inactivo")
        
        self.assigned_operator = operator
        self.tracking_info.add_event(TrackingEvent(
            event_type="operator_assigned",
            description=f"Asignado a operador {operator.business_name}",
            location="warehouse",
            timestamp=datetime.now()
        ))
        
        self._add_domain_event(
            OperatorAssigned(
                guide_id=self.guide.guide_id.value,
                operator_id=operator.operator_id.value,
                operator_name=operator.business_name
            )
        )

    def schedule_pickup(self, pickup_date: datetime, pickup_address: str) -> None:
        """Programar recolección"""
        if not self.assigned_operator:
            raise ValueError("Debe asignar un operador antes de programar recolección")
        
        self.tracking_info.add_event(TrackingEvent(
            event_type="pickup_scheduled",
            description=f"Recolección programada para {pickup_date}",
            location=pickup_address,
            timestamp=datetime.now()
        ))
        
        self._add_domain_event(
            PickupScheduled(
                guide_id=self.guide.guide_id.value,
                pickup_date=pickup_date,
                pickup_address=pickup_address,
                operator_id=self.assigned_operator.operator_id.value
            )
        )

    def confirm_pickup(self, pickup_datetime: datetime, pickup_location: str) -> None:
        """Confirmar recolección del paquete"""
        self.tracking_info.add_event(TrackingEvent(
            event_type="picked_up",
            description="Paquete recolectado",
            location=pickup_location,
            timestamp=pickup_datetime
        ))
        
        self.tracking_info.current_status = "in_transit"
        
        self._add_domain_event(
            ShipmentPickedUp(
                guide_id=self.guide.guide_id.value,
                pickup_datetime=pickup_datetime,
                pickup_location=pickup_location,
                operator_id=self.assigned_operator.operator_id.value if self.assigned_operator else ""
            )
        )

    def update_transit_status(self, location: str, description: str) -> None:
        """Actualizar estado durante tránsito"""
        self.tracking_info.add_event(TrackingEvent(
            event_type="in_transit",
            description=description,
            location=location,
            timestamp=datetime.now()
        ))
        
        self._add_domain_event(
            ShipmentInTransit(
                guide_id=self.guide.guide_id.value,
                current_location=location,
                description=description,
                timestamp=datetime.now()
            )
        )

    def attempt_delivery(
        self,
        attempt_datetime: datetime,
        delivery_address: str,
        success: bool,
        notes: str = "",
        recipient_name: str = ""
    ) -> DeliveryAttempt:
        """Registrar intento de entrega"""
        attempt = DeliveryAttempt(
            attempt_id=f"att_{len(self.delivery_attempts) + 1}",
            guide_id=self.guide.guide_id,
            attempted_at=attempt_datetime,
            delivery_address=delivery_address,
            was_successful=success,
            notes=notes,
            recipient_name=recipient_name
        )
        
        self.delivery_attempts.append(attempt)
        
        if success:
            self.tracking_info.add_event(TrackingEvent(
                event_type="delivered",
                description=f"Entregado a {recipient_name}",
                location=delivery_address,
                timestamp=attempt_datetime
            ))
            
            self.tracking_info.current_status = "delivered"
            self.tracking_info.delivered_at = attempt_datetime
            
            self._add_domain_event(
                ShipmentDelivered(
                    guide_id=self.guide.guide_id.value,
                    delivery_datetime=attempt_datetime,
                    delivery_address=delivery_address,
                    recipient_name=recipient_name,
                    delivery_attempt=len(self.delivery_attempts)
                )
            )
        else:
            self.tracking_info.add_event(TrackingEvent(
                event_type="delivery_failed",
                description=f"Intento de entrega fallido: {notes}",
                location=delivery_address,
                timestamp=attempt_datetime
            ))
            
            # Si es el último intento permitido, marcar como fallido
            if len(self.delivery_attempts) >= 3:  # máximo 3 intentos
                self.tracking_info.current_status = "failed"
                
                self._add_domain_event(
                    ShipmentFailed(
                        guide_id=self.guide.guide_id.value,
                        failure_reason="Máximo de intentos de entrega excedido",
                        final_attempt_date=attempt_datetime,
                        total_attempts=len(self.delivery_attempts)
                    )
                )
            else:
                # Programar reintento
                self._add_domain_event(
                    DeliveryRescheduled(
                        guide_id=self.guide.guide_id.value,
                        attempt_number=len(self.delivery_attempts),
                        reschedule_reason=notes,
                        next_attempt_date=None  # Se calculará en el servicio
                    )
                )
        
        return attempt

    def report_incident(
        self,
        incident_type: str,
        description: str,
        severity: str,
        location: str,
        reported_by: str
    ) -> Incident:
        """Reportar incidente durante el envío"""
        incident = Incident(
            incident_id=f"inc_{datetime.now().timestamp()}",
            guide_id=self.guide.guide_id,
            incident_type=incident_type,
            description=description,
            severity=severity,
            location=location,
            reported_by=reported_by,
            reported_at=datetime.now()
        )
        
        self.incidents.append(incident)
        
        self.tracking_info.add_event(TrackingEvent(
            event_type="incident",
            description=f"Incidente reportado: {description}",
            location=location,
            timestamp=datetime.now()
        ))
        
        # Si es un incidente crítico, marcar envío como problemático
        if severity in ["high", "critical"]:
            self.tracking_info.current_status = "incident"
        
        self._add_domain_event(
            IncidentReported(
                guide_id=self.guide.guide_id.value,
                incident_id=incident.incident_id,
                incident_type=incident_type,
                description=description,
                severity=severity,
                location=location,
                reported_by=reported_by
            )
        )
        
        return incident

    def resolve_incident(self, incident_id: str, resolution: str, resolved_by: str) -> None:
        """Resolver incidente"""
        incident = next((i for i in self.incidents if i.incident_id == incident_id), None)
        if not incident:
            raise ValueError(f"Incidente {incident_id} no encontrado")
        
        incident.resolve(resolution, resolved_by)
        
        # Si todos los incidentes están resueltos, reanudar envío normal
        if all(i.is_resolved for i in self.incidents):
            if self.tracking_info.current_status == "incident":
                self.tracking_info.current_status = "in_transit"
        
        self.tracking_info.add_event(TrackingEvent(
            event_type="incident_resolved",
            description=f"Incidente resuelto: {resolution}",
            location=incident.location,
            timestamp=datetime.now()
        ))

    def cancel_shipment(self, reason: str, cancelled_by: str) -> None:
        """Cancelar envío"""
        if self.tracking_info.current_status in ["delivered", "cancelled"]:
            raise ValueError("No se puede cancelar un envío entregado o ya cancelado")
        
        self.tracking_info.current_status = "cancelled"
        self.tracking_info.add_event(TrackingEvent(
            event_type="cancelled",
            description=f"Envío cancelado: {reason}",
            location="",
            timestamp=datetime.now()
        ))
        
        self._add_domain_event(
            ShipmentCancelled(
                guide_id=self.guide.guide_id.value,
                cancellation_reason=reason,
                cancelled_by=cancelled_by,
                cancelled_at=datetime.now()
            )
        )

    def return_to_origin(self, reason: str) -> None:
        """Devolver paquete al origen"""
        if len(self.delivery_attempts) == 0:
            raise ValueError("No se puede devolver sin intentos de entrega")
        
        self.tracking_info.current_status = "returning"
        self.tracking_info.add_event(TrackingEvent(
            event_type="returning_to_origin",
            description=f"Devolviendo al origen: {reason}",
            location="",
            timestamp=datetime.now()
        ))
        
        self._add_domain_event(
            ShipmentReturning(
                guide_id=self.guide.guide_id.value,
                return_reason=reason,
                delivery_attempts=len(self.delivery_attempts),
                return_initiated_at=datetime.now()
            )
        )

    def get_current_status(self) -> str:
        """Obtener estado actual del envío"""
        return self.tracking_info.current_status

    def get_delivery_attempts_count(self) -> int:
        """Obtener número de intentos de entrega"""
        return len(self.delivery_attempts)

    def has_active_incidents(self) -> bool:
        """Verificar si hay incidentes activos"""
        return any(not i.is_resolved for i in self.incidents)

    def get_tracking_events(self) -> List[TrackingEvent]:
        """Obtener todos los eventos de tracking"""
        return self.tracking_info.events

    def estimate_delivery_date(self) -> Optional[datetime]:
        """Obtener fecha estimada de entrega"""
        return self.tracking_info.estimated_delivery_date

    def update_estimated_delivery(self, new_estimate: datetime) -> None:
        """Actualizar fecha estimada de entrega"""
        old_estimate = self.tracking_info.estimated_delivery_date
        self.tracking_info.estimated_delivery_date = new_estimate
        
        if old_estimate != new_estimate:
            self.tracking_info.add_event(TrackingEvent(
                event_type="delivery_estimate_updated",
                description=f"Fecha estimada actualizada a {new_estimate}",
                location="",
                timestamp=datetime.now()
            ))

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()


# Eventos de dominio adicionales para el agregado de envío
from dataclasses import dataclass

@dataclass
class ShipmentCreated:
    guide_id: str
    order_id: str
    origin: str
    destination: str
    estimated_delivery: datetime

@dataclass
class OperatorAssigned:
    guide_id: str
    operator_id: str
    operator_name: str

@dataclass
class PickupScheduled:
    guide_id: str
    pickup_date: datetime
    pickup_address: str
    operator_id: str

@dataclass
class ShipmentCancelled:
    guide_id: str
    cancellation_reason: str
    cancelled_by: str
    cancelled_at: datetime

@dataclass
class ShipmentReturning:
    guide_id: str
    return_reason: str
    delivery_attempts: int
    return_initiated_at: datetime