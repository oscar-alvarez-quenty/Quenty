from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from src.domain.entities.order import OrderStatus, ServiceType

class RecipientRequest(BaseModel):
    name: str
    phone: str
    email: str
    address: str
    city: str
    country: str = "Colombia"
    postal_code: Optional[str] = None
    
    @validator('name', 'phone', 'email', 'address', 'city')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class PackageDimensionsRequest(BaseModel):
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    weight_kg: Decimal
    
    @validator('length_cm', 'width_cm', 'height_cm', 'weight_kg')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Dimensions must be positive')
        return v

class OrderCreateRequest(BaseModel):
    customer_id: str
    recipient: RecipientRequest
    package_dimensions: PackageDimensionsRequest
    declared_value: Decimal = Decimal('0.00')
    service_type: ServiceType = ServiceType.NATIONAL
    origin_address: str
    origin_city: str
    notes: Optional[str] = None
    
    @validator('declared_value')
    def validate_declared_value(cls, v):
        if v < 0:
            raise ValueError('Declared value cannot be negative')
        return v

class OrderQuoteRequest(BaseModel):
    origin: str
    destination: str
    package_dimensions: PackageDimensionsRequest

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    recipient: dict
    package_dimensions: dict
    declared_value: Decimal
    service_type: ServiceType
    status: OrderStatus
    origin_address: str
    origin_city: str
    notes: Optional[str]
    quoted_price: Optional[Decimal]
    estimated_delivery_days: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderQuoteResponse(BaseModel):
    price: Decimal
    delivery_days: int
    billable_weight: Decimal

class GuideResponse(BaseModel):
    id: str
    order_id: str
    customer_id: str
    status: str
    logistics_operator: str
    barcode: str
    qr_code: str
    pickup_code: str
    created_at: datetime
    
    class Config:
        from_attributes = True