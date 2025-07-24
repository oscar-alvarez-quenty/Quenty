from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from enum import Enum

# Enums
class FranchiseStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended" 
    TERMINATED = "terminated"
    ON_HOLD = "on_hold"

class ContractStatus(str, Enum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"

class TerritoryStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    RESTRICTED = "restricted"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIAL = "partial"
    FAILED = "failed"

# Base schemas
class FranchiseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    business_name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    
    # Franchisee Information
    franchisee_name: str = Field(..., min_length=1, max_length=500)
    franchisee_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    franchisee_phone: Optional[str] = Field(None, max_length=50)
    franchisee_id: Optional[str] = None
    
    # Location Information
    address: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    territory_code: str = Field(..., min_length=1, max_length=50)
    
    # Geographic Coordinates (optional)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    
    # Financial Information
    initial_fee: Optional[Decimal] = Field(0, ge=0)
    royalty_rate: Optional[Decimal] = Field(0.05, ge=0, le=1)
    marketing_fee_rate: Optional[Decimal] = Field(0.02, ge=0, le=1)

class FranchiseCreate(FranchiseBase):
    # Contract Information (optional during creation)
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_terms: Optional[Dict[str, Any]] = {}
    
    # Operational Details (optional during creation)
    operational_hours: Optional[Dict[str, Any]] = {}
    services_offered: Optional[List[str]] = []
    equipment_list: Optional[List[str]] = []

class FranchiseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    business_name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    
    franchisee_name: Optional[str] = Field(None, min_length=1, max_length=500)
    franchisee_email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    franchisee_phone: Optional[str] = Field(None, max_length=50)
    
    address: Optional[str] = Field(None, min_length=1)
    city: Optional[str] = Field(None, min_length=1, max_length=255)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    
    status: Optional[FranchiseStatus] = None
    opening_date: Optional[date] = None
    
    # Performance Updates
    monthly_revenue: Optional[Decimal] = Field(None, ge=0)
    customer_count: Optional[int] = Field(None, ge=0)
    order_count: Optional[int] = Field(None, ge=0)
    
    # Operational Updates
    staff_count: Optional[int] = Field(None, ge=0)
    operational_hours: Optional[Dict[str, Any]] = None
    services_offered: Optional[List[str]] = None
    equipment_list: Optional[List[str]] = None

class FranchiseResponse(FranchiseBase):
    id: int
    franchise_id: str
    status: FranchiseStatus
    opening_date: Optional[date] = None
    closure_date: Optional[date] = None
    
    # Performance Metrics
    monthly_revenue: Decimal
    total_revenue: Decimal
    customer_count: int
    order_count: int
    performance_score: Decimal
    
    # Contract Information
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    
    # Operational Details
    staff_count: int
    operational_hours: Optional[Dict[str, Any]] = None
    services_offered: List[str]
    equipment_list: List[str]
    
    # Support and Training
    training_completed: bool
    training_completion_date: Optional[date] = None
    support_level: str
    
    # Compliance
    last_audit_date: Optional[date] = None
    audit_score: Decimal
    compliance_status: str
    quality_certifications: List[str]
    
    # System Fields
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Contract schemas
class ContractBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    contract_type: str = Field("standard", max_length=50)
    
    # Legal Information
    legal_entity: Optional[str] = Field(None, max_length=500)
    governing_law: Optional[str] = Field(None, max_length=100)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    
    # Terms
    start_date: date
    end_date: date
    renewal_terms: Optional[Dict[str, Any]] = {}
    termination_clauses: Optional[Dict[str, Any]] = {}
    
    # Financial Terms
    initial_fee: Decimal = Field(..., ge=0)
    royalty_rate: Decimal = Field(..., ge=0, le=1)
    marketing_fee_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    minimum_performance: Optional[Dict[str, Any]] = {}

class ContractCreate(ContractBase):
    franchise_id: int

class ContractResponse(ContractBase):
    id: int
    contract_id: str
    franchise_id: int
    status: ContractStatus
    
    # Document Information
    contract_document_url: Optional[str] = None
    signed_document_url: Optional[str] = None
    signature_date: Optional[datetime] = None
    signed_by: Optional[str] = None
    witness_name: Optional[str] = None
    witness_signature_date: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Territory schemas
class TerritoryBase(BaseModel):
    territory_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    
    country: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=255)
    region: Optional[str] = Field(None, max_length=255)
    
    # Boundary and Area
    boundary_coordinates: Optional[Dict[str, Any]] = None  # GeoJSON
    area_size: Optional[Decimal] = Field(None, ge=0)
    population: Optional[int] = Field(None, ge=0)
    population_density: Optional[Decimal] = Field(None, ge=0)
    
    # Market Information
    market_potential: Optional[str] = Field(None, pattern=r'^(high|medium|low)$')
    competition_level: Optional[str] = Field(None, pattern=r'^(high|medium|low)$')
    average_income: Optional[Decimal] = Field(None, ge=0)
    demographic_profile: Optional[Dict[str, Any]] = {}

class TerritoryCreate(TerritoryBase):
    pass

