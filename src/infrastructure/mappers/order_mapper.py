from typing import Optional
from src.domain.entities.order import Order, Recipient
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.package_dimensions import PackageDimensions
from src.infrastructure.models.order_model import OrderModel

class OrderMapper:
    
    def to_entity(self, model: Optional[OrderModel]) -> Optional[Order]:
        if not model:
            return None
        
        recipient = Recipient(
            name=model.recipient_name,
            phone=model.recipient_phone,
            email=model.recipient_email,
            address=model.recipient_address,
            city=model.recipient_city,
            country=model.recipient_country,
            postal_code=model.recipient_postal_code or ""
        )
        
        package_dimensions = PackageDimensions(
            length_cm=model.package_length_cm,
            width_cm=model.package_width_cm,
            height_cm=model.package_height_cm,
            weight_kg=model.package_weight_kg
        )
        
        return Order(
            id=OrderId(model.id),
            customer_id=CustomerId(model.customer_id),
            recipient=recipient,
            package_dimensions=package_dimensions,
            declared_value=model.declared_value,
            service_type=model.service_type,
            status=model.status,
            origin_address=model.origin_address,
            origin_city=model.origin_city,
            notes=model.notes or "",
            quoted_price=model.quoted_price,
            estimated_delivery_days=model.estimated_delivery_days,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def to_model(self, entity: Order) -> OrderModel:
        return OrderModel(
            id=entity.id.value,
            customer_id=entity.customer_id.value,
            recipient_name=entity.recipient.name,
            recipient_phone=entity.recipient.phone,
            recipient_email=entity.recipient.email,
            recipient_address=entity.recipient.address,
            recipient_city=entity.recipient.city,
            recipient_country=entity.recipient.country,
            recipient_postal_code=entity.recipient.postal_code,
            package_length_cm=entity.package_dimensions.length_cm,
            package_width_cm=entity.package_dimensions.width_cm,
            package_height_cm=entity.package_dimensions.height_cm,
            package_weight_kg=entity.package_dimensions.weight_kg,
            declared_value=entity.declared_value,
            service_type=entity.service_type,
            status=entity.status,
            origin_address=entity.origin_address,
            origin_city=entity.origin_city,
            notes=entity.notes,
            quoted_price=entity.quoted_price,
            estimated_delivery_days=entity.estimated_delivery_days,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )