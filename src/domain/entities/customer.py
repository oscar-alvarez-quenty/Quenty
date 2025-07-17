"""Entidades de dominio para la gestión de clientes.

Este módulo contiene la entidad principal Cliente que representa a los usuarios
de la plataforma logística, incluyendo validaciones de negocio y capacidades
según el tipo de cliente.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email
from src.domain.value_objects.customer_type import CustomerType


@dataclass
class Customer:
    """Entidad principal que representa un cliente de la plataforma logística.
    
    Esta clase encapsula toda la información de un cliente, incluyendo sus datos
    básicos, estado de validación KYC, tipo de cliente y permisos asociados.
    Los clientes pueden ser pequeños, medianos o grandes, cada tipo con diferentes
    capacidades y privilegios en la plataforma.
    
    Attributes:
        id: Identificador único del cliente
        email: Dirección de correo electrónico del cliente
        customer_type: Tipo de cliente (pequeño, mediano, grande)
        business_name: Nombre del negocio o empresa
        tax_id: Número de identificación tributaria (NIT/RUT)
        phone: Número de teléfono de contacto
        address: Dirección física del cliente
        kyc_validated: Indica si el cliente ha pasado la validación KYC
        is_active: Indica si el cliente está activo en la plataforma
        created_at: Fecha y hora de creación del cliente
        updated_at: Fecha y hora de última actualización
    """
    id: CustomerId = field(default_factory=CustomerId.generate)
    email: Email = None
    customer_type: CustomerType = CustomerType.SMALL
    business_name: str = ""
    tax_id: str = ""
    phone: str = ""
    address: str = ""
    kyc_validated: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def validate_kyc(self) -> None:
        """Valida el proceso KYC (Know Your Customer) del cliente.
        
        Marca al cliente como validado KYC, lo cual le permite acceder a
        servicios avanzados como envíos internacionales y crédito.
        
        Raises:
            BusinessRuleException: Si el cliente ya está validado
        """
        self.kyc_validated = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Desactiva el cliente en la plataforma.
        
        El cliente desactivado no puede realizar nuevas operaciones
        pero mantiene su historial y datos para auditoría.
        
        Raises:
            BusinessRuleException: Si el cliente ya está desactivado
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def can_create_international_shipment(self) -> bool:
        """Verifica si el cliente puede crear envíos internacionales.
        
        Los envíos internacionales requieren validación KYC completa
        por regulaciones aduaneras y de comercio exterior.
        
        Returns:
            bool: True si el cliente puede crear envíos internacionales
        """
        return self.kyc_validated
    
    def can_use_credit(self) -> bool:
        """Verifica si el cliente puede usar crédito en la plataforma.
        
        Solo clientes medianos y grandes tienen acceso a facilidades
        de crédito para pagos diferidos y líneas de crédito.
        
        Returns:
            bool: True si el cliente puede usar crédito
        """
        return self.customer_type in [CustomerType.MEDIUM, CustomerType.LARGE]
    
    def can_request_pickup(self) -> bool:
        """Verifica si el cliente puede solicitar recolecciones.
        
        Las recolecciones domiciliarias están disponibles solo para
        clientes medianos y grandes debido al costo operativo.
        
        Returns:
            bool: True si el cliente puede solicitar recolecciones
        """
        return self.customer_type in [CustomerType.MEDIUM, CustomerType.LARGE]