class TerritoryResponse(TerritoryBase):
    id: int
    status: TerritoryStatus
    reserved_until: Optional[datetime] = None
    reserved_by: Optional[str] = None
    
    # Assignment Information
    assigned_franchise_id: Optional[int] = None
    assignment_date: Optional[date] = None
    exclusivity_radius: Optional[Decimal] = None
    
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    payment_type: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., ge=0)
    currency: str = Field("USD", max_length=3)
    
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    due_date: date
    
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_reference: Optional[str] = Field(None, max_length=255)

class PaymentCreate(PaymentBase):
    franchise_id: int

class PaymentResponse(PaymentBase):
    id: int
    payment_id: str
    franchise_id: int
    status: PaymentStatus
    
    paid_date: Optional[datetime] = None
    paid_amount: Decimal
    transaction_id: Optional[str] = None
    
    days_overdue: int
    late_fee: Decimal
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Performance schemas
class PerformanceBase(BaseModel):
    period_start: date
    period_end: date
    period_type: str = Field(..., pattern=r'^(daily|weekly|monthly|quarterly|annual)$')
    
    # Financial Metrics
    revenue: Optional[Decimal] = Field(0, ge=0)
    profit: Optional[Decimal] = Field(0)
    expenses: Optional[Decimal] = Field(0, ge=0)
    
    # Operational Metrics
    order_count: Optional[int] = Field(0, ge=0)
    customer_count: Optional[int] = Field(0, ge=0)
    new_customers: Optional[int] = Field(0, ge=0)
    repeat_customers: Optional[int] = Field(0, ge=0)
    average_order_value: Optional[Decimal] = Field(0, ge=0)
    
    # Service Metrics
    service_quality_score: Optional[Decimal] = Field(0, ge=0, le=100)
    customer_satisfaction: Optional[Decimal] = Field(0, ge=0, le=100)
    delivery_performance: Optional[Decimal] = Field(0, ge=0, le=100)
    complaint_count: Optional[int] = Field(0, ge=0)
    
    # Staff Metrics
    staff_count: Optional[int] = Field(0, ge=0)
    staff_turnover_rate: Optional[Decimal] = Field(0, ge=0, le=100)

class PerformanceCreate(PerformanceBase):
    franchise_id: int

class PerformanceResponse(PerformanceBase):
    id: int
    franchise_id: int
    
    # Additional calculated metrics
    royalty_paid: Decimal
    marketing_fee_paid: Decimal
    resolution_rate: Decimal
    training_completion_rate: Decimal
    
    # Goals and Performance
    revenue_target: Optional[Decimal] = None
    order_target: Optional[int] = None
    customer_target: Optional[int] = None
    targets_met: int
    
    performance_score: Decimal
    performance_grade: Optional[str] = None
    ranking: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Audit schemas
class AuditBase(BaseModel):
    audit_type: str = Field(..., min_length=1, max_length=50)
    audit_date: date
    auditor_name: str = Field(..., min_length=1, max_length=255)
    auditor_id: Optional[str] = None
    
    areas_audited: Optional[List[str]] = []
    checklist_used: Optional[str] = None
    duration_hours: Optional[Decimal] = Field(None, ge=0)

class AuditCreate(AuditBase):
    franchise_id: int

class AuditUpdate(BaseModel):
    # Results
    overall_score: Optional[Decimal] = Field(None, ge=0, le=100)
    grade: Optional[str] = Field(None, pattern=r'^[ABCDF]$')
    pass_status: Optional[bool] = None
    
    # Findings
    findings: Optional[List[Dict[str, Any]]] = []
    violations: Optional[List[Dict[str, Any]]] = []
    recommendations: Optional[List[Dict[str, Any]]] = []
    
    # Issues Count
    critical_issues: Optional[int] = Field(None, ge=0)
    major_issues: Optional[int] = Field(None, ge=0)
    minor_issues: Optional[int] = Field(None, ge=0)
    compliant_items: Optional[int] = Field(None, ge=0)
    
    # Action Plan
    corrective_actions: Optional[List[Dict[str, Any]]] = []
    action_deadline: Optional[date] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None
    
    audit_status: Optional[str] = None
    report_url: Optional[str] = None

class AuditResponse(AuditBase):
    id: int
    audit_id: str
    franchise_id: int
    
    # Results
    overall_score: Decimal
    grade: Optional[str] = None
    pass_status: bool
    
    # Findings
    findings: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    # Issues
    critical_issues: int
    major_issues: int
    minor_issues: int
    compliant_items: int
    
    # Action Plan
    corrective_actions: List[Dict[str, Any]]
    action_deadline: Optional[date] = None
    follow_up_required: bool
    follow_up_date: Optional[date] = None
    
    audit_status: str
    report_url: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# List schemas
class PaginatedFranchises(BaseModel):
    franchises: List[FranchiseResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

class PaginatedTerritories(BaseModel):
    territories: List[TerritoryResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

class PaginatedPayments(BaseModel):
    payments: List[PaymentResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

# Status update schemas
class StatusUpdate(BaseModel):
    status: FranchiseStatus
    reason: Optional[str] = None
    effective_date: Optional[date] = None

# Health check schema
class HealthCheck(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]

# Error response schema
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime