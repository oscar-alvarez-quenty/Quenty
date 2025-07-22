from fastapi import FastAPI, HTTPException, Depends, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date
import structlog
import consul
import requests
import os
from decimal import Decimal

from .database import get_db, init_db, close_db
from .models import (
    Franchise, FranchiseContract, Territory, FranchisePayment, 
    FranchisePerformance, FranchiseAudit, FranchiseStatus, 
    ContractStatus, TerritoryStatus, PaymentStatus
)
from .schemas import (
    FranchiseCreate, FranchiseUpdate, FranchiseResponse, PaginatedFranchises,
    ContractCreate, ContractResponse, TerritoryCreate, TerritoryResponse, PaginatedTerritories,
    PaymentCreate, PaymentResponse, PaginatedPayments,
    PerformanceCreate, PerformanceResponse, AuditCreate, AuditResponse, AuditUpdate,
    StatusUpdate, HealthCheck, ErrorResponse
)

# Configure logging
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
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Settings
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8009")
CONSUL_HOST = os.getenv("CONSUL_HOST", "consul")
CONSUL_PORT = int(os.getenv("CONSUL_PORT", "8500"))
SERVICE_NAME = "franchise-service"

# Create FastAPI app
app = FastAPI(
    title="Quenty Franchise Service",
    description="Comprehensive franchise management microservice with territory management, contracts, payments, performance tracking, and audit capabilities",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token with auth service"""
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/api/v1/profile", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return response.json()
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

def require_permissions(permissions: List[str]):
    """Decorator to require specific permissions"""
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        # Superusers have all permissions
        if "*" in user_permissions:
            return current_user
            
        # Check if user has required permissions
        if not any(perm in user_permissions for perm in permissions + ["franchises:*"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return permission_checker

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        await init_db()
        await register_with_consul()
        logger.info("Franchise service started successfully")
    except Exception as e:
        logger.error("Failed to start franchise service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await deregister_from_consul()
        await close_db()
        logger.info("Franchise service shutdown successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

async def register_with_consul():
    """Register service with Consul"""
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    try:
        c.agent.service.register(
            name=SERVICE_NAME,
            service_id=f"{SERVICE_NAME}-1",
            address="franchise-service",
            port=8008,
            check=consul.Check.http(
                url="http://franchise-service:8008/health",
                interval="10s",
                timeout="5s"
            ),
            tags=["franchise", "management", "territory", "v2"]
        )
        logger.info(f"Registered {SERVICE_NAME} with Consul")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {str(e)}")

async def deregister_from_consul():
    """Deregister service from Consul"""
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    try:
        c.agent.service.deregister(f"{SERVICE_NAME}-1")
        logger.info(f"Deregistered {SERVICE_NAME} from Consul")
    except Exception as e:
        logger.error(f"Failed to deregister from Consul: {str(e)}")

# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        service=SERVICE_NAME,
        version="2.0.0",
        timestamp=datetime.utcnow(),
        dependencies={
            "database": "healthy",
            "auth_service": "healthy"
        }
    )

# Franchise management endpoints
@app.post("/api/v1/franchises", response_model=FranchiseResponse)
async def create_franchise(
    franchise_data: FranchiseCreate,
    current_user: dict = Depends(require_permissions(["franchises:create"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new franchise"""
    try:
        # Check if territory is available
        territory_stmt = select(Territory).where(Territory.territory_code == franchise_data.territory_code)
        territory_result = await db.execute(territory_stmt)
        territory = territory_result.scalar_one_or_none()
        
        if not territory or territory.status != TerritoryStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Territory not available"
            )
        
        # Create franchise
        franchise = Franchise(
            **franchise_data.dict(exclude={"contract_start_date", "contract_end_date", "contract_terms", "operational_hours", "services_offered", "equipment_list"}),
            created_by=str(current_user["id"])
        )
        
        # Handle optional fields
        if franchise_data.contract_start_date:
            franchise.contract_start_date = franchise_data.contract_start_date
        if franchise_data.contract_end_date:
            franchise.contract_end_date = franchise_data.contract_end_date
        if franchise_data.contract_terms:
            franchise.contract_terms = franchise_data.contract_terms
        if franchise_data.operational_hours:
            franchise.operational_hours = franchise_data.operational_hours
        if franchise_data.services_offered:
            franchise.services_offered = franchise_data.services_offered
        if franchise_data.equipment_list:
            franchise.equipment_list = franchise_data.equipment_list
        
        db.add(franchise)
        await db.flush()
        await db.refresh(franchise)
        
        # Reserve territory
        territory.status = TerritoryStatus.RESERVED
        territory.reserved_until = datetime.utcnow().replace(hour=23, minute=59, second=59)
        territory.reserved_by = str(current_user["id"])
        
        await db.commit()
        
        logger.info("Franchise created", franchise_id=franchise.franchise_id)
        return FranchiseResponse.from_orm(franchise)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Create franchise error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create franchise"
        )

