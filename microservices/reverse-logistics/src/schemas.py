from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from .models import ReturnStatus, ReturnReason, ReturnType, DisposalMethod, InspectionResult

# Base schemas
class ReturnItemBase(BaseModel):
    """Base schema for return items"""
    item_id: str = Field(..., min_length=1)
    item_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = Field(..., ge=1)
    unit_price: Optional[Decimal] = None
    return_reason: Optional[str] = None
    reason_details: Optional[str] = None

class ReturnItemCreate(ReturnItemBase):
    """Schema for creating return items"""
    photos: Optional[List[str]] = []

class ReturnItemUpdate(BaseModel):
    """Schema for updating return items"""
    condition_received: Optional[str] = None
    inspection_result: Optional[str] = None
    resale_value: Optional[Decimal] = None
    refund_eligible: Optional[bool] = None
    refund_amount: Optional[Decimal] = None
    exchange_item_id: Optional[str] = None
    exchange_quantity: Optional[int] = None

class ReturnItemResponse(ReturnItemBase):
    """Schema for return item response"""
    model_config = ConfigDict(from_attributes=True)
    
    return_item_id: str
    condition_received: Optional[str] = None
    photos: List[str] = []
    inspection_result: Optional[str] = None
    resale_value: Optional[Decimal] = None
    refund_eligible: bool = True
    refund_amount: Optional[Decimal] = None
    exchange_item_id: Optional[str] = None
    exchange_quantity: Optional[int] = None
    created_at: datetime
    updated_at: datetime

# Return schemas
class ReturnBase(BaseModel):
    """Base schema for returns"""
    original_order_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    return_type: ReturnType = ReturnType.RETURN
    return_reason: ReturnReason
    description: str = Field(..., min_length=1)
    preferred_resolution: str = Field(..., pattern="^(refund|exchange|store_credit)$")

class ReturnCreate(ReturnBase):
    """Schema for creating a return"""
    items: List[ReturnItemCreate] = Field(..., min_items=1)
    photos: Optional[List[str]] = []
    return_address: Optional[str] = None

class ReturnUpdate(BaseModel):
    """Schema for updating a return"""
    description: Optional[str] = None
    preferred_resolution: Optional[str] = None
    pickup_address: Optional[str] = None
    return_address: Optional[str] = None
    customer_action_required: Optional[str] = None
    requires_customer_action: Optional[bool] = None

class ReturnResponse(ReturnBase):
    """Schema for return response"""
    model_config = ConfigDict(from_attributes=True)
    
    return_id: str
    status: ReturnStatus
    return_authorization_number: str
    
    # Financial Information
    original_order_value: Optional[Decimal] = None
    estimated_refund_amount: Optional[Decimal] = None
    actual_refund_amount: Optional[Decimal] = None
    return_shipping_cost: Decimal = Decimal("0")
    processing_fee: Decimal = Decimal("0")
    
    # Shipping Information
    pickup_address: Optional[str] = None
    return_address: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    
    # Timeline
    estimated_pickup_date: Optional[date] = None
    actual_pickup_date: Optional[date] = None
    estimated_processing_time: Optional[str] = None
    expires_at: datetime
    
    # Processing Information
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    processing_notes: Optional[str] = None
    
    # Additional Data
    photos: List[str] = []
    customer_action_required: Optional[str] = None
    requires_customer_action: bool = False
    
    # Items
    items: List[ReturnItemResponse] = []
    
    # System Fields
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

# Status and processing schemas
class StatusUpdate(BaseModel):
    """Schema for status updates"""
    status: ReturnStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None

class ReturnApproval(BaseModel):
    """Schema for return approval"""
    approval_notes: Optional[str] = None
    estimated_pickup_date: Optional[date] = None
    pickup_address: Optional[str] = None

class ReturnRejection(BaseModel):
    """Schema for return rejection"""
    rejection_reason: str = Field(..., min_length=1)
    detailed_explanation: Optional[str] = None
    appeal_available: bool = True

class PickupSchedule(BaseModel):
    """Schema for pickup scheduling"""
    pickup_date: date
    time_window: str = Field(..., pattern="^(morning|afternoon|evening|all_day)$")
    pickup_address: Optional[str] = None
    special_instructions: Optional[str] = None

# Inspection schemas
class InspectionReportCreate(BaseModel):
    """Schema for creating inspection report"""
    item_id: str = Field(..., min_length=1)
    inspector_id: str = Field(..., min_length=1)
    overall_condition: InspectionResult
    functional_status: str = Field(..., pattern="^(working|partially_working|non_functional)$")
    cosmetic_condition: str = Field(..., pattern="^(excellent|good|fair|poor)$")
    completeness: str = Field(..., pattern="^(complete|missing_accessories|incomplete)$")
    defects_found: List[str] = []
    photos: List[str] = []
    notes: str = ""
    current_market_value: Optional[Decimal] = None
    resale_value: Optional[Decimal] = None
    salvage_value: Optional[Decimal] = None
    recommended_action: str = Field(..., pattern="^(full_refund|partial_refund|exchange|reject|repair)$")
    disposition_recommendation: DisposalMethod = DisposalMethod.RESELL
    repair_cost_estimate: Optional[Decimal] = None
    refurbishment_cost: Optional[Decimal] = None

