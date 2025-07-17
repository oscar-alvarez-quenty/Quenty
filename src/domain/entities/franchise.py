"""Entidades de dominio para la gestión de franquicias y puntos logísticos.

Este módulo contiene las entidades para manejar franquicias, puntos logísticos,
zonas de cobertura y operadores logísticos del sistema.
"""

from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from src.domain.value_objects.customer_id import CustomerId


class FranchiseStatus(Enum):
    """Estados posibles de una franquicia.
    
    Attributes:
        PENDING: Franquicia solicitada pero no aprobada
        ACTIVE: Franquicia activa y operando
        SUSPENDED: Franquicia suspendida temporalmente
        TERMINATED: Franquicia terminada definitivamente
    """
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class LogisticPointType(Enum):
    """Tipos de puntos logísticos disponibles.
    
    Attributes:
        FRANCHISE: Punto operado por franquiciado
        ALLY: Punto operado por aliado comercial
        HUB: Centro de distribución principal
    """
    FRANCHISE = "franchise"
    ALLY = "ally"
    HUB = "hub"

@dataclass
class LogisticZone:
    """Zona logística para organización territorial.
    
    Define áreas geográficas para optimizar la distribución
    y asignación de franquicias y puntos logísticos.
    
    Attributes:
        id: Identificador único de la zona
        name: Nombre descriptivo de la zona
        code: Código corto de identificación
        city: Ciudad principal de la zona
        state: Departamento o estado
        country: País (por defecto Colombia)
        postal_codes: Lista de códigos postales cubiertos
        is_active: Indica si la zona está activa
        created_at: Fecha de creación
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    city: str = ""
    state: str = ""
    country: str = "Colombia"
    postal_codes: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class LogisticPoint:
    """Punto logístico para recepción y entrega de paquetes.
    
    Representa ubicaciones físicas donde los clientes pueden
    entregar o recibir paquetes, operados por franquiciados o aliados.
    
    Attributes:
        id: Identificador único del punto
        name: Nombre comercial del punto
        address: Dirección física completa
        city: Ciudad donde se ubica
        phone: Teléfono de contacto
        email: Correo electrónico de contacto
        point_type: Tipo de punto (franquicia, aliado, hub)
        zone_id: ID de la zona logística asignada
        operating_hours: Horarios de atención
        is_active: Indica si el punto está operativo
        created_at: Fecha de creación
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    address: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    point_type: LogisticPointType = LogisticPointType.ALLY
    zone_id: UUID = None
    operating_hours: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def can_receive_packages(self) -> bool:
        """Verifica si el punto puede recibir paquetes.
        
        Solo puntos activos de tipo franquicia o aliado
        pueden recibir paquetes de clientes.
        
        Returns:
            bool: True si puede recibir paquetes
        """
        return self.is_active and self.point_type in [LogisticPointType.FRANCHISE, LogisticPointType.ALLY]

