from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Numeric, Date, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()

class MetricType(str, Enum):
    """Metric type enumeration"""
    REVENUE = "revenue"
    ORDERS = "orders"
    CUSTOMERS = "customers"
    PERFORMANCE = "performance"
    INVENTORY = "inventory"
    DELIVERY = "delivery"
    MARKETING = "marketing"
    FINANCE = "finance"

class ReportStatus(str, Enum):
    """Report status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Metric(Base):
    """Metrics storage for analytics"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(String(255), unique=True, index=True, default=lambda: f"METRIC-{str(uuid.uuid4())[:8].upper()}")
    
    # Metric Information
    metric_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Value and Metadata
    value = Column(Numeric(20, 4), nullable=False)
    unit = Column(String(50))  # currency, percentage, count, etc.
    tags = Column(JSON, default=dict)  # Key-value tags for filtering
    
    # Time Information
    timestamp = Column(DateTime, nullable=False, index=True)
    period = Column(String(20))  # daily, weekly, monthly, etc.
    
    # Source Information
    source_service = Column(String(100))  # Which service generated this metric
    source_entity_id = Column(String(255))  # ID of the entity (order, customer, etc.)
    source_entity_type = Column(String(100))  # Type of entity
    
    # System Fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_metrics_type_timestamp', 'metric_type', 'timestamp'),
        Index('idx_metrics_source_timestamp', 'source_service', 'timestamp'),
        Index('idx_metrics_tags', 'tags', postgresql_using='gin'),
    )

class Dashboard(Base):
    """Dashboard configuration"""
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(String(255), unique=True, index=True, default=lambda: f"DASH-{str(uuid.uuid4())[:8].upper()}")
    
    # Dashboard Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    dashboard_type = Column(String(50), default="standard")  # standard, executive, operational
    
    # Configuration
    widgets = Column(JSON, default=list)  # Widget configurations
    layout = Column(JSON, default=dict)  # Layout configuration
    filters = Column(JSON, default=dict)  # Default filters
    refresh_interval = Column(Integer, default=300)  # Seconds
    
    # Access Control
    owner_id = Column(String(255))
    is_public = Column(Boolean, default=False)
    allowed_users = Column(JSON, default=list)
    allowed_roles = Column(JSON, default=list)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class Report(Base):
    """Report generation and storage"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(255), unique=True, index=True, default=lambda: f"RPT-{str(uuid.uuid4())[:8].upper()}")
    
    # Report Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False)  # financial, operational, performance
    format = Column(String(20), default="json")  # json, csv, pdf, excel
    
    # Generation Parameters
    parameters = Column(JSON, default=dict)
    filters = Column(JSON, default=dict)
    date_range = Column(JSON)  # start_date, end_date
    
    # Status and Results
    status = Column(String(20), default=ReportStatus.PENDING, nullable=False)
    progress_percentage = Column(Integer, default=0)
    file_url = Column(String(500))
    file_size = Column(Integer)
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_expression = Column(String(100))  # Cron expression
    next_run = Column(DateTime)
    
    # System Fields
    requested_by = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)

class Alert(Base):
    """Analytics alerts and notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(255), unique=True, index=True, default=lambda: f"ALERT-{str(uuid.uuid4())[:8].upper()}")
    
    # Alert Configuration
    name = Column(String(255), nullable=False)
    description = Column(Text)
    metric_type = Column(String(50), nullable=False)
    
    # Conditions
    condition_expression = Column(Text, nullable=False)  # Mathematical expression
    threshold_value = Column(Numeric(20, 4))
    comparison_operator = Column(String(10))  # >, <, >=, <=, ==, !=
    
    # Notification Settings
    notification_channels = Column(JSON, default=list)  # email, slack, webhook
    notification_template = Column(Text)
    cooldown_minutes = Column(Integer, default=60)  # Minimum time between alerts
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    
    # System Fields
    created_by = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class AnalyticsQuery(Base):
    """Saved analytics queries"""
    __tablename__ = "analytics_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(255), unique=True, index=True, default=lambda: f"QRY-{str(uuid.uuid4())[:8].upper()}")
    
    # Query Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    
    # Query Definition
    query_type = Column(String(50), nullable=False)  # aggregation, timeseries, comparison
    query_definition = Column(JSON, nullable=False)  # The actual query parameters
    
    # Usage Statistics
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime)
    average_execution_time = Column(Numeric(10, 3))  # Seconds
    
    # System Fields
    created_by = Column(String(255))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)