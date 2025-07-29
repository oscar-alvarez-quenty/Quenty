from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Date, Time
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date, time
from enum import Enum

Base = declarative_base()

class PickupStatus(str, Enum):
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class PickupType(str, Enum):
    ON_DEMAND = "on_demand"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"
    EXPRESS = "express"

class VehicleType(str, Enum):
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"

class RouteStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Pickup(Base):
    """Pickup request model"""
    __tablename__ = "pickups"
    
    id = Column(Integer, primary_key=True, index=True)
    pickup_id = Column(String(255), unique=True, index=True, nullable=False)
    customer_id = Column(String(255), nullable=False, index=True)  # Reference to Auth service
    
    # Pickup details
    pickup_type = Column(String(50), nullable=False)
    status = Column(String(50), default=PickupStatus.SCHEDULED, nullable=False)
    pickup_date = Column(Date, nullable=False)
    time_window_start = Column(Time, nullable=False)
    time_window_end = Column(Time, nullable=False)
    
    # Location information
    pickup_address = Column(Text, nullable=False)
    pickup_latitude = Column(Float)
    pickup_longitude = Column(Float)
    postal_code = Column(String(20))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(10), default="MX")
    
    # Contact information
    contact_name = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(255))
    
    # Package information
    package_count = Column(Integer, nullable=False)
    estimated_weight_kg = Column(Float, nullable=False)
    actual_weight_kg = Column(Float)
    estimated_volume_m3 = Column(Float)
    actual_volume_m3 = Column(Float)
    
    # Special requirements
    requires_packaging = Column(Boolean, default=False)
    fragile_items = Column(Boolean, default=False)
    special_instructions = Column(Text)
    
    # Assignment information
    assigned_driver_id = Column(String(255))
    assigned_vehicle_type = Column(String(50))
    assigned_route_id = Column(Integer, ForeignKey("pickup_routes.id"))
    estimated_arrival_time = Column(DateTime)
    actual_pickup_time = Column(DateTime)
    
    # Completion information
    completion_notes = Column(Text)
    customer_signature = Column(Text)  # Base64 encoded
    driver_notes = Column(Text)
    completion_photos = Column(JSON)  # List of photo URLs
    
    # Billing information
    pickup_cost = Column(Float)
    currency = Column(String(10), default="MXN")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    route = relationship("PickupRoute", back_populates="pickups")
    packages = relationship("PickupPackage", back_populates="pickup", cascade="all, delete-orphan")
    attempts = relationship("PickupAttempt", back_populates="pickup", cascade="all, delete-orphan")

class PickupRoute(Base):
    """Pickup route for drivers"""
    __tablename__ = "pickup_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(String(255), unique=True, index=True, nullable=False)
    driver_id = Column(String(255), nullable=False, index=True)  # Reference to driver system
    
    # Route information
    route_name = Column(String(255))
    route_date = Column(Date, nullable=False)
    status = Column(String(50), default=RouteStatus.PLANNED, nullable=False)
    vehicle_type = Column(String(50), nullable=False)
    vehicle_license_plate = Column(String(50))
    
    # Route optimization
    total_distance_km = Column(Float)
    estimated_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer)
    total_pickups = Column(Integer, default=0)
    completed_pickups = Column(Integer, default=0)
    
    # Route coordinates (optimized path)
    optimized_waypoints = Column(JSON)  # List of coordinates
    
    # Time tracking
    route_start_time = Column(DateTime)
    route_end_time = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    pickups = relationship("Pickup", back_populates="route")

