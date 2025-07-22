from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Numeric, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime
from enum import Enum
import uuid

class FranchiseStatus(str, Enum):
    """Franchise status enumeration"""
    PENDING = "pending"
    ACTIVE = "active" 
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ON_HOLD = "on_hold"

class ContractStatus(str, Enum):
    """Contract status enumeration"""
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"

class TerritoryStatus(str, Enum):
    """Territory status enumeration"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    RESTRICTED = "restricted"

class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIAL = "partial"
    FAILED = "failed"

class Franchise(Base):
    """Franchise model for managing franchise locations"""
    __tablename__ = "franchises"
    
    id = Column(Integer, primary_key=True, index=True)
    franchise_id = Column(String(255), unique=True, index=True, default=lambda: f"FRAN-{str(uuid.uuid4())[:8].upper()}")
    
    # Basic Information
    name = Column(String(500), nullable=False)
    business_name = Column(String(500))
    description = Column(Text)
    
    # Franchisee Information
    franchisee_name = Column(String(500), nullable=False)
    franchisee_email = Column(String(255), nullable=False)
    franchisee_phone = Column(String(50))
    franchisee_id = Column(String(255))  # Reference to user ID from auth service
    
    # Location Information
    address = Column(Text, nullable=False)
    city = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20))
    territory_code = Column(String(50), nullable=False, index=True)
    
    # Geographic Coordinates
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    
    # Business Details
    status = Column(SQLEnum(FranchiseStatus), default=FranchiseStatus.PENDING, nullable=False)
    opening_date = Column(Date)
    closure_date = Column(Date, nullable=True)
    
    # Financial Information
    initial_fee = Column(Numeric(15, 2), default=0)
    royalty_rate = Column(Numeric(5, 4), default=0.05)  # 5% default
    marketing_fee_rate = Column(Numeric(5, 4), default=0.02)  # 2% default
    
    # Performance Metrics
    monthly_revenue = Column(Numeric(15, 2), default=0)
    total_revenue = Column(Numeric(15, 2), default=0)
    customer_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)
    performance_score = Column(Numeric(3, 2), default=0)  # 0-100
    
    # Contract Information
    contract_start_date = Column(Date)
    contract_end_date = Column(Date)
    contract_terms = Column(JSON)
    
    # Operational Details
    staff_count = Column(Integer, default=0)
    operational_hours = Column(JSON)  # Store hours in JSON format
    services_offered = Column(JSON, default=list)
    equipment_list = Column(JSON, default=list)
    
    # Support and Training
    training_completed = Column(Boolean, default=False)
    training_completion_date = Column(Date)
    support_level = Column(String(50), default="standard")  # standard, premium, enterprise
    
    # Compliance and Quality
    last_audit_date = Column(Date)
    audit_score = Column(Numeric(3, 2), default=0)
    compliance_status = Column(String(50), default="pending")
    quality_certifications = Column(JSON, default=list)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(255))
    updated_by = Column(String(255))
    
    # Relationships
    contracts = relationship("FranchiseContract", back_populates="franchise", cascade="all, delete-orphan")
    payments = relationship("FranchisePayment", back_populates="franchise", cascade="all, delete-orphan")
    performance_records = relationship("FranchisePerformance", back_populates="franchise", cascade="all, delete-orphan")
    audits = relationship("FranchiseAudit", back_populates="franchise", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Franchise(id={self.id}, name='{self.name}', status='{self.status}')>"

class FranchiseContract(Base):
    """Franchise contract management"""
    __tablename__ = "franchise_contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(String(255), unique=True, index=True, default=lambda: f"CONT-{str(uuid.uuid4())[:8].upper()}")
    franchise_id = Column(Integer, ForeignKey("franchises.id"), nullable=False)
    
    # Contract Details
    contract_type = Column(String(50), default="standard")  # standard, renewal, amendment
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Legal Information
    legal_entity = Column(String(500))
    governing_law = Column(String(100))
    jurisdiction = Column(String(100))
    
    # Terms and Conditions
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.DRAFT, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    renewal_terms = Column(JSON)
    termination_clauses = Column(JSON)
    
    # Financial Terms
    initial_fee = Column(Numeric(15, 2), nullable=False)
    royalty_rate = Column(Numeric(5, 4), nullable=False)
    marketing_fee_rate = Column(Numeric(5, 4))
    minimum_performance = Column(JSON)
    
    # Document Management
    contract_document_url = Column(String(500))
    signed_document_url = Column(String(500))
    signature_date = Column(DateTime)
    signed_by = Column(String(255))
    witness_name = Column(String(255))
    witness_signature_date = Column(DateTime)
    
    # System Fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(255))
    
    # Relationships
    franchise = relationship("Franchise", back_populates="contracts")
    
    def __repr__(self):
        return f"<FranchiseContract(id={self.id}, contract_id='{self.contract_id}', status='{self.status}')>"

class Territory(Base):
    """Territory management for franchise locations"""
    __tablename__ = "territories"
    
    id = Column(Integer, primary_key=True, index=True)
    territory_code = Column(String(50), unique=True, index=True, nullable=False)
    
    # Geographic Information
    name = Column(String(500), nullable=False)
    description = Column(Text)
    country = Column(String(100), nullable=False)
    state = Column(String(100))
    city = Column(String(255))
    region = Column(String(255))
    
    # Boundary Information
    boundary_coordinates = Column(JSON)  # GeoJSON polygon
    area_size = Column(Numeric(15, 4))  # Square kilometers
    population = Column(Integer)
    population_density = Column(Numeric(10, 2))
    
    # Market Information
    market_potential = Column(String(50))  # high, medium, low
    competition_level = Column(String(50))  # high, medium, low
    average_income = Column(Numeric(15, 2))
    demographic_profile = Column(JSON)
    
    # Territory Status
    status = Column(SQLEnum(TerritoryStatus), default=TerritoryStatus.AVAILABLE, nullable=False)
    reserved_until = Column(DateTime)
    reserved_by = Column(String(255))
    
    # Assignment Information
    assigned_franchise_id = Column(Integer, ForeignKey("franchises.id"), nullable=True)
    assignment_date = Column(Date)
    exclusivity_radius = Column(Numeric(10, 4))  # Kilometers
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    assigned_franchise = relationship("Franchise", foreign_keys=[assigned_franchise_id])
    
    def __repr__(self):
        return f"<Territory(code='{self.territory_code}', name='{self.name}', status='{self.status}')>"

class FranchisePayment(Base):
    """Franchise payment tracking (royalties, fees, etc.)"""
    __tablename__ = "franchise_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String(255), unique=True, index=True, default=lambda: f"PAY-{str(uuid.uuid4())[:8].upper()}")
    franchise_id = Column(Integer, ForeignKey("franchises.id"), nullable=False)
    
    # Payment Information
    payment_type = Column(String(50), nullable=False)  # initial_fee, royalty, marketing_fee, renewal_fee
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Payment Period (for recurring payments)
    period_start = Column(Date)
    period_end = Column(Date)
    due_date = Column(Date, nullable=False)
    
    # Status Information
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    paid_date = Column(DateTime)
    paid_amount = Column(Numeric(15, 2), default=0)
    
    # Payment Method
    payment_method = Column(String(50))  # bank_transfer, credit_card, check, etc.
    transaction_id = Column(String(255))
    payment_reference = Column(String(255))
    
    # Late Payment Tracking
    days_overdue = Column(Integer, default=0)
    late_fee = Column(Numeric(15, 2), default=0)
    
    # System Fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    processed_by = Column(String(255))
    
    # Relationships
    franchise = relationship("Franchise", back_populates="payments")
    
    def __repr__(self):
        return f"<FranchisePayment(id={self.id}, type='{self.payment_type}', amount={self.amount}, status='{self.status}')>"

class FranchisePerformance(Base):
    """Franchise performance tracking and metrics"""
    __tablename__ = "franchise_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    franchise_id = Column(Integer, ForeignKey("franchises.id"), nullable=False)
    
    # Reporting Period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, annual
    
    # Financial Metrics
    revenue = Column(Numeric(15, 2), default=0)
    profit = Column(Numeric(15, 2), default=0)
    expenses = Column(Numeric(15, 2), default=0)
    royalty_paid = Column(Numeric(15, 2), default=0)
    marketing_fee_paid = Column(Numeric(15, 2), default=0)
    
    # Operational Metrics
    order_count = Column(Integer, default=0)
    customer_count = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)
    repeat_customers = Column(Integer, default=0)
    average_order_value = Column(Numeric(15, 2), default=0)
    
    # Service Metrics
    service_quality_score = Column(Numeric(3, 2), default=0)
    customer_satisfaction = Column(Numeric(3, 2), default=0)
    delivery_performance = Column(Numeric(3, 2), default=0)
    complaint_count = Column(Integer, default=0)
    resolution_rate = Column(Numeric(3, 2), default=0)
    
    # Staff Metrics
    staff_count = Column(Integer, default=0)
    staff_turnover_rate = Column(Numeric(3, 2), default=0)
    training_completion_rate = Column(Numeric(3, 2), default=0)
    
    # Goals and Targets
    revenue_target = Column(Numeric(15, 2))
    order_target = Column(Integer)
    customer_target = Column(Integer)
    targets_met = Column(Integer, default=0)
    
    # Overall Performance
    performance_score = Column(Numeric(3, 2), default=0)  # 0-100
    performance_grade = Column(String(2))  # A, B, C, D, F
    ranking = Column(Integer)  # Ranking among all franchises
    
    # System Fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    franchise = relationship("Franchise", back_populates="performance_records")
    
    def __repr__(self):
        return f"<FranchisePerformance(franchise_id={self.franchise_id}, period='{self.period_start}-{self.period_end}', score={self.performance_score})>"

class FranchiseAudit(Base):
    """Franchise audit and compliance tracking"""
    __tablename__ = "franchise_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(255), unique=True, index=True, default=lambda: f"AUDIT-{str(uuid.uuid4())[:8].upper()}")
    franchise_id = Column(Integer, ForeignKey("franchises.id"), nullable=False)
    
    # Audit Information
    audit_type = Column(String(50), nullable=False)  # compliance, quality, financial, operational
    audit_date = Column(Date, nullable=False)
    auditor_name = Column(String(255), nullable=False)
    auditor_id = Column(String(255))
    
    # Audit Scope
    areas_audited = Column(JSON, default=list)  # List of areas checked
    checklist_used = Column(String(255))
    duration_hours = Column(Numeric(5, 2))
    
    # Results
    overall_score = Column(Numeric(3, 2), default=0)  # 0-100
    grade = Column(String(2))  # A, B, C, D, F
    pass_status = Column(Boolean, default=False)
    
    # Findings
    findings = Column(JSON, default=list)  # List of findings/issues
    violations = Column(JSON, default=list)  # Compliance violations
    recommendations = Column(JSON, default=list)  # Improvement recommendations
    
    # Compliance Status
    critical_issues = Column(Integer, default=0)
    major_issues = Column(Integer, default=0)
    minor_issues = Column(Integer, default=0)
    compliant_items = Column(Integer, default=0)
    
    # Action Plan
    corrective_actions = Column(JSON, default=list)
    action_deadline = Column(Date)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    
    # Status
    audit_status = Column(String(50), default="completed")  # scheduled, in_progress, completed, follow_up
    report_url = Column(String(500))
    
    # System Fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    franchise = relationship("Franchise", back_populates="audits")
    
    def __repr__(self):
        return f"<FranchiseAudit(audit_id='{self.audit_id}', type='{self.audit_type}', score={self.overall_score})>"