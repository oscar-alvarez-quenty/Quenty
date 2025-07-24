from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict, Any
import consul
import httpx
import os
import logging
from datetime import datetime, date, time as dt_time, timedelta
from enum import Enum
import uuid
import time

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from .models import (
    Pickup, PickupRoute, PickupPackage, PickupAttempt, PickupCapacity, 
    Driver, PickupZone, Base, PickupStatus, PickupType, VehicleType, RouteStatus
)
from .database import get_db, create_tables, engine

# Import logging configuration
try:
    from .logging_config import LOGGING_MESSAGES, ERROR_MESSAGES, INFO_MESSAGES, DEBUG_MESSAGES, WARNING_MESSAGES
except ImportError:
    # Fallback if logging_config is not available
    LOGGING_MESSAGES = ERROR_MESSAGES = INFO_MESSAGES = DEBUG_MESSAGES = WARNING_MESSAGES = {}

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Set log level from environment
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = structlog.get_logger("pickup-service")

class Settings(BaseSettings):
    service_name: str = "pickup-service"
    database_url: str = "postgresql+asyncpg://pickup:pickup_pass@pickup-db:5432/pickup_db"
    redis_url: str = "redis://redis:6379/3"
    consul_host: str = "consul"
    consul_port: int = 8500
    auth_service_url: str = "http://auth-service:8003"

    class Config:
        env_file = ".env"

settings = Settings()

# HTTP Bearer for token extraction
security = HTTPBearer()

app = FastAPI(
    title="Pickup Service",
    description="Microservice for package pickup scheduling and management",
    version="2.0.0"
)
# Prometheus metrics
pickup_service_operations_total = Counter(
    'pickup_service_operations_total',
    'Total number of pickup-service operations',
    ['operation', 'status']
)
pickup_service_request_duration = Histogram(
    'pickup_service_request_duration_seconds',
    'Duration of pickup-service requests in seconds',
    ['method', 'endpoint']
)
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)

# Auth dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service and return user info"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/profile",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(user_info = Depends(verify_token)):
    """Get current authenticated user"""
    return user_info

def require_permissions(permissions: list[str]):
    """Require specific permissions"""
    def permission_checker(current_user = Depends(get_current_user)):
        user_permissions = set(current_user.get('permissions', []))
        required_permissions = set(permissions)
        
        # Superusers have all permissions
        if current_user.get('is_superuser'):
            return current_user
        
        # Check if user has required permissions
        if not required_permissions.issubset(user_permissions):
            missing_perms = required_permissions - user_permissions
            raise HTTPException(
                status_code=403,
                detail=f"Missing permissions: {', '.join(missing_perms)}"
            )
        
        return current_user
    
    return permission_checker

async def validate_pickup_ownership(pickup_id: int, current_user: dict, db: AsyncSession):
    """Validate that user owns pickup or has admin permissions"""
    # Admin and manager can access all pickups
    if current_user.get('is_superuser') or 'pickups:read:all' in current_user.get('permissions', []):
        return True
    
    # Check if pickup belongs to current user
    stmt = select(Pickup).where(
        Pickup.id == pickup_id,
        Pickup.customer_id == current_user['unique_id']
    )
    result = await db.execute(stmt)
    pickup = result.scalar_one_or_none()
    
    if not pickup:
        raise HTTPException(
            status_code=403,
            detail="Access denied: You can only access your own pickups"
        )
    
    return True

# Pydantic models for API
class PickupRequest(BaseModel):
    pickup_type: PickupType
    pickup_date: date
    time_window_start: dt_time
    time_window_end: dt_time
    pickup_address: str
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    postal_code: str
    city: str
    state: str = "CDMX"
    country: str = "MX"
    contact_name: str
    contact_phone: str
    contact_email: Optional[str] = None
    package_count: int = Field(ge=1)
    estimated_weight_kg: float = Field(gt=0)
    estimated_volume_m3: Optional[float] = None
    requires_packaging: bool = False
    fragile_items: bool = False
    special_instructions: Optional[str] = None
    packages: Optional[List[Dict[str, Any]]] = None

    @validator('pickup_date')
    def validate_pickup_date(cls, v):
        if v < date.today():
            raise ValueError('Pickup date cannot be in the past')
        return v

    @validator('time_window_end')
    def validate_time_window(cls, v, values):
        if 'time_window_start' in values and v <= values['time_window_start']:
            raise ValueError('End time must be after start time')
        return v

