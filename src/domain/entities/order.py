"""Entidades de dominio para la gestión de órdenes.

Este módulo contiene las entidades principales para manejar órdenes de envío,
incluyendo información del destinatario, dimensiones del paquete, cotizaciones
y seguimiento del estado de la orden.
"""

from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.package_dimensions import PackageDimensions


class OrderStatus(Enum):
    """Estados posibles de una orden de envío.
    
    Attributes:
        PENDING: Orden creada pero sin cotización
        QUOTED: Orden cotizada esperando confirmación del cliente
        CONFIRMED: Orden confirmada por el cliente
        WITH_GUIDE: Orden con guía generada lista para envío
        CANCELLED: Orden cancelada
    """
    PENDING = "pending"
    QUOTED = "quoted"
    CONFIRMED = "confirmed"
    WITH_GUIDE = "with_guide"
    CANCELLED = "cancelled"

class ServiceType(Enum):
    """Tipos de servicio de envío disponibles.
    
    Attributes:
        NATIONAL: Envío nacional dentro de Colombia
        INTERNATIONAL: Envío internacional a otros países
    """
    NATIONAL = "national"
    INTERNATIONAL = "international"

@dataclass
class Recipient:
    """Información del destinatario de la orden.
    
    Attributes:
        name: Nombre completo del destinatario
        phone: Número de teléfono de contacto
        email: Dirección de correo electrónico
        address: Dirección completa de entrega
        city: Ciudad de destino
        country: País de destino (por defecto Colombia)
        postal_code: Código postal del destino
    """
    name: str
    phone: str
    email: str
    address: str
    city: str
    country: str = "Colombia"
    postal_code: str = ""

@dataclass
class Order:
    """Entidad principal que representa una orden de envío.
    
    Esta clase encapsula toda la información necesaria para procesar
    una orden de envío, desde su creación hasta la generación de la guía.
    Incluye información del destinatario, dimensiones del paquete,
    cotización y seguimiento del estado.
    
    Attributes:
        id: Identificador único de la orden
        customer_id: ID del cliente que crea la orden
        recipient: Información del destinatario
        package_dimensions: Dimensiones y peso del paquete
        declared_value: Valor declarado del contenido
        service_type: Tipo de servicio (nacional/internacional)
        status: Estado actual de la orden
        origin_address: Dirección de origen del envío
        origin_city: Ciudad de origen
        notes: Notas adicionales para el envío
        created_at: Fecha y hora de creación
        updated_at: Fecha y hora de última actualización
        quoted_price: Precio cotizado para el envío
        estimated_delivery_days: Días estimados de entrega
    """
    id: OrderId = field(default_factory=OrderId.generate)
    customer_id: CustomerId = None
    recipient: Recipient = None
    package_dimensions: PackageDimensions = None
    declared_value: Decimal = Decimal('0.00')
    service_type: ServiceType = ServiceType.NATIONAL
    status: OrderStatus = OrderStatus.PENDING
    origin_address: str = ""
    origin_city: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    quoted_price: Optional[Decimal] = None
    estimated_delivery_days: Optional[int] = None
    
    def set_quote(self, price: Decimal, delivery_days: int) -> None:
        """Establece la cotización para la orden.
        
        Asigna el precio cotizado y los días estimados de entrega,
        cambiando el estado de la orden a QUOTED.
        
        Args:
            price: Precio cotizado para el envío
            delivery_days: Días estimados para la entrega
            
        Raises:
            ValueError: Si el precio es negativo o los días son inválidos
        """
        if price < 0:
            raise ValueError("El precio no puede ser negativo")
        if delivery_days <= 0:
            raise ValueError("Los días de entrega deben ser positivos")
            
        self.quoted_price = price
        self.estimated_delivery_days = delivery_days
        self.status = OrderStatus.QUOTED
        self.updated_at = datetime.utcnow()
    
    def confirm(self) -> None:
        """Confirma la orden después de la cotización.
        
        El cliente acepta la cotización y la orden pasa a estado CONFIRMED,
        lista para generar la guía de envío.
        
        Raises:
            ValueError: Si la orden no está en estado QUOTED
        """
        if self.status != OrderStatus.QUOTED:
            raise ValueError("Solo se pueden confirmar órdenes cotizadas")
        
        self.status = OrderStatus.CONFIRMED
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancela la orden.
        
        Solo se pueden cancelar órdenes que no tengan guía generada.
        Una vez generada la guía, el proceso debe manejarse como
        devolución o cancelación de envío.
        
        Raises:
            ValueError: Si la orden ya tiene guía generada
        """
        if self.status in [OrderStatus.WITH_GUIDE]:
            raise ValueError("No se puede cancelar una orden con guía ya generada")
        
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def mark_with_guide(self) -> None:
        """Marca la orden como con guía generada.
        
        Indica que se ha generado la guía de envío y la orden
        está lista para ser procesada por el operador logístico.
        
        Raises:
            ValueError: Si la orden no está confirmada
        """
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError("Solo se puede generar guía para órdenes confirmadas")
        
        self.status = OrderStatus.WITH_GUIDE
        self.updated_at = datetime.utcnow()
    
    def is_international(self) -> bool:
        """Verifica si la orden es de envío internacional.
        
        Returns:
            bool: True si es envío internacional, False si es nacional
        """
        return self.service_type == ServiceType.INTERNATIONAL