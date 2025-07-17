from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId

class GuideStatus(Enum):
    GENERATED = "generated"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    RETURNED = "returned"
    CANCELLED = "cancelled"

@dataclass
class Guide:
    id: GuideId = field(default_factory=GuideId.generate)
    order_id: OrderId = None
    customer_id: CustomerId = None
    status: GuideStatus = GuideStatus.GENERATED
    logistics_operator: str = ""
    barcode: str = ""
    qr_code: str = ""
    pickup_code: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    estimated_pickup_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.barcode:
            self.barcode = self._generate_barcode()
        if not self.qr_code:
            self.qr_code = self._generate_qr_code()
        if not self.pickup_code:
            self.pickup_code = self._generate_pickup_code()
    
    def _generate_barcode(self) -> str:
        return f"*{self.id.value}*"
    
    def _generate_qr_code(self) -> str:
        return f"QR_{self.id.value}"
    
    def _generate_pickup_code(self) -> str:
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def mark_picked_up(self) -> None:
        if self.status != GuideStatus.GENERATED:
            raise ValueError("Can only pick up generated guides")
        
        self.status = GuideStatus.PICKED_UP
        self.updated_at = datetime.utcnow()
    
    def mark_in_transit(self) -> None:
        if self.status != GuideStatus.PICKED_UP:
            raise ValueError("Can only mark in transit after pickup")
        
        self.status = GuideStatus.IN_TRANSIT
        self.updated_at = datetime.utcnow()
    
    def mark_out_for_delivery(self) -> None:
        if self.status != GuideStatus.IN_TRANSIT:
            raise ValueError("Can only mark out for delivery from in transit")
        
        self.status = GuideStatus.OUT_FOR_DELIVERY
        self.updated_at = datetime.utcnow()
    
    def mark_delivered(self) -> None:
        if self.status != GuideStatus.OUT_FOR_DELIVERY:
            raise ValueError("Can only deliver packages out for delivery")
        
        self.status = GuideStatus.DELIVERED
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        if self.status in [GuideStatus.DELIVERED, GuideStatus.RETURNED]:
            raise ValueError("Cannot cancel delivered or returned guides")
        
        self.status = GuideStatus.CANCELLED
        self.updated_at = datetime.utcnow()