from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from pydantic_settings import BaseSettings
import structlog
from typing import Optional
import consul
from datetime import datetime

logger = structlog.get_logger()

class Settings(BaseSettings):
    service_name: str = "customer-service"
    database_url: str = "postgresql+asyncpg://customer:customer_pass@customer-db:5432/customer_db"
    redis_url: str = "redis://redis:6379/1"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="Customer Service",
    description="Microservice for customer management",
    version="2.0.0"
)

# Pydantic models
class CustomerCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    address: str
    city: str
    state: str
    postal_code: str
    country: str = "MX"

class CustomerResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    address: str
    city: str
    state: str
    postal_code: str
    country: str
    wallet_balance: float
    created_at: datetime
    updated_at: datetime
    is_active: bool
    kyc_verified: bool

class WalletTransaction(BaseModel):
    amount: float
    transaction_type: str  # "credit" or "debit"
    description: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.post("/api/v1/customers", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate):
    # Here you would implement the actual customer creation logic
    # For now, returning a mock response
    return CustomerResponse(
        id="CUST-001",
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone=customer.phone,
        address=customer.address,
        city=customer.city,
        state=customer.state,
        postal_code=customer.postal_code,
        country=customer.country,
        wallet_balance=0.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True,
        kyc_verified=False
    )

@app.get("/api/v1/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str):
    # Mock implementation
    if customer_id == "CUST-001":
        return CustomerResponse(
            id=customer_id,
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            phone="+521234567890",
            address="123 Main St",
            city="Mexico City",
            state="CDMX",
            postal_code="01000",
            country="MX",
            wallet_balance=1500.50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True,
            kyc_verified=True
        )
    else:
        raise HTTPException(status_code=404, detail="Customer not found")

@app.put("/api/v1/customers/{customer_id}")
async def update_customer(customer_id: str, customer: CustomerCreate):
    # Mock implementation
    return {"message": f"Customer {customer_id} updated successfully"}

@app.post("/api/v1/customers/{customer_id}/kyc")
async def verify_kyc(customer_id: str):
    # Mock KYC verification
    return {"customer_id": customer_id, "kyc_status": "verified", "verified_at": datetime.utcnow()}

@app.get("/api/v1/customers/{customer_id}/wallet")
async def get_wallet_balance(customer_id: str):
    # Mock wallet balance
    return {"customer_id": customer_id, "balance": 1500.50, "currency": "MXN"}

@app.post("/api/v1/customers/{customer_id}/wallet/transaction")
async def create_wallet_transaction(customer_id: str, transaction: WalletTransaction):
    # Mock transaction
    return {
        "transaction_id": "TXN-001",
        "customer_id": customer_id,
        "amount": transaction.amount,
        "type": transaction.transaction_type,
        "description": transaction.description,
        "timestamp": datetime.utcnow(),
        "status": "completed"
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="customer-service",
            port=8001,
            check=consul.Check.http(
                url="http://customer-service:8001/health",
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
    uvicorn.run(app, host="0.0.0.0", port=8001)