class PickupUpdate(BaseModel):
    pickup_date: Optional[date] = None
    time_window_start: Optional[dt_time] = None
    time_window_end: Optional[dt_time] = None
    pickup_address: Optional[str] = None
    contact_phone: Optional[str] = None
    package_count: Optional[int] = None
    special_instructions: Optional[str] = None

class DriverAssignment(BaseModel):
    driver_id: str
    vehicle_type: VehicleType
    estimated_arrival_time: datetime
    route_id: Optional[str] = None

class PickupCompletion(BaseModel):
    actual_package_count: int = Field(ge=1)
    actual_weight_kg: float = Field(gt=0)
    actual_volume_m3: Optional[float] = None
    pickup_time: datetime
    packages: List[Dict[str, Any]]
    driver_notes: Optional[str] = None
    customer_signature: Optional[str] = None
    completion_photos: Optional[List[str]] = None

class PickupResponse(BaseModel):
    id: int
    pickup_id: str
    customer_id: str
    pickup_type: PickupType
    status: PickupStatus
    pickup_date: date
    time_window_start: dt_time
    time_window_end: dt_time
    pickup_address: str
    contact_name: str
    contact_phone: str
    package_count: int
    estimated_weight_kg: float
    assigned_driver_id: Optional[str] = None
    assigned_vehicle_type: Optional[str] = None
    estimated_arrival_time: Optional[datetime] = None
    pickup_cost: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RouteRequest(BaseModel):
    driver_id: str
    route_date: date
    vehicle_type: VehicleType
    pickup_ids: List[int]