class InspectionReportResponse(BaseModel):
    """Schema for inspection report response"""
    model_config = ConfigDict(from_attributes=True)
    
    inspection_id: str
    item_id: str
    inspector_id: str
    inspector_name: Optional[str] = None
    inspection_date: datetime
    overall_condition: str
    functional_status: str
    cosmetic_condition: str
    completeness: str
    defects_found: List[str] = []
    photos: List[str] = []
    notes: str
    original_value: Optional[Decimal] = None
    current_market_value: Optional[Decimal] = None
    resale_value: Optional[Decimal] = None
    salvage_value: Optional[Decimal] = None
    recommended_action: str
    disposition_recommendation: str
    repair_cost_estimate: Optional[Decimal] = None
    refurbishment_cost: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

# Processing schemas
class ReturnProcessing(BaseModel):
    """Schema for return processing"""
    processing_action: str = Field(..., pattern="^(approve_full_refund|approve_partial_refund|approve_exchange|reject)$")
    refund_amount: Optional[Decimal] = None
    exchange_item_id: Optional[str] = None
    exchange_quantity: Optional[int] = None
    processing_notes: str = ""
    processing_fee: Optional[Decimal] = None
    requires_customer_action: bool = False
    customer_action_required: Optional[str] = None

class ReturnProcessingResponse(BaseModel):
    """Schema for return processing response"""
    return_id: str
    processing_action: str
    status: ReturnStatus
    refund_amount: Optional[Decimal] = None
    exchange_item_id: Optional[str] = None
    exchange_quantity: Optional[int] = None
    processing_fee: Optional[Decimal] = None
    processed_at: datetime
    processing_notes: str
    expected_refund_time: Optional[str] = None
    requires_customer_action: bool = False
    customer_action_required: Optional[str] = None

# Disposal schemas
class DisposalRecordCreate(BaseModel):
    """Schema for creating disposal record"""
    item_id: str = Field(..., min_length=1)
    disposal_method: DisposalMethod
    disposal_date: date
    disposal_reason: Optional[str] = None
    disposal_value: Decimal = Decimal("0")
    disposal_cost: Decimal = Decimal("0")
    disposal_partner: Optional[str] = None
    partner_contact: Optional[str] = None
    partner_reference: Optional[str] = None
    environmental_impact: Optional[Dict[str, Any]] = {}
    sustainability_score: Optional[Decimal] = None
    carbon_footprint: Optional[Decimal] = None
    documentation_urls: List[str] = []
    certificates: List[str] = []

class DisposalRecordResponse(BaseModel):
    """Schema for disposal record response"""
    model_config = ConfigDict(from_attributes=True)
    
    disposal_id: str
    item_id: str
    disposal_method: str
    disposal_date: date
    disposal_reason: Optional[str] = None
    disposal_value: Decimal
    disposal_cost: Decimal
    net_recovery: Decimal
    disposal_partner: Optional[str] = None
    partner_contact: Optional[str] = None
    partner_reference: Optional[str] = None
    environmental_impact: Dict[str, Any] = {}
    sustainability_score: Optional[Decimal] = None
    carbon_footprint: Optional[Decimal] = None
    documentation_urls: List[str] = []
    certificates: List[str] = []
    processed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Analytics schemas
class ReturnsSummary(BaseModel):
    """Schema for returns summary analytics"""
    period: Dict[str, str]
    total_returns: int
    return_rate: float
    returns_by_reason: Dict[str, int]
    returns_by_status: Dict[str, int]
    financial_impact: Dict[str, float]
    processing_metrics: Dict[str, float]

class DispositionInventory(BaseModel):
    """Schema for disposition inventory"""
    pending_disposition: List[Dict[str, Any]]
    disposition_options: Dict[str, Dict[str, Any]]

# Pagination schemas
class PaginatedReturns(BaseModel):
    """Schema for paginated returns"""
    returns: List[ReturnResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

class PaginatedInspections(BaseModel):
    """Schema for paginated inspections"""
    inspections: List[InspectionReportResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

class PaginatedDisposals(BaseModel):
    """Schema for paginated disposals"""
    disposals: List[DisposalRecordResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

# Utility schemas
class HealthCheck(BaseModel):
    """Health check response schema"""
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    status_code: int
    timestamp: datetime
    request_id: Optional[str] = None

class BatchProcessRequest(BaseModel):
    """Schema for batch processing returns"""
    return_ids: List[str] = Field(..., min_items=1)
    processing_action: str = Field(..., pattern="^(approve_full_refund|approve_partial_refund|approve_exchange|reject)$")
    processing_notes: Optional[str] = None
    batch_name: Optional[str] = None

class BatchProcessResponse(BaseModel):
    """Schema for batch processing response"""
    batch_id: str
    batch_name: Optional[str] = None
    processed_count: int
    processing_action: str
    results: List[Dict[str, Any]]
    batch_completed_at: datetime
    success_count: int
    failure_count: int
    failures: List[Dict[str, str]] = []