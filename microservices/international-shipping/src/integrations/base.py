"""
Base carrier integration abstract class
Defines the interface that all carrier integrations must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class ShipmentStatus(str, Enum):
    """Standard shipment statuses across all carriers"""
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class TrackingEvent(BaseModel):
    """Standard tracking event model"""
    timestamp: datetime
    location: str
    status: ShipmentStatus
    description: str
    raw_status: Optional[str] = None  # Original carrier status


class ShippingRate(BaseModel):
    """Standard shipping rate response"""
    carrier: str
    service_type: str
    base_rate: float
    weight_rate: float
    fuel_surcharge: float
    insurance_rate: float
    total_cost: float
    currency: str
    transit_days: int
    valid_until: datetime
    additional_fees: Optional[Dict[str, float]] = {}


class ShipmentRequest(BaseModel):
    """Standard shipment creation request"""
    origin_address: Dict[str, str]
    destination_address: Dict[str, str]
    weight_kg: float
    length_cm: float
    width_cm: float
    height_cm: float
    value: float
    currency: str
    description: str
    reference_number: Optional[str] = None
    insurance_required: bool = False
    signature_required: bool = False


class ShipmentResponse(BaseModel):
    """Standard shipment creation response"""
    tracking_number: str
    carrier: str
    service_type: str
    label_url: str
    label_format: str
    estimated_delivery: datetime
    total_cost: float
    currency: str
    reference_number: Optional[str] = None


class CarrierIntegrationBase(ABC):
    """Abstract base class for carrier integrations"""
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None, sandbox: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.base_url = self._get_base_url()
    
    @abstractmethod
    def _get_base_url(self) -> str:
        """Get the base URL for the carrier API"""
        pass
    
    @abstractmethod
    async def calculate_rates(
        self,
        origin_country: str,
        destination_country: str,
        weight_kg: float,
        length_cm: float,
        width_cm: float,
        height_cm: float,
        value: float,
        currency: str = "USD"
    ) -> List[ShippingRate]:
        """Calculate shipping rates for given parameters"""
        pass
    
    @abstractmethod
    async def create_shipment(self, request: ShipmentRequest) -> ShipmentResponse:
        """Create a shipment and generate shipping label"""
        pass
    
    @abstractmethod
    async def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """Track a shipment by tracking number"""
        pass
    
    @abstractmethod
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel a shipment"""
        pass
    
    @abstractmethod
    async def validate_address(self, address: Dict[str, str]) -> Dict[str, Any]:
        """Validate a shipping address"""
        pass
    
    def _normalize_status(self, carrier_status: str) -> ShipmentStatus:
        """Normalize carrier-specific status to standard status"""
        # This will be overridden by each carrier implementation
        return ShipmentStatus.IN_TRANSIT