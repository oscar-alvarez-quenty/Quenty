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

class BulkUploadStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BulkUpload(Base):
    __tablename__ = "bulk_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(255), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), default=BulkUploadStatus.PENDING.value)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    error_summary = Column(JSON)  # Summary of validation errors
    
    # Foreign Keys
    company_id = Column(String(255), nullable=False)
    uploaded_by = Column(String(255), nullable=False)
    
    # Relationships
    bulk_items = relationship("BulkUploadItem", back_populates="bulk_upload")

class BulkUploadItem(Base):
    __tablename__ = "bulk_upload_items"
    
    id = Column(Integer, primary_key=True, index=True)
    row_number = Column(Integer, nullable=False)  # Original row number in file
    status = Column(String(50), default="pending")  # pending, valid, invalid, processed
    description = Column(Text)
    quantity = Column(Integer)
    weight = Column(Float)
    volume = Column(Float)
    value = Column(Float)
    hs_code = Column(String(50))
    country_of_origin = Column(String(100))
    destination_country = Column(String(100))
    validation_errors = Column(JSON)  # List of validation error messages
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    bulk_upload_id = Column(Integer, ForeignKey("bulk_uploads.id"), nullable=False)
    manifest_id = Column(Integer, ForeignKey("manifests.id"))  # Set when successfully processed
    manifest_item_id = Column(Integer)  # References the created manifest item
    
    # Relationships
    bulk_upload = relationship("BulkUpload", back_populates="bulk_items")