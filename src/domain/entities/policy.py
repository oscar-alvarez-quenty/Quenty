from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from src.domain.value_objects.money import Money


class PolicyType(Enum):
    COMMERCIAL = "commercial"
    PRICING = "pricing"
    OPERATIONAL = "operational"
    SECURITY = "security"


class PolicyScope(Enum):
    GLOBAL = "global"
    COUNTRY = "country" 
    ZONE = "zone"
    CUSTOMER = "customer"


class PolicyStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


@dataclass
class PolicyRule:
    rule_id: str
    condition: str  # JSON condition string
    action: str  # Action to take when condition is met
    parameters: Dict[str, Any]
    priority: int  # Higher number = higher priority


@dataclass
class PolicyException:
    exception_id: str
    entity_type: str  # "customer", "zone", "product"
    entity_id: str
    rule_override: Dict[str, Any]
    valid_from: datetime
    valid_until: Optional[datetime]
    reason: str


class CommercialPolicy:
    def __init__(
        self,
        policy_id: str,
        name: str,
        policy_type: PolicyType,
        scope: PolicyScope,
        scope_value: str  # country_code, zone_id, customer_id, or "global"
    ):
        self.policy_id = policy_id
        self.name = name
        self.description = ""
        self.policy_type = policy_type
        self.scope = scope
        self.scope_value = scope_value
        self.status = PolicyStatus.DRAFT
        self.version = 1
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.effective_from = datetime.now()
        self.effective_until: Optional[datetime] = None
        self.rules: List[PolicyRule] = []
        self.exceptions: List[PolicyException] = []
        self.created_by: str = ""
        self.approved_by: Optional[str] = None
        self.approval_date: Optional[datetime] = None

    def add_rule(self, rule: PolicyRule) -> None:
        """Agregar regla a la política"""
        # Verificar que no existe una regla con el mismo ID
        if any(r.rule_id == rule.rule_id for r in self.rules):
            raise ValueError(f"Ya existe una regla con ID {rule.rule_id}")
        
        self.rules.append(rule)
        self.updated_at = datetime.now()

    def remove_rule(self, rule_id: str) -> None:
        """Remover regla de la política"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        self.updated_at = datetime.now()

    def add_exception(self, exception: PolicyException) -> None:
        """Agregar excepción a la política"""
        # Verificar que no existe una excepción con el mismo ID
        if any(e.exception_id == exception.exception_id for e in self.exceptions):
            raise ValueError(f"Ya existe una excepción con ID {exception.exception_id}")
        
        self.exceptions.append(exception)
        self.updated_at = datetime.now()

    def activate(self, approved_by: str) -> None:
        """Activar política después de aprobación"""
        if self.status != PolicyStatus.DRAFT:
            raise ValueError("Solo se pueden activar políticas en borrador")
        
        self.status = PolicyStatus.ACTIVE
        self.approved_by = approved_by
        self.approval_date = datetime.now()
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Desactivar política"""
        if self.status != PolicyStatus.ACTIVE:
            raise ValueError("Solo se pueden desactivar políticas activas")
        
        self.status = PolicyStatus.INACTIVE
        self.updated_at = datetime.now()

    def create_new_version(self) -> "CommercialPolicy":
        """Crear nueva versión de la política"""
        new_policy = CommercialPolicy(
            policy_id=f"{self.policy_id}_v{self.version + 1}",
            name=self.name,
            policy_type=self.policy_type,
            scope=self.scope,
            scope_value=self.scope_value
        )
        new_policy.description = self.description
        new_policy.version = self.version + 1
        new_policy.rules = self.rules.copy()
        new_policy.exceptions = self.exceptions.copy()
        new_policy.created_by = self.created_by
        
        return new_policy

    def is_applicable_to(self, entity_type: str, entity_id: str, current_time: datetime = None) -> bool:
        """Verificar si la política es aplicable a una entidad"""
        if current_time is None:
            current_time = datetime.now()
        
        # Verificar estado y vigencia
        if self.status != PolicyStatus.ACTIVE:
            return False
        
        if current_time < self.effective_from:
            return False
        
        if self.effective_until and current_time > self.effective_until:
            return False
        
        # Verificar scope
        if self.scope == PolicyScope.GLOBAL:
            return True
        
        if self.scope == PolicyScope.CUSTOMER and entity_type == "customer":
            return entity_id == self.scope_value
        
        # Para zone y country se requiere lógica adicional según la estructura de datos
        return False

    def get_applicable_rules(self, context: Dict[str, Any]) -> List[PolicyRule]:
        """Obtener reglas aplicables según el contexto"""
        applicable_rules = []
        
        for rule in self.rules:
            # Evaluar condición de la regla (esto requeriría un engine de reglas)
            # Por simplicidad, asumimos que todas las reglas son aplicables
            applicable_rules.append(rule)
        
        # Ordenar por prioridad (mayor prioridad primero)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        return applicable_rules

    def get_exceptions_for_entity(self, entity_type: str, entity_id: str) -> List[PolicyException]:
        """Obtener excepciones aplicables a una entidad"""
        current_time = datetime.now()
        applicable_exceptions = []
        
        for exception in self.exceptions:
            if (exception.entity_type == entity_type and 
                exception.entity_id == entity_id and
                exception.valid_from <= current_time and
                (exception.valid_until is None or exception.valid_until >= current_time)):
                applicable_exceptions.append(exception)
        
        return applicable_exceptions


