from fastapi import FastAPI, HTTPException, Depends, Query, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
import structlog
import consul
import httpx
import json
import os
import logging
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

from .models import CustomerProfile, SupportTicket, TicketMessage, CustomerNote, CustomerInteraction, Base
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
logger = structlog.get_logger("customer-service")

class Settings(BaseSettings):
    service_name: str = "customer-service"
    database_url: str = "postgresql+asyncpg://customer:customer_pass@customer-db:5432/customer_db"
    redis_url: str = "redis://redis:6379/1"
    consul_host: str = "consul"
    consul_port: int = 8500
    auth_service_url: str = "http://auth-service:8003"  # Auth service URL

    class Config:
        env_file = ".env"

settings = Settings()

# HTTP Bearer for token extraction
security = HTTPBearer()

app = FastAPI(
    title="Customer Service",
    description="Customer relationship management and support",
    version="2.0.0"
)

# Prometheus metrics
customer_operations_total = Counter(
    'customer_operations_total',
    'Total number of customer operations',
    ['operation', 'status']
)
customer_request_duration = Histogram(
    'customer_request_duration_seconds',
    'Duration of customer requests in seconds',
    ['method', 'endpoint']
)
support_tickets_total = Counter(
    'customer_support_tickets_total',
    'Total number of support tickets',
    ['status', 'priority']
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

async def validate_customer_ownership(customer_id: int, current_user: dict, db: AsyncSession):
    """Validate that user owns customer profile or has admin permissions"""
    # Admin and manager can access all customers
    if current_user.get('is_superuser') or 'customers:read:all' in current_user.get('permissions', []):
        return True
    
    # Check if customer profile belongs to current user
    stmt = select(CustomerProfile).where(
        CustomerProfile.id == customer_id,
        CustomerProfile.user_id == current_user['unique_id']
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(
            status_code=403,
            detail="Access denied: You can only access your own customer data"
        )
    
    return True

# Pydantic models
class Address(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    is_default: Optional[bool] = False

class CustomerProfileCreate(BaseModel):
    user_id: str = Field(..., description="User ID from auth service")
    customer_type: str = Field("individual", description="Customer type")
    credit_limit: float = Field(0.0, ge=0)
    payment_terms: int = Field(30, ge=0, le=365)
    preferred_payment_method: Optional[str] = None
    default_shipping_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    shipping_preferences: Optional[Dict[str, Any]] = None

class CustomerProfileUpdate(BaseModel):
    customer_type: Optional[str] = None
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[int] = Field(None, ge=0, le=365)
    preferred_payment_method: Optional[str] = None
    default_shipping_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    shipping_preferences: Optional[Dict[str, Any]] = None
    customer_status: Optional[str] = None
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None

class CustomerProfileResponse(BaseModel):
    id: int
    user_id: str
    customer_type: str
    credit_limit: float
    credit_used: float
    available_credit: float
    payment_terms: int
    preferred_payment_method: Optional[str]
    default_shipping_address: Optional[Dict[str, Any]]
    billing_address: Optional[Dict[str, Any]]
    shipping_preferences: Optional[Dict[str, Any]]
    customer_status: str
    loyalty_points: int
    discount_percentage: float
    email_notifications: bool
    sms_notifications: bool
    marketing_emails: bool
    created_at: datetime
    updated_at: datetime
    
    @validator('available_credit', pre=False, always=True)
    def calculate_available_credit(cls, v, values):
        return values.get('credit_limit', 0) - values.get('credit_used', 0)
    
    class Config:
        from_attributes = True

class SupportTicketCreate(BaseModel):
    subject: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10)
    category: str = Field("general")
    priority: str = Field("medium")

class SupportTicketUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None

class SupportTicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    subject: str
    description: str
    category: str
    priority: str
    status: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TicketMessageCreate(BaseModel):
    message: str = Field(..., min_length=1)
    is_internal: bool = Field(False)
    attachments: Optional[List[str]] = None

class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    message: str
    is_internal: bool
    sender_id: str
    sender_type: str
    attachments: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CustomerNoteCreate(BaseModel):
    note: str = Field(..., min_length=5)
    category: str = Field("general")
    is_important: bool = Field(False)

class CustomerNoteResponse(BaseModel):
    id: int
    customer_id: int
    note: str
    category: str
    is_important: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Customer Profile endpoints
@app.get("/api/v1/customers", response_model=Dict[str, Any])
async def get_customers(
    limit: int = Query(20, le=100, ge=1),
    offset: int = Query(0, ge=0),
    customer_status: Optional[str] = None,
    customer_type: Optional[str] = None,
    current_user = Depends(require_permissions(["customers:read:all"])),
    db: AsyncSession = Depends(get_db)
):
    """Get customer profiles with filtering and pagination"""
    try:
        # Build query
        stmt = select(CustomerProfile)
        
        # Apply filters
        filters = []
        if customer_status:
            filters.append(CustomerProfile.customer_status == customer_status)
        if customer_type:
            filters.append(CustomerProfile.customer_type == customer_type)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        # Get total count
        count_stmt = select(func.count(CustomerProfile.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination
        stmt = stmt.order_by(CustomerProfile.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        customers = result.scalars().all()
        
        return {
            "customers": [CustomerProfileResponse.from_orm(customer) for customer in customers],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_previous": offset > 0
        }
        
    except Exception as e:
        logger.error("Error fetching customers", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/customers/{customer_id}", response_model=CustomerProfileResponse)
async def get_customer(
    customer_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer profile by ID"""
    try:
        # Validate ownership or admin permissions
        await validate_customer_ownership(customer_id, current_user, db)
        
        stmt = select(CustomerProfile).where(CustomerProfile.id == customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerProfileResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching customer", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/customers/by-user/{user_id}", response_model=CustomerProfileResponse)
async def get_customer_by_user_id(
    user_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer profile by user ID"""
    try:
        stmt = select(CustomerProfile).where(CustomerProfile.user_id == user_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer profile not found")
        
        return CustomerProfileResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching customer by user ID", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/customers", response_model=CustomerProfileResponse)
async def create_customer(
    customer_data: CustomerProfileCreate,
    current_user = Depends(require_permissions(["customers:create"])),
    db: AsyncSession = Depends(get_db)
):
    """Create customer profile"""
    try:
        # Check if customer profile already exists for this user
        stmt = select(CustomerProfile).where(CustomerProfile.user_id == customer_data.user_id)
        result = await db.execute(stmt)
        existing_customer = result.scalar_one_or_none()
        
        if existing_customer:
            raise HTTPException(
                status_code=409, 
                detail="Customer profile already exists for this user"
            )
        
        # Create customer profile
        customer = CustomerProfile(
            user_id=customer_data.user_id,
            customer_type=customer_data.customer_type,
            credit_limit=customer_data.credit_limit,
            payment_terms=customer_data.payment_terms,
            preferred_payment_method=customer_data.preferred_payment_method,
            default_shipping_address=customer_data.default_shipping_address.dict() if customer_data.default_shipping_address else None,
            billing_address=customer_data.billing_address.dict() if customer_data.billing_address else None,
            shipping_preferences=customer_data.shipping_preferences or {},
        )
        
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        
        return CustomerProfileResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating customer", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/customers/{customer_id}", response_model=CustomerProfileResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerProfileUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update customer profile"""
    try:
        # Get customer
        stmt = select(CustomerProfile).where(CustomerProfile.id == customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update fields
        update_data = customer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['default_shipping_address', 'billing_address'] and value:
                value = value.dict() if hasattr(value, 'dict') else value
            setattr(customer, field, value)
        
        customer.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(customer)
        
        return CustomerProfileResponse.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating customer", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/v1/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    current_user = Depends(require_permissions(["customers:delete"])),
    db: AsyncSession = Depends(get_db)
):
    """Delete customer profile"""
    try:
        # Get customer
        stmt = select(CustomerProfile).where(CustomerProfile.id == customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Instead of hard delete, mark as inactive
        customer.customer_status = "deleted"
        customer.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Customer profile deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting customer", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Support Ticket endpoints
@app.get("/api/v1/customers/{customer_id}/tickets", response_model=List[SupportTicketResponse])
async def get_customer_tickets(
    customer_id: int,
    status: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer support tickets"""
    try:
        # Validate ownership or admin permissions
        await validate_customer_ownership(customer_id, current_user, db)
        
        stmt = select(SupportTicket).where(SupportTicket.customer_id == customer_id)
        
        if status:
            stmt = stmt.where(SupportTicket.status == status)
        
        stmt = stmt.order_by(SupportTicket.created_at.desc())
        
        result = await db.execute(stmt)
        tickets = result.scalars().all()
        
        return [SupportTicketResponse.from_orm(ticket) for ticket in tickets]
        
    except Exception as e:
        logger.error("Error fetching customer tickets", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/customers/{customer_id}/tickets", response_model=SupportTicketResponse)
async def create_support_ticket(
    customer_id: int,
    ticket_data: SupportTicketCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create support ticket"""
    try:
        # Validate ownership or admin permissions  
        await validate_customer_ownership(customer_id, current_user, db)
        
        # Verify customer exists
        stmt = select(CustomerProfile).where(CustomerProfile.id == customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Generate ticket number
        ticket_number = f"TICK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        ticket = SupportTicket(
            ticket_number=ticket_number,
            customer_id=customer_id,
            subject=ticket_data.subject,
            description=ticket_data.description,
            category=ticket_data.category,
            priority=ticket_data.priority
        )
        
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        return SupportTicketResponse.from_orm(ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating support ticket", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/tickets/{ticket_id}/messages", response_model=List[TicketMessageResponse])
async def get_ticket_messages(
    ticket_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get ticket messages"""
    try:
        stmt = select(TicketMessage).where(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.created_at)
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return [TicketMessageResponse.from_orm(message) for message in messages]
        
    except Exception as e:
        logger.error("Error fetching ticket messages", ticket_id=ticket_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/tickets/{ticket_id}/messages", response_model=TicketMessageResponse)
async def add_ticket_message(
    ticket_id: int,
    message_data: TicketMessageCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add message to ticket"""
    try:
        # Verify ticket exists
        stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
        result = await db.execute(stmt)
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        message = TicketMessage(
            ticket_id=ticket_id,
            message=message_data.message,
            is_internal=message_data.is_internal,
            sender_id=current_user["unique_id"],
            sender_type="agent" if current_user["role"] in ["admin", "manager"] else "customer",
            attachments=message_data.attachments
        )
        
        db.add(message)
        
        # Update ticket timestamp
        ticket.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)
        
        return TicketMessageResponse.from_orm(message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding ticket message", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Customer Analytics
@app.get("/api/v1/customers/analytics")
async def get_customer_analytics(
    current_user = Depends(require_permissions(["analytics:view"])),
    db: AsyncSession = Depends(get_db)
):
    """Get customer analytics"""
    try:
        # Total customers
        total_stmt = select(func.count(CustomerProfile.id))
        total_result = await db.execute(total_stmt)
        total_customers = total_result.scalar()
        
        # Customers by status
        status_stmt = select(
            CustomerProfile.customer_status,
            func.count(CustomerProfile.id).label('count')
        ).group_by(CustomerProfile.customer_status)
        status_result = await db.execute(status_stmt)
        status_counts = {row[0]: row[1] for row in status_result.fetchall()}
        
        # Customers by type
        type_stmt = select(
            CustomerProfile.customer_type,
            func.count(CustomerProfile.id).label('count')
        ).group_by(CustomerProfile.customer_type)
        type_result = await db.execute(type_stmt)
        type_counts = {row[0]: row[1] for row in type_result.fetchall()}
        
        # Support ticket stats
        tickets_stmt = select(func.count(SupportTicket.id))
        tickets_result = await db.execute(tickets_stmt)
        total_tickets = tickets_result.scalar()
        
        return {
            "total_customers": total_customers,
            "customers_by_status": status_counts,
            "customers_by_type": type_counts,
            "total_support_tickets": total_tickets,
            "analytics_updated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Error fetching customer analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

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
    await create_tables()
    await register_with_consul()
    if INFO_MESSAGES and "CUST_I006" in INFO_MESSAGES:
        logger.info(
            INFO_MESSAGES["CUST_I006"]["message"].format(port=8001),
            **INFO_MESSAGES["CUST_I006"]
        )
    else:
        logger.info(f"{settings.service_name} started")

@app.on_event("shutdown")
async def shutdown_event():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.deregister(f"{settings.service_name}-1")
        logger.info(f"Deregistered {settings.service_name} from Consul")
    except Exception as e:
        logger.error(f"Failed to deregister from Consul: {str(e)}")