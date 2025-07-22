from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict, Any
import consul
from datetime import datetime, date, time, timedelta
from enum import Enum

logger = structlog.get_logger()

class Settings(BaseSettings):
    service_name: str = "pickup-service"
    database_url: str = "postgresql+asyncpg://pickup:pickup_pass@pickup-db:5432/pickup_db"
    redis_url: str = "redis://redis:6379/3"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="Pickup Service",
    description="Microservice for package pickup scheduling and management",
    version="2.0.0"
)

# Enums
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

# Pydantic models
class PickupRequest(BaseModel):
    customer_id: str
    pickup_type: PickupType
    pickup_date: date
    time_window_start: time
    time_window_end: time
    pickup_address: str
    contact_name: str
    contact_phone: str
    package_count: int = Field(ge=1)
    estimated_weight_kg: float
    special_instructions: Optional[str] = None
    requires_packaging: bool = False

class PickupResponse(BaseModel):
    pickup_id: str
    customer_id: str
    pickup_type: PickupType
    status: PickupStatus
    pickup_date: date
    time_window_start: time
    time_window_end: time
    pickup_address: str
    contact_name: str
    contact_phone: str
    package_count: int
    estimated_weight_kg: float
    assigned_driver_id: Optional[str] = None
    assigned_vehicle_type: Optional[VehicleType] = None
    estimated_arrival_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class PickupUpdate(BaseModel):
    pickup_date: Optional[date] = None
    time_window_start: Optional[time] = None
    time_window_end: Optional[time] = None
    pickup_address: Optional[str] = None
    contact_phone: Optional[str] = None
    package_count: Optional[int] = None
    special_instructions: Optional[str] = None

class DriverAssignment(BaseModel):
    driver_id: str
    vehicle_type: VehicleType
    estimated_arrival_time: datetime

class PickupCompletion(BaseModel):
    actual_package_count: int
    actual_weight_kg: float
    pickup_time: datetime
    packages: List[Dict[str, Any]]  # List of package details
    driver_notes: Optional[str] = None
    customer_signature: Optional[str] = None  # Base64 encoded signature

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.post("/api/v1/pickups", response_model=PickupResponse)
async def create_pickup(pickup: PickupRequest):
    # Mock implementation
    pickup_id = f"PU-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return PickupResponse(
        pickup_id=pickup_id,
        customer_id=pickup.customer_id,
        pickup_type=pickup.pickup_type,
        status=PickupStatus.SCHEDULED,
        pickup_date=pickup.pickup_date,
        time_window_start=pickup.time_window_start,
        time_window_end=pickup.time_window_end,
        pickup_address=pickup.pickup_address,
        contact_name=pickup.contact_name,
        contact_phone=pickup.contact_phone,
        package_count=pickup.package_count,
        estimated_weight_kg=pickup.estimated_weight_kg,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/v1/pickups/{pickup_id}", response_model=PickupResponse)
