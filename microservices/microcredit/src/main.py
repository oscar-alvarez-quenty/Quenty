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
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import uuid
import math

from .models import (
    CreditApplication, CreditAccount, CreditPayment, CreditDisbursement,
    CreditDocument, CreditScore, CreditPolicy, CreditLimit, Base,
    CreditStatus, CreditType, PaymentFrequency, RiskLevel, PaymentStatus
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
logger = structlog.get_logger("microcredit-service")

class Settings(BaseSettings):
    service_name: str = "microcredit-service"
    database_url: str = "postgresql+asyncpg://credit:credit_pass@microcredit-db:5432/microcredit_db"
    redis_url: str = "redis://redis:6379/5"
    consul_host: str = "consul"
    consul_port: int = 8500
    auth_service_url: str = "http://auth-service:8009"

    model_config = {"env_file": ".env"}

settings = Settings()

# Settings loaded successfully

# HTTP Bearer for token extraction
security = HTTPBearer()

app = FastAPI(
    title="Microcredit Service",
    description="Microservice for microcredit and financing management",
    version="2.0.0"
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

async def validate_credit_ownership(application_id: int, current_user: dict, db: AsyncSession):
    """Validate that user owns credit application or has admin permissions"""
    # Admin and manager can access all applications
    if current_user.get('is_superuser') or 'microcredit:read:all' in current_user.get('permissions', []):
        return True
    
    # Check if application belongs to current user
    stmt = select(CreditApplication).where(
        CreditApplication.id == application_id,
        CreditApplication.customer_id == current_user['unique_id']
    )
    result = await db.execute(stmt)
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=403,
            detail="Access denied: You can only access your own credit applications"
        )
    
    return True

# Pydantic models for API
class CreditApplicationRequest(BaseModel):
    credit_type: CreditType
    requested_amount: float = Field(gt=0, le=1000000)
    requested_term_months: int = Field(ge=3, le=60)
    payment_frequency: PaymentFrequency
    purpose: str = Field(min_length=10, max_length=1000)
    
    # Personal information
    monthly_income: float = Field(gt=0)
    employment_status: str
    employment_years: float = Field(ge=0)
    existing_debts: float = Field(ge=0, default=0)
    
    # Business information (optional)
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_revenue_monthly: Optional[float] = None
    business_years: Optional[float] = None

    @validator('business_revenue_monthly')
    def validate_business_info(cls, v, values):
        if values.get('credit_type') == CreditType.BUSINESS and not v:
            raise ValueError('Business revenue is required for business credits')
        return v

class CreditApplicationResponse(BaseModel):
    id: int
    application_id: str
    customer_id: str
    credit_type: CreditType
    requested_amount: Decimal
    requested_term_months: int
    payment_frequency: PaymentFrequency
    purpose: str
    status: CreditStatus
    approval_amount: Optional[Decimal] = None
    approval_term_months: Optional[int] = None
    interest_rate: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    credit_score: Optional[int] = None
    monthly_income: Decimal
    employment_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CreditDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    approved_amount: Optional[float] = None
    approved_term_months: Optional[int] = None
    interest_rate: Optional[float] = None
    rejection_reason: Optional[str] = None
    review_notes: Optional[str] = None

class CreditAccountResponse(BaseModel):
    id: int
    account_id: str
    customer_id: str
    principal_amount: Decimal
    interest_rate: float
    term_months: int
    payment_frequency: PaymentFrequency
    monthly_payment: Decimal
    status: CreditStatus
    current_balance: Decimal
    total_paid: Decimal
    next_payment_date: date
    payments_made: int
    payments_remaining: int
    days_overdue: int
    disbursed_at: Optional[datetime] = None
    maturity_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    payment_amount: float = Field(gt=0)
    payment_method: str
    reference_number: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    payment_id: str
    payment_amount: Decimal
    principal_amount: Decimal
    interest_amount: Decimal
    fee_amount: Decimal
    payment_date: date
    due_date: date
    status: PaymentStatus
    payment_method: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DisbursementRequest(BaseModel):
    disbursement_method: str = Field(pattern="^(bank_transfer|wallet|cash)$")
    destination_account: Optional[str] = None

class CreditScoreResponse(BaseModel):
    customer_id: str
    score: int
    risk_level: RiskLevel
    payment_history_score: Optional[int] = None
    credit_utilization_score: Optional[int] = None
    total_accounts: int
    active_accounts: int
    on_time_payments: int
    late_payments: int
    calculated_at: datetime

    class Config:
        from_attributes = True

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

# Credit Application endpoints
@app.post("/api/v1/applications", response_model=CreditApplicationResponse)
async def create_credit_application(
    application: CreditApplicationRequest,
    current_user = Depends(require_permissions(["microcredit:apply"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new credit application"""
    try:
        application_id = f"CA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate credit score and risk assessment
        credit_score = await calculate_credit_score(current_user['unique_id'], db)
        risk_level = determine_risk_level(credit_score, application.debt_to_income_ratio)
        
        db_application = CreditApplication(
            application_id=application_id,
            customer_id=current_user['unique_id'],
            credit_type=application.credit_type.value,
            requested_amount=Decimal(str(application.requested_amount)),
            requested_term_months=application.requested_term_months,
            payment_frequency=application.payment_frequency.value,
            purpose=application.purpose,
            monthly_income=Decimal(str(application.monthly_income)),
            employment_status=application.employment_status,
            employment_years=application.employment_years,
            existing_debts=Decimal(str(application.existing_debts)),
            business_name=application.business_name,
            business_type=application.business_type,
            business_revenue_monthly=Decimal(str(application.business_revenue_monthly)) if application.business_revenue_monthly else None,
            business_years=application.business_years,
            credit_score=credit_score,
            risk_level=risk_level.value,
            debt_to_income_ratio=float(application.existing_debts / application.monthly_income)
        )
        
        db.add(db_application)
        await db.commit()
        await db.refresh(db_application)
        
        return CreditApplicationResponse.from_orm(db_application)
        
    except Exception as e:
        logger.error("Error creating credit application", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/applications", response_model=Dict[str, Any])
async def get_credit_applications(
    status: Optional[CreditStatus] = None,
    credit_type: Optional[CreditType] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get credit applications with filtering"""
    try:
        # Build query
        stmt = select(CreditApplication)
        
        # Apply access control
        if not current_user.get('is_superuser') and 'microcredit:read:all' not in current_user.get('permissions', []):
            # Users can only see their own applications
            stmt = stmt.where(CreditApplication.customer_id == current_user['unique_id'])
        
        # Apply filters
        if status:
            stmt = stmt.where(CreditApplication.status == status.value)
        if credit_type:
            stmt = stmt.where(CreditApplication.credit_type == credit_type.value)
        
        # Get total count
        count_stmt = select(func.count(CreditApplication.id))
        if not current_user.get('is_superuser') and 'microcredit:read:all' not in current_user.get('permissions', []):
            count_stmt = count_stmt.where(CreditApplication.customer_id == current_user['unique_id'])
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination and ordering
        stmt = stmt.order_by(CreditApplication.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        applications = result.scalars().all()
        
        return {
            "applications": [CreditApplicationResponse.from_orm(app) for app in applications],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_previous": offset > 0
        }
        
    except Exception as e:
        logger.error("Error fetching credit applications", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/applications/{application_id}", response_model=CreditApplicationResponse)
async def get_credit_application(
    application_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get credit application by ID"""
    try:
        await validate_credit_ownership(application_id, current_user, db)
        
        stmt = select(CreditApplication).where(CreditApplication.id == application_id)
        result = await db.execute(stmt)
        application = result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(status_code=404, detail="Credit application not found")
        
        return CreditApplicationResponse.from_orm(application)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching credit application", application_id=application_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/applications/{application_id}/decision")
async def make_credit_decision(
    application_id: int,
    decision: CreditDecision,
    current_user = Depends(require_permissions(["microcredit:approve"])),
    db: AsyncSession = Depends(get_db)
):
    """Make a credit decision (approve/reject)"""
    try:
        stmt = select(CreditApplication).where(CreditApplication.id == application_id)
        result = await db.execute(stmt)
        application = result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(status_code=404, detail="Credit application not found")
        
        if application.status != CreditStatus.PENDING:
            raise HTTPException(status_code=400, detail="Application must be pending to make decision")
        
        if decision.decision == "approve":
            application.status = CreditStatus.APPROVED
            application.approval_amount = Decimal(str(decision.approved_amount))
            application.approval_term_months = decision.approved_term_months
            application.interest_rate = decision.interest_rate
            application.approved_at = datetime.utcnow()
            
            # Create credit account
            await create_credit_account(application, db)
            
        else:  # reject
            application.status = CreditStatus.REJECTED
            application.rejection_reason = decision.rejection_reason
            application.rejected_at = datetime.utcnow()
        
        application.reviewed_by = current_user['unique_id']
        application.review_notes = decision.review_notes
        application.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "application_id": application.application_id,
            "decision": decision.decision,
            "status": application.status,
            "decided_at": datetime.utcnow(),
            "reviewed_by": current_user['username']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error making credit decision", application_id=application_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Credit Account endpoints
@app.get("/api/v1/accounts", response_model=Dict[str, Any])
async def get_credit_accounts(
    status: Optional[CreditStatus] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get credit accounts"""
    try:
        # Build query
        stmt = select(CreditAccount)
        
        # Apply access control
        if not current_user.get('is_superuser') and 'microcredit:read:all' not in current_user.get('permissions', []):
            # Users can only see their own accounts
            stmt = stmt.where(CreditAccount.customer_id == current_user['unique_id'])
        
        # Apply filters
        if status:
            stmt = stmt.where(CreditAccount.status == status.value)
        
        # Get total count
        count_stmt = select(func.count(CreditAccount.id))
        if not current_user.get('is_superuser') and 'microcredit:read:all' not in current_user.get('permissions', []):
            count_stmt = count_stmt.where(CreditAccount.customer_id == current_user['unique_id'])
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination and ordering
        stmt = stmt.order_by(CreditAccount.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        
        return {
            "accounts": [CreditAccountResponse.from_orm(account) for account in accounts],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_previous": offset > 0
        }
        
    except Exception as e:
        logger.error("Error fetching credit accounts", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/accounts/{account_id}/disburse")
async def disburse_credit(
    account_id: int,
    disbursement: DisbursementRequest,
    current_user = Depends(require_permissions(["microcredit:disburse"])),
    db: AsyncSession = Depends(get_db)
):
    """Disburse approved credit"""
    try:
        stmt = select(CreditAccount).where(CreditAccount.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        if account.status != CreditStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Account must be approved for disbursement")
        
        # Create disbursement record
        disbursement_id = f"DIS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        db_disbursement = CreditDisbursement(
            disbursement_id=disbursement_id,
            account_id=account.id,
            amount=account.principal_amount,
            disbursement_method=disbursement.disbursement_method,
            destination_account=disbursement.destination_account,
            status="disbursed",
            approved_by=current_user['unique_id'],
            processed_by=current_user['unique_id'],
            approved_at=datetime.utcnow(),
            disbursed_at=datetime.utcnow()
        )
        
        db.add(db_disbursement)
        
        # Update account status
        account.status = CreditStatus.ACTIVE
        account.disbursed_at = datetime.utcnow()
        account.current_balance = account.principal_amount
        
        await db.commit()
        
        return {
            "account_id": account.account_id,
            "disbursement_id": disbursement_id,
            "amount": float(account.principal_amount),
            "method": disbursement.disbursement_method,
            "status": "disbursed",
            "disbursed_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error disbursing credit", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Payment endpoints
@app.post("/api/v1/accounts/{account_id}/payments", response_model=PaymentResponse)
async def make_payment(
    account_id: int,
    payment: PaymentRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Make a payment on credit account"""
    try:
        stmt = select(CreditAccount).where(CreditAccount.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        # Validate ownership or admin permissions
        if (account.customer_id != current_user['unique_id'] and 
            not current_user.get('is_superuser') and 
            'microcredit:payment:all' not in current_user.get('permissions', [])):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if account.status not in [CreditStatus.ACTIVE]:
            raise HTTPException(status_code=400, detail="Cannot make payment on inactive account")
        
        # Calculate payment breakdown
        payment_breakdown = calculate_payment_breakdown(
            Decimal(str(payment.payment_amount)), 
            account.current_balance, 
            account.interest_rate,
            account.monthly_payment
        )
        
        payment_id = f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        db_payment = CreditPayment(
            payment_id=payment_id,
            account_id=account.id,
            payment_amount=payment_breakdown['total_payment'],
            principal_amount=payment_breakdown['principal'],
            interest_amount=payment_breakdown['interest'],
            fee_amount=payment_breakdown['fees'],
            payment_date=date.today(),
            due_date=account.next_payment_date,
            status=PaymentStatus.PAID,
            payment_method=payment.payment_method,
            reference_number=payment.reference_number,
            processed_at=datetime.utcnow(),
            processed_by=current_user['unique_id']
        )
        
        db.add(db_payment)
        
        # Update account
        account.current_balance -= payment_breakdown['principal']
        account.total_paid += payment_breakdown['total_payment']
        account.total_interest_paid += payment_breakdown['interest']
        account.payments_made += 1
        account.payments_remaining -= 1
        account.last_payment_date = date.today()
        
        # Calculate next payment date
        if account.payment_frequency == PaymentFrequency.WEEKLY:
            account.next_payment_date = date.today() + timedelta(weeks=1)
        elif account.payment_frequency == PaymentFrequency.BIWEEKLY:
            account.next_payment_date = date.today() + timedelta(weeks=2)
        else:  # monthly
            account.next_payment_date = date.today() + timedelta(days=30)
        
        # Check if loan is paid off
        if account.current_balance <= Decimal('0.01'):
            account.status = CreditStatus.PAID
            account.closed_at = datetime.utcnow()
            account.current_balance = Decimal('0.00')
        
        await db.commit()
        await db.refresh(db_payment)
        
        return PaymentResponse.from_orm(db_payment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error making payment", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/accounts/{account_id}/payments", response_model=List[PaymentResponse])
async def get_account_payments(
    account_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get payment history for account"""
    try:
        # Validate account ownership
        stmt = select(CreditAccount).where(CreditAccount.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Credit account not found")
        
        if (account.customer_id != current_user['unique_id'] and 
            not current_user.get('is_superuser') and 
            'microcredit:read:all' not in current_user.get('permissions', [])):
            raise HTTPException(status_code=403, detail="Access denied")
        
        stmt = select(CreditPayment).where(CreditPayment.account_id == account_id).order_by(CreditPayment.payment_date.desc())
        result = await db.execute(stmt)
        payments = result.scalars().all()
        
        return [PaymentResponse.from_orm(payment) for payment in payments]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching account payments", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Credit Score endpoints
@app.get("/api/v1/credit-score/{customer_id}", response_model=CreditScoreResponse)
async def get_credit_score(
    customer_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer credit score"""
    try:
        # Validate access
        if (customer_id != current_user['unique_id'] and 
            not current_user.get('is_superuser') and 
            'microcredit:read:all' not in current_user.get('permissions', [])):
            raise HTTPException(status_code=403, detail="Access denied")
        
        stmt = select(CreditScore).where(CreditScore.customer_id == customer_id).order_by(CreditScore.calculated_at.desc()).limit(1)
        result = await db.execute(stmt)
        score = result.scalar_one_or_none()
        
        if not score:
            # Calculate new credit score
            credit_score = await calculate_credit_score(customer_id, db)
            risk_level = determine_risk_level(credit_score, 0.0)
            
            score = CreditScore(
                customer_id=customer_id,
                score=credit_score,
                risk_level=risk_level.value,
                scoring_model_version="1.0"
            )
            db.add(score)
            await db.commit()
            await db.refresh(score)
        
        return CreditScoreResponse.from_orm(score)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching credit score", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Helper functions
async def calculate_credit_score(customer_id: str, db: AsyncSession) -> int:
    """Calculate credit score for customer"""
    # Mock implementation - in real system would consider multiple factors
    base_score = 650
    
    # Check payment history
    stmt = select(func.count(CreditPayment.id)).where(
        CreditPayment.account_id.in_(
            select(CreditAccount.id).where(CreditAccount.customer_id == customer_id)
        ),
        CreditPayment.status == PaymentStatus.PAID
    )
    result = await db.execute(stmt)
    on_time_payments = result.scalar() or 0
    
    # Adjust score based on payment history
    payment_bonus = min(on_time_payments * 5, 100)
    
    return min(850, base_score + payment_bonus)

def determine_risk_level(credit_score: int, debt_to_income_ratio: float) -> RiskLevel:
    """Determine risk level based on credit score and DTI ratio"""
    if credit_score >= 750 and debt_to_income_ratio <= 0.2:
        return RiskLevel.LOW
    elif credit_score >= 650 and debt_to_income_ratio <= 0.3:
        return RiskLevel.MEDIUM
    elif credit_score >= 550 and debt_to_income_ratio <= 0.4:
        return RiskLevel.HIGH
    else:
        return RiskLevel.VERY_HIGH

async def create_credit_account(application: CreditApplication, db: AsyncSession):
    """Create credit account from approved application"""
    account_id = f"ACC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Calculate monthly payment
    monthly_rate = application.interest_rate / 100 / 12
    num_payments = application.approval_term_months
    
    if monthly_rate > 0:
        monthly_payment = application.approval_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
    else:
        monthly_payment = application.approval_amount / num_payments
    
    # Calculate payment frequency multiplier
    freq_multiplier = {
        PaymentFrequency.WEEKLY: 4.33,
        PaymentFrequency.BIWEEKLY: 2.17,
        PaymentFrequency.MONTHLY: 1
    }.get(PaymentFrequency(application.payment_frequency), 1)
    
    payment_amount = monthly_payment / freq_multiplier
    total_payments = int(num_payments * freq_multiplier)
    
    account = CreditAccount(
        account_id=account_id,
        application_id=application.id,
        customer_id=application.customer_id,
        principal_amount=application.approval_amount,
        interest_rate=application.interest_rate,
        term_months=application.approval_term_months,
        payment_frequency=application.payment_frequency,
        monthly_payment=payment_amount,
        current_balance=application.approval_amount,
        payments_remaining=total_payments,
        next_payment_date=date.today() + timedelta(days=30),
        first_payment_date=date.today() + timedelta(days=30),
        maturity_date=date.today() + timedelta(days=application.approval_term_months * 30)
    )
    
    db.add(account)
    return account

def calculate_payment_breakdown(payment_amount: Decimal, current_balance: Decimal, interest_rate: float, monthly_payment: Decimal) -> Dict[str, Decimal]:
    """Calculate payment breakdown between principal and interest"""
    monthly_interest_rate = Decimal(str(interest_rate / 100 / 12))
    
    # Calculate interest portion
    interest_amount = current_balance * monthly_interest_rate
    
    # Calculate principal portion
    principal_amount = payment_amount - interest_amount
    
    # Ensure principal doesn't exceed balance
    if principal_amount > current_balance:
        principal_amount = current_balance
        interest_amount = payment_amount - principal_amount
    
    return {
        'total_payment': payment_amount,
        'principal': principal_amount,
        'interest': interest_amount,
        'fees': Decimal('0.00')
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="microcredit-service",
            port=8006,
            check=consul.Check.http(
                url="http://microcredit-service:8006/health",
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
    uvicorn.run(app, host="0.0.0.0", port=8006)