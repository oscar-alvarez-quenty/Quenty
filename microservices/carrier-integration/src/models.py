from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class CarrierType(enum.Enum):
    DHL = "DHL"
    FEDEX = "FedEx"
    UPS = "UPS"
    SERVIENTREGA = "Servientrega"
    INTERRAPIDISIMO = "Interrapidisimo"
    PASAREX = "Pasarex"
    AEROPOST = "Aeropost"
    PICKIT = "Pickit"

class EnvironmentType(enum.Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

class ServiceStatus(enum.Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    DOWN = "down"

class CarrierCredential(Base):
    __tablename__ = "carrier_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    environment = Column(SQLEnum(EnvironmentType), nullable=False)
    credentials = Column(Text, nullable=False)  # Encrypted JSON
    is_active = Column(Boolean, default=True)
    validated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class CarrierHealthStatus(Base):
    __tablename__ = "carrier_health_status"
    
    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    status = Column(SQLEnum(ServiceStatus), nullable=False)
    latency_ms = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    last_check = Column(DateTime, server_default=func.now())
    last_success = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    circuit_breaker_open = Column(Boolean, default=False)
    details = Column(JSON, nullable=True)

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Float, nullable=False)
    source = Column(String(50), nullable=False)  # e.g., "banco_republica"
    valid_date = Column(DateTime, nullable=False)
    spread = Column(Float, default=0.0)  # Percentage spread to apply
    created_at = Column(DateTime, server_default=func.now())

class ShippingQuote(Base):
    __tablename__ = "shipping_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(String(100), unique=True, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    origin_country = Column(String(2), nullable=False)
    origin_city = Column(String(100), nullable=False)
    destination_country = Column(String(2), nullable=False)
    destination_city = Column(String(100), nullable=False)
    weight_kg = Column(Float, nullable=False)
    dimensions_cm = Column(JSON, nullable=False)  # {"length": x, "width": y, "height": z}
    service_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    estimated_days = Column(Integer, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class ShippingLabel(Base):
    __tablename__ = "shipping_labels"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), nullable=False, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    tracking_number = Column(String(100), unique=True, index=True)
    label_url = Column(Text, nullable=True)
    label_data = Column(Text, nullable=True)  # Base64 encoded
    awb_number = Column(String(100), nullable=True)  # For DHL
    service_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(100), nullable=False, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    event_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class PickupSchedule(Base):
    __tablename__ = "pickup_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    confirmation_number = Column(String(100), unique=True, index=True)
    pickup_date = Column(DateTime, nullable=False)
    pickup_window_start = Column(String(5), nullable=False)  # HH:MM
    pickup_window_end = Column(String(5), nullable=False)  # HH:MM
    address = Column(JSON, nullable=False)
    contact = Column(JSON, nullable=False)
    packages = Column(Integer, nullable=False)
    status = Column(String(50), default="scheduled")
    created_at = Column(DateTime, server_default=func.now())

class FallbackConfiguration(Base):
    __tablename__ = "fallback_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(200), nullable=False, unique=True)  # e.g., "CO-US", "BOG-NYC"
    priority_order = Column(JSON, nullable=False)  # ["DHL", "FedEx", "UPS"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class FallbackEvent(Base):
    __tablename__ = "fallback_events"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), nullable=False)
    from_carrier = Column(SQLEnum(CarrierType), nullable=False)
    to_carrier = Column(SQLEnum(CarrierType), nullable=False)
    reason = Column(Text, nullable=False)
    price_difference = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class ApiCallLog(Base):
    __tablename__ = "api_call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# International Mailbox Models

class InternationalMailbox(Base):
    __tablename__ = "international_mailboxes"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(100), nullable=False, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)  # PASAREX or AEROPOST
    mailbox_id = Column(String(100), unique=True, index=True)
    mailbox_number = Column(String(50), nullable=False)
    miami_address = Column(JSON, nullable=False)
    spain_address = Column(JSON, nullable=True)  # Only for Pasarex
    status = Column(String(20), default="active")
    membership_type = Column(String(20), default="standard")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class PackagePrealert(Base):
    __tablename__ = "package_prealerts"
    
    id = Column(Integer, primary_key=True, index=True)
    mailbox_id = Column(String(100), nullable=False, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    tracking_number = Column(String(100), nullable=False, index=True)
    origin_carrier = Column(String(50), nullable=True)
    description = Column(Text, nullable=False)
    declared_value = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    weight_lb = Column(Float, nullable=False)
    dimensions = Column(JSON, nullable=True)
    category = Column(String(50), default="GENERAL")
    status = Column(String(50), default="prealerted")
    expected_arrival = Column(DateTime, nullable=True)
    arrived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class PackageConsolidation(Base):
    __tablename__ = "package_consolidations"
    
    id = Column(Integer, primary_key=True, index=True)
    consolidation_id = Column(String(100), unique=True, index=True)
    customer_id = Column(String(100), nullable=False)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    package_ids = Column(JSON, nullable=False)  # List of package IDs
    master_tracking = Column(String(100), nullable=True)
    status = Column(String(50), default="pending")
    packages_count = Column(Integer, nullable=False)
    total_weight_lb = Column(Float, nullable=False)
    volumetric_weight = Column(Float, nullable=True)
    billable_weight = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    savings_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

class CustomsDeclaration(Base):
    __tablename__ = "customs_declarations"
    
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String(100), nullable=False, index=True)
    declaration_id = Column(String(100), unique=True, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    items = Column(JSON, nullable=False)  # List of declared items
    total_value = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    invoice_number = Column(String(100), nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    merchant = Column(String(200), nullable=True)
    customs_form_id = Column(String(100), nullable=True)
    status = Column(String(50), default="declared")
    created_at = Column(DateTime, server_default=func.now())

class ImportCostCalculation(Base):
    __tablename__ = "import_cost_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String(100), nullable=False, index=True)
    carrier = Column(SQLEnum(CarrierType), nullable=False)
    product_value = Column(Float, nullable=False)
    shipping_cost = Column(Float, nullable=False)
    customs_duty = Column(Float, nullable=False)
    vat = Column(Float, nullable=False)
    handling_fee = Column(Float, nullable=False)
    insurance = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=False)
    currency = Column(String(3), default="COP")
    exchange_rate = Column(Float, nullable=False)
    duty_rate = Column(Float, nullable=False)
    vat_rate = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    calculated_at = Column(DateTime, server_default=func.now())