async def get_pickup(pickup_id: str):
    # Mock implementation
    if pickup_id.startswith("PU-"):
        return PickupResponse(
            pickup_id=pickup_id,
            customer_id="CUST-001",
            pickup_type=PickupType.SCHEDULED,
            status=PickupStatus.ASSIGNED,
            pickup_date=date.today(),
            time_window_start=time(14, 0),
            time_window_end=time(16, 0),
            pickup_address="123 Main St, Mexico City",
            contact_name="John Doe",
            contact_phone="+521234567890",
            package_count=3,
            estimated_weight_kg=15.5,
            assigned_driver_id="DRV-123",
            assigned_vehicle_type=VehicleType.VAN,
            estimated_arrival_time=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    else:
        raise HTTPException(status_code=404, detail="Pickup not found")

@app.get("/api/v1/pickups")
async def list_pickups(
    customer_id: Optional[str] = None,
    status: Optional[PickupStatus] = None,
    pickup_date: Optional[date] = None,
    driver_id: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    # Mock implementation
    pickups = [
        {
            "pickup_id": "PU-20250122001",
            "customer_id": "CUST-001",
            "status": "scheduled",
            "pickup_date": date.today().isoformat(),
            "time_window": "14:00-16:00",
            "address": "123 Main St",
            "package_count": 3
        },
        {
            "pickup_id": "PU-20250122002",
            "customer_id": "CUST-002",
            "status": "in_progress",
            "pickup_date": date.today().isoformat(),
            "time_window": "10:00-12:00",
            "address": "456 Oak Ave",
            "package_count": 1
        }
    ]
    return {
        "pickups": pickups,
        "total": len(pickups),
        "limit": limit,
        "offset": offset
    }

@app.put("/api/v1/pickups/{pickup_id}")
async def update_pickup(pickup_id: str, update: PickupUpdate):
    # Mock implementation
    return {
        "pickup_id": pickup_id,
        "message": "Pickup updated successfully",
        "updated_fields": [k for k, v in update.dict().items() if v is not None],
        "updated_at": datetime.utcnow()
    }

@app.post("/api/v1/pickups/{pickup_id}/assign")
async def assign_driver(pickup_id: str, assignment: DriverAssignment):
    # Mock implementation
    return {
        "pickup_id": pickup_id,
        "driver_id": assignment.driver_id,
        "vehicle_type": assignment.vehicle_type,
        "estimated_arrival_time": assignment.estimated_arrival_time,
        "status": PickupStatus.ASSIGNED,
        "assigned_at": datetime.utcnow()
    }

@app.post("/api/v1/pickups/{pickup_id}/complete")
async def complete_pickup(pickup_id: str, completion: PickupCompletion):
    # Mock implementation
    return {
        "pickup_id": pickup_id,
        "status": PickupStatus.COMPLETED,
        "completion_details": completion.dict(),
        "completed_at": datetime.utcnow(),
        "tracking_numbers": [f"QTY{pickup_id}{i:03d}" for i in range(completion.actual_package_count)]
    }

@app.post("/api/v1/pickups/{pickup_id}/cancel")
async def cancel_pickup(pickup_id: str, reason: str):
    # Mock implementation
    return {
        "pickup_id": pickup_id,
        "status": PickupStatus.CANCELLED,
        "cancellation_reason": reason,
        "cancelled_at": datetime.utcnow()
    }

@app.get("/api/v1/pickups/availability")
async def check_pickup_availability(
    pickup_date: date = Query(...),
    postal_code: str = Query(...),
    pickup_type: PickupType = Query(...)
):
    # Mock implementation
    time_slots = []
    for hour in range(8, 18, 2):  # 8 AM to 6 PM, 2-hour windows
        time_slots.append({
            "start_time": f"{hour:02d}:00",
            "end_time": f"{hour+2:02d}:00",
            "available": hour not in [12, 14],  # Mock some slots as unavailable
            "capacity": 10 if hour not in [12, 14] else 0
        })
    
    return {
        "pickup_date": pickup_date,
        "postal_code": postal_code,
        "pickup_type": pickup_type,
        "available_slots": time_slots,
        "next_available_date": (pickup_date + timedelta(days=1)).isoformat() if not any(slot["available"] for slot in time_slots) else None
    }

@app.get("/api/v1/pickups/{pickup_id}/tracking")
async def track_pickup(pickup_id: str):
    # Mock implementation
    return {
        "pickup_id": pickup_id,
        "status": PickupStatus.IN_PROGRESS,
        "driver": {
            "name": "Carlos Martinez",
            "phone": "+521234567890",
            "vehicle_type": "van",
            "license_plate": "ABC-123"
        },
        "location": {
            "latitude": 19.4326,
            "longitude": -99.1332,
            "last_updated": datetime.utcnow()
        },
        "estimated_arrival": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        "distance_km": 2.5
    }

@app.post("/api/v1/pickups/bulk")
async def create_bulk_pickups(pickups: List[PickupRequest]):
    # Mock implementation
    created_pickups = []
    for idx, pickup in enumerate(pickups):
        pickup_id = f"PU-BULK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{idx:03d}"
        created_pickups.append({
            "pickup_id": pickup_id,
            "customer_id": pickup.customer_id,
            "status": "scheduled"
        })
    
    return {
        "created_count": len(created_pickups),
        "pickups": created_pickups,
        "batch_id": f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="pickup-service",
            port=8003,
            check=consul.Check.http(
                url="http://pickup-service:8003/health",
                interval="10s",
                timeout="5s"
            )
        )
        logger.info(f"Registered {settings.service_name} with Consul")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {str(e)}")

@app.on_event("startup")
async def startup_event():
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
    uvicorn.run(app, host="0.0.0.0", port=8003)