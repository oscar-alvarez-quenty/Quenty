from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.domain.entities.reverse_logistics import ReturnReason, ReturnStatus, InspectionResult, RefundMethod


class ReturnRequestCreate(BaseModel):
    original_guide_id: str
    customer_id: str
    return_reason: str
    customer_comments: str
    contact_info: Dict[str, str]
    
    @validator('original_guide_id', 'customer_id', 'customer_comments')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('return_reason')
    def validate_return_reason(cls, v):
        valid_reasons = ['defective_product', 'not_as_described', 'wrong_item', 'damaged_shipping', 'changed_mind']
        if v.lower() not in valid_reasons:
            raise ValueError(f'Return reason must be one of: {valid_reasons}')
        return v.lower()
    
    @validator('contact_info')
    def validate_contact_info(cls, v):
        required_fields = ['phone', 'email']
        for field in required_fields:
            if field not in v or not v[field].strip():
                raise ValueError(f'{field} is required in contact info')
        return v


class ReturnItemAdd(BaseModel):
    return_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price_amount: float
    unit_price_currency: str
    item_reason: str
    condition_description: str
    photos_urls: Optional[List[str]] = None
    
    @validator('return_id', 'product_id', 'product_name', 'condition_description')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('quantity')
    def validate_quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('unit_price_amount')
    def validate_unit_price_positive(cls, v):
        if v < 0:
            raise ValueError('Unit price cannot be negative')
        return v
    
    @validator('unit_price_currency')
    def validate_currency_code(cls, v):
        valid_currencies = ['USD', 'COP', 'EUR']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.upper()
    
    @validator('item_reason')
    def validate_item_reason(cls, v):
        valid_reasons = ['defective_product', 'not_as_described', 'wrong_item', 'damaged_shipping', 'changed_mind']
        if v.lower() not in valid_reasons:
            raise ValueError(f'Item reason must be one of: {valid_reasons}')
        return v.lower()