class RouteResponse(BaseModel):
    id: int
    route_id: str
    driver_id: str
    route_name: Optional[str]
    route_date: date
    status: RouteStatus
    vehicle_type: VehicleType
    total_distance_km: Optional[float]
    estimated_duration_minutes: Optional[int]
    total_pickups: int
    completed_pickups: int
    created_at: datetime

    class Config:
        from_attributes = True

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Pickup endpoints
@app.post("/api/v1/pickups", response_model=PickupResponse)
async def create_pickup(
    pickup: PickupRequest,
    current_user = Depends(require_permissions(["pickups:create"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new pickup request"""
    try:
        pickup_id = f"PU-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate pickup cost based on type and location
        pickup_cost = calculate_pickup_cost(pickup.pickup_type, pickup.estimated_weight_kg, pickup.postal_code)
        
        db_pickup = Pickup(
            pickup_id=pickup_id,
            customer_id=current_user['unique_id'],
            pickup_type=pickup.pickup_type.value,
            pickup_date=pickup.pickup_date,
            time_window_start=pickup.time_window_start,
            time_window_end=pickup.time_window_end,
            pickup_address=pickup.pickup_address,
            pickup_latitude=pickup.pickup_latitude,
            pickup_longitude=pickup.pickup_longitude,
            postal_code=pickup.postal_code,
            city=pickup.city,
            state=pickup.state,
            country=pickup.country,
            contact_name=pickup.contact_name,
            contact_phone=pickup.contact_phone,
            contact_email=pickup.contact_email,
            package_count=pickup.package_count,
            estimated_weight_kg=pickup.estimated_weight_kg,
            estimated_volume_m3=pickup.estimated_volume_m3,
            requires_packaging=pickup.requires_packaging,
            fragile_items=pickup.fragile_items,
            special_instructions=pickup.special_instructions,
            pickup_cost=pickup_cost
        )
        
        db.add(db_pickup)
        await db.commit()
        await db.refresh(db_pickup)
        
        # Create pickup packages if provided
        if pickup.packages:
            for pkg_data in pickup.packages:
                tracking_number = f"QTY{pickup_id}{len(pickup.packages):03d}"
                db_package = PickupPackage(
                    pickup_id=db_pickup.id,
                    description=pkg_data.get('description'),
                    category=pkg_data.get('category'),
                    weight_kg=pkg_data.get('weight_kg'),
                    tracking_number=tracking_number,
                    **{k: v for k, v in pkg_data.items() if k in ['package_reference', 'is_fragile', 'insurance_value']}
                )
                db.add(db_package)
        
        await db.commit()
        return PickupResponse.from_orm(db_pickup)
        
    except Exception as e:
        logger.error("Error creating pickup", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/pickups", response_model=Dict[str, Any])
async def get_pickups(
    customer_id: Optional[str] = None,
    status: Optional[PickupStatus] = None,
    pickup_date: Optional[date] = None,
    driver_id: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pickups with filtering"""
    try:
        # Build query
        stmt = select(Pickup)
        
        # Apply access control
        if not current_user.get('is_superuser') and 'pickups:read:all' not in current_user.get('permissions', []):
            # Users can only see their own pickups
            stmt = stmt.where(Pickup.customer_id == current_user['unique_id'])
        elif customer_id:
            stmt = stmt.where(Pickup.customer_id == customer_id)
        
        # Apply filters
        if status:
            stmt = stmt.where(Pickup.status == status.value)
        if pickup_date:
            stmt = stmt.where(Pickup.pickup_date == pickup_date)
        if driver_id:
            stmt = stmt.where(Pickup.assigned_driver_id == driver_id)
        
        # Get total count
        count_stmt = select(func.count(Pickup.id))
        if not current_user.get('is_superuser') and 'pickups:read:all' not in current_user.get('permissions', []):
            count_stmt = count_stmt.where(Pickup.customer_id == current_user['unique_id'])
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Pickup.pickup_date.desc(), Pickup.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        pickups = result.scalars().all()
        
        return {
            "pickups": [PickupResponse.from_orm(pickup) for pickup in pickups],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_previous": offset > 0
        }
        
    except Exception as e:
        logger.error("Error fetching pickups", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/pickups/{pickup_id}", response_model=PickupResponse)
async def get_pickup(
    pickup_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pickup by ID"""
    try:
        await validate_pickup_ownership(pickup_id, current_user, db)
        
        stmt = select(Pickup).where(Pickup.id == pickup_id)
        result = await db.execute(stmt)
        pickup = result.scalar_one_or_none()
        
        if not pickup:
            raise HTTPException(status_code=404, detail="Pickup not found")
        
        return PickupResponse.from_orm(pickup)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching pickup", pickup_id=pickup_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/pickups/{pickup_id}", response_model=PickupResponse)
async def update_pickup(
    pickup_id: int,
    pickup_update: PickupUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update pickup details"""
    try:
        await validate_pickup_ownership(pickup_id, current_user, db)
        
        stmt = select(Pickup).where(Pickup.id == pickup_id)
        result = await db.execute(stmt)
        pickup = result.scalar_one_or_none()
        
        if not pickup:
            raise HTTPException(status_code=404, detail="Pickup not found")
        
        # Only allow updates for scheduled or assigned pickups
        if pickup.status not in [PickupStatus.SCHEDULED, PickupStatus.ASSIGNED]:
            raise HTTPException(status_code=400, detail="Cannot update pickup in current status")
        
        # Update fields
        update_data = pickup_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pickup, field, value)
        
        pickup.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(pickup)
        
        return PickupResponse.from_orm(pickup)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating pickup", pickup_id=pickup_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/pickups/{pickup_id}/assign")
async def assign_driver(
    pickup_id: int,
    assignment: DriverAssignment,
    current_user = Depends(require_permissions(["pickups:assign"])),
    db: AsyncSession = Depends(get_db)
):
    """Assign driver to pickup"""
    try:
        stmt = select(Pickup).where(Pickup.id == pickup_id)
        result = await db.execute(stmt)
        pickup = result.scalar_one_or_none()
        
        if not pickup:
            raise HTTPException(status_code=404, detail="Pickup not found")
        
        if pickup.status != PickupStatus.SCHEDULED:
            raise HTTPException(status_code=400, detail="Pickup must be scheduled to assign driver")
        
        # Update pickup with assignment
        pickup.assigned_driver_id = assignment.driver_id
        pickup.assigned_vehicle_type = assignment.vehicle_type.value
        pickup.estimated_arrival_time = assignment.estimated_arrival_time
        pickup.status = PickupStatus.ASSIGNED
        pickup.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "pickup_id": pickup.pickup_id,
            "driver_id": assignment.driver_id,
            "vehicle_type": assignment.vehicle_type,
            "estimated_arrival_time": assignment.estimated_arrival_time,
            "status": PickupStatus.ASSIGNED,
            "assigned_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error assigning driver", pickup_id=pickup_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/pickups/{pickup_id}/complete")
async def complete_pickup(
    pickup_id: int,
    completion: PickupCompletion,
    current_user = Depends(require_permissions(["pickups:complete"])),
    db: AsyncSession = Depends(get_db)
):
    """Complete pickup"""
    try:
        stmt = select(Pickup).where(Pickup.id == pickup_id)
        result = await db.execute(stmt)
        pickup = result.scalar_one_or_none()
        
        if not pickup:
            raise HTTPException(status_code=404, detail="Pickup not found")
        
        if pickup.status not in [PickupStatus.ASSIGNED, PickupStatus.IN_PROGRESS]:
            raise HTTPException(status_code=400, detail="Cannot complete pickup in current status")
        
        # Update pickup with completion details
        pickup.status = PickupStatus.COMPLETED
        pickup.actual_pickup_time = completion.pickup_time
        pickup.actual_weight_kg = completion.actual_weight_kg
        pickup.actual_volume_m3 = completion.actual_volume_m3
        pickup.driver_notes = completion.driver_notes
        pickup.customer_signature = completion.customer_signature
        pickup.completion_photos = completion.completion_photos
        pickup.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Generate tracking numbers for packages
        tracking_numbers = []
        for i, pkg in enumerate(completion.packages):
            tracking_number = f"QTY{pickup.pickup_id}{i+1:03d}"
            tracking_numbers.append(tracking_number)
        
        return {
            "pickup_id": pickup.pickup_id,
            "status": PickupStatus.COMPLETED,
            "completion_details": completion.dict(),
            "completed_at": pickup.actual_pickup_time,
            "tracking_numbers": tracking_numbers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error completing pickup", pickup_id=pickup_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/pickups/{pickup_id}/cancel")
async def cancel_pickup(
    pickup_id: int,
    reason: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel pickup"""
    try:
        await validate_pickup_ownership(pickup_id, current_user, db)
        
        stmt = select(Pickup).where(Pickup.id == pickup_id)
        result = await db.execute(stmt)
        pickup = result.scalar_one_or_none()
        
        if not pickup:
            raise HTTPException(status_code=404, detail="Pickup not found")
        
        if pickup.status in [PickupStatus.COMPLETED, PickupStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Cannot cancel pickup in current status")
        
        pickup.status = PickupStatus.CANCELLED
        pickup.completion_notes = f"Cancelled: {reason}"
        pickup.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "pickup_id": pickup.pickup_id,
            "status": PickupStatus.CANCELLED,
            "cancellation_reason": reason,
            "cancelled_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling pickup", pickup_id=pickup_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/pickups/availability")
async def check_pickup_availability(
    pickup_date: date = Query(...),
    postal_code: str = Query(...),
    pickup_type: PickupType = Query(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check pickup availability for date and location"""
    try:
        # Get pickup zone configuration
        stmt = select(PickupZone).where(PickupZone.postal_codes.contains([postal_code]))
        result = await db.execute(stmt)
        zone = result.scalar_one_or_none()
        
        if not zone or not zone.service_available:
            return {
                "pickup_date": pickup_date,
                "postal_code": postal_code,
                "pickup_type": pickup_type,
                "available": False,
                "message": "Service not available in this area"
            }
        
        # Generate time slots based on zone configuration
        time_slots = []
        current_time = zone.service_start_time
        slot_duration = timedelta(minutes=zone.time_slot_duration_minutes)
        
        while current_time < zone.service_end_time:
            end_time = (datetime.combine(date.today(), current_time) + slot_duration).time()
            if end_time > zone.service_end_time:
                break
            
            # Check capacity for this time slot
            capacity_stmt = select(PickupCapacity).where(
                and_(
                    PickupCapacity.postal_code == postal_code,
                    PickupCapacity.pickup_date == pickup_date,
                    PickupCapacity.time_slot_start == current_time
                )
            )
            capacity_result = await db.execute(capacity_stmt)
            capacity = capacity_result.scalar_one_or_none()
            
            if capacity:
                available_slots = capacity.max_capacity - capacity.current_bookings
            else:
                available_slots = 10  # Default capacity
            
            time_slots.append({
                "start_time": current_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "available": available_slots > 0,
                "capacity": available_slots,
                "fee": zone.express_fee if pickup_type == PickupType.EXPRESS else zone.pickup_fee
            })
            
            current_time = end_time
        
        return {
            "pickup_date": pickup_date,
            "postal_code": postal_code,
            "pickup_type": pickup_type,
            "available_slots": time_slots,
            "zone_info": {
                "zone_name": zone.zone_name,
                "express_available": zone.express_available
            }
        }
        
    except Exception as e:
        logger.error("Error checking availability", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Route management endpoints
@app.post("/api/v1/routes", response_model=RouteResponse)
async def create_route(
    route: RouteRequest,
    current_user = Depends(require_permissions(["routes:create"])),
    db: AsyncSession = Depends(get_db)
):
    """Create pickup route for driver"""
    try:
        route_id = f"RT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        db_route = PickupRoute(
            route_id=route_id,
            driver_id=route.driver_id,
            route_name=f"Route {route.route_date}",
            route_date=route.route_date,
            vehicle_type=route.vehicle_type.value,
            total_pickups=len(route.pickup_ids)
        )
        
        db.add(db_route)
        await db.commit()
        await db.refresh(db_route)
        
        # Assign pickups to route
        for pickup_id in route.pickup_ids:
            stmt = update(Pickup).where(Pickup.id == pickup_id).values(
                assigned_route_id=db_route.id,
                assigned_driver_id=route.driver_id,
                assigned_vehicle_type=route.vehicle_type.value,
                status=PickupStatus.ASSIGNED
            )
            await db.execute(stmt)
        
        await db.commit()
        
        return RouteResponse.from_orm(db_route)
        
    except Exception as e:
        logger.error("Error creating route", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/routes/{route_id}/pickups")
async def get_route_pickups(
    route_id: int,
    current_user = Depends(require_permissions(["routes:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get pickups for a route"""
    try:
        stmt = select(Pickup).where(Pickup.assigned_route_id == route_id).order_by(Pickup.time_window_start)
        result = await db.execute(stmt)
        pickups = result.scalars().all()
        
        return {
            "route_id": route_id,
            "total_pickups": len(pickups),
            "pickups": [PickupResponse.from_orm(pickup) for pickup in pickups]
        }
        
    except Exception as e:
        logger.error("Error fetching route pickups", route_id=route_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

def calculate_pickup_cost(pickup_type: PickupType, weight_kg: float, postal_code: str) -> float:
    """Calculate pickup cost based on type, weight, and location"""
    base_cost = {
        PickupType.ON_DEMAND: 80.0,
        PickupType.SCHEDULED: 50.0,
        PickupType.RECURRING: 40.0,
        PickupType.EXPRESS: 120.0
    }.get(pickup_type, 50.0)
    
    # Weight surcharge (per kg over 5kg)
    weight_surcharge = max(0, weight_kg - 5) * 5.0
    
    # Zone surcharge (mock implementation)
    zone_surcharge = 20.0 if postal_code.startswith("1") else 0.0
    
    return base_cost + weight_surcharge + zone_surcharge

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="pickup-service",
            port=8005,
            check=consul.Check.http(
                url="http://pickup-service:8005/health",
                interval="10s",
                timeout="5s"
            )
        )
        logger.info(f"Registered {settings.service_name} with Consul")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {str(e)}")

@app.on_event("startup")
async def startup_event():
    await create_tables()
    await register_with_consul()
    logger.info(f"{settings.service_name} started")

@app.on_event("shutdown")
async def shutdown_event():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.deregister(f"{settings.service_name}-1")
        logger.info(f"Deregistered {settings.service_name} from Consul")
    except Exception as e:
        logger.error(f"Failed to deregister from Consul: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)