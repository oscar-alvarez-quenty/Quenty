from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.domain.entities.microcredit import ApplicationStatus, MicrocreditStatus, PaymentStatus


class MicrocreditApplicationCreate(BaseModel):
    customer_id: str
    requested_amount: float
    requested_currency: str
    purpose: str
    monthly_income_amount: Optional[float] = None
    monthly_income_currency: Optional[str] = None
    employment_type: str = "self_employed"
    business_description: Optional[str] = None
    
    @validator('customer_id', 'purpose', 'employment_type')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('requested_amount')
    def validate_requested_amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Requested amount must be positive')
        return v
    
    @validator('requested_currency', 'monthly_income_currency')
    def validate_currency_code(cls, v):
        if v is None:
            return v
        valid_currencies = ['USD', 'COP', 'EUR']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.upper()
    
    @validator('monthly_income_amount')
    def validate_monthly_income_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Monthly income must be positive')
        return v
    
    @validator('employment_type')
    def validate_employment_type(cls, v):
        valid_types = ['employed', 'self_employed', 'unemployed', 'student']
        if v.lower() not in valid_types:
            raise ValueError(f'Employment type must be one of: {valid_types}')
        return v.lower()


class ApplicationEvaluate(BaseModel):
    application_id: str
    order_date: datetime
    delivery_date: datetime
    product_categories: List[str]
    
    @validator('application_id')
    def validate_application_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Application ID cannot be empty')
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


class ApplicationApprove(BaseModel):
    application_id: str
    approved_amount: float
    approved_currency: str
    interest_rate: float
    term_months: int
    approved_by: str
    
    @validator('application_id', 'approved_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('approved_amount')
    def validate_approved_amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Approved amount must be positive')
        return v
    
    @validator('approved_currency')
    def validate_currency_code(cls, v):
        valid_currencies = ['USD', 'COP', 'EUR']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.upper()
    
    @validator('interest_rate')
    def validate_interest_rate_range(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Interest rate must be between 0 and 100')
        return v
    
    @validator('term_months')
    def validate_term_months_positive(cls, v):
        if v <= 0:
            raise ValueError('Term months must be positive')
        return v


class ApplicationReject(BaseModel):
    application_id: str
    rejection_reasons: List[str]
    rejected_by: str
    
    @validator('application_id', 'rejected_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('rejection_reasons')
    def validate_rejection_reasons_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one rejection reason is required')
        for reason in v:
            if not reason or not reason.strip():
                raise ValueError('Rejection reasons cannot be empty')
        return [reason.strip() for reason in v]


class MicrocreditDisburse(BaseModel):
    microcredit_id: str
    disbursement_method: str = "wallet"
    
    @validator('microcredit_id', 'disbursement_method')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('disbursement_method')
    def validate_disbursement_method(cls, v):
        valid_methods = ['wallet', 'bank_transfer', 'cash']
        if v.lower() not in valid_methods:
            raise ValueError(f'Disbursement method must be one of: {valid_methods}')
        return v.lower()


class PaymentProcess(BaseModel):
    microcredit_id: str
    payment_amount: float
    payment_currency: str
    payment_method: str
    reference_number: Optional[str] = None
    
    @validator('microcredit_id', 'payment_method')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('payment_amount')
    def validate_payment_amount_positive(cls, v):
        if v <= 0:
            raise ValueError('Payment amount must be positive')
        return v
    
    @validator('payment_currency')
    def validate_currency_code(cls, v):
        valid_currencies = ['USD', 'COP', 'EUR']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.upper()
    
    @validator('payment_method')
    def validate_payment_method(cls, v):
        valid_methods = ['bank_transfer', 'cash', 'wallet', 'credit_card']
        if v.lower() not in valid_methods:
            raise ValueError(f'Payment method must be one of: {valid_methods}')
        return v.lower()


class CreditLimitUpdate(BaseModel):
    customer_id: str
    new_limit_amount: float
    new_limit_currency: str
    reason: str
    approved_by: str
    
    @validator('customer_id', 'reason', 'approved_by')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('new_limit_amount')
    def validate_new_limit_positive(cls, v):
        if v < 0:
            raise ValueError('Credit limit cannot be negative')
        return v
    
    @validator('new_limit_currency')
    def validate_currency_code(cls, v):
        valid_currencies = ['USD', 'COP', 'EUR']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {valid_currencies}')
        return v.upper()


class MicrocreditApplicationResponse(BaseModel):
    application_id: str
    customer_id: str
    requested_amount: Dict[str, Any]
    purpose: str
    status: str
    created_at: datetime
    credit_score: Optional[int] = None
    risk_assessment: Optional[str] = None
    rejection_reasons: Optional[List[str]] = None
    approved_amount: Optional[Dict[str, Any]] = None
    interest_rate: Optional[float] = None
    term_months: Optional[int] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MicrocreditResponse(BaseModel):
    microcredit_id: str
    customer_id: str
    principal_amount: Dict[str, Any]
    interest_rate: float
    term_months: int
    status: str
    created_at: datetime
    disbursement_date: Optional[datetime] = None
    disbursement_method: Optional[str] = None
    outstanding_balance: Dict[str, Any]
    total_paid: Dict[str, Any]
    payments_count: int
    monthly_payment: Dict[str, Any]
    is_overdue: bool
    days_overdue: int
    
    class Config:
        from_attributes = True


class CreditProfileResponse(BaseModel):
    customer_id: str
    credit_score: int
    credit_limit: Dict[str, Any]
    current_debt: Dict[str, Any]
    available_credit: Dict[str, Any]
    payment_history_score: float
    risk_category: str
    utilization_ratio: float
    created_at: datetime
    last_updated_score: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    payment_id: str
    microcredit_id: str
    amount: Dict[str, Any]
    payment_date: datetime
    payment_method: str
    status: str
    is_late_payment: bool
    days_late: int
    transaction_reference: Optional[str] = None
    late_fee: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CreditScoringResponse(BaseModel):
    application_id: str
    credit_score: int
    risk_level: str
    recommendation: str
    scoring_factors: Dict[str, float]
    model_version: str
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class PaymentScheduleResponse(BaseModel):
    microcredit_id: str
    schedule: List[Dict[str, Any]]
    total_payments: int
    total_interest: Dict[str, Any]
    total_amount: Dict[str, Any]
    
    class Config:
        from_attributes = True


class MicrocreditAnalyticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_applications: int
    approved_applications: int
    rejected_applications: int
    approval_rate: float
    total_disbursed: Dict[str, Any]
    total_collected: Dict[str, Any]
    overdue_amount: Dict[str, Any]
    default_rate: float
    
    class Config:
        from_attributes = True