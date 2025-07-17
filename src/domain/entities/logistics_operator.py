from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from datetime import datetime

from src.domain.value_objects.operator_id import OperatorId
from src.domain.value_objects.email import Email
from src.domain.value_objects.money import Money


class OperatorType(Enum):
    NATIONAL = "national"
    INTERNATIONAL = "international"
    SPECIALIZED = "specialized"


class OperatorStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"


@dataclass
class ServiceCapability:
    service_type: str
    max_weight_kg: float
    max_dimensions_cm: dict  # {"length": float, "width": float, "height": float}
    coverage_areas: List[str]
    estimated_delivery_days: int


@dataclass
class OperatorRating:
    on_time_delivery_rate: float
    customer_satisfaction: float
    damage_rate: float
    total_shipments: int
    last_updated: datetime


class LogisticsOperator:
    def __init__(
        self,
        operator_id: OperatorId,
        business_name: str,
        email: Email,
        operator_type: OperatorType,
        tax_id: str,
        contact_phone: str,
        contact_person: str
    ):
        self.operator_id = operator_id
        self.business_name = business_name
        self.email = email
        self.operator_type = operator_type
        self.tax_id = tax_id
        self.contact_phone = contact_phone
        self.contact_person = contact_person
        self.status = OperatorStatus.UNDER_REVIEW
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.is_active = False
        self.capabilities: List[ServiceCapability] = []
        self.base_rates: dict = {}  # {"service_type": Money}
        self.rating: Optional[OperatorRating] = None
        self.contract_start_date: Optional[datetime] = None
        self.contract_end_date: Optional[datetime] = None
        self.api_credentials: Optional[dict] = None

    def activate(self) -> None:
        """Activar operador después de aprobación"""
        if self.status != OperatorStatus.UNDER_REVIEW:
            raise ValueError("Solo se pueden activar operadores en revisión")
        
        self.status = OperatorStatus.ACTIVE
        self.is_active = True
        self.updated_at = datetime.now()

    def suspend(self, reason: str) -> None:
        """Suspender operador por incumplimiento"""
        if not self.is_active:
            raise ValueError("Solo se pueden suspender operadores activos")
        
        self.status = OperatorStatus.SUSPENDED
        self.is_active = False
        self.updated_at = datetime.now()

    def add_service_capability(self, capability: ServiceCapability) -> None:
        """Agregar capacidad de servicio"""
        # Verificar que no existe ya un servicio del mismo tipo
        existing = next((c for c in self.capabilities if c.service_type == capability.service_type), None)
        if existing:
            raise ValueError(f"Ya existe capacidad para servicio {capability.service_type}")
        
        self.capabilities.append(capability)
        self.updated_at = datetime.now()

    def set_base_rate(self, service_type: str, rate: Money) -> None:
        """Establecer tarifa base para un tipo de servicio"""
        if not any(c.service_type == service_type for c in self.capabilities):
            raise ValueError(f"No existe capacidad para servicio {service_type}")
        
        self.base_rates[service_type] = rate
        self.updated_at = datetime.now()

    def update_rating(self, rating: OperatorRating) -> None:
        """Actualizar calificación del operador"""
        self.rating = rating
        self.updated_at = datetime.now()

    def can_handle_shipment(self, weight_kg: float, dimensions_cm: dict, destination: str, service_type: str) -> bool:
        """Verificar si el operador puede manejar un envío"""
        if not self.is_active:
            return False
        
        capability = next((c for c in self.capabilities if c.service_type == service_type), None)
        if not capability:
            return False
        
        # Verificar peso
        if weight_kg > capability.max_weight_kg:
            return False
        
        # Verificar dimensiones
        if (dimensions_cm.get("length", 0) > capability.max_dimensions_cm.get("length", 0) or
            dimensions_cm.get("width", 0) > capability.max_dimensions_cm.get("width", 0) or
            dimensions_cm.get("height", 0) > capability.max_dimensions_cm.get("height", 0)):
            return False
        
        # Verificar cobertura
        if destination not in capability.coverage_areas:
            return False
        
        return True

    def get_rate_for_service(self, service_type: str) -> Money:
        """Obtener tarifa para un tipo de servicio"""
        if service_type not in self.base_rates:
            raise ValueError(f"No hay tarifa configurada para servicio {service_type}")
        
        return self.base_rates[service_type]

    def get_estimated_delivery_days(self, service_type: str) -> int:
        """Obtener días estimados de entrega para un servicio"""
        capability = next((c for c in self.capabilities if c.service_type == service_type), None)
        if not capability:
            raise ValueError(f"No existe capacidad para servicio {service_type}")
        
        return capability.estimated_delivery_days

    def has_good_rating(self, min_on_time_rate: float = 0.85, min_satisfaction: float = 4.0) -> bool:
        """Verificar si el operador tiene buena calificación"""
        if not self.rating:
            return False
        
        return (self.rating.on_time_delivery_rate >= min_on_time_rate and 
                self.rating.customer_satisfaction >= min_satisfaction)

    def set_api_credentials(self, credentials: dict) -> None:
        """Configurar credenciales de API para integración"""
        self.api_credentials = credentials
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        return f"LogisticsOperator({self.business_name}, {self.operator_type.value}, {self.status.value})"