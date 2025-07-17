from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.domain.entities.pickup import PickupRequest, PickupRoute, PickupTimeSlot, PickupType, PickupStatus
from src.domain.entities.franchise import LogisticPoint
from src.domain.entities.customer import Customer, CustomerType
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.events.pickup_events import (
    PickupRequested, PickupScheduled, PickupCompleted, 
    PickupFailed, PickupRescheduled, RouteOptimized
)


@dataclass
class PickupCapacity:
    operator_id: str
    date: datetime
    max_pickups_per_day: int
    current_pickups: int
    available_time_slots: List[PickupTimeSlot]


@dataclass
class NearbyLogisticPoint:
    point_id: str
    name: str
    address: str
    distance_km: float
    operating_hours: Dict[str, str]
    current_capacity: int
    max_capacity: int
    estimated_wait_time_minutes: int


class PickupService:
    def __init__(self):
        self.pickup_requests: Dict[str, PickupRequest] = {}
        self.pickup_routes: Dict[str, PickupRoute] = {}
        self.logistic_points: Dict[str, LogisticPoint] = {}
        self.operator_capacities: Dict[str, PickupCapacity] = {}
        self._domain_events: List = []

    def request_pickup(
        self,
        pickup_id: str,
        guide_id: GuideId,
        customer: Customer,
        pickup_address: str,
        contact_name: str,
        contact_phone: str,
        preferred_date: Optional[datetime] = None,
        special_instructions: Optional[str] = None
    ) -> PickupRequest:
        """Solicitar recolección basada en tipo de cliente"""
        
        # Determinar tipo de recolección según cliente
        pickup_type = self._determine_pickup_type(customer)
        
        pickup_request = PickupRequest(
            pickup_id=pickup_id,
            guide_id=guide_id,
            customer_id=customer.customer_id,
            pickup_type=pickup_type,
            pickup_address=pickup_address,
            contact_name=contact_name,
            contact_phone=contact_phone
        )
        
        if special_instructions:
            pickup_request.add_special_instructions(special_instructions)
        
        # Configurar prioridad según tipo de cliente
        priority = self._calculate_pickup_priority(customer, preferred_date)
        pickup_request.set_priority(priority)
        
        self.pickup_requests[pickup_id] = pickup_request
        
        self._add_domain_event(
            PickupRequested(
                pickup_id=pickup_id,
                guide_id=guide_id.value,
                customer_id=customer.customer_id.value,
                pickup_type=pickup_type.value,
                pickup_address=pickup_address,
                preferred_date=preferred_date,
                priority=priority
            )
        )
        
        return pickup_request

    def find_nearby_logistic_points(
        self,
        customer_address: str,
        max_distance_km: float = 5.0
    ) -> List[NearbyLogisticPoint]:
        """Buscar puntos logísticos cercanos para clientes pequeños"""
        nearby_points = []
        
        for point in self.logistic_points.values():
            if not point.is_active:
                continue
            
            # Calcular distancia (simplificado - en real usaría geolocalización)
            distance = self._calculate_distance(customer_address, point.address)
            
            if distance <= max_distance_km:
                nearby_point = NearbyLogisticPoint(
                    point_id=point.point_id,
                    name=point.name,
                    address=point.address,
                    distance_km=distance,
                    operating_hours=point.operating_hours,
                    current_capacity=point.get_current_packages(),
                    max_capacity=point.capacity,
                    estimated_wait_time_minutes=self._estimate_wait_time(point)
                )
                nearby_points.append(nearby_point)
        
        # Ordenar por distancia
        nearby_points.sort(key=lambda p: p.distance_km)
        
        return nearby_points

    def schedule_direct_pickup(
        self,
        pickup_id: str,
        preferred_date: datetime,
        time_preference: str = "any"  # "morning", "afternoon", "any"
    ) -> bool:
        """Programar recolección directa para clientes medianos/grandes"""
        pickup_request = self.pickup_requests.get(pickup_id)
        if not pickup_request:
            raise ValueError(f"Solicitud de recolección {pickup_id} no encontrada")
        
        if pickup_request.pickup_type != PickupType.DIRECT_PICKUP:
            raise ValueError("Solo recolecciones directas pueden ser programadas")
        
        # Buscar operador disponible
        available_operator = self._find_available_operator(preferred_date, time_preference)
        if not available_operator:
            return False
        
        # Buscar slot de tiempo disponible
        time_slot = self._find_available_time_slot(
            available_operator["operator_id"], 
            preferred_date, 
            time_preference
        )
        
        if not time_slot:
            return False
        
        # Programar recolección
        pickup_request.schedule_pickup(
            scheduled_date=preferred_date,
            time_slot=time_slot,
            assigned_operator_id=available_operator["operator_id"]
        )
        
        self._add_domain_event(
            PickupScheduled(
                pickup_id=pickup_id,
                scheduled_date=preferred_date,
                assigned_operator_id=available_operator["operator_id"],
                time_slot_start=time_slot.start_time,
                time_slot_end=time_slot.end_time
            )
        )
        
        return True

    def assign_to_logistic_point(
        self,
        pickup_id: str,
        point_id: str
    ) -> bool:
        """Asignar recolección a punto logístico"""
        pickup_request = self.pickup_requests.get(pickup_id)
        if not pickup_request:
            raise ValueError(f"Solicitud de recolección {pickup_id} no encontrada")
        
        if pickup_request.pickup_type != PickupType.POINT_DELIVERY:
            raise ValueError("Solo entregas en punto pueden ser asignadas")
        
        logistic_point = self.logistic_points.get(point_id)
        if not logistic_point:
            raise ValueError(f"Punto logístico {point_id} no encontrado")
        
        if not logistic_point.is_active:
            raise ValueError("Punto logístico no está activo")
        
        if logistic_point.is_at_capacity():
            return False
        
        pickup_request.assign_to_point(point_id)
        
        return True

    def complete_pickup(
        self,
        pickup_id: str,
        operator_id: str,
        completion_notes: str,
        packages_collected: int,
        evidence_urls: List[str] = None
    ) -> bool:
        """Completar recolección"""
        pickup_request = self.pickup_requests.get(pickup_id)
        if not pickup_request:
            raise ValueError(f"Solicitud de recolección {pickup_id} no encontrada")
        
        attempt = pickup_request.complete_pickup(
            operator_id=operator_id,
            completion_notes=completion_notes,
            evidence_urls=evidence_urls or []
        )
        
        self._add_domain_event(
            PickupCompleted(
                pickup_id=pickup_id,
                guide_id=pickup_request.guide_id.value,
                operator_id=operator_id,
                completed_at=attempt.attempted_at,
                packages_collected=packages_collected,
                completion_notes=completion_notes
            )
        )
        
        return True

    def fail_pickup(
        self,
        pickup_id: str,
        operator_id: str,
        failure_reason: str,
        failure_notes: str,
        evidence_urls: List[str] = None
    ) -> bool:
        """Registrar fallo en recolección"""
        pickup_request = self.pickup_requests.get(pickup_id)
        if not pickup_request:
            raise ValueError(f"Solicitud de recolección {pickup_id} no encontrada")
        
        attempt = pickup_request.fail_pickup(
            operator_id=operator_id,
            failure_reason=failure_reason,
            notes=failure_notes,
            evidence_urls=evidence_urls or []
        )
        
        # Determinar si se debe reprogramar automáticamente
        auto_reschedule = self._should_auto_reschedule(pickup_request, failure_reason)
        
        self._add_domain_event(
            PickupFailed(
                pickup_id=pickup_id,
                guide_id=pickup_request.guide_id.value,
                operator_id=operator_id,
                failure_reason=failure_reason,
                attempt_number=len(pickup_request.pickup_attempts),
                auto_reschedule=auto_reschedule
            )
        )
        
        if auto_reschedule:
            self._auto_reschedule_pickup(pickup_request)
        
        return True

    def reschedule_pickup(
        self,
        pickup_id: str,
        new_date: datetime,
        reschedule_reason: str,
        time_preference: str = "any"
    ) -> bool:
        """Reprogramar recolección"""
        pickup_request = self.pickup_requests.get(pickup_id)
        if not pickup_request:
            raise ValueError(f"Solicitud de recolección {pickup_id} no encontrada")
        
        if not pickup_request.can_be_rescheduled():
            return False
        
        # Buscar nuevo slot disponible
        available_operator = self._find_available_operator(new_date, time_preference)
        if not available_operator:
            return False
        
        time_slot = self._find_available_time_slot(
            available_operator["operator_id"], 
            new_date, 
            time_preference
        )
        
        if not time_slot:
            return False
        
        pickup_request.reschedule_pickup(new_date, time_slot, reschedule_reason)
        pickup_request.assigned_operator_id = available_operator["operator_id"]
        
        self._add_domain_event(
            PickupRescheduled(
                pickup_id=pickup_id,
                old_date=pickup_request.scheduled_date,
                new_date=new_date,
                reschedule_reason=reschedule_reason,
                new_operator_id=available_operator["operator_id"]
            )
        )
        
        return True

    def create_pickup_route(
        self,
        route_id: str,
        operator_id: str,
        date: datetime,
        pickup_ids: List[str]
    ) -> PickupRoute:
        """Crear ruta de recolecciones para un operador"""
        pickup_route = PickupRoute(route_id, operator_id, date)
        
        # Agregar recolecciones a la ruta
        for pickup_id in pickup_ids:
            pickup_request = self.pickup_requests.get(pickup_id)
            if pickup_request:
                pickup_route.add_pickup(pickup_request)
        
        # Optimizar ruta
        pickup_route.optimize_route()
        
        self.pickup_routes[route_id] = pickup_route
        
        self._add_domain_event(
            RouteOptimized(
                route_id=route_id,
                operator_id=operator_id,
                pickup_count=len(pickup_ids),
                scheduled_date=date,
                estimated_duration_hours=pickup_route.estimated_duration_hours
            )
        )
        
        return pickup_route

    def get_pickup_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        operator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtener métricas de recolecciones"""
        # Filtrar recolecciones por período
        period_pickups = [
            pickup for pickup in self.pickup_requests.values()
            if start_date <= pickup.created_at <= end_date
        ]
        
        if operator_id:
            period_pickups = [
                pickup for pickup in period_pickups
                if pickup.assigned_operator_id == operator_id
            ]
        
        total_pickups = len(period_pickups)
        completed_pickups = len([p for p in period_pickups if p.status == PickupStatus.COMPLETED])
        failed_pickups = len([p for p in period_pickups if p.status == PickupStatus.FAILED])
        
        # Calcular tiempo promedio de recolección
        completed_with_times = [
            p for p in period_pickups 
            if p.status == PickupStatus.COMPLETED and p.scheduled_date and p.completed_at
        ]
        
        avg_pickup_time = 0
        if completed_with_times:
            total_time = sum(
                (p.completed_at - p.scheduled_date).total_seconds() / 3600 
                for p in completed_with_times
            )
            avg_pickup_time = total_time / len(completed_with_times)
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_pickups": total_pickups,
            "completed_pickups": completed_pickups,
            "failed_pickups": failed_pickups,
            "success_rate": completed_pickups / total_pickups if total_pickups > 0 else 0,
            "failure_rate": failed_pickups / total_pickups if total_pickups > 0 else 0,
            "avg_pickup_time_hours": avg_pickup_time,
            "rescheduled_pickups": len([p for p in period_pickups if p.status == PickupStatus.RESCHEDULED]),
            "operator_id": operator_id
        }

    def get_daily_pickup_schedule(
        self,
        date: datetime,
        operator_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtener cronograma de recolecciones del día"""
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        scheduled_pickups = [
            pickup for pickup in self.pickup_requests.values()
            if (pickup.scheduled_date and 
                day_start <= pickup.scheduled_date < day_end and
                pickup.status in [PickupStatus.CONFIRMED, PickupStatus.IN_PROGRESS])
        ]
        
        if operator_id:
            scheduled_pickups = [
                pickup for pickup in scheduled_pickups
                if pickup.assigned_operator_id == operator_id
            ]
        
        # Ordenar por hora programada
        scheduled_pickups.sort(key=lambda p: p.scheduled_date)
        
        return [pickup.get_pickup_summary() for pickup in scheduled_pickups]

    def _determine_pickup_type(self, customer: Customer) -> PickupType:
        """Determinar tipo de recolección según cliente"""
        if customer.customer_type == CustomerType.SMALL:
            return PickupType.POINT_DELIVERY
        else:
            return PickupType.DIRECT_PICKUP

    def _calculate_pickup_priority(
        self,
        customer: Customer,
        preferred_date: Optional[datetime]
    ) -> str:
        """Calcular prioridad de recolección"""
        if customer.customer_type == CustomerType.LARGE:
            return "high"
        elif customer.customer_type == CustomerType.MEDIUM:
            return "normal"
        
        # Para clientes pequeños, prioridad basada en urgencia
        if preferred_date and preferred_date <= datetime.now() + timedelta(hours=4):
            return "high"
        
        return "normal"

    def _find_available_operator(
        self,
        date: datetime,
        time_preference: str
    ) -> Optional[Dict[str, Any]]:
        """Buscar operador disponible para fecha y preferencia"""
        for operator_id, capacity in self.operator_capacities.items():
            if (capacity.date.date() == date.date() and 
                capacity.current_pickups < capacity.max_pickups_per_day):
                return {"operator_id": operator_id, "capacity": capacity}
        
        return None

    def _find_available_time_slot(
        self,
        operator_id: str,
        date: datetime,
        time_preference: str
    ) -> Optional[PickupTimeSlot]:
        """Buscar slot de tiempo disponible"""
        capacity = self.operator_capacities.get(operator_id)
        if not capacity:
            return None
        
        for slot in capacity.available_time_slots:
            if slot.is_available and slot.current_pickups < slot.max_pickups:
                # Filtrar por preferencia de tiempo
                if time_preference == "morning" and slot.start_time.hour < 12:
                    return slot
                elif time_preference == "afternoon" and 12 <= slot.start_time.hour < 18:
                    return slot
                elif time_preference == "any":
                    return slot
        
        return None

    def _calculate_distance(self, address1: str, address2: str) -> float:
        """Calcular distancia entre direcciones (simplificado)"""
        # En implementación real usaría API de geolocalización
        return 2.5  # km promedio

    def _estimate_wait_time(self, point: LogisticPoint) -> int:
        """Estimar tiempo de espera en punto logístico"""
        utilization = point.get_current_packages() / point.capacity
        base_time = 5  # minutos base
        return int(base_time * (1 + utilization))

    def _should_auto_reschedule(self, pickup_request: PickupRequest, failure_reason: str) -> bool:
        """Determinar si se debe reprogramar automáticamente"""
        auto_reschedule_reasons = [
            "customer_not_available",
            "address_not_found",
            "traffic_delay"
        ]
        return (failure_reason in auto_reschedule_reasons and 
                pickup_request.can_be_rescheduled())

    def _auto_reschedule_pickup(self, pickup_request: PickupRequest) -> None:
        """Reprogramar automáticamente una recolección"""
        # Buscar siguiente día disponible
        next_date = datetime.now() + timedelta(days=1)
        self.reschedule_pickup(
            pickup_request.pickup_id,
            next_date,
            "Reprogramación automática por fallo",
            "any"
        )

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()