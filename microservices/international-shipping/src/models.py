from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

class ManifestStatus(PyEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

class ShippingZone(PyEnum):
    ZONE_1 = "zone_1"
    ZONE_2 = "zone_2"
    ZONE_3 = "zone_3"
    ZONE_4 = "zone_4"

class Manifest(Base):
    __tablename__ = "manifests"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default=ManifestStatus.DRAFT.value)
    total_weight = Column(Float, default=0.0)
    total_volume = Column(Float, default=0.0)
    total_value = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    origin_country = Column(String(100), nullable=False)
    destination_country = Column(String(100), nullable=False)
    shipping_zone = Column(String(50))
    estimated_delivery = Column(DateTime)
    tracking_number = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Foreign Keys
    company_id = Column(String(255), nullable=False)  # References Company from Customer service
    created_by = Column(String(255), nullable=False)  # References User from Customer service
    
    # Relationships
    manifest_items = relationship("ManifestItem", back_populates="manifest")
    shipping_rates = relationship("ShippingRate", back_populates="manifest")
    tracking_events = relationship("TrackingEvent", back_populates="manifest")

class ManifestItem(Base):
    __tablename__ = "manifest_items"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    volume = Column(Float)
    value = Column(Float, nullable=False)
    hs_code = Column(String(50))  # Harmonized System code for customs
    country_of_origin = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    manifest_id = Column(Integer, ForeignKey("manifests.id"), nullable=False)
    product_id = Column(Integer)  # References Product from Order service
    
    # Relationships
    manifest = relationship("Manifest", back_populates="manifest_items")

class ShippingRate(Base):
    __tablename__ = "shipping_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    carrier_name = Column(String(255), nullable=False)
    service_type = Column(String(255), nullable=False)
    base_rate = Column(Float, nullable=False)
    weight_rate = Column(Float, default=0.0)
    volume_rate = Column(Float, default=0.0)
    fuel_surcharge = Column(Float, default=0.0)
    insurance_rate = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    transit_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Foreign Keys
    manifest_id = Column(Integer, ForeignKey("manifests.id"), nullable=False)
    
    # Relationships
    manifest = relationship("Manifest", back_populates="shipping_rates")

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    iso_code = Column(String(10), unique=True, nullable=False)
    zone = Column(String(50))  # ShippingZone enum
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    api_endpoint = Column(String(500))
    api_key = Column(String(500))
    active = Column(Boolean, default=True)
    supported_services = Column(JSON)  # List of service types
    created_at = Column(DateTime, default=datetime.utcnow)

class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(255), nullable=False, index=True)
    event_timestamp = Column(DateTime, nullable=False)
    location = Column(String(255))
    status = Column(String(100), nullable=False)
    description = Column(Text)
    carrier_code = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    manifest_id = Column(Integer, ForeignKey("manifests.id"))
    
    # Relationships
    manifest = relationship("Manifest", back_populates="tracking_events")

class BulkTrackingDashboard(Base):
    __tablename__ = "bulk_tracking_dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    tracking_numbers = Column(JSON)  # List of tracking numbers to monitor
    status_filters = Column(JSON)  # Status filters for dashboard
    carrier_filters = Column(JSON)  # Carrier filters
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    refresh_interval = Column(Integer, default=300)  # Refresh interval in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    company_id = Column(String(255), nullable=False)
    created_by = Column(String(255), nullable=False)