@dataclass
class Franchise:
    """Franquicia del sistema logístico.
    
    Representa un acuerdo comercial donde un franquiciado opera
    en una zona específica bajo el modelo de negocio de la plataforma,
    incluyendo inversión, comisiones y asignación de tokens.
    
    Attributes:
        id: Identificador único de la franquicia
        franchisee_id: ID del cliente franquiciado
        zone_id: ID de la zona asignada
        business_name: Nombre comercial de la franquicia
        investment_amount: Monto de inversión realizada
        franchise_fee: Cuota inicial de franquicia
        monthly_fee: Cuota mensual fija
        commission_rate: Porcentaje de comisión sobre ventas
        status: Estado actual de la franquicia
        contract_start_date: Fecha de inicio del contrato
        contract_end_date: Fecha de finalización del contrato
        minimum_capital_required: Capital mínimo requerido
        token_allocation: Tokens asignados a la franquicia
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    id: UUID = field(default_factory=uuid4)
    franchisee_id: CustomerId = None
    zone_id: UUID = None
    business_name: str = ""
    investment_amount: Decimal = Decimal('0.00')
    franchise_fee: Decimal = Decimal('0.00')
    monthly_fee: Decimal = Decimal('0.00')
    commission_rate: Decimal = Decimal('0.15')  # 15% default
    status: FranchiseStatus = FranchiseStatus.PENDING
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    minimum_capital_required: Decimal = Decimal('5000000')  # 5M COP
    token_allocation: Decimal = Decimal('0.00')
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def approve_franchise(self, start_date: datetime, end_date: datetime) -> None:
        """Aprueba una solicitud de franquicia.
        
        Valida que se cumplan los requisitos de capital y
        activa la franquicia con las fechas de contrato especificadas.
        
        Args:
            start_date: Fecha de inicio del contrato
            end_date: Fecha de finalización del contrato
            
        Raises:
            ValueError: Si la franquicia no está pendiente o no cumple requisitos
        """
        if self.status != FranchiseStatus.PENDING:
            raise ValueError("Solo se pueden aprobar franquicias pendientes")
        
        if self.investment_amount < self.minimum_capital_required:
            raise ValueError(f"La inversión debe ser al menos ${self.minimum_capital_required}")
        
        if end_date <= start_date:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio")
        
        self.status = FranchiseStatus.ACTIVE
        self.contract_start_date = start_date
        self.contract_end_date = end_date
        self.updated_at = datetime.utcnow()
    
    def suspend_franchise(self, reason: str = "") -> None:
        """Suspende una franquicia activa.
        
        La franquicia suspendida no puede operar pero mantiene
        el contrato para posible reactivación futura.
        
        Args:
            reason: Motivo de la suspensión
            
        Raises:
            ValueError: Si la franquicia no está activa
        """
        if self.status != FranchiseStatus.ACTIVE:
            raise ValueError("Solo se pueden suspender franquicias activas")
        
        self.status = FranchiseStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def terminate_franchise(self, reason: str = "") -> None:
        """Termina definitivamente una franquicia.
        
        La terminación es irreversible y finaliza completamente
        la relación comercial con el franquiciado.
        
        Args:
            reason: Motivo de la terminación
            
        Raises:
            ValueError: Si la franquicia no puede ser terminada
        """
        if self.status not in [FranchiseStatus.ACTIVE, FranchiseStatus.SUSPENDED]:
            raise ValueError("Solo se pueden terminar franquicias activas o suspendidas")
        
        self.status = FranchiseStatus.TERMINATED
        self.updated_at = datetime.utcnow()
    
    def calculate_monthly_revenue_share(self, gross_revenue: Decimal) -> Decimal:
        """Calcula la participación mensual de ingresos.
        
        Suma la cuota mensual fija más la comisión por ventas
        para determinar el pago total a la franquicia.
        
        Args:
            gross_revenue: Ingresos brutos del mes
            
        Returns:
            Decimal: Monto total a pagar a la franquicia
        """
        if gross_revenue < 0:
            raise ValueError("Los ingresos no pueden ser negativos")
        return self.monthly_fee + (gross_revenue * self.commission_rate)
    
    def is_contract_valid(self) -> bool:
        """Verifica si el contrato de franquicia está vigente.
        
        Valida que existan fechas de contrato y que la fecha
        actual esté dentro del período contractual.
        
        Returns:
            bool: True si el contrato está vigente
        """
        if not self.contract_start_date or not self.contract_end_date:
            return False
        
        now = datetime.utcnow()
        return self.contract_start_date <= now <= self.contract_end_date
    
    def can_allocate_tokens(self) -> bool:
        """Verifica si la franquicia puede asignar tokens.
        
        Solo franquicias activas con contrato vigente y
        asignación de tokens pueden distribuir tokens.
        
        Returns:
            bool: True si puede asignar tokens
        """
        return (self.status == FranchiseStatus.ACTIVE and 
                self.is_contract_valid() and
                self.token_allocation > 0)

@dataclass
class LogisticOperator:
    """Operador logístico externo para transporte.
    
    Representa empresas de logística que proporcionan servicios
    de transporte y entrega, con integración API y tarifas.
    
    Attributes:
        id: Identificador único del operador
        name: Nombre de la empresa operadora
        code: Código corto de identificación
        contact_email: Email de contacto comercial
        contact_phone: Teléfono de contacto
        api_endpoint: URL del API para integración
        api_key: Clave de acceso al API
        supported_services: Tipos de servicio soportados
        coverage_zones: Zonas de cobertura del operador
        base_rate: Tarifa base por envío
        weight_rate: Tarifa por kilogramo
        is_active: Indica si el operador está activo
        created_at: Fecha de creación
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    api_endpoint: str = ""
    api_key: str = ""
    supported_services: List[str] = field(default_factory=list)  # national, international
    coverage_zones: List[UUID] = field(default_factory=list)
    base_rate: Decimal = Decimal('0.00')
    weight_rate: Decimal = Decimal('0.00')
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def supports_service_type(self, service_type: str) -> bool:
        """Verifica si el operador soporta un tipo de servicio.
        
        Args:
            service_type: Tipo de servicio (national/international)
            
        Returns:
            bool: True si soporta el tipo de servicio
        """
        return service_type in self.supported_services
    
    def covers_zone(self, zone_id: UUID) -> bool:
        """Verifica si el operador cubre una zona específica.
        
        Args:
            zone_id: ID de la zona a verificar
            
        Returns:
            bool: True si cubre la zona
        """
        return zone_id in self.coverage_zones
    
    def calculate_shipping_cost(self, weight_kg: Decimal, distance_factor: Decimal = Decimal('1.0')) -> Decimal:
        """Calcula el costo de envío basado en peso y distancia.
        
        Args:
            weight_kg: Peso del paquete en kilogramos
            distance_factor: Factor de distancia (por defecto 1.0)
            
        Returns:
            Decimal: Costo total del envío
            
        Raises:
            ValueError: Si el peso es negativo
        """
        if weight_kg < 0:
            raise ValueError("El peso no puede ser negativo")
        if distance_factor < 0:
            raise ValueError("El factor de distancia no puede ser negativo")
            
        return (self.base_rate + (weight_kg * self.weight_rate)) * distance_factor