class PickupPackage(Base):
    """Individual packages in a pickup"""
    __tablename__ = "pickup_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    pickup_id = Column(Integer, ForeignKey("pickups.id"), nullable=False)
    package_reference = Column(String(255))  # Customer's package reference
    
    # Package details
    description = Column(String(500))
    category = Column(String(100))
    weight_kg = Column(Float)
    length_cm = Column(Float)
    width_cm = Column(Float)
    height_cm = Column(Float)
    
    # Package status
    is_fragile = Column(Boolean, default=False)
    requires_signature = Column(Boolean, default=True)
    insurance_value = Column(Float)
    
    # Destination information (if different from pickup address)
    destination_address = Column(Text)
    destination_contact_name = Column(String(255))
    destination_contact_phone = Column(String(50))
    
    # Generated tracking information
    tracking_number = Column(String(255), unique=True)
    order_id = Column(String(255))  # Reference to Order service
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    pickup = relationship("Pickup", back_populates="packages")

class PickupAttempt(Base):
    """Pickup attempts and failures"""
    __tablename__ = "pickup_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    pickup_id = Column(Integer, ForeignKey("pickups.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    
    # Attempt details
    attempted_at = Column(DateTime, nullable=False)
    driver_id = Column(String(255))
    attempt_status = Column(String(50), nullable=False)  # successful, failed, rescheduled
    
    # Failure information
    failure_reason = Column(String(500))
    failure_category = Column(String(100))  # customer_not_available, address_issue, etc.
    
    # Rescheduling information
    reschedule_date = Column(Date)
    reschedule_time_start = Column(Time)
    reschedule_time_end = Column(Time)
    
    # Driver notes and evidence
    driver_notes = Column(Text)
    attempt_photos = Column(JSON)  # Photos as evidence
    gps_coordinates = Column(JSON)  # GPS location during attempt
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    pickup = relationship("Pickup", back_populates="attempts")

class PickupCapacity(Base):
    """Pickup capacity management by area and time"""
    __tablename__ = "pickup_capacity"
    
    id = Column(Integer, primary_key=True, index=True)
    postal_code = Column(String(20), nullable=False)
    pickup_date = Column(Date, nullable=False)
    time_slot_start = Column(Time, nullable=False)
    time_slot_end = Column(Time, nullable=False)
    
    # Capacity information
    max_capacity = Column(Integer, default=10)
    current_bookings = Column(Integer, default=0)
    available_vehicles = Column(Integer, default=1)
    
    # Special conditions
    special_event = Column(String(255))  # Holiday, weather, etc.
    capacity_modifier = Column(Float, default=1.0)  # Capacity multiplier
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Driver(Base):
    """Driver information for pickup service"""
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(String(255), nullable=False, index=True)  # Reference to Auth service
    
    # Driver details
    license_number = Column(String(255), nullable=False)
    license_expiry = Column(Date)
    license_category = Column(String(50))
    
    # Vehicle information
    vehicle_type = Column(String(50), nullable=False)
    vehicle_license_plate = Column(String(50), nullable=False)
    vehicle_capacity_kg = Column(Float)
    vehicle_capacity_m3 = Column(Float)
    
    # Work information
    is_active = Column(Boolean, default=True)
    current_zone = Column(String(100))
    work_start_time = Column(Time)
    work_end_time = Column(Time)
    max_pickups_per_day = Column(Integer, default=20)
    
    # Performance metrics
    total_pickups = Column(Integer, default=0)
    successful_pickups = Column(Integer, default=0)
    average_rating = Column(Float, default=5.0)
    total_distance_km = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class PickupZone(Base):
    """Pickup service zones"""
    __tablename__ = "pickup_zones"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String(255), unique=True, index=True, nullable=False)
    zone_name = Column(String(255), nullable=False)
    
    # Geographic boundaries
    postal_codes = Column(JSON)  # List of postal codes covered
    boundary_coordinates = Column(JSON)  # GeoJSON polygon
    
    # Service configuration
    service_available = Column(Boolean, default=True)
    pickup_fee = Column(Float, default=0.0)
    express_available = Column(Boolean, default=True)
    express_fee = Column(Float, default=50.0)
    
    # Time configuration
    service_start_time = Column(Time, default=time(8, 0))
    service_end_time = Column(Time, default=time(18, 0))
    time_slot_duration_minutes = Column(Integer, default=120)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)