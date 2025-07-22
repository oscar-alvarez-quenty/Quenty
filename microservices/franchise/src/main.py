from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict
import consul
from datetime import datetime, date
from enum import Enum

logger = structlog.get_logger()

class Settings(BaseSettings):
    service_name: str = "franchise-service"
    database_url: str = "postgresql+asyncpg://franchise:franchise_pass@franchise-db:5432/franchise_db"
    redis_url: str = "redis://redis:6379/8"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="Franchise Service",
    description="Microservice for franchise management and operations",
    version="2.0.0"
)

# Enums
class FranchiseStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class FranchiseType(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    PREMIUM = "premium"

# Pydantic models
class FranchiseCreate(BaseModel):
    name: str
    owner_name: str
    owner_email: EmailStr
    phone: str
    address: str
    city: str
    state: str
    postal_code: str
    franchise_type: FranchiseType
    initial_investment: float
    territory_code: str

class FranchiseResponse(BaseModel):
    id: str
    name: str
    owner_name: str
    owner_email: str
    phone: str
    address: str
    city: str
    state: str
    postal_code: str
    franchise_type: FranchiseType
    status: FranchiseStatus
    initial_investment: float
    territory_code: str
    monthly_royalty_rate: float
    active_since: date
    created_at: datetime
    updated_at: datetime

class FranchisePerformance(BaseModel):
    franchise_id: str
    month: str
    total_sales: float
    total_orders: int
    average_order_value: float
    customer_satisfaction: float
    royalty_due: float

class FranchiseContract(BaseModel):
    contract_term_years: int
    royalty_percentage: float
    marketing_fee_percentage: float
    minimum_monthly_sales: float
    territory_exclusivity_radius_km: float

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.post("/api/v1/franchises", response_model=FranchiseResponse)
async def create_franchise(franchise: FranchiseCreate):
    # Mock implementation
    return FranchiseResponse(
        id="FRAN-001",
        name=franchise.name,
        owner_name=franchise.owner_name,
        owner_email=franchise.owner_email,
        phone=franchise.phone,
        address=franchise.address,
        city=franchise.city,
        state=franchise.state,
        postal_code=franchise.postal_code,
        franchise_type=franchise.franchise_type,
        status=FranchiseStatus.PENDING,
        initial_investment=franchise.initial_investment,
        territory_code=franchise.territory_code,
        monthly_royalty_rate=5.0,
        active_since=date.today(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/v1/franchises/{franchise_id}", response_model=FranchiseResponse)
async def get_franchise(franchise_id: str):
    # Mock implementation
    if franchise_id == "FRAN-001":
        return FranchiseResponse(
            id=franchise_id,
            name="Quenty Express - Centro",
            owner_name="Maria Rodriguez",
            owner_email="maria.rodriguez@example.com",
            phone="+525512345678",
            address="Av. Reforma 123",
            city="Mexico City",
            state="CDMX",
            postal_code="06600",
            franchise_type=FranchiseType.EXPRESS,
            status=FranchiseStatus.ACTIVE,
            initial_investment=500000.0,
            territory_code="CDMX-01",
            monthly_royalty_rate=5.0,
            active_since=date(2024, 1, 15),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    else:
        raise HTTPException(status_code=404, detail="Franchise not found")

@app.get("/api/v1/franchises")
async def list_franchises(
    status: Optional[FranchiseStatus] = None,
    franchise_type: Optional[FranchiseType] = None,
    city: Optional[str] = None
):
    # Mock implementation
    franchises = [
        {
            "id": "FRAN-001",
            "name": "Quenty Express - Centro",
            "city": "Mexico City",
            "status": "active",
            "franchise_type": "express"
        },
        {
            "id": "FRAN-002",
            "name": "Quenty Premium - Polanco",
            "city": "Mexico City",
            "status": "active",
            "franchise_type": "premium"
        }
    ]
    return {"franchises": franchises, "total": len(franchises)}

@app.put("/api/v1/franchises/{franchise_id}/status")
async def update_franchise_status(franchise_id: str, status: FranchiseStatus):
    # Mock implementation
    return {
        "franchise_id": franchise_id,
        "status": status,
        "updated_at": datetime.utcnow()
    }

@app.get("/api/v1/franchises/{franchise_id}/performance")
async def get_franchise_performance(franchise_id: str, month: str):
    # Mock implementation
    return FranchisePerformance(
        franchise_id=franchise_id,
        month=month,
        total_sales=150000.0,
        total_orders=320,
        average_order_value=468.75,
        customer_satisfaction=4.5,
        royalty_due=7500.0
    )

@app.post("/api/v1/franchises/{franchise_id}/contract")
async def create_franchise_contract(franchise_id: str, contract: FranchiseContract):
    # Mock implementation
    return {
        "franchise_id": franchise_id,
        "contract_id": "CONT-001",
        "contract_details": contract.dict(),
        "created_at": datetime.utcnow(),
        "status": "active"
    }

@app.get("/api/v1/franchises/territory/{territory_code}")
async def check_territory_availability(territory_code: str):
    # Mock implementation
    return {
        "territory_code": territory_code,
        "available": True,
        "nearby_franchises": 2,
        "population_density": "high",
        "market_potential_score": 8.5
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="franchise-service",
            port=8008,
            check=consul.Check.http(
                url="http://franchise-service:8008/health",
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
    uvicorn.run(app, host="0.0.0.0", port=8008)