"""Entidades de dominio para la gestión de recolecciones.

Este módulo contiene las entidades principales para manejar las solicitudes de recolección,
rutas de recolección, horarios disponibles y intentos de recolección.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timedelta

from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId


class PickupStatus(Enum):
    """Estados posibles de una solicitud de recolección.
    
    Attributes:
        SCHEDULED: Solicitud creada pero no confirmada
        CONFIRMED: Solicitud confirmada con fecha y hora
        IN_PROGRESS: Recolección en curso
        COMPLETED: Recolección completada exitosamente
        FAILED: Recolección falló después de todos los intentos
        CANCELLED: Solicitud cancelada
        RESCHEDULED: Solicitud reprogramada para nueva fecha
    """
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class PickupType(Enum):
    """Tipos de recolección disponibles.
    
    Attributes:
        POINT_DELIVERY: Cliente entrega el paquete en un punto logístico
        DIRECT_PICKUP: Recolección directa en la dirección del cliente
        SCHEDULED_PICKUP: Recolección programada con cita previa
    """
    POINT_DELIVERY = "point_delivery"  # Cliente entrega en punto logístico
    DIRECT_PICKUP = "direct_pickup"    # Recolección directa en dirección
    SCHEDULED_PICKUP = "scheduled_pickup"  # Recolección programada


@dataclass
class PickupTimeSlot:
    """Representa un horario disponible para recolecciones.
    
    Attributes:
        start_time: Hora de inicio del slot
        end_time: Hora de fin del slot
        is_available: Indica si el slot está disponible
        max_pickups: Número máximo de recolecciones por slot
        current_pickups: Número actual de recolecciones asignadas
    """
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    max_pickups: int = 10
    current_pickups: int = 0


@dataclass
class PickupAttempt:
    """Representa un intento de recolección.
    
    Attributes:
        attempt_id: Identificador único del intento
        attempted_at: Fecha y hora del intento
        status: Estado del intento (success, failed, partial)
        notes: Notas del operador sobre el intento
        attempted_by: ID del operador que realizó el intento
        failure_reason: Razón del fallo si el intento falló
        evidence_urls: URLs de evidencias (fotos, documentos)
    """
    attempt_id: str
    attempted_at: datetime
    status: str  # "success", "failed", "partial"
    notes: str
    attempted_by: str  # operator_id
    failure_reason: Optional[str] = None
    evidence_urls: List[str] = None


class PickupRequest:
    """Entidad principal para manejar solicitudes de recolección.
    
    Esta clase representa una solicitud de recolección de paquetes, incluyendo
    toda la información necesaria para coordinar la recolección, seguimiento
    del estado y gestión de intentos de recolección.
    
    Attributes:
        pickup_id: Identificador único de la solicitud
        guide_id: ID de la guía asociada
        customer_id: ID del cliente que solicita la recolección
        pickup_type: Tipo de recolección (directa, punto, programada)
        pickup_address: Dirección donde realizar la recolección
        contact_name: Nombre de la persona de contacto
        contact_phone: Teléfono de contacto
        status: Estado actual de la solicitud
        created_at: Fecha y hora de creación
        updated_at: Fecha y hora de última actualización
        scheduled_date: Fecha programada para la recolección
        time_slot: Horario asignado para la recolección
        assigned_operator_id: ID del operador asignado
        assigned_point_id: ID del punto logístico (si aplica)
        completed_at: Fecha y hora de completación
        priority: Prioridad de la recolección
        estimated_packages: Número estimado de paquetes
        total_weight_kg: Peso total estimado
        max_attempts: Máximo número de intentos permitidos
        pickup_attempts: Lista de intentos realizados
        special_instructions: Instrucciones especiales
    """
    
    def __init__(
        self,
        pickup_id: str,
        guide_id: GuideId,
        customer_id: CustomerId,
        pickup_type: PickupType,
        pickup_address: str,
        contact_name: str,
        contact_phone: str
    ):
        self.pickup_id = pickup_id
        self.guide_id = guide_id
        self.customer_id = customer_id
        self.pickup_type = pickup_type
        self.pickup_address = pickup_address
        self.contact_name = contact_name
        self.contact_phone = contact_phone
        self.status = PickupStatus.SCHEDULED
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.scheduled_date: Optional[datetime] = None
        self.time_slot: Optional[PickupTimeSlot] = None
        self.assigned_operator_id: Optional[str] = None
        self.assigned_point_id: Optional[str] = None
        self.special_instructions: Optional[str] = None
        self.pickup_attempts: List[PickupAttempt] = []
        self.completed_at: Optional[datetime] = None
        self.max_attempts = 3
        self.priority = "normal"  # "low", "normal", "high", "urgent"
        self.estimated_packages = 1
        self.total_weight_kg: Optional[float] = None
        self.requires_special_handling = False

    def schedule_pickup(
        self,
        scheduled_date: datetime,
        time_slot: PickupTimeSlot,
        assigned_operator_id: str
    ) -> None:
        """Programa una recolección asignando fecha, horario y operador.
        
        Valida que el slot esté disponible y tiene capacidad, luego asigna
        la recolección y reserva el espacio en el horario.
        
        Args:
            scheduled_date: Fecha programada para la recolección
            time_slot: Horario específico asignado
            assigned_operator_id: ID del operador asignado
            
        Raises:
            ValueError: Si la solicitud no está en estado válido para programar,
                       si el slot no está disponible o está lleno
        """
        if self.status not in [PickupStatus.SCHEDULED, PickupStatus.RESCHEDULED]:
            raise ValueError("Solo se pueden programar recolecciones pendientes o reprogramadas")
        
        if not time_slot.is_available:
            raise ValueError("Slot de tiempo no disponible")
        
        if time_slot.current_pickups >= time_slot.max_pickups:
            raise ValueError("Slot de tiempo completo")
        
        self.scheduled_date = scheduled_date
        self.time_slot = time_slot
        self.assigned_operator_id = assigned_operator_id
        self.status = PickupStatus.CONFIRMED
        self.updated_at = datetime.now()
        
        # Reservar slot
        time_slot.current_pickups += 1

    def assign_to_point(self, point_id: str) -> None:
        """Asigna la recolección a un punto logístico específico.
        
        Solo aplicable para recolecciones de tipo POINT_DELIVERY donde el cliente
        entrega el paquete en un punto logístico en lugar de recolección directa.
        
        Args:
            point_id: Identificador del punto logístico
            
        Raises:
            ValueError: Si el tipo de recolección no permite asignación a punto
        """
        if self.pickup_type != PickupType.POINT_DELIVERY:
            raise ValueError("Solo las entregas en punto pueden ser asignadas a un punto")
        
        self.assigned_point_id = point_id
        self.status = PickupStatus.CONFIRMED
        self.updated_at = datetime.now()

    def start_pickup(self, operator_id: str) -> None:
        """Inicia el proceso de recolección marcando el estado como en progreso.
        
        Solo el operador asignado puede iniciar la recolección y debe estar
        en estado CONFIRMED.
        
        Args:
            operator_id: ID del operador que inicia la recolección
            
        Raises:
            ValueError: Si la recolección no está confirmada o el operador no coincide
        """
        if self.status != PickupStatus.CONFIRMED:
            raise ValueError("Solo se pueden iniciar recolecciones confirmadas")
        
        if self.assigned_operator_id != operator_id:
            raise ValueError("Solo el operador asignado puede iniciar la recolección")
        
        self.status = PickupStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def complete_pickup(
        self,
        operator_id: str,
        completion_notes: str,
        evidence_urls: List[str] = None
    ) -> PickupAttempt:
        """Marca la recolección como completada exitosamente.
        
        Registra el intento exitoso y actualiza el estado a COMPLETED.
        
        Args:
            operator_id: ID del operador que completa la recolección
            completion_notes: Notas sobre la recolección completada
            evidence_urls: URLs de evidencias fotográficas (opcional)
            
        Returns:
            PickupAttempt: Registro del intento exitoso de recolección
            
        Raises:
            ValueError: Si la recolección no está en progreso
        """
        if self.status != PickupStatus.IN_PROGRESS:
            raise ValueError("Solo se pueden completar recolecciones en progreso")
        
        attempt = PickupAttempt(
            attempt_id=f"att_{len(self.pickup_attempts) + 1}",
            attempted_at=datetime.now(),
            status="success",
            notes=completion_notes,
            attempted_by=operator_id,
            evidence_urls=evidence_urls or []
        )
        
        self.pickup_attempts.append(attempt)
        self.status = PickupStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        
        return attempt

    def fail_pickup(
        self,
        operator_id: str,
        failure_reason: str,
        notes: str,
        evidence_urls: List[str] = None
    ) -> PickupAttempt:
        """Registrar fallo en recolección"""
        if self.status != PickupStatus.IN_PROGRESS:
            raise ValueError("Solo se pueden fallar recolecciones en progreso")
        
        attempt = PickupAttempt(
            attempt_id=f"att_{len(self.pickup_attempts) + 1}",
            attempted_at=datetime.now(),
            status="failed",
            notes=notes,
            attempted_by=operator_id,
            failure_reason=failure_reason,
            evidence_urls=evidence_urls or []
        )
        
        self.pickup_attempts.append(attempt)
        
        # Determinar siguiente acción
        if len(self.pickup_attempts) >= self.max_attempts:
            self.status = PickupStatus.FAILED
        else:
            self.status = PickupStatus.RESCHEDULED
        
        self.updated_at = datetime.now()
        return attempt

    def reschedule_pickup(
        self,
        new_scheduled_date: datetime,
        new_time_slot: PickupTimeSlot,
        reschedule_reason: str
    ) -> None:
        """Reprogramar recolección"""
        if self.status not in [PickupStatus.CONFIRMED, PickupStatus.RESCHEDULED, PickupStatus.FAILED]:
            raise ValueError("Solo se pueden reprogramar recolecciones confirmadas, reprogramadas o fallidas")
        
        if len(self.pickup_attempts) >= self.max_attempts:
            raise ValueError("Se ha alcanzado el máximo de intentos")
        
        # Liberar slot anterior
        if self.time_slot:
            self.time_slot.current_pickups -= 1
        
        self.scheduled_date = new_scheduled_date
        self.time_slot = new_time_slot
        self.status = PickupStatus.RESCHEDULED
        self.updated_at = datetime.now()
        
        # Reservar nuevo slot
        new_time_slot.current_pickups += 1

    def cancel_pickup(self, cancellation_reason: str, cancelled_by: str) -> None:
        """Cancelar recolección"""
        if self.status in [PickupStatus.COMPLETED, PickupStatus.CANCELLED]:
            raise ValueError("No se puede cancelar una recolección completada o ya cancelada")
        
        # Liberar slot si está reservado
        if self.time_slot:
            self.time_slot.current_pickups -= 1
        
        self.status = PickupStatus.CANCELLED
        self.updated_at = datetime.now()

    def set_priority(self, priority: str) -> None:
        """Establecer prioridad de recolección"""
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            raise ValueError(f"Prioridad debe ser una de: {valid_priorities}")
        
        self.priority = priority
        self.updated_at = datetime.now()

    def add_special_instructions(self, instructions: str) -> None:
        """Agregar instrucciones especiales"""
        self.special_instructions = instructions
        self.updated_at = datetime.now()

    def set_package_details(self, estimated_packages: int, total_weight_kg: float) -> None:
        """Establecer detalles de paquetes"""
        if estimated_packages <= 0:
            raise ValueError("Número de paquetes debe ser mayor a 0")
        
        if total_weight_kg <= 0:
            raise ValueError("Peso total debe ser mayor a 0")
        
        self.estimated_packages = estimated_packages
        self.total_weight_kg = total_weight_kg
        self.updated_at = datetime.now()

    def can_be_rescheduled(self) -> bool:
        """Verificar si se puede reprogramar"""
        return (len(self.pickup_attempts) < self.max_attempts and 
                self.status not in [PickupStatus.COMPLETED, PickupStatus.CANCELLED])

    def get_next_available_slot(self, date: datetime) -> Optional[datetime]:
        """Obtener siguiente slot disponible después de una fecha"""
        # Lógica simplificada - en implementación real consultaría disponibilidad
        return date + timedelta(hours=24)

    def is_overdue(self) -> bool:
        """Verificar si la recolección está vencida"""
        if not self.scheduled_date:
            return False
        
        # Considerar vencido si han pasado 2 horas del slot programado
        return datetime.now() > self.scheduled_date + timedelta(hours=2)

    def get_pickup_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la recolección"""
        return {
            "pickup_id": self.pickup_id,
            "guide_id": self.guide_id.value,
            "status": self.status.value,
            "pickup_type": self.pickup_type.value,
            "pickup_address": self.pickup_address,
            "contact_name": self.contact_name,
            "scheduled_date": self.scheduled_date,
            "assigned_operator_id": self.assigned_operator_id,
            "assigned_point_id": self.assigned_point_id,
            "attempts_count": len(self.pickup_attempts),
            "max_attempts": self.max_attempts,
            "priority": self.priority,
            "is_overdue": self.is_overdue(),
            "can_be_rescheduled": self.can_be_rescheduled(),
            "completed_at": self.completed_at,
            "special_instructions": self.special_instructions,
            "estimated_packages": self.estimated_packages,
            "total_weight_kg": self.total_weight_kg
        }

    def __str__(self) -> str:
        return f"PickupRequest({self.pickup_id}, {self.guide_id.value}, {self.status.value})"


