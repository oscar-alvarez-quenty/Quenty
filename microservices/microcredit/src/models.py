from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

Base = declarative_base()

class CreditStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    PAID = "paid"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"

class CreditType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    INVENTORY = "inventory"
    EQUIPMENT = "equipment"
    EMERGENCY = "emergency"

class PaymentFrequency(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIAL = "partial"
    FAILED = "failed"

class CreditApplication(Base):
    """Credit application model"""
    __tablename__ = "credit_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(255), unique=True, index=True, nullable=False)
    customer_id = Column(String(255), nullable=False, index=True)  # Reference to Auth service
    
    # Application details
    credit_type = Column(String(50), nullable=False)
    requested_amount = Column(Numeric(15, 2), nullable=False)
    requested_term_months = Column(Integer, nullable=False)
    payment_frequency = Column(String(20), nullable=False)
    purpose = Column(Text)
    
    # Application status
    status = Column(String(50), default=CreditStatus.PENDING, nullable=False)
    approval_amount = Column(Numeric(15, 2))
    approval_term_months = Column(Integer)
    interest_rate = Column(Float)  # Annual percentage rate
    
    # Risk assessment
    risk_level = Column(String(20))
    credit_score = Column(Integer)
    debt_to_income_ratio = Column(Float)
    
    # Personal information
    monthly_income = Column(Numeric(15, 2))
    employment_status = Column(String(100))
    employment_years = Column(Float)
    existing_debts = Column(Numeric(15, 2), default=0)
    
    # Business information (if applicable)
    business_name = Column(String(255))
    business_type = Column(String(100))
    business_revenue_monthly = Column(Numeric(15, 2))
    business_years = Column(Float)
    
    # Decision information
    reviewed_by = Column(String(255))  # User ID who reviewed
    review_notes = Column(Text)
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    credit_accounts = relationship("CreditAccount", back_populates="application")
    documents = relationship("CreditDocument", back_populates="application", cascade="all, delete-orphan")

class CreditAccount(Base):
    """Active credit account"""
    __tablename__ = "credit_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(255), unique=True, index=True, nullable=False)
    application_id = Column(Integer, ForeignKey("credit_applications.id"), nullable=False)
    customer_id = Column(String(255), nullable=False, index=True)  # Reference to Auth service
    
    # Credit terms
    principal_amount = Column(Numeric(15, 2), nullable=False)
    interest_rate = Column(Float, nullable=False)  # Annual percentage rate
    term_months = Column(Integer, nullable=False)
    payment_frequency = Column(String(20), nullable=False)
    monthly_payment = Column(Numeric(15, 2), nullable=False)
    
    # Account status
    status = Column(String(50), default=CreditStatus.ACTIVE, nullable=False)
    current_balance = Column(Numeric(15, 2), nullable=False)
    total_paid = Column(Numeric(15, 2), default=0)
    total_interest_paid = Column(Numeric(15, 2), default=0)
    
    # Payment tracking
    next_payment_date = Column(Date, nullable=False)
    last_payment_date = Column(Date)
    payments_made = Column(Integer, default=0)
    payments_remaining = Column(Integer, nullable=False)
    days_overdue = Column(Integer, default=0)
    
    # Fees and penalties
    late_fees = Column(Numeric(15, 2), default=0)
    penalty_fees = Column(Numeric(15, 2), default=0)
    
    # Account dates
    disbursed_at = Column(DateTime)
    first_payment_date = Column(Date)
    maturity_date = Column(Date)
    closed_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    application = relationship("CreditApplication", back_populates="credit_accounts")
    payments = relationship("CreditPayment", back_populates="account", cascade="all, delete-orphan")
    disbursements = relationship("CreditDisbursement", back_populates="account", cascade="all, delete-orphan")

class CreditPayment(Base):
    """Credit payment records"""
    __tablename__ = "credit_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String(255), unique=True, index=True, nullable=False)
    account_id = Column(Integer, ForeignKey("credit_accounts.id"), nullable=False)
    
    # Payment details
    payment_amount = Column(Numeric(15, 2), nullable=False)
    principal_amount = Column(Numeric(15, 2), nullable=False)
    interest_amount = Column(Numeric(15, 2), nullable=False)
    fee_amount = Column(Numeric(15, 2), default=0)
    
    # Payment information
    payment_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(String(100))
    reference_number = Column(String(255))
    
    # Processing information
    processed_at = Column(DateTime)
    processed_by = Column(String(255))  # User ID who processed
    failure_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("CreditAccount", back_populates="payments")

class CreditDisbursement(Base):
    """Credit disbursement records"""
    __tablename__ = "credit_disbursements"
    
    id = Column(Integer, primary_key=True, index=True)
    disbursement_id = Column(String(255), unique=True, index=True, nullable=False)
    account_id = Column(Integer, ForeignKey("credit_accounts.id"), nullable=False)
    
    # Disbursement details
    amount = Column(Numeric(15, 2), nullable=False)
    disbursement_method = Column(String(100), nullable=False)  # bank_transfer, wallet, cash
    destination_account = Column(String(255))
    reference_number = Column(String(255))
    
    # Status tracking
    status = Column(String(50), default="pending", nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime)
    disbursed_at = Column(DateTime)
    
    # Processing information
    approved_by = Column(String(255))  # User ID who approved
    processed_by = Column(String(255))  # User ID who processed
    failure_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("CreditAccount", back_populates="disbursements")

class CreditDocument(Base):
    """Documents for credit applications"""
    __tablename__ = "credit_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("credit_applications.id"), nullable=False)
    
    # Document details
    document_type = Column(String(100), nullable=False)  # identity, income_proof, bank_statement, etc.
    document_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(255))  # User ID who verified
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    application = relationship("CreditApplication", back_populates="documents")

class CreditScore(Base):
    """Customer credit scoring history"""
    __tablename__ = "credit_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(255), nullable=False, index=True)  # Reference to Auth service
    
    # Scoring details
    score = Column(Integer, nullable=False)  # 300-850 range
    risk_level = Column(String(20), nullable=False)
    scoring_model_version = Column(String(50))
    
    # Score factors
    payment_history_score = Column(Integer)
    credit_utilization_score = Column(Integer)
    credit_length_score = Column(Integer)
    credit_mix_score = Column(Integer)
    new_credit_score = Column(Integer)
    
    # Additional factors
    total_accounts = Column(Integer, default=0)
    active_accounts = Column(Integer, default=0)
    total_credit_limit = Column(Numeric(15, 2), default=0)
    total_debt = Column(Numeric(15, 2), default=0)
    on_time_payments = Column(Integer, default=0)
    late_payments = Column(Integer, default=0)
    
    # Timestamp
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class CreditPolicy(Base):
    """Credit policies and rules"""
    __tablename__ = "credit_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String(255), unique=True, index=True, nullable=False)
    credit_type = Column(String(50), nullable=False)
    
    # Policy rules
    min_amount = Column(Numeric(15, 2), default=1000)
    max_amount = Column(Numeric(15, 2), default=100000)
    min_term_months = Column(Integer, default=3)
    max_term_months = Column(Integer, default=60)
    
    # Interest rates by risk level
    interest_rate_low_risk = Column(Float, default=15.0)
    interest_rate_medium_risk = Column(Float, default=25.0)
    interest_rate_high_risk = Column(Float, default=35.0)
    
    # Eligibility criteria
    min_credit_score = Column(Integer, default=300)
    max_debt_to_income_ratio = Column(Float, default=0.4)
    min_monthly_income = Column(Numeric(15, 2), default=5000)
    min_employment_months = Column(Integer, default=6)
    
    # Fees
    origination_fee_rate = Column(Float, default=0.02)
    late_payment_fee = Column(Numeric(15, 2), default=500)
    processing_fee = Column(Numeric(15, 2), default=200)
    
    # Policy status
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class CreditLimit(Base):
    """Customer credit limits"""
    __tablename__ = "credit_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(255), unique=True, index=True, nullable=False)  # Reference to Auth service
    
    # Credit limits by type
    personal_limit = Column(Numeric(15, 2), default=0)
    business_limit = Column(Numeric(15, 2), default=0)
    inventory_limit = Column(Numeric(15, 2), default=0)
    equipment_limit = Column(Numeric(15, 2), default=0)
    emergency_limit = Column(Numeric(15, 2), default=5000)
    
    # Utilization tracking
    personal_used = Column(Numeric(15, 2), default=0)
    business_used = Column(Numeric(15, 2), default=0)
    inventory_used = Column(Numeric(15, 2), default=0)
    equipment_used = Column(Numeric(15, 2), default=0)
    emergency_used = Column(Numeric(15, 2), default=0)
    
    # Limit management
    total_limit = Column(Numeric(15, 2), nullable=False)
    available_limit = Column(Numeric(15, 2), nullable=False)
    last_review_date = Column(Date)
    next_review_date = Column(Date)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)