class PricingPolicy(CommercialPolicy):
    def __init__(self, policy_id: str, name: str, scope: PolicyScope, scope_value: str):
        super().__init__(policy_id, name, PolicyType.PRICING, scope, scope_value)
        self.base_rates: Dict[str, Money] = {}
        self.weight_multipliers: Dict[str, float] = {}
        self.distance_multipliers: Dict[str, float] = {}
        self.volume_discounts: Dict[str, float] = {}

    def set_base_rate(self, service_type: str, rate: Money) -> None:
        """Establecer tarifa base para un tipo de servicio"""
        self.base_rates[service_type] = rate
        self.updated_at = datetime.now()

    def set_weight_multiplier(self, weight_range: str, multiplier: float) -> None:
        """Establecer multiplicador por peso"""
        self.weight_multipliers[weight_range] = multiplier
        self.updated_at = datetime.now()

    def calculate_price(self, service_type: str, weight: float, distance: float, volume: int) -> Money:
        """Calcular precio según parámetros"""
        if service_type not in self.base_rates:
            raise ValueError(f"No hay tarifa base para servicio {service_type}")
        
        base_price = self.base_rates[service_type]
        
        # Aplicar multiplicadores (lógica simplificada)
        # En una implementación real, esto sería más complejo
        final_amount = base_price.amount
        
        return Money(final_amount, base_price.currency)


class ServiceCatalog:
    def __init__(self, catalog_id: str, name: str):
        self.catalog_id = catalog_id
        self.name = name
        self.description = ""
        self.is_active = True
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.services: Dict[str, Dict[str, Any]] = {}

    def add_service(self, service_id: str, service_config: Dict[str, Any]) -> None:
        """Agregar servicio al catálogo"""
        if service_id in self.services:
            raise ValueError(f"El servicio {service_id} ya existe en el catálogo")
        
        self.services[service_id] = service_config
        self.updated_at = datetime.now()

    def remove_service(self, service_id: str) -> None:
        """Remover servicio del catálogo"""
        if service_id in self.services:
            del self.services[service_id]
            self.updated_at = datetime.now()

    def is_service_available(self, service_id: str) -> bool:
        """Verificar si un servicio está disponible"""
        return self.is_active and service_id in self.services

    def get_service_config(self, service_id: str) -> Dict[str, Any]:
        """Obtener configuración de un servicio"""
        if not self.is_service_available(service_id):
            raise ValueError(f"Servicio {service_id} no disponible")
        
        return self.services[service_id]