class PickupRoute:
    def __init__(self, route_id: str, operator_id: str, scheduled_date: datetime):
        self.route_id = route_id
        self.operator_id = operator_id
        self.scheduled_date = scheduled_date
        self.pickup_requests: List[PickupRequest] = []
        self.status = "planned"  # "planned", "in_progress", "completed", "cancelled"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.total_distance_km: Optional[float] = None
        self.estimated_duration_hours: Optional[float] = None

    def add_pickup(self, pickup_request: PickupRequest) -> None:
        """Agregar recolección a la ruta"""
        if pickup_request.assigned_operator_id != self.operator_id:
            raise ValueError("La recolección debe estar asignada al mismo operador")
        
        if pickup_request.scheduled_date.date() != self.scheduled_date.date():
            raise ValueError("La recolección debe ser del mismo día")
        
        self.pickup_requests.append(pickup_request)

    def optimize_route(self) -> None:
        """Optimizar orden de recolecciones en la ruta"""
        # Ordenar por prioridad y luego por proximidad geográfica
        # En implementación real usaría algoritmo de optimización de rutas
        self.pickup_requests.sort(key=lambda p: (
            {"urgent": 0, "high": 1, "normal": 2, "low": 3}[p.priority],
            p.pickup_address  # Simplificado - en real usaría coordenadas
        ))

    def start_route(self) -> None:
        """Iniciar ruta de recolecciones"""
        if self.status != "planned":
            raise ValueError("Solo se pueden iniciar rutas planificadas")
        
        self.status = "in_progress"
        self.started_at = datetime.now()

    def complete_route(self) -> None:
        """Completar ruta de recolecciones"""
        if self.status != "in_progress":
            raise ValueError("Solo se pueden completar rutas en progreso")
        
        # Verificar que todas las recolecciones estén completadas o fallidas
        pending_pickups = [p for p in self.pickup_requests 
                          if p.status not in [PickupStatus.COMPLETED, PickupStatus.FAILED, PickupStatus.CANCELLED]]
        
        if pending_pickups:
            raise ValueError("Hay recolecciones pendientes en la ruta")
        
        self.status = "completed"
        self.completed_at = datetime.now()

    def get_route_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la ruta"""
        completed_pickups = len([p for p in self.pickup_requests if p.status == PickupStatus.COMPLETED])
        failed_pickups = len([p for p in self.pickup_requests if p.status == PickupStatus.FAILED])
        
        return {
            "route_id": self.route_id,
            "operator_id": self.operator_id,
            "scheduled_date": self.scheduled_date,
            "status": self.status,
            "total_pickups": len(self.pickup_requests),
            "completed_pickups": completed_pickups,
            "failed_pickups": failed_pickups,
            "success_rate": completed_pickups / len(self.pickup_requests) if self.pickup_requests else 0,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_distance_km": self.total_distance_km,
            "estimated_duration_hours": self.estimated_duration_hours
        }