from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Numeric, JSON
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


class Rate(Base):
    __tablename__ = "rates"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(String, nullable=False)
    service_id = Column(String, nullable=False)
    name = Column(String(255), nullable=False)
    weight_min = Column(Numeric, nullable=False)
    weight_max = Column(Numeric, nullable=False)
    fixed_fee = Column(Numeric, nullable=False)
    percentage = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    catalogs = relationship("CatalogRate", back_populates="rate", cascade="all, delete-orphan")



class Catalog(Base):
    __tablename__ = "catalogs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    rates = relationship("CatalogRate", back_populates="catalog", cascade="all, delete-orphan")



class CatalogRate(Base):
    __tablename__ = "catalog_rates"

    catalog_id = Column(Integer, ForeignKey("catalogs.id"), primary_key=True)
    rate_id = Column(Integer, ForeignKey("rates.id"), primary_key=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    catalog = relationship("Catalog", back_populates="rates")
    rate = relationship("Rate", back_populates="catalogs")



class ClientRatebook(Base):
    __tablename__ = "client_ratebooks"

    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(String, nullable=False)
    warehouse_id = Column(String, nullable=False)

    catalog_id = Column(Integer, ForeignKey("catalogs.id"), nullable=True)
    rate_id = Column(Integer, ForeignKey("rates.id"), nullable=True)

    operator_id = Column(String, nullable=False)
    service_id = Column(String, nullable=False)

    name = Column(String(255), nullable=False)
    weight_min = Column(Numeric, nullable=False)
    weight_max = Column(Numeric, nullable=False)
    fixed_fee = Column(Numeric, nullable=False)
    percentage = Column(Boolean, default=False)
    dependent = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    catalog = relationship("Catalog", backref="client_ratebooks", foreign_keys=[catalog_id])
    rate = relationship("Rate", backref="client_ratebooks", foreign_keys=[rate_id])
