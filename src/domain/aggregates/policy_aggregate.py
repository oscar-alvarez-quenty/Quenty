from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.entities.policy import (
    CommercialPolicy, PricingPolicy, ServiceCatalog,
    PolicyType, PolicyScope, PolicyStatus, PolicyRule, PolicyException
)
from src.domain.value_objects.money import Money
from src.domain.events.policy_events import (
    PolicyCreated, PolicyActivated, PolicyDeactivated,
    PricingUpdated, ServiceCatalogUpdated, PolicyExceptionAdded
)


class PolicyAggregate:
    def __init__(self):
        self.commercial_policies: List[CommercialPolicy] = []
        self.pricing_policies: List[PricingPolicy] = []
        self.service_catalogs: List[ServiceCatalog] = []
        self.active_policies_cache: Dict[str, List[CommercialPolicy]] = {}
        self._domain_events: List = []

    def create_commercial_policy(
        self,
        policy_id: str,
        name: str,
        policy_type: PolicyType,
        scope: PolicyScope,
        scope_value: str,
        created_by: str
    ) -> CommercialPolicy:
        """Crear nueva política comercial"""
        policy = CommercialPolicy(
            policy_id=policy_id,
            name=name,
            policy_type=policy_type,
            scope=scope,
            scope_value=scope_value
        )
        
        policy.created_by = created_by
        self.commercial_policies.append(policy)
        
        self._add_domain_event(
            PolicyCreated(
                policy_id=policy_id,
                name=name,
                policy_type=policy_type.value,
                scope=scope.value,
                scope_value=scope_value,
                created_by=created_by
            )
        )
        
        return policy

    def create_pricing_policy(
        self,
        policy_id: str,
        name: str,
        scope: PolicyScope,
        scope_value: str,
        base_rates: Dict[str, Money],
        created_by: str
    ) -> PricingPolicy:
        """Crear nueva política de precios"""
        pricing_policy = PricingPolicy(
            policy_id=policy_id,
            name=name,
            scope=scope,
            scope_value=scope_value
        )
        
        pricing_policy.created_by = created_by
        
        # Establecer tarifas base
        for service_type, rate in base_rates.items():
            pricing_policy.set_base_rate(service_type, rate)
        
        self.pricing_policies.append(pricing_policy)
        
        self._add_domain_event(
            PolicyCreated(
                policy_id=policy_id,
                name=name,
                policy_type="pricing",
                scope=scope.value,
                scope_value=scope_value,
                created_by=created_by
            )
        )
        
        return pricing_policy

    def create_service_catalog(
        self,
        catalog_id: str,
        name: str,
        services: Dict[str, Dict[str, Any]]
    ) -> ServiceCatalog:
        """Crear catálogo de servicios"""
        catalog = ServiceCatalog(catalog_id, name)
        
        for service_id, service_config in services.items():
            catalog.add_service(service_id, service_config)
        
        self.service_catalogs.append(catalog)
        
        self._add_domain_event(
            ServiceCatalogUpdated(
                catalog_id=catalog_id,
                name=name,
                services_count=len(services),
                updated_at=datetime.now()
            )
        )
        
        return catalog

    def activate_policy(self, policy_id: str, approved_by: str) -> None:
        """Activar política"""
        policy = self._find_policy_by_id(policy_id)
        if not policy:
            raise ValueError(f"Política {policy_id} no encontrada")
        
        policy.activate(approved_by)
        self._invalidate_cache()
        
        self._add_domain_event(
            PolicyActivated(
                policy_id=policy_id,
                approved_by=approved_by,
                activated_at=datetime.now(),
                scope=policy.scope.value,
                scope_value=policy.scope_value
            )
        )

    def deactivate_policy(self, policy_id: str) -> None:
        """Desactivar política"""
        policy = self._find_policy_by_id(policy_id)
        if not policy:
            raise ValueError(f"Política {policy_id} no encontrada")
        
        policy.deactivate()
        self._invalidate_cache()
        
        self._add_domain_event(
            PolicyDeactivated(
                policy_id=policy_id,
                deactivated_at=datetime.now(),
                scope=policy.scope.value,
                scope_value=policy.scope_value
            )
        )

    def add_policy_rule(self, policy_id: str, rule: PolicyRule) -> None:
        """Agregar regla a política"""
        policy = self._find_policy_by_id(policy_id)
        if not policy:
            raise ValueError(f"Política {policy_id} no encontrada")
        
        policy.add_rule(rule)
        self._invalidate_cache()

    def add_policy_exception(self, policy_id: str, exception: PolicyException) -> None:
        """Agregar excepción a política"""
        policy = self._find_policy_by_id(policy_id)
        if not policy:
            raise ValueError(f"Política {policy_id} no encontrada")
        
        policy.add_exception(exception)
        
        self._add_domain_event(
            PolicyExceptionAdded(
                policy_id=policy_id,
                exception_id=exception.exception_id,
                entity_type=exception.entity_type,
                entity_id=exception.entity_id,
                valid_from=exception.valid_from,
                valid_until=exception.valid_until
            )
        )

    def update_pricing(
        self,
        policy_id: str,
        service_type: str,
        new_rate: Money,
        updated_by: str
    ) -> None:
        """Actualizar precio en política de precios"""
        pricing_policy = next(
            (p for p in self.pricing_policies if p.policy_id == policy_id),
            None
        )
        
        if not pricing_policy:
            raise ValueError(f"Política de precios {policy_id} no encontrada")
        
        old_rate = pricing_policy.base_rates.get(service_type)
        pricing_policy.set_base_rate(service_type, new_rate)
        
        self._add_domain_event(
            PricingUpdated(
                policy_id=policy_id,
                service_type=service_type,
                old_rate=old_rate.amount if old_rate else 0,
                new_rate=new_rate.amount,
                updated_by=updated_by,
                updated_at=datetime.now()
            )
        )

    def get_applicable_policies(
        self,
        entity_type: str,
        entity_id: str,
        policy_type: Optional[PolicyType] = None
    ) -> List[CommercialPolicy]:
        """Obtener políticas aplicables a una entidad"""
        # Buscar en cache primero
        cache_key = f"{entity_type}:{entity_id}:{policy_type.value if policy_type else 'all'}"
        if cache_key in self.active_policies_cache:
            return self.active_policies_cache[cache_key]
        
        applicable_policies = []
        
        for policy in self.commercial_policies:
            if policy_type and policy.policy_type != policy_type:
                continue
            
            if policy.is_applicable_to(entity_type, entity_id):
                applicable_policies.append(policy)
        
        # Agregar políticas de precios si aplica
        if not policy_type or policy_type == PolicyType.PRICING:
            for pricing_policy in self.pricing_policies:
                if pricing_policy.is_applicable_to(entity_type, entity_id):
                    applicable_policies.append(pricing_policy)
        
        # Ordenar por prioridad (scope más específico primero)
        applicable_policies.sort(key=self._get_policy_priority, reverse=True)
        
        # Cache result
        self.active_policies_cache[cache_key] = applicable_policies
        
        return applicable_policies

    def calculate_price(
        self,
        customer_id: str,
        service_type: str,
        weight: float,
        distance: float,
        volume: int,
        destination_zone: str
    ) -> Money:
        """Calcular precio usando políticas aplicables"""
        # Buscar política de precios más específica
        pricing_policies = [
            p for p in self.get_applicable_policies("customer", customer_id, PolicyType.PRICING)
            if isinstance(p, PricingPolicy)
        ]
        
        if not pricing_policies:
            # Buscar política global de precios
            global_policies = [
                p for p in self.pricing_policies
                if p.scope == PolicyScope.GLOBAL and p.status == PolicyStatus.ACTIVE
            ]
            if global_policies:
                pricing_policies = [global_policies[0]]
        
        if not pricing_policies:
            raise ValueError("No se encontró política de precios aplicable")
        
        # Usar la primera política (más específica)
        pricing_policy = pricing_policies[0]
        
        # Calcular precio base
        price = pricing_policy.calculate_price(service_type, weight, distance, volume)
        
        # Aplicar excepciones si existen
        exceptions = pricing_policy.get_exceptions_for_entity("customer", customer_id)
        for exception in exceptions:
            # Aplicar modificaciones según la excepción
            # Por simplicidad, no implementamos la lógica completa aquí
            pass
        
        return price

    def get_available_services(
        self,
        customer_id: str,
        customer_type: str,
        destination_zone: str
    ) -> List[Dict[str, Any]]:
        """Obtener servicios disponibles para un cliente"""
        available_services = []
        
        # Buscar catálogo aplicable
        for catalog in self.service_catalogs:
            if not catalog.is_active:
                continue
            
            for service_id, service_config in catalog.services.items():
                # Verificar si el servicio está disponible según políticas
                if self._is_service_allowed(customer_id, customer_type, service_id, destination_zone):
                    available_services.append({
                        "service_id": service_id,
                        "service_name": service_config.get("name", service_id),
                        "description": service_config.get("description", ""),
                        "estimated_delivery_days": service_config.get("delivery_days", 0),
                        "features": service_config.get("features", [])
                    })
        
        return available_services

    def create_policy_version(self, policy_id: str) -> CommercialPolicy:
        """Crear nueva versión de una política"""
        policy = self._find_policy_by_id(policy_id)
        if not policy:
            raise ValueError(f"Política {policy_id} no encontrada")
        
        new_policy = policy.create_new_version()
        self.commercial_policies.append(new_policy)
        
        return new_policy

    def get_policy_history(self, base_policy_id: str) -> List[CommercialPolicy]:
        """Obtener historial de versiones de una política"""
        # Buscar todas las políticas que empiecen con el ID base
        return [
            p for p in self.commercial_policies
            if p.policy_id.startswith(base_policy_id)
        ]

    def get_policy_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de políticas"""
        active_policies = [p for p in self.commercial_policies if p.status == PolicyStatus.ACTIVE]
        
        return {
            "total_policies": len(self.commercial_policies),
            "active_policies": len(active_policies),
            "pricing_policies": len(self.pricing_policies),
            "service_catalogs": len(self.service_catalogs),
            "policies_by_type": {
                policy_type.value: len([p for p in active_policies if p.policy_type == policy_type])
                for policy_type in PolicyType
            },
            "policies_by_scope": {
                scope.value: len([p for p in active_policies if p.scope == scope])
                for scope in PolicyScope
            }
        }

    def _find_policy_by_id(self, policy_id: str) -> Optional[CommercialPolicy]:
        """Buscar política por ID"""
        # Buscar en políticas comerciales
        for policy in self.commercial_policies:
            if policy.policy_id == policy_id:
                return policy
        
        # Buscar en políticas de precios
        for policy in self.pricing_policies:
            if policy.policy_id == policy_id:
                return policy
        
        return None

    def _get_policy_priority(self, policy: CommercialPolicy) -> int:
        """Obtener prioridad de política (más específico = mayor prioridad)"""
        if policy.scope == PolicyScope.CUSTOMER:
            return 4
        elif policy.scope == PolicyScope.ZONE:
            return 3
        elif policy.scope == PolicyScope.COUNTRY:
            return 2
        else:  # GLOBAL
            return 1

    def _is_service_allowed(
        self,
        customer_id: str,
        customer_type: str,
        service_id: str,
        destination_zone: str
    ) -> bool:
        """Verificar si un servicio está permitido según políticas"""
        # Buscar políticas operacionales que puedan restringir servicios
        operational_policies = self.get_applicable_policies(
            "customer", customer_id, PolicyType.OPERATIONAL
        )
        
        # Por simplicidad, asumimos que todos los servicios están permitidos
        # En una implementación real, evaluaríamos las reglas de las políticas
        return True

    def _invalidate_cache(self) -> None:
        """Invalidar cache de políticas activas"""
        self.active_policies_cache.clear()

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()