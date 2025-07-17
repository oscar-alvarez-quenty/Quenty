from typing import Optional, List
from src.domain.entities.order import Order, Recipient
from src.domain.entities.guide import Guide
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.package_dimensions import PackageDimensions
from src.domain.services.order_service import OrderService
from src.api.schemas.order_schemas import OrderCreateRequest, OrderQuoteRequest

class OrderApplicationService:
    
    def __init__(self, order_service: OrderService):
        self.order_service = order_service
    
    async def create_order(self, request: OrderCreateRequest) -> Order:
        # Convert request to domain objects
        recipient = Recipient(
            name=request.recipient.name,
            phone=request.recipient.phone,
            email=request.recipient.email,
            address=request.recipient.address,
            city=request.recipient.city,
            country=request.recipient.country,
            postal_code=request.recipient.postal_code or ""
        )
        
        package_dimensions = PackageDimensions(
            length_cm=request.package_dimensions.length_cm,
            width_cm=request.package_dimensions.width_cm,
            height_cm=request.package_dimensions.height_cm,
            weight_kg=request.package_dimensions.weight_kg
        )
        
        order_data = {
            'customer_id': CustomerId.from_string(request.customer_id),
            'recipient': recipient,
            'package_dimensions': package_dimensions,
            'declared_value': request.declared_value,
            'service_type': request.service_type,
            'origin_address': request.origin_address,
            'origin_city': request.origin_city,
            'notes': request.notes or ""
        }
        
        return await self.order_service.create_order(order_data)
    
    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        return await self.order_service.order_repository.find_by_id(OrderId.from_string(order_id))
    
    async def get_orders_by_customer(self, customer_id: str) -> List[Order]:
        return await self.order_service.order_repository.find_by_customer_id(
            CustomerId.from_string(customer_id)
        )
    
    async def quote_order(self, order_id: str) -> Order:
        return await self.order_service.quote_order(OrderId.from_string(order_id))
    
    def calculate_shipping_quote(self, request: OrderQuoteRequest) -> dict:
        package_dimensions = PackageDimensions(
            length_cm=request.package_dimensions.length_cm,
            width_cm=request.package_dimensions.width_cm,
            height_cm=request.package_dimensions.height_cm,
            weight_kg=request.package_dimensions.weight_kg
        )
        
        return self.order_service.calculate_shipping(
            request.origin,
            request.destination,
            package_dimensions
        )
    
    async def confirm_order(self, order_id: str) -> Order:
        order = await self.order_service.order_repository.find_by_id(OrderId.from_string(order_id))
        if not order:
            raise ValueError("Order not found")
        
        order.confirm()
        return await self.order_service.order_repository.save(order)
    
    async def cancel_order(self, order_id: str) -> bool:
        return await self.order_service.cancel_order(OrderId.from_string(order_id))
    
    async def generate_guide(self, order_id: str) -> Guide:
        return await self.order_service.generate_guide(OrderId.from_string(order_id))