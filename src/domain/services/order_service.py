"""Servicios de dominio para la gestión de órdenes.

Este módulo contiene la lógica de negocio para la creación, cotización,
confirmación y gestión de órdenes de envío.
"""

from decimal import Decimal
from typing import Optional
from datetime import datetime, timedelta
from src.domain.entities.order import Order, OrderStatus
from src.domain.entities.guide import Guide
from src.domain.entities.customer import Customer
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.package_dimensions import PackageDimensions
from src.domain.repositories.order_repository import OrderRepository
from src.domain.repositories.customer_repository import CustomerRepository


class OrderService:
    """Servicio de dominio para la gestión de órdenes.
    
    Coordina las operaciones de negocio relacionadas con órdenes,
    incluyendo validaciones, cálculos de envío y generación de guías.
    
    Attributes:
        order_repository: Repositorio para persistencia de órdenes
        customer_repository: Repositorio para acceso a datos de clientes
    """
    
    def __init__(self, order_repository: OrderRepository, customer_repository: CustomerRepository):
        """Inicializa el servicio de órdenes.
        
        Args:
            order_repository: Repositorio para órdenes
            customer_repository: Repositorio para clientes
        """
        self.order_repository = order_repository
        self.customer_repository = customer_repository
    
    async def create_order(self, order_data: dict) -> Order:
        """Crea una nueva orden de envío.
        
        Valida que el cliente exista y cumpla los requisitos
        para el tipo de envío solicitado.
        
        Args:
            order_data: Datos de la orden a crear
            
        Returns:
            Order: Orden creada y persistida
            
        Raises:
            ValueError: Si el cliente no existe o no cumple requisitos
        """
        # Validar que el cliente existe
        customer = await self.customer_repository.find_by_id(order_data['customer_id'])
        if not customer:
            raise ValueError("Cliente no encontrado")
        
        # Crear orden
        order = Order(**order_data)
        
        # Validar requisitos para envíos internacionales
        if order.is_international() and not customer.can_create_international_shipment():
            raise ValueError("Cliente debe completar KYC para envíos internacionales")
        
        return await self.order_repository.save(order)
    
    def calculate_shipping(self, origin: str, destination: str, package: PackageDimensions) -> dict:
        """Calcula el costo y tiempo de envío.
        
        Implementa la lógica de negocio para calcular tarifas
        basadas en peso, dimensiones y destino.
        
        Args:
            origin: Ciudad de origen
            destination: Ciudad de destino
            package: Dimensiones y peso del paquete
            
        Returns:
            dict: Diccionario con precio, días de entrega y peso facturable
        """
        # Cálculo simple - en realidad integraría con APIs de operadores
        base_price = Decimal('10000')  # Precio base en COP
        
        # Calcular por peso
        billable_weight = package.get_billable_weight()
        weight_cost = billable_weight * Decimal('2000')
        
        # Multiplicador de distancia (simplificado)
        distance_multiplier = Decimal('1.5') if "international" in destination.lower() else Decimal('1.0')
        
        total_price = (base_price + weight_cost) * distance_multiplier
        delivery_days = 5 if distance_multiplier > 1 else 3
        
        return {
            'price': total_price,
            'delivery_days': delivery_days,
            'billable_weight': billable_weight
        }
    
    async def generate_guide(self, order_id: OrderId) -> Guide:
        """Genera la guía de envío para una orden confirmada.
        
        Valida que la orden esté en estado correcto y genera
        la guía con el operador logístico asignado.
        
        Args:
            order_id: ID de la orden para generar guía
            
        Returns:
            Guide: Guía generada
            
        Raises:
            ValueError: Si la orden no existe o no está confirmada
        """
        order = await self.order_repository.find_by_id(order_id)
        if not order:
            raise ValueError("Orden no encontrada")
        
        if order.status != OrderStatus.CONFIRMED:
            raise ValueError("Solo se puede generar guía para órdenes confirmadas")
        
        # Validar cliente
        customer = await self.customer_repository.find_by_id(order.customer_id)
        if not customer:
            raise ValueError("Cliente no encontrado")
        
        # Crear guía
        guide = Guide(
            order_id=order.id,
            customer_id=order.customer_id,
            logistics_operator="Quenty Express"
        )
        
        # Actualizar estado de la orden
        order.mark_with_guide()
        await self.order_repository.save(order)
        
        return guide
    
    async def cancel_order(self, order_id: OrderId) -> bool:
        """Cancela una orden existente.
        
        Args:
            order_id: ID de la orden a cancelar
            
        Returns:
            bool: True si se canceló exitosamente, False si no existe
            
        Raises:
            ValueError: Si la orden no se puede cancelar
        """
        order = await self.order_repository.find_by_id(order_id)
        if not order:
            return False
        
        order.cancel()
        await self.order_repository.save(order)
        return True
    
    async def quote_order(self, order_id: OrderId) -> Order:
        """Genera cotización para una orden.
        
        Calcula el precio y tiempo de entrega para la orden
        y actualiza la orden con la cotización.
        
        Args:
            order_id: ID de la orden a cotizar
            
        Returns:
            Order: Orden actualizada con cotización
            
        Raises:
            ValueError: Si la orden no existe
        """
        order = await self.order_repository.find_by_id(order_id)
        if not order:
            raise ValueError("Orden no encontrada")
        
        # Calcular cotización de envío
        quote = self.calculate_shipping(
            order.origin_city,
            order.recipient.city,
            order.package_dimensions
        )
        
        order.set_quote(quote['price'], quote['delivery_days'])
        return await self.order_repository.save(order)