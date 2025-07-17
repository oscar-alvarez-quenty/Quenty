from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.domain.entities.international_shipping import DocumentType, KYCStatus, CustomsStatus


class InternationalShipmentCreate(BaseModel):
    guide_id: str
    customer_id: str
    destination_country: str
    declared_value_amount: float
    declared_value_currency: str
    product_description: str
    product_category: str
    weight_kg: float
    
    @validator('guide_id', 'customer_id', 'destination_country', 'product_description', 'product_category')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('declared_value_amount', 'weight_kg')
    def validate_positive_amounts(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('declared_value_currency')
    def validate_currency_code(cls, v):
        valid_currencies = ['USD', 'COP', 'EUR', 'GBP']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.upper()


class KYCValidationStart(BaseModel):
    customer_id: str
    provider: str = "truora"
    
    @validator('customer_id', 'provider')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class KYCDocumentSubmit(BaseModel):
    kyc_id: str
    document_type: str
    file_url: str
    
    @validator('kyc_id', 'document_type', 'file_url')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class KYCValidationApprove(BaseModel):
    kyc_id: str
    approved_by: str
    validation_score: float
    risk_level: str
    expiry_months: int = 12
    
    @validator('kyc_id', 'approved_by', 'risk_level')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('validation_score')
    def validate_score_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Validation score must be between 0 and 100')
        return v
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        valid_levels = ['low', 'medium', 'high']
        if v.lower() not in valid_levels:
            raise ValueError(f'Risk level must be one of: {valid_levels}')
        return v.lower()
    
    @validator('expiry_months')
    def validate_expiry_months_positive(cls, v):
        if v <= 0:
            raise ValueError('Expiry months must be positive')
        return v


class KYCValidationReject(BaseModel):
    kyc_id: str
    rejection_reasons: List[str]
    
    @validator('kyc_id')
    def validate_kyc_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('KYC ID cannot be empty')
        return v.strip()
    
    @validator('rejection_reasons')
    def validate_rejection_reasons_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one rejection reason is required')
        for reason in v:
            if not reason or not reason.strip():
                raise ValueError('Rejection reasons cannot be empty')
        return [reason.strip() for reason in v]


class CustomsDeclarationCreate(BaseModel):
    shipment_id: str
    product_description: str
    product_category: str
    quantity: int
    weight_kg: float
    country_of_origin: str
    
    @validator('shipment_id', 'product_description', 'product_category', 'country_of_origin')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('quantity')
    def validate_quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('weight_kg')
    def validate_weight_positive(cls, v):
        if v <= 0:
            raise ValueError('Weight must be positive')
        return v


class DocumentUpload(BaseModel):
    shipment_id: str
    document_type: str
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('shipment_id', 'document_type')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class InternationalShipmentResponse(BaseModel):
    shipment_id: str
    guide_id: str
    customer_id: str
    destination_country: str
    declared_value: Dict[str, Any]
    product_description: str
    product_category: str
    weight_kg: float
    customs_status: str
    compliance_status: str
    is_ready_for_shipping: bool
    missing_documents: List[str]
    created_at: datetime
    estimated_customs_clearance_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class KYCValidationResponse(BaseModel):
    kyc_id: str
    customer_id: str
    provider: str
    status: str
    created_at: datetime
    expiry_date: Optional[datetime] = None
    validation_score: Optional[float] = None
    risk_level: str
    is_valid_for_international_shipping: bool
    documents_submitted: List[Dict[str, Any]]
    rejection_reasons: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class CustomsDeclarationResponse(BaseModel):
    declaration_id: str
    guide_id: str
    declared_value: Dict[str, Any]
    product_description: str
    product_category: str
    quantity: int
    weight_kg: float
    country_of_origin: str
    hs_code: Optional[str] = None
    customs_duties: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class InternationalDocumentResponse(BaseModel):
    document_id: str
    guide_id: str
    document_type: str
    file_url: Optional[str] = None
    is_translated: bool
    validation_status: str
    requires_translation: bool
    translated_file_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShippingRestrictionResponse(BaseModel):
    restriction_id: str
    destination_country: str
    product_category: str
    restriction_level: str
    required_documents: List[str]
    max_value: Optional[Dict[str, Any]] = None
    max_weight_kg: Optional[float] = None
    estimated_customs_days: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ShipmentStatusResponse(BaseModel):
    shipment_id: str
    guide_id: str
    destination_country: str
    kyc_status: str
    customs_status: str
    compliance_status: str
    documents_submitted: int
    documents_required: int
    missing_documents: List[str]
    ready_for_shipping: bool
    total_international_costs: Dict[str, Any]
    estimated_delivery_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShipmentReadinessResponse(BaseModel):
    shipment_id: str
    is_ready: bool
    readiness_percentage: float
    missing_requirements: List[str]
    kyc_validation_status: str
    customs_declaration_status: str
    required_documents_status: str
    compliance_check_status: str
    
    class Config:
        from_attributes = True


class InternationalCostsResponse(BaseModel):
    shipment_id: str
    customs_fees: Dict[str, Any]
    insurance: Dict[str, Any]
    documentation_fees: Dict[str, Any]
    total_cost: Dict[str, Any]
    cost_breakdown: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True