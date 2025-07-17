from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.domain.entities.guide import Guide
from src.domain.entities.tracking import TrackingInfo, TrackingEvent
from src.domain.entities.logistics_operator import LogisticsOperator, ServiceCapability
from src.domain.entities.incident import Incident
from src.domain.aggregates.shipping_aggregate import ShippingAggregate
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.money import Money


@dataclass
class ShippingQuote:
    operator_id: str
    operator_name: str
    service_type: str
    estimated_cost: Money
    estimated_delivery_days: int
    features: List[str]
    terms_and_conditions: str


@dataclass
class PickupRequest:
    guide_id: GuideId
    pickup_address: str
    pickup_contact: str
    pickup_phone: str
    preferred_time_start: datetime
    preferred_time_end: datetime
    special_instructions: Optional[str] = None


@dataclass
class DeliveryInstruction:
    delivery_address: str
    recipient_name: str
    recipient_phone: str
    delivery_notes: Optional[str] = None
    requires_signature: bool = True
    delivery_time_preference: Optional[str] = None  # "morning", "afternoon", "evening"


class ShippingService:
    def __init__(self):
        self.operators: List[LogisticsOperator] = []
        self.active_shipments: Dict[str, ShippingAggregate] = {}

    def add_logistics_operator(self, operator: LogisticsOperator) -> None:
        """Agregar operador logístico al servicio"""
        if operator.is_active:
            self.operators.append(operator)

    def get_shipping_quotes(
        self,
        origin: str,
        destination: str,
        package_weight: float,
        package_dimensions: Dict[str, float],
        service_type: str,
        declared_value: Money
    ) -> List[ShippingQuote]:
        """Obtener cotizaciones de envío de múltiples operadores"""
        quotes = []
        
        for operator in self.operators:
            if operator.can_handle_shipment(
                package_weight, package_dimensions, destination, service_type
            ):
                try:
                    # Calcular costo estimado
                    base_rate = operator.get_rate_for_service(service_type)
                    estimated_cost = self._calculate_shipping_cost(
                        base_rate, package_weight, package_dimensions, declared_value
                    )
                    
                    # Obtener días estimados de entrega
                    delivery_days = operator.get_estimated_delivery_days(service_type)
                    
                    # Obtener características del servicio
                    capability = next(
                        (c for c in operator.capabilities if c.service_type == service_type),
                        None
                    )
                    
                    quote = ShippingQuote(
                        operator_id=operator.operator_id.value,
                        operator_name=operator.business_name,
                        service_type=service_type,
                        estimated_cost=estimated_cost,
                        estimated_delivery_days=delivery_days,
                        features=self._get_service_features(capability),
                        terms_and_conditions=f"Servicio provisto por {operator.business_name}"
                    )
                    
                    quotes.append(quote)
                    
                except Exception as e:
                    # Log error pero continua con otros operadores
                    continue
        
        # Ordenar por costo (más barato primero)
        quotes.sort(key=lambda q: q.estimated_cost.amount)
        
        return quotes

    def create_shipment(
        self,
        guide: Guide,
        selected_operator_id: str,
        pickup_request: PickupRequest,
        delivery_instruction: DeliveryInstruction
    ) -> ShippingAggregate:
        """Crear nuevo envío con operador seleccionado"""
        # Buscar operador seleccionado
        operator = next(
            (op for op in self.operators if op.operator_id.value == selected_operator_id),
            None
        )
        
        if not operator:
            raise ValueError(f"Operador {selected_operator_id} no encontrado o no disponible")
        
        # Calcular fecha estimada de entrega
        service_capability = next(
            (c for c in operator.capabilities if c.service_type == guide.service_type),
            None
        )
        
        estimated_delivery = datetime.now() + timedelta(
            days=service_capability.estimated_delivery_days if service_capability else 5
        )
        
        # Crear agregado de envío
        shipping_aggregate = ShippingAggregate.create_shipment(
            guide=guide,
            origin_address=pickup_request.pickup_address,
            destination_address=delivery_instruction.delivery_address,
            estimated_delivery_date=estimated_delivery
        )
        
        # Asignar operador
        shipping_aggregate.assign_operator(operator)
        
        # Programar recolección
        shipping_aggregate.schedule_pickup(
            pickup_request.preferred_time_start,
            pickup_request.pickup_address
        )
        
        # Guardar en memoria (en implementación real sería en repositorio)
        self.active_shipments[guide.guide_id.value] = shipping_aggregate
        
        return shipping_aggregate

    def schedule_pickup(
        self,
        guide_id: GuideId,
        pickup_date: datetime,
        pickup_address: str,
        contact_info: Dict[str, str]
    ) -> bool:
        """Programar recolección de paquete"""
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        try:
            shipment.schedule_pickup(pickup_date, pickup_address)
            
            # Notificar al operador (integración externa)
            self._notify_operator_pickup_scheduled(shipment, pickup_date, contact_info)
            
            return True
            
        except Exception as e:
            return False

    def confirm_pickup(
        self,
        guide_id: GuideId,
        pickup_datetime: datetime,
        pickup_location: str,
        operator_notes: str = ""
    ) -> None:
        """Confirmar recolección de paquete"""
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        shipment.confirm_pickup(pickup_datetime, pickup_location)
        
        # Notificar al cliente sobre recolección exitosa
        self._notify_customer_pickup_confirmed(shipment, pickup_datetime)

    def update_shipment_location(
        self,
        guide_id: GuideId,
        current_location: str,
        update_description: str,
        update_timestamp: datetime = None
    ) -> None:
        """Actualizar ubicación del envío durante tránsito"""
        if update_timestamp is None:
            update_timestamp = datetime.now()
        
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        shipment.update_transit_status(current_location, update_description)

    def attempt_delivery(
        self,
        guide_id: GuideId,
        delivery_address: str,
        success: bool,
        recipient_name: str = "",
        delivery_notes: str = "",
        delivery_photo_url: str = ""
    ) -> bool:
        """Registrar intento de entrega"""
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        notes = delivery_notes
        if delivery_photo_url:
            notes += f" | Evidencia: {delivery_photo_url}"
        
        attempt = shipment.attempt_delivery(
            attempt_datetime=datetime.now(),
            delivery_address=delivery_address,
            success=success,
            notes=notes,
            recipient_name=recipient_name
        )
        
        if success:
            # Notificar entrega exitosa
            self._notify_delivery_completed(shipment, attempt)
        else:
            # Programar reintento si es posible
            if shipment.get_delivery_attempts_count() < 3:
                self._schedule_delivery_retry(shipment)
            else:
                # Iniciar proceso de devolución
                self._initiate_return_process(shipment)
        
        return success

    def report_incident(
        self,
        guide_id: GuideId,
        incident_type: str,
        description: str,
        severity: str,
        location: str,
        reported_by: str,
        evidence_urls: List[str] = None
    ) -> Incident:
        """Reportar incidente durante el envío"""
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        # Agregar URLs de evidencia a la descripción
        if evidence_urls:
            description += f" | Evidencias: {', '.join(evidence_urls)}"
        
        incident = shipment.report_incident(
            incident_type=incident_type,
            description=description,
            severity=severity,
            location=location,
            reported_by=reported_by
        )
        
        # Notificar según severidad
        if severity in ["high", "critical"]:
            self._notify_critical_incident(shipment, incident)
        
        return incident

    def resolve_incident(
        self,
        guide_id: GuideId,
        incident_id: str,
        resolution: str,
        resolved_by: str
    ) -> None:
        """Resolver incidente"""
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        shipment.resolve_incident(incident_id, resolution, resolved_by)
        
        # Notificar resolución
        self._notify_incident_resolved(shipment, incident_id, resolution)

    def cancel_shipment(
        self,
        guide_id: GuideId,
        cancellation_reason: str,
        cancelled_by: str
    ) -> None:
        """Cancelar envío"""
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        shipment.cancel_shipment(cancellation_reason, cancelled_by)
        
        # Notificar cancelación
        self._notify_shipment_cancelled(shipment, cancellation_reason)

    def get_shipment_tracking(self, guide_id: GuideId) -> TrackingInfo:
        """Obtener información de tracking"""
        shipment = self.active_shipments.get(guide_id.value)
        if not shipment:
            raise ValueError(f"Envío {guide_id.value} no encontrado")
        
        return shipment.tracking_info

    def get_operator_performance(self, operator_id: str, days: int = 30) -> Dict[str, Any]:
        """Obtener métricas de rendimiento de operador"""
        operator = next(
            (op for op in self.operators if op.operator_id.value == operator_id),
            None
        )
        
        if not operator:
            raise ValueError(f"Operador {operator_id} no encontrado")
        
        # Buscar envíos del operador en el período
        cutoff_date = datetime.now() - timedelta(days=days)
        operator_shipments = [
            shipment for shipment in self.active_shipments.values()
            if (shipment.assigned_operator and 
                shipment.assigned_operator.operator_id.value == operator_id and
                shipment.tracking_info.created_at >= cutoff_date)
        ]
        
        total_shipments = len(operator_shipments)
        delivered_shipments = len([
            s for s in operator_shipments 
            if s.get_current_status() == "delivered"
        ])
        
        on_time_deliveries = len([
            s for s in operator_shipments
            if (s.get_current_status() == "delivered" and 
                s.tracking_info.delivered_at and
                s.tracking_info.delivered_at <= s.tracking_info.estimated_delivery_date)
        ])
        
        incidents_count = sum(len(s.incidents) for s in operator_shipments)
        
        return {
            "operator_id": operator_id,
            "operator_name": operator.business_name,
            "period_days": days,
            "total_shipments": total_shipments,
            "delivered_shipments": delivered_shipments,
            "delivery_rate": delivered_shipments / total_shipments if total_shipments > 0 else 0,
            "on_time_deliveries": on_time_deliveries,
            "on_time_rate": on_time_deliveries / delivered_shipments if delivered_shipments > 0 else 0,
            "incidents_count": incidents_count,
            "incident_rate": incidents_count / total_shipments if total_shipments > 0 else 0,
            "average_delivery_time": self._calculate_average_delivery_time(operator_shipments)
        }

    def _calculate_shipping_cost(
        self,
        base_rate: Money,
        weight: float,
        dimensions: Dict[str, float],
        declared_value: Money
    ) -> Money:
        """Calcular costo de envío"""
        # Cálculo simplificado - en implementación real sería más complejo
        cost = base_rate.amount
        
        # Aplicar multiplicador por peso
        if weight > 1.0:  # kg
            cost *= (1 + (weight - 1) * 0.1)
        
        # Aplicar multiplicador por volumen
        volume = dimensions.get("length", 0) * dimensions.get("width", 0) * dimensions.get("height", 0)
        if volume > 1000:  # cm³
            cost *= (1 + (volume - 1000) / 10000 * 0.05)
        
        # Aplicar seguro si el valor declarado es alto
        if declared_value.amount > 100000:  # COP
            insurance_cost = declared_value.amount * 0.001  # 0.1%
            cost += insurance_cost
        
        return Money(cost, base_rate.currency)

    def _get_service_features(self, capability: Optional[ServiceCapability]) -> List[str]:
        """Obtener características del servicio"""
        if not capability:
            return ["Envío estándar"]
        
        features = []
        
        if capability.max_weight_kg >= 30:
            features.append("Paquetes pesados")
        
        if capability.estimated_delivery_days <= 1:
            features.append("Entrega express")
        elif capability.estimated_delivery_days <= 3:
            features.append("Entrega rápida")
        
        if "tracking" in capability.service_type.lower():
            features.append("Seguimiento en tiempo real")
        
        if "insurance" in capability.service_type.lower():
            features.append("Seguro incluido")
        
        return features if features else ["Envío estándar"]

    def _notify_operator_pickup_scheduled(
        self,
        shipment: ShippingAggregate,
        pickup_date: datetime,
        contact_info: Dict[str, str]
    ) -> None:
        """Notificar al operador sobre recolección programada"""
        # Implementar integración con API del operador
        pass

    def _notify_customer_pickup_confirmed(
        self,
        shipment: ShippingAggregate,
        pickup_datetime: datetime
    ) -> None:
        """Notificar al cliente sobre recolección confirmada"""
        # Implementar notificación al cliente
        pass

    def _notify_delivery_completed(
        self,
        shipment: ShippingAggregate,
        attempt
    ) -> None:
        """Notificar entrega completada"""
        # Implementar notificación de entrega
        pass

    def _notify_critical_incident(
        self,
        shipment: ShippingAggregate,
        incident: Incident
    ) -> None:
        """Notificar incidente crítico"""
        # Implementar notificación de emergencia
        pass

    def _notify_incident_resolved(
        self,
        shipment: ShippingAggregate,
        incident_id: str,
        resolution: str
    ) -> None:
        """Notificar resolución de incidente"""
        # Implementar notificación de resolución
        pass

    def _notify_shipment_cancelled(
        self,
        shipment: ShippingAggregate,
        reason: str
    ) -> None:
        """Notificar cancelación de envío"""
        # Implementar notificación de cancelación
        pass

    def _schedule_delivery_retry(self, shipment: ShippingAggregate) -> None:
        """Programar reintento de entrega"""
        # Implementar lógica de reprogramación
        pass

    def _initiate_return_process(self, shipment: ShippingAggregate) -> None:
        """Iniciar proceso de devolución"""
        shipment.return_to_origin("Máximo de intentos de entrega excedido")

    def _calculate_average_delivery_time(self, shipments: List[ShippingAggregate]) -> float:
        """Calcular tiempo promedio de entrega en días"""
        delivered_shipments = [
            s for s in shipments 
            if s.get_current_status() == "delivered" and s.tracking_info.delivered_at
        ]
        
        if not delivered_shipments:
            return 0.0
        
        total_time = 0.0
        for shipment in delivered_shipments:
            delivery_time = (shipment.tracking_info.delivered_at - shipment.tracking_info.created_at).total_seconds()
            total_time += delivery_time / (24 * 3600)  # Convertir a días
        
        return total_time / len(delivered_shipments)