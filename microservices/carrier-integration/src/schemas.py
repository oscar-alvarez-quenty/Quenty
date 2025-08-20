from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class CarrierEnum(str, Enum):
    DHL = "DHL"
    FEDEX = "FedEx"
    UPS = "UPS"
    SERVIENTREGA = "Servientrega"
    INTERRAPIDISIMO = "Interrapidisimo"

class ServiceTypeEnum(str, Enum):
    EXPRESS = "express"
    STANDARD = "standard"
    ECONOMY = "economy"
    OVERNIGHT = "overnight"
    SAME_DAY = "same_day"

class Address(BaseModel):
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    company: Optional[str] = None
    contact_name: str
    contact_phone: str
    contact_email: Optional[str] = None

class Package(BaseModel):
    weight_kg: float
    length_cm: float
    width_cm: float
    height_cm: float
    declared_value: Optional[float] = None
    currency: str = "COP"
    description: Optional[str] = None

class QuoteRequest(BaseModel):
    carrier: Optional[CarrierEnum] = None
    origin: Address
    destination: Address
    packages: List[Package]
    service_type: Optional[ServiceTypeEnum] = None
    pickup_date: Optional[datetime] = None
    insurance_required: bool = False
    customs_value: Optional[float] = None

class QuoteResponse(BaseModel):
    quote_id: str
    carrier: CarrierEnum
    service_type: str
    amount: float
    currency: str
    estimated_days: int
    valid_until: datetime
    breakdown: Optional[Dict[str, float]] = None
    notes: Optional[List[str]] = None

class LabelRequest(BaseModel):
    carrier: CarrierEnum
    order_id: str
    quote_id: Optional[str] = None
    origin: Address
    destination: Address
    packages: List[Package]
    service_type: str
    reference_number: Optional[str] = None
    customs_documents: Optional[List[Dict]] = None

class LabelResponse(BaseModel):
    tracking_number: str
    carrier: CarrierEnum
    label_url: Optional[str] = None
    label_data: Optional[str] = None  # Base64 encoded
    awb_number: Optional[str] = None  # For international shipments
    barcode: Optional[str] = None
    estimated_delivery: datetime
    cost: float
    currency: str

class TrackingRequest(BaseModel):
    carrier: CarrierEnum
    tracking_number: str

class TrackingEvent(BaseModel):
    date: datetime
    status: str
    description: str
    location: Optional[str] = None
    details: Optional[Dict] = None

class TrackingResponse(BaseModel):
    tracking_number: str
    carrier: CarrierEnum
    status: str
    current_location: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    events: List[TrackingEvent]
    proof_of_delivery: Optional[Dict] = None

class PickupRequest(BaseModel):
    carrier: CarrierEnum
    pickup_date: datetime
    pickup_window_start: str  # HH:MM
    pickup_window_end: str  # HH:MM
    address: Address
    packages_count: int
    total_weight_kg: float
    special_instructions: Optional[str] = None
    tracking_numbers: Optional[List[str]] = None

class PickupResponse(BaseModel):
    confirmation_number: str
    carrier: CarrierEnum
    pickup_date: datetime
    pickup_window: str
    status: str
    cost: Optional[float] = None
    currency: Optional[str] = None

class CarrierCredentialCreate(BaseModel):
    environment: str = "production"
    credentials: Dict[str, Any]
    
    @validator('credentials')
    def validate_credentials(cls, v, values):
        # Basic validation - ensure required fields exist
        if not v:
            raise ValueError("Credentials cannot be empty")
        return v

class CarrierCredentialResponse(BaseModel):
    carrier: CarrierEnum
    environment: str
    is_active: bool
    validated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CarrierHealthResponse(BaseModel):
    carrier: CarrierEnum
    status: str
    latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
    last_check: datetime
    last_success: Optional[datetime] = None
    circuit_breaker_open: bool = False
    details: Optional[Dict] = None

class TRMResponse(BaseModel):
    rate: float
    from_currency: str = "COP"
    to_currency: str = "USD"
    valid_date: datetime
    source: str = "banco_republica"
    spread: float = 0.0
    effective_rate: float

class CurrencyConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    apply_spread: bool = True

class CurrencyConversionResponse(BaseModel):
    original_amount: float
    converted_amount: float
    from_currency: str
    to_currency: str
    exchange_rate: float
    spread_applied: float
    conversion_date: datetime

class FallbackConfigurationRequest(BaseModel):
    route: str
    carriers: List[CarrierEnum]
    is_active: bool = True

class FallbackConfigurationResponse(BaseModel):
    route: str
    priority_order: List[CarrierEnum]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None