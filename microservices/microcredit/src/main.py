from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict, Any
import consul
from datetime import datetime, date, timedelta
from enum import Enum
from decimal import Decimal

logger = structlog.get_logger()

class Settings(BaseSettings):
    service_name: str = "microcredit-service"
    database_url: str = "postgresql+asyncpg://microcredit:microcredit_pass@microcredit-db:5432/microcredit_db"
    redis_url: str = "redis://redis:6379/5"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="Microcredit Service",
    description="Microservice for microcredit and financing management",
    version="2.0.0"
)

# Enums
class CreditStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    PAID = "paid"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"

class CreditType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    INVENTORY = "inventory"
    EQUIPMENT = "equipment"
    EMERGENCY = "emergency"

class PaymentFrequency(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

# Pydantic models
class CreditApplication(BaseModel):
    customer_id: str
    credit_type: CreditType
    requested_amount: float = Field(gt=0)
    purpose: str
    term_months: int = Field(ge=1, le=24)
    payment_frequency: PaymentFrequency
    monthly_income: float
    monthly_expenses: float
    existing_credits: int = Field(ge=0)
    references: List[Dict[str, Any]] = Field(min_items=2)

class CreditResponse(BaseModel):
    credit_id: str
    customer_id: str
    credit_type: CreditType
    status: CreditStatus
    requested_amount: float
    approved_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    term_months: int
    payment_frequency: PaymentFrequency
    monthly_payment: Optional[float] = None
    total_to_pay: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    first_payment_date: Optional[date] = None

class PaymentSchedule(BaseModel):
    payment_number: int
    due_date: date
    principal_amount: float
    interest_amount: float
    total_amount: float
    balance_remaining: float
    status: str  # "pending", "paid", "overdue"

class CreditPayment(BaseModel):
    payment_amount: float
    payment_method: str  # "wallet", "bank_transfer", "card", "cash"
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class CreditScoring(BaseModel):
    customer_id: str
    credit_score: float
    risk_level: RiskLevel
    max_credit_amount: float
    payment_history_score: float
    income_stability_score: float
    debt_to_income_ratio: float
    recommendation: str
    factors: List[Dict[str, Any]]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.post("/api/v1/credits/apply", response_model=CreditResponse)
async def apply_for_credit(application: CreditApplication):
    # Mock implementation
    credit_id = f"CRD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Mock credit scoring
    risk_score = 750 if application.monthly_income > 20000 else 650
    risk_level = RiskLevel.LOW if risk_score > 700 else RiskLevel.MEDIUM
    approved_amount = min(application.requested_amount, application.monthly_income * 3)
    interest_rate = 15.0 if risk_level == RiskLevel.LOW else 20.0
    
    # Calculate payment
    monthly_rate = interest_rate / 100 / 12
    monthly_payment = (approved_amount * monthly_rate * (1 + monthly_rate) ** application.term_months) / \
                     ((1 + monthly_rate) ** application.term_months - 1)
    total_to_pay = monthly_payment * application.term_months
    
    return CreditResponse(
        credit_id=credit_id,
        customer_id=application.customer_id,
        credit_type=application.credit_type,
        status=CreditStatus.PENDING,
        requested_amount=application.requested_amount,
        approved_amount=approved_amount,
        interest_rate=interest_rate,
        term_months=application.term_months,
        payment_frequency=application.payment_frequency,
        monthly_payment=round(monthly_payment, 2),
        total_to_pay=round(total_to_pay, 2),
        risk_score=risk_score,
        risk_level=risk_level,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/v1/credits/{credit_id}", response_model=CreditResponse)
async def get_credit(credit_id: str):
    # Mock implementation
    if credit_id.startswith("CRD-"):
        return CreditResponse(
            credit_id=credit_id,
            customer_id="CUST-001",
            credit_type=CreditType.BUSINESS,
            status=CreditStatus.ACTIVE,
            requested_amount=50000.0,
            approved_amount=45000.0,
            interest_rate=18.0,
            term_months=12,
            payment_frequency=PaymentFrequency.MONTHLY,
            monthly_payment=4125.50,
            total_to_pay=49506.0,
            risk_score=720,
            risk_level=RiskLevel.LOW,
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow(),
            approved_at=datetime.utcnow() - timedelta(days=28),
            first_payment_date=date.today() + timedelta(days=2)
        )
    else:
        raise HTTPException(status_code=404, detail="Credit not found")

@app.get("/api/v1/credits")
async def list_credits(
    customer_id: Optional[str] = None,
    status: Optional[CreditStatus] = None,
    credit_type: Optional[CreditType] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    # Mock implementation
    credits = [
        {
            "credit_id": "CRD-20250122001",
            "customer_id": "CUST-001",
            "credit_type": "business",
            "status": "active",
            "approved_amount": 45000.0,
            "monthly_payment": 4125.50,
            "remaining_balance": 37125.50
        },
        {
            "credit_id": "CRD-20250115001",
            "customer_id": "CUST-002",
            "credit_type": "personal",
            "status": "active",
            "approved_amount": 15000.0,
            "monthly_payment": 1625.75,
            "remaining_balance": 12500.0
        }
    ]
    return {
        "credits": credits,
        "total": len(credits),
        "limit": limit,
        "offset": offset
    }

@app.put("/api/v1/credits/{credit_id}/approve")
async def approve_credit(credit_id: str, approved_amount: float, notes: Optional[str] = None):
    # Mock implementation
    return {
        "credit_id": credit_id,
        "status": CreditStatus.APPROVED,
        "approved_amount": approved_amount,
        "approved_by": "ADMIN-001",
        "approved_at": datetime.utcnow(),
        "notes": notes,
        "next_steps": "Credit will be disbursed within 24 hours"
    }

@app.put("/api/v1/credits/{credit_id}/reject")
async def reject_credit(credit_id: str, reason: str):
    # Mock implementation
    return {
        "credit_id": credit_id,
        "status": CreditStatus.REJECTED,
        "rejected_at": datetime.utcnow(),
        "rejection_reason": reason,
        "can_reapply_after": (date.today() + timedelta(days=30)).isoformat()
    }

@app.get("/api/v1/credits/{credit_id}/schedule")
async def get_payment_schedule(credit_id: str):
    # Mock implementation
    schedule = []
    principal_per_payment = 45000 / 12
    interest_per_payment = 375.50
    remaining_balance = 45000
    
    for i in range(12):
        remaining_balance -= principal_per_payment
        schedule.append(
            PaymentSchedule(
                payment_number=i + 1,
                due_date=date.today() + timedelta(days=30 * (i + 1)),
                principal_amount=principal_per_payment,
                interest_amount=interest_per_payment,
                total_amount=principal_per_payment + interest_per_payment,
                balance_remaining=remaining_balance,
                status="paid" if i < 2 else "pending"
            ).dict()
        )
    
    return {
        "credit_id": credit_id,
        "payment_schedule": schedule,
        "total_payments": 12,
        "payments_made": 2,
        "next_payment_date": (date.today() + timedelta(days=3)).isoformat()
    }

@app.post("/api/v1/credits/{credit_id}/payments")
async def make_payment(credit_id: str, payment: CreditPayment):
    # Mock implementation
    return {
        "payment_id": f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "credit_id": credit_id,
        "payment_amount": payment.payment_amount,
        "payment_method": payment.payment_method,
        "payment_status": "completed",
        "processed_at": datetime.utcnow(),
        "new_balance": 33000.0,
        "next_payment_due": (date.today() + timedelta(days=30)).isoformat()
    }

@app.get("/api/v1/credits/{credit_id}/payments")
async def get_payment_history(credit_id: str):
    # Mock implementation
    return {
        "credit_id": credit_id,
        "payments": [
            {
                "payment_id": "PAY-20250101001",
                "payment_date": "2025-01-01",
                "amount": 4125.50,
                "status": "completed",
                "payment_method": "wallet"
            },
            {
                "payment_id": "PAY-20250201001",
                "payment_date": "2025-02-01",
                "amount": 4125.50,
                "status": "completed",
                "payment_method": "bank_transfer"
            }
        ],
        "total_paid": 8251.0,
        "remaining_balance": 37125.50
    }

@app.get("/api/v1/credits/scoring/{customer_id}")
async def get_credit_scoring(customer_id: str):
    # Mock implementation
    return CreditScoring(
        customer_id=customer_id,
        credit_score=750.0,
        risk_level=RiskLevel.LOW,
        max_credit_amount=100000.0,
        payment_history_score=95.0,
        income_stability_score=85.0,
        debt_to_income_ratio=0.25,
        recommendation="Eligible for premium credit products",
        factors=[
            {"factor": "payment_history", "impact": "positive", "description": "Excellent payment history"},
            {"factor": "income_stability", "impact": "positive", "description": "Stable income for 2+ years"},
            {"factor": "debt_ratio", "impact": "positive", "description": "Low debt-to-income ratio"}
        ]
    )

@app.post("/api/v1/credits/{credit_id}/restructure")
async def restructure_credit(credit_id: str, new_term_months: int, reason: str):
    # Mock implementation
    return {
        "credit_id": credit_id,
        "restructure_id": f"RST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "original_term": 12,
        "new_term": new_term_months,
        "new_monthly_payment": 2500.0,
        "reason": reason,
        "status": "approved",
        "effective_date": date.today().isoformat()
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="microcredit-service",
            port=8005,
            check=consul.Check.http(
                url="http://microcredit-service:8005/health",
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
    uvicorn.run(app, host="0.0.0.0", port=8005)