class ReturnApprove(BaseModel):
    return_id: str
    approved_by: str
    pickup_date: Optional[datetime] = None
    special_instructions: Optional[str] = None
    
    @validator('return_id', 'approved_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('pickup_date')
    def validate_pickup_date_future(cls, v):
        if v is not None and v <= datetime.now():
            raise ValueError('Pickup date must be in the future')
        return v


class ReturnReject(BaseModel):
    return_id: str
    rejection_reason: str
    rejected_by: str
    
    @validator('return_id', 'rejection_reason', 'rejected_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class ReturnReceive(BaseModel):
    return_id: str
    center_id: str
    received_by: str
    packages_count: int
    initial_condition: str = "pending_inspection"
    receipt_notes: Optional[str] = None
    
    @validator('return_id', 'center_id', 'received_by', 'initial_condition')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('packages_count')
    def validate_packages_count_positive(cls, v):
        if v <= 0:
            raise ValueError('Packages count must be positive')
        return v
    
    @validator('initial_condition')
    def validate_initial_condition(cls, v):
        valid_conditions = ['good', 'damaged', 'pending_inspection', 'poor']
        if v.lower() not in valid_conditions:
            raise ValueError(f'Initial condition must be one of: {valid_conditions}')
        return v.lower()


class InspectionConduct(BaseModel):
    return_id: str
    inspector_id: str
    item_inspections: List[Dict[str, Any]]
    overall_notes: Optional[str] = None
    
    @validator('return_id', 'inspector_id')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('item_inspections')
    def validate_item_inspections_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one item inspection is required')
        
        required_fields = ['item_id', 'result', 'condition', 'disposition']
        for inspection in v:
            for field in required_fields:
                if field not in inspection:
                    raise ValueError(f'{field} is required in item inspection')
        return v


class RefundProcess(BaseModel):
    return_id: str
    refund_method: str
    processed_by: str
    partial_refund_amount: Optional[float] = None
    partial_refund_currency: Optional[str] = None
    
    @validator('return_id', 'processed_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('refund_method')
    def validate_refund_method(cls, v):
        valid_methods = ['original_payment', 'bank_transfer', 'wallet_credit', 'store_credit']
        if v.lower() not in valid_methods:
            raise ValueError(f'Refund method must be one of: {valid_methods}')
        return v.lower()
    
    @validator('partial_refund_amount')
    def validate_partial_refund_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Partial refund amount must be positive')
        return v
    
    @validator('partial_refund_currency')
    def validate_currency_code(cls, v):
        if v is None:
            return v
        valid_currencies = ['USD', 'COP', 'EUR']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.upper()


class InventoryProcess(BaseModel):
    return_id: str
    center_id: str
    processed_by: str
    
    @validator('return_id', 'center_id', 'processed_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class ReturnEligibilityCheck(BaseModel):
    return_id: str
    order_date: datetime
    delivery_date: datetime
    product_categories: List[str]
    
    @validator('return_id')
    def validate_return_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Return ID cannot be empty')
        return v.strip()
    
    @validator('delivery_date')
    def validate_delivery_after_order(cls, v, values):
        if 'order_date' in values and v < values['order_date']:
            raise ValueError('Delivery date must be after order date')
        return v
    
    @validator('product_categories')
    def validate_product_categories_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one product category is required')
        return v


class ReturnPolicyUpdate(BaseModel):
    policy_id: str
    return_window_days: Optional[int] = None
    eligible_reasons: Optional[List[str]] = None
    excluded_categories: Optional[List[str]] = None
    restocking_fee_percentage: Optional[float] = None
    
    @validator('policy_id')
    def validate_policy_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Policy ID cannot be empty')
        return v.strip()
    
    @validator('return_window_days')
    def validate_return_window_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Return window days must be positive')
        return v
    
    @validator('restocking_fee_percentage')
    def validate_restocking_fee_range(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Restocking fee percentage must be between 0 and 100')
        return v


class ReturnRequestResponse(BaseModel):
    return_id: str
    original_guide_id: str
    customer_id: str
    return_reason: str
    status: str
    created_at: datetime
    expected_return_value: Dict[str, Any]
    items_count: int
    is_within_deadline: bool
    refund_processed: bool
    pickup_date: Optional[datetime] = None
    received_at: Optional[datetime] = None
    refund_processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReturnItemResponse(BaseModel):
    item_id: str
    product_id: str
    product_name: str
    quantity_returned: int
    unit_price: Dict[str, Any]
    return_reason: str
    condition_description: str
    disposition_action: Optional[str] = None
    photos_urls: List[str]
    
    class Config:
        from_attributes = True


class InspectionReportResponse(BaseModel):
    inspection_id: str
    inspector_id: str
    inspection_date: datetime
    overall_result: str
    approved_items: int
    rejected_items: int
    refund_amount: Dict[str, Any]
    items_inspected: List[Dict[str, Any]]
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class LogisticsCenterResponse(BaseModel):
    center_id: str
    name: str
    address: str
    capacity: int
    current_inventory_count: int
    capacity_utilization: float
    processing_queue_size: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ReturnPolicyResponse(BaseModel):
    policy_id: str
    name: str
    description: str
    is_active: bool
    return_window_days: int
    eligible_reasons: List[str]
    excluded_categories: List[str]
    restocking_fee_percentage: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReturnAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_returns: int
    approved_returns: int
    rejected_returns: int
    refunded_returns: int
    approval_rate: float
    refund_rate: float
    total_refund_amount: float
    reason_distribution: Dict[str, int]
    average_processing_days: float
    
    class Config:
        from_attributes = True


class QualityIssueResponse(BaseModel):
    alert_id: str
    product_id: str
    total_returns: int
    quality_issue_rate: float
    lookback_days: int
    reason_distribution: Dict[str, int]
    recommended_action: str
    severity_level: str
    first_detected: datetime
    
    class Config:
        from_attributes = True


class ReturnEligibilityResponse(BaseModel):
    return_id: str
    is_eligible: bool
    eligibility_reason: Optional[str] = None
    policy_applied: str
    return_window_remaining_days: Optional[int] = None
    restrictions: List[str]
    
    class Config:
        from_attributes = True


class InventoryProcessingResponse(BaseModel):
    return_id: str
    center_id: str
    processing_summary: Dict[str, Any]
    restocked_items: int
    disposed_items: int
    items_for_repair: int
    total_value_recovered: Dict[str, Any]
    
    class Config:
        from_attributes = True