@app.get("/api/v1/franchises", response_model=PaginatedFranchises)
async def list_franchises(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[FranchiseStatus] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    territory_code: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_permissions(["franchises:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of franchises"""
    try:
        # Build query
        stmt = select(Franchise)
        
        # Apply filters
        filters = []
        if status:
            filters.append(Franchise.status == status)
        if city:
            filters.append(Franchise.city.ilike(f"%{city}%"))
        if state:
            filters.append(Franchise.state.ilike(f"%{state}%"))
        if territory_code:
            filters.append(Franchise.territory_code == territory_code)
        if search:
            search_filter = or_(
                Franchise.name.ilike(f"%{search}%"),
                Franchise.franchisee_name.ilike(f"%{search}%"),
                Franchise.city.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        # Get total count
        count_stmt = select(func.count(Franchise.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Franchise.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        franchises = result.scalars().all()
        
        return PaginatedFranchises(
            franchises=[FranchiseResponse.from_orm(franchise) for franchise in franchises],
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total,
            has_previous=offset > 0
        )
        
    except Exception as e:
        logger.error("List franchises error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve franchises"
        )

@app.get("/api/v1/franchises/{franchise_id}", response_model=FranchiseResponse)
async def get_franchise(
    franchise_id: str,
    current_user: dict = Depends(require_permissions(["franchises:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get franchise by ID"""
    try:
        stmt = select(Franchise).where(Franchise.franchise_id == franchise_id)
        result = await db.execute(stmt)
        franchise = result.scalar_one_or_none()
        
        if not franchise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Franchise not found"
            )
        
        return FranchiseResponse.from_orm(franchise)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get franchise error", franchise_id=franchise_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve franchise"
        )

@app.put("/api/v1/franchises/{franchise_id}", response_model=FranchiseResponse)
async def update_franchise(
    franchise_id: str,
    update_data: FranchiseUpdate,
    current_user: dict = Depends(require_permissions(["franchises:update"])),
    db: AsyncSession = Depends(get_db)
):
    """Update franchise information"""
    try:
        stmt = select(Franchise).where(Franchise.franchise_id == franchise_id)
        result = await db.execute(stmt)
        franchise = result.scalar_one_or_none()
        
        if not franchise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Franchise not found"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(franchise, field, value)
        
        franchise.updated_at = datetime.utcnow()
        franchise.updated_by = str(current_user["id"])
        
        await db.commit()
        await db.refresh(franchise)
        
        logger.info("Franchise updated", franchise_id=franchise_id)
        return FranchiseResponse.from_orm(franchise)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update franchise error", franchise_id=franchise_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update franchise"
        )

@app.put("/api/v1/franchises/{franchise_id}/status")
async def update_franchise_status(
    franchise_id: str,
    status_update: StatusUpdate,
    current_user: dict = Depends(require_permissions(["franchises:update"])),
    db: AsyncSession = Depends(get_db)
):
    """Update franchise status"""
    try:
        stmt = select(Franchise).where(Franchise.franchise_id == franchise_id)
        result = await db.execute(stmt)
        franchise = result.scalar_one_or_none()
        
        if not franchise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Franchise not found"
            )
        
        old_status = franchise.status
        franchise.status = status_update.status
        franchise.updated_at = datetime.utcnow()
        franchise.updated_by = str(current_user["id"])
        
        # Handle status-specific logic
        if status_update.status == FranchiseStatus.ACTIVE and old_status != FranchiseStatus.ACTIVE:
            franchise.opening_date = status_update.effective_date or date.today()
        elif status_update.status == FranchiseStatus.TERMINATED:
            franchise.closure_date = status_update.effective_date or date.today()
        
        await db.commit()
        
        logger.info("Franchise status updated", 
                   franchise_id=franchise_id, 
                   old_status=old_status, 
                   new_status=status_update.status)
        
        return {
            "franchise_id": franchise_id,
            "old_status": old_status,
            "new_status": status_update.status,
            "reason": status_update.reason,
            "updated_at": datetime.utcnow(),
            "updated_by": current_user["username"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update franchise status error", franchise_id=franchise_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update franchise status"
        )

# Territory management endpoints
@app.get("/api/v1/territories", response_model=PaginatedTerritories)
async def list_territories(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[TerritoryStatus] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    current_user: dict = Depends(require_permissions(["territories:read"])),
    db: AsyncSession = Depends(get_db)
):
    """List available territories"""
    try:
        stmt = select(Territory)
        
        filters = [Territory.is_active == True]
        if status:
            filters.append(Territory.status == status)
        if country:
            filters.append(Territory.country.ilike(f"%{country}%"))
        if state:
            filters.append(Territory.state.ilike(f"%{state}%"))
        
        stmt = stmt.where(and_(*filters))
        
        # Get total count
        count_stmt = select(func.count(Territory.id)).where(and_(*filters))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination
        stmt = stmt.order_by(Territory.territory_code).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        territories = result.scalars().all()
        
        return PaginatedTerritories(
            territories=[TerritoryResponse.from_orm(territory) for territory in territories],
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total,
            has_previous=offset > 0
        )
        
    except Exception as e:
        logger.error("List territories error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve territories"
        )

@app.get("/api/v1/territories/{territory_code}")
async def check_territory_availability(
    territory_code: str,
    current_user: dict = Depends(require_permissions(["territories:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Check territory availability and details"""
    try:
        stmt = select(Territory).where(Territory.territory_code == territory_code)
        result = await db.execute(stmt)
        territory = result.scalar_one_or_none()
        
        if not territory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Territory not found"
            )
        
        # Calculate nearby franchises
        nearby_stmt = select(func.count(Franchise.id)).where(
            and_(
                Franchise.territory_code != territory_code,
                Franchise.state == territory.state,
                Franchise.status == FranchiseStatus.ACTIVE
            )
        )
        nearby_result = await db.execute(nearby_stmt)
        nearby_count = nearby_result.scalar()
        
        return {
            "territory_code": territory_code,
            "name": territory.name,
            "status": territory.status,
            "available": territory.status == TerritoryStatus.AVAILABLE,
            "reserved_until": territory.reserved_until,
            "nearby_franchises": nearby_count,
            "market_potential": territory.market_potential,
            "competition_level": territory.competition_level,
            "population": territory.population,
            "area_size_km2": float(territory.area_size) if territory.area_size else None,
            "average_income": float(territory.average_income) if territory.average_income else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Check territory error", territory_code=territory_code, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check territory"
        )

# Performance tracking endpoints
@app.get("/api/v1/franchises/{franchise_id}/performance")
async def get_franchise_performance(
    franchise_id: str,
    period_type: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly|annual)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(require_permissions(["franchises:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get franchise performance metrics"""
    try:
        # Verify franchise exists
        franchise_stmt = select(Franchise).where(Franchise.franchise_id == franchise_id)
        franchise_result = await db.execute(franchise_stmt)
        franchise = franchise_result.scalar_one_or_none()
        
        if not franchise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Franchise not found"
            )
        
        # Build performance query
        stmt = select(FranchisePerformance).where(
            FranchisePerformance.franchise_id == franchise.id
        )
        
        filters = []
        if period_type:
            filters.append(FranchisePerformance.period_type == period_type)
        if start_date:
            filters.append(FranchisePerformance.period_start >= start_date)
        if end_date:
            filters.append(FranchisePerformance.period_end <= end_date)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        stmt = stmt.order_by(FranchisePerformance.period_start.desc()).limit(12)
        
        result = await db.execute(stmt)
        performance_records = result.scalars().all()
        
        return {
            "franchise_id": franchise_id,
            "performance_history": [PerformanceResponse.from_orm(record) for record in performance_records],
            "summary": {
                "total_periods": len(performance_records),
                "avg_revenue": sum(float(r.revenue) for r in performance_records) / len(performance_records) if performance_records else 0,
                "avg_performance_score": sum(float(r.performance_score) for r in performance_records) / len(performance_records) if performance_records else 0,
                "current_ranking": performance_records[0].ranking if performance_records else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get franchise performance error", franchise_id=franchise_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance data"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)