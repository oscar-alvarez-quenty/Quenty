from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Numeric, Date, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()

class ReturnStatus(str, Enum):
    """Return status enumeration"""
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKUP_SCHEDULED = "pickup_scheduled"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTED = "inspected"
    PROCESSED = "processed"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    DISPOSED = "disposed"

class ReturnReason(str, Enum):
    """Return reason enumeration"""
    DAMAGED = "damaged"
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    SIZE_ISSUE = "size_issue"
    CHANGE_OF_MIND = "change_of_mind"
    DUPLICATE_ORDER = "duplicate_order"
    LATE_DELIVERY = "late_delivery"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"

class ReturnType(str, Enum):
    """Return type enumeration"""
    RETURN = "return"
    EXCHANGE = "exchange"
    REPAIR = "repair"
    WARRANTY_CLAIM = "warranty_claim"

class DisposalMethod(str, Enum):
    """Disposal method enumeration"""
    RESELL = "resell"
    REFURBISH = "refurbish"
    DONATE = "donate"
    RECYCLE = "recycle"
    DESTROY = "destroy"

class InspectionResult(str, Enum):
    """Inspection result enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"
    UNUSABLE = "unusable"

class Return(Base):
    """Return request model"""
    __tablename__ = "returns"
    
    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(String(255), unique=True, index=True, default=lambda: f"RET-{str(uuid.uuid4())[:8].upper()}")
    
    # Order and Customer Information
    original_order_id = Column(String(255), nullable=False, index=True)
    customer_id = Column(String(255), nullable=False, index=True)
    
    # Return Details
    return_type = Column(String(50), nullable=False, default=ReturnType.RETURN)
    return_reason = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=ReturnStatus.REQUESTED, index=True)
    
    # Return Information
    description = Column(Text)
    preferred_resolution = Column(String(50))  # refund, exchange, store_credit
    return_authorization_number = Column(String(255), unique=True, index=True)
    
    # Financial Information
    original_order_value = Column(Numeric(10, 2))
    estimated_refund_amount = Column(Numeric(10, 2))
    actual_refund_amount = Column(Numeric(10, 2))
    return_shipping_cost = Column(Numeric(10, 2), default=0)
    processing_fee = Column(Numeric(10, 2), default=0)
    
    # Shipping and Logistics
    pickup_address = Column(Text)
    return_address = Column(Text)
    tracking_number = Column(String(255), unique=True)
    carrier = Column(String(100))
    
    # Timeline Information
    estimated_pickup_date = Column(Date)
    actual_pickup_date = Column(Date)
    estimated_processing_time = Column(String(50))
    expires_at = Column(DateTime, nullable=False)
    
    # Processing Information
    approval_notes = Column(Text)
    rejection_reason = Column(Text)
    processing_notes = Column(Text)
    
    # Additional Data
    photos = Column(JSON, default=list)  # URLs to uploaded photos
    customer_action_required = Column(String(255))
    requires_customer_action = Column(Boolean, default=False)
    
    # System Fields
    created_by = Column(String(255))
    processed_by = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    approved_at = Column(DateTime)
    rejected_at = Column(DateTime)
    processed_at = Column(DateTime)
    
    # Relationships
    items = relationship("ReturnItem", back_populates="return_record", cascade="all, delete-orphan")
    inspections = relationship("InspectionReport", back_populates="return_record", cascade="all, delete-orphan")
    status_history = relationship("ReturnStatusHistory", back_populates="return_record", cascade="all, delete-orphan")
    disposals = relationship("DisposalRecord", back_populates="return_record", cascade="all, delete-orphan")

class ReturnItem(Base):
    """Items included in return request"""
    __tablename__ = "return_items"
    
    id = Column(Integer, primary_key=True, index=True)
    return_item_id = Column(String(255), unique=True, index=True, default=lambda: f"RI-{str(uuid.uuid4())[:8].upper()}")
    
    # Relationships
    return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    
    # Item Information
    item_id = Column(String(255), nullable=False, index=True)
    item_name = Column(String(255))
    sku = Column(String(100))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    
    # Return Specific Information
    return_reason = Column(String(50))
    reason_details = Column(Text)
    condition_received = Column(String(50))
    photos = Column(JSON, default=list)
    
    # Processing Information
    inspection_result = Column(String(50))
    resale_value = Column(Numeric(10, 2))
    refund_eligible = Column(Boolean, default=True)
    refund_amount = Column(Numeric(10, 2))
    
    # Exchange Information
    exchange_item_id = Column(String(255))
    exchange_quantity = Column(Integer)
    
    # System Fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    return_record = relationship("Return", back_populates="items")

class InspectionReport(Base):
    """Inspection reports for returned items"""
    __tablename__ = "inspection_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String(255), unique=True, index=True, default=lambda: f"INSP-{str(uuid.uuid4())[:8].upper()}")
    
    # Relationships
    return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    item_id = Column(String(255), nullable=False, index=True)
    
    # Inspector Information
    inspector_id = Column(String(255), nullable=False)
    inspector_name = Column(String(255))
    inspection_date = Column(DateTime, nullable=False, default=func.now())
    
    # Inspection Results
    overall_condition = Column(String(50), nullable=False)
    functional_status = Column(String(50))  # working, partially_working, non_functional
    cosmetic_condition = Column(String(50))  # excellent, good, fair, poor
    completeness = Column(String(50))  # complete, missing_accessories, incomplete
    
    # Detailed Findings
    defects_found = Column(JSON, default=list)  # List of defects
    photos = Column(JSON, default=list)  # URLs to inspection photos
    notes = Column(Text)
    
    # Valuation
    original_value = Column(Numeric(10, 2))
    current_market_value = Column(Numeric(10, 2))
    resale_value = Column(Numeric(10, 2))
    salvage_value = Column(Numeric(10, 2))
    
    # Recommendations
    recommended_action = Column(String(100))  # full_refund, partial_refund, exchange, reject, repair
    disposition_recommendation = Column(String(50))  # resell, refurbish, donate, recycle, destroy
    repair_cost_estimate = Column(Numeric(10, 2))
    refurbishment_cost = Column(Numeric(10, 2))
    
    # System Fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    return_record = relationship("Return", back_populates="inspections")

class ReturnStatusHistory(Base):
    """History of status changes for returns"""
    __tablename__ = "return_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    history_id = Column(String(255), unique=True, index=True, default=lambda: f"HIST-{str(uuid.uuid4())[:8].upper()}")
    
    # Relationships
    return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    
    # Status Information
    previous_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    status_reason = Column(String(255))
    notes = Column(Text)
    
    # Location and Tracking
    location = Column(String(255))
    tracking_number = Column(String(255))
    carrier = Column(String(100))
    
    # System Fields
    changed_by = Column(String(255))
    changed_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    return_record = relationship("Return", back_populates="status_history")

class DisposalRecord(Base):
    """Records of item disposal/disposition"""
    __tablename__ = "disposal_records"
    
    id = Column(Integer, primary_key=True, index=True)
    disposal_id = Column(String(255), unique=True, index=True, default=lambda: f"DISP-{str(uuid.uuid4())[:8].upper()}")
    
    # Relationships
    return_id = Column(Integer, ForeignKey("returns.id"), nullable=False)
    item_id = Column(String(255), nullable=False, index=True)
    
    # Disposal Information
    disposal_method = Column(String(50), nullable=False)
    disposal_date = Column(Date, nullable=False)
    disposal_reason = Column(String(255))
    
    # Financial Impact
    disposal_value = Column(Numeric(10, 2), default=0)  # Amount received
    disposal_cost = Column(Numeric(10, 2), default=0)   # Cost to dispose
    net_recovery = Column(Numeric(10, 2), default=0)    # Value - Cost
    
    # Partner Information
    disposal_partner = Column(String(255))
    partner_contact = Column(String(255))
    partner_reference = Column(String(255))
    
    # Environmental Impact
    environmental_impact = Column(JSON, default=dict)
    sustainability_score = Column(Numeric(3, 2))  # 0-10 scale
    carbon_footprint = Column(Numeric(8, 2))  # CO2 equivalent
    
    # Documentation
    documentation_urls = Column(JSON, default=list)
    certificates = Column(JSON, default=list)
    
    # System Fields
    processed_by = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    return_record = relationship("Return", back_populates="disposals")

class ReturnMetrics(Base):
    """Daily return metrics for analytics"""
    __tablename__ = "return_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(String(255), unique=True, index=True, default=lambda: f"RM-{str(uuid.uuid4())[:8].upper()}")
    
    # Date Information
    metric_date = Column(Date, nullable=False, index=True)
    
    # Volume Metrics
    total_returns_requested = Column(Integer, default=0)
    total_returns_approved = Column(Integer, default=0)
    total_returns_rejected = Column(Integer, default=0)
    total_returns_processed = Column(Integer, default=0)
    
    # Financial Metrics
    total_refund_amount = Column(Numeric(12, 2), default=0)
    total_processing_costs = Column(Numeric(12, 2), default=0)
    total_recovery_value = Column(Numeric(12, 2), default=0)
    net_cost = Column(Numeric(12, 2), default=0)
    
    # Processing Metrics
    avg_processing_time_hours = Column(Numeric(8, 2))
    avg_pickup_time_hours = Column(Numeric(8, 2))
    customer_satisfaction_score = Column(Numeric(3, 2))
    
    # Return Reasons Breakdown
    returns_by_reason = Column(JSON, default=dict)
    returns_by_status = Column(JSON, default=dict)
    
    # System Fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)