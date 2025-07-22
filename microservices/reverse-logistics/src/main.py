from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import structlog
import consul
import requests
import os

from .database import get_db, init_db, close_db
from .models import (
    Return, ReturnItem, InspectionReport, ReturnStatusHistory, DisposalRecord, 
    ReturnMetrics, ReturnStatus, ReturnReason, ReturnType, DisposalMethod, InspectionResult
)
from .schemas import (
    ReturnCreate, ReturnUpdate, ReturnResponse, ReturnItemResponse, PaginatedReturns,
    StatusUpdate, ReturnApproval, ReturnRejection, PickupSchedule,
    InspectionReportCreate, InspectionReportResponse, PaginatedInspections,
    ReturnProcessing, ReturnProcessingResponse, DisposalRecordCreate, DisposalRecordResponse, PaginatedDisposals,
    ReturnsSummary, DispositionInventory, BatchProcessRequest, BatchProcessResponse,
    HealthCheck, ErrorResponse
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
SERVICE_NAME = "reverse-logistics-service"

app = FastAPI(
    title="Quenty Reverse Logistics Service",
    description="Comprehensive returns, exchanges, and reverse logistics management microservice with tracking, inspection, and disposal capabilities",
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
        if not any(perm in user_permissions for perm in permissions + ["returns:*"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return permission_checker

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        await init_db()
        await register_with_consul()
        logger.info("Reverse logistics service started successfully")
    except Exception as e:
        logger.error("Failed to start reverse logistics service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await deregister_from_consul()
        await close_db()
        logger.info("Reverse logistics service shutdown successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

async def register_with_consul():
    """Register service with Consul"""
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    try:
        c.agent.service.register(
            name=SERVICE_NAME,
            service_id=f"{SERVICE_NAME}-1",
            address="reverse-logistics-service",
            port=8007,
            check=consul.Check.http(
                url="http://reverse-logistics-service:8007/health",
                interval="10s",
                timeout="5s"
            ),
            tags=["returns", "logistics", "reverse", "v2"]
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

@app.post("/api/v1/returns", response_model=ReturnResponse)
async def create_return_request(
    return_request: ReturnCreate,
    current_user: dict = Depends(require_permissions(["returns:create"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new return request"""
    try:
        # Calculate refund multipliers based on return reason
        refund_multiplier = {
            ReturnReason.DAMAGED: 1.0,
            ReturnReason.DEFECTIVE: 1.0,
            ReturnReason.WRONG_ITEM: 1.0,
            ReturnReason.NOT_AS_DESCRIBED: 1.0,
            ReturnReason.CHANGE_OF_MIND: 0.9,  # 10% restocking fee
            ReturnReason.SIZE_ISSUE: 0.95,
            ReturnReason.OTHER: 0.95
        }
        
        # Mock original order value (in a real system, fetch from order service)
        original_value = Decimal("1500.0")
        estimated_refund = original_value * Decimal(str(refund_multiplier.get(return_request.return_reason, 0.9)))
        
        # Calculate return shipping cost
        return_shipping_cost = Decimal("0.0") if return_request.return_reason in [
            ReturnReason.DAMAGED, ReturnReason.DEFECTIVE, ReturnReason.WRONG_ITEM
        ] else Decimal("50.0")
        
        # Create return record
        return_record = Return(
            original_order_id=return_request.original_order_id,
            customer_id=return_request.customer_id,
            return_type=return_request.return_type,
            return_reason=return_request.return_reason,
            description=return_request.description,
            preferred_resolution=return_request.preferred_resolution,
            original_order_value=original_value,
            estimated_refund_amount=estimated_refund,
            return_shipping_cost=return_shipping_cost,
            pickup_address=return_request.return_address,
            photos=return_request.photos or [],
            estimated_pickup_date=date.today() + timedelta(days=2),
            estimated_processing_time="3-5 business days",
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_by=str(current_user["id"])
        )
        
        # Generate authorization number
        return_record.return_authorization_number = f"RMA{return_record.return_id}"
        
        db.add(return_record)
        await db.flush()
        await db.refresh(return_record)
        
        # Add return items
        for item_data in return_request.items:
            return_item = ReturnItem(
                return_id=return_record.id,
                **item_data.dict()
            )
            db.add(return_item)
        
        # Add status history
        status_history = ReturnStatusHistory(
            return_id=return_record.id,
            new_status=ReturnStatus.REQUESTED,
            status_reason="Return request created",
            changed_by=str(current_user["id"])
        )
        db.add(status_history)
        
        await db.commit()
        
        # Reload with items
        stmt = select(Return).options(selectinload(Return.items)).where(Return.id == return_record.id)
        result = await db.execute(stmt)
        return_with_items = result.scalar_one()
        
        logger.info("Return created", return_id=return_record.return_id)
        return ReturnResponse.model_validate(return_with_items)
        
    except Exception as e:
        logger.error("Create return error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create return request"
        )

@app.get("/api/v1/returns/{return_id}", response_model=ReturnResponse)
async def get_return(
    return_id: str,
    current_user: dict = Depends(require_permissions(["returns:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get return by ID"""
    try:
        stmt = select(Return).options(
            selectinload(Return.items)
        ).where(Return.return_id == return_id)
        result = await db.execute(stmt)
        return_record = result.scalar_one_or_none()
        
        if not return_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return not found"
            )
        
        return ReturnResponse.model_validate(return_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get return error", return_id=return_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve return"
        )

@app.get("/api/v1/returns", response_model=PaginatedReturns)
async def list_returns(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    customer_id: Optional[str] = None,
    status: Optional[ReturnStatus] = None,
    return_type: Optional[ReturnType] = None,
    return_reason: Optional[ReturnReason] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_permissions(["returns:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of returns"""
    try:
        # Build query
        stmt = select(Return).options(selectinload(Return.items))
        
        # Apply filters
        filters = []
        if customer_id:
            filters.append(Return.customer_id == customer_id)
        if status:
            filters.append(Return.status == status)
        if return_type:
            filters.append(Return.return_type == return_type)
        if return_reason:
            filters.append(Return.return_reason == return_reason)
        if date_from:
            filters.append(Return.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(Return.created_at <= datetime.combine(date_to, datetime.max.time()))
        if search:
            search_filter = or_(
                Return.return_id.ilike(f"%{search}%"),
                Return.original_order_id.ilike(f"%{search}%"),
                Return.return_authorization_number.ilike(f"%{search}%"),
                Return.description.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        # Get total count
        count_stmt = select(func.count(Return.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination and ordering
        stmt = stmt.order_by(Return.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        returns = result.scalars().all()
        
        return PaginatedReturns(
            returns=[ReturnResponse.model_validate(return_record) for return_record in returns],
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total,
            has_previous=offset > 0
        )
        
    except Exception as e:
        logger.error("List returns error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve returns"
        )

@app.put("/api/v1/returns/{return_id}/approve")
async def approve_return(
    return_id: str,
    approval: ReturnApproval,
    current_user: dict = Depends(require_permissions(["returns:approve"])),
    db: AsyncSession = Depends(get_db)
):
    """Approve return request"""
    try:
        stmt = select(Return).where(Return.return_id == return_id)
        result = await db.execute(stmt)
        return_record = result.scalar_one_or_none()
        
        if not return_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return not found"
            )
        
        if return_record.status != ReturnStatus.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return cannot be approved in current status"
            )
        
        # Update return status
        return_record.status = ReturnStatus.APPROVED
        return_record.approval_notes = approval.approval_notes
        return_record.approved_at = datetime.utcnow()
        return_record.estimated_pickup_date = approval.estimated_pickup_date or date.today() + timedelta(days=2)
        if approval.pickup_address:
            return_record.pickup_address = approval.pickup_address
        return_record.updated_at = datetime.utcnow()
        
        # Add status history
        status_history = ReturnStatusHistory(
            return_id=return_record.id,
            previous_status=ReturnStatus.REQUESTED,
            new_status=ReturnStatus.APPROVED,
            status_reason="Return approved by administrator",
            notes=approval.approval_notes,
            changed_by=str(current_user["id"])
        )
        db.add(status_history)
        
        await db.commit()
        
        logger.info("Return approved", return_id=return_id)
        
        return {
            "return_id": return_id,
            "status": ReturnStatus.APPROVED,
            "approved_at": return_record.approved_at,
            "approval_notes": approval.approval_notes,
            "next_steps": "Return shipping label will be emailed to customer",
            "pickup_scheduled_for": return_record.estimated_pickup_date.isoformat() if return_record.estimated_pickup_date else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Approve return error", return_id=return_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve return"
        )

@app.put("/api/v1/returns/{return_id}/reject")
async def reject_return(
    return_id: str,
    rejection: ReturnRejection,
    current_user: dict = Depends(require_permissions(["returns:approve"])),
    db: AsyncSession = Depends(get_db)
):
    """Reject return request"""
    try:
        stmt = select(Return).where(Return.return_id == return_id)
        result = await db.execute(stmt)
        return_record = result.scalar_one_or_none()
        
        if not return_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return not found"
            )
        
        if return_record.status not in [ReturnStatus.REQUESTED, ReturnStatus.INSPECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return cannot be rejected in current status"
            )
        
        # Update return status
        return_record.status = ReturnStatus.REJECTED
        return_record.rejection_reason = rejection.rejection_reason
        return_record.rejected_at = datetime.utcnow()
        return_record.processing_notes = rejection.detailed_explanation
        return_record.updated_at = datetime.utcnow()
        
        # Add status history
        status_history = ReturnStatusHistory(
            return_id=return_record.id,
            previous_status=return_record.status,
            new_status=ReturnStatus.REJECTED,
            status_reason=rejection.rejection_reason,
            notes=rejection.detailed_explanation,
            changed_by=str(current_user["id"])
        )
        db.add(status_history)
        
        await db.commit()
        
        logger.info("Return rejected", return_id=return_id, reason=rejection.rejection_reason)
        
        return {
            "return_id": return_id,
            "status": ReturnStatus.REJECTED,
            "rejected_at": return_record.rejected_at,
            "rejection_reason": rejection.rejection_reason,
            "detailed_explanation": rejection.detailed_explanation,
            "appeal_available": rejection.appeal_available,
            "appeal_deadline": (date.today() + timedelta(days=7)).isoformat() if rejection.appeal_available else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Reject return error", return_id=return_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject return"
        )

@app.post("/api/v1/returns/{return_id}/schedule-pickup")
async def schedule_return_pickup(
    return_id: str,
    pickup: PickupSchedule,
    current_user: dict = Depends(require_permissions(["returns:schedule"])),
    db: AsyncSession = Depends(get_db)
):
    """Schedule pickup for approved return"""
    try:
        stmt = select(Return).where(Return.return_id == return_id)
        result = await db.execute(stmt)
        return_record = result.scalar_one_or_none()
        
        if not return_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return not found"
            )
        
        if return_record.status != ReturnStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return must be approved before scheduling pickup"
            )
        
        # Update return with pickup details
        return_record.status = ReturnStatus.PICKUP_SCHEDULED
        return_record.estimated_pickup_date = pickup.pickup_date
        if pickup.pickup_address:
            return_record.pickup_address = pickup.pickup_address
        return_record.tracking_number = f"QTYRET{return_record.return_id}"
        return_record.carrier = "Quenty Logistics"
        return_record.updated_at = datetime.utcnow()
        
        # Add status history
        status_history = ReturnStatusHistory(
            return_id=return_record.id,
            previous_status=ReturnStatus.APPROVED,
            new_status=ReturnStatus.PICKUP_SCHEDULED,
            status_reason="Pickup scheduled",
            notes=f"Time window: {pickup.time_window}. {pickup.special_instructions or ''}",
            tracking_number=return_record.tracking_number,
            carrier="Quenty Logistics",
            changed_by=str(current_user["id"])
        )
        db.add(status_history)
        
        await db.commit()
        
        logger.info("Pickup scheduled", return_id=return_id, pickup_date=pickup.pickup_date)
        
        return {
            "return_id": return_id,
            "status": ReturnStatus.PICKUP_SCHEDULED,
            "pickup_date": pickup.pickup_date.isoformat(),
            "time_window": pickup.time_window,
            "pickup_id": f"PU-{return_record.return_id}",
            "tracking_number": return_record.tracking_number,
            "carrier": "Quenty Logistics",
            "special_instructions": pickup.special_instructions,
            "scheduled_at": datetime.utcnow()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Schedule pickup error", return_id=return_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule pickup"
        )

@app.post("/api/v1/returns/{return_id}/inspection", response_model=InspectionReportResponse)
async def create_inspection_report(
    return_id: str,
    inspection: InspectionReportCreate,
    current_user: dict = Depends(require_permissions(["returns:inspect"])),
    db: AsyncSession = Depends(get_db)
):
    """Create inspection report for returned item"""
    try:
        # Verify return exists and is in correct status
        return_stmt = select(Return).where(Return.return_id == return_id)
        return_result = await db.execute(return_stmt)
        return_record = return_result.scalar_one_or_none()
        
        if not return_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return not found"
            )
        
        if return_record.status not in [ReturnStatus.RECEIVED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return must be received before inspection"
            )
        
        # Create inspection report
        inspection_report = InspectionReport(
            return_id=return_record.id,
            inspector_name=current_user.get("full_name", "Inspector"),
            original_value=return_record.original_order_value,
            **inspection.dict()
        )
        
        # Calculate net recovery value
        inspection_report.net_recovery = (inspection_report.resale_value or Decimal("0")) - (inspection_report.refurbishment_cost or Decimal("0"))
        
        db.add(inspection_report)
        await db.flush()
        await db.refresh(inspection_report)
        
        # Update return status to inspected
        return_record.status = ReturnStatus.INSPECTED
        return_record.updated_at = datetime.utcnow()
        
        # Add status history
        status_history = ReturnStatusHistory(
            return_id=return_record.id,
            previous_status=ReturnStatus.RECEIVED,
            new_status=ReturnStatus.INSPECTED,
            status_reason="Item inspection completed",
            notes=f"Overall condition: {inspection.overall_condition}",
            changed_by=str(current_user["id"])
        )
        db.add(status_history)
        
        await db.commit()
        
        logger.info("Inspection report created", 
                   return_id=return_id, 
                   inspection_id=inspection_report.inspection_id,
                   condition=inspection.overall_condition)
        
        return InspectionReportResponse.model_validate(inspection_report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Create inspection error", return_id=return_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create inspection report"
        )

@app.post("/api/v1/returns/{return_id}/process", response_model=ReturnProcessingResponse)
async def process_return(
    return_id: str,
    processing: ReturnProcessing,
    current_user: dict = Depends(require_permissions(["returns:process"])),
    db: AsyncSession = Depends(get_db)
):
    """Process inspected return"""
    try:
        stmt = select(Return).where(Return.return_id == return_id)
        result = await db.execute(stmt)
        return_record = result.scalar_one_or_none()
        
        if not return_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return not found"
            )
        
        if return_record.status != ReturnStatus.INSPECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return must be inspected before processing"
            )
        
        # Map processing actions to statuses
        status_mapping = {
            "approve_full_refund": ReturnStatus.REFUNDED,
            "approve_partial_refund": ReturnStatus.REFUNDED,
            "approve_exchange": ReturnStatus.EXCHANGED,
            "reject": ReturnStatus.REJECTED
        }
        
        new_status = status_mapping.get(processing.processing_action, ReturnStatus.PROCESSED)
        
        # Update return record
        return_record.status = new_status
        return_record.actual_refund_amount = processing.refund_amount
        return_record.processing_fee = processing.processing_fee or Decimal("0")
        return_record.processing_notes = processing.processing_notes
        return_record.requires_customer_action = processing.requires_customer_action
        return_record.customer_action_required = processing.customer_action_required
        return_record.processed_at = datetime.utcnow()
        return_record.processed_by = str(current_user["id"])
        return_record.updated_at = datetime.utcnow()
        
        # Add status history
        status_history = ReturnStatusHistory(
            return_id=return_record.id,
            previous_status=ReturnStatus.INSPECTED,
            new_status=new_status,
            status_reason=f"Processing action: {processing.processing_action}",
            notes=processing.processing_notes,
            changed_by=str(current_user["id"])
        )
        db.add(status_history)
        
        await db.commit()
        
        logger.info("Return processed", 
                   return_id=return_id, 
                   action=processing.processing_action,
                   new_status=new_status)
        
        return ReturnProcessingResponse(
            return_id=return_id,
            processing_action=processing.processing_action,
            status=new_status,
            refund_amount=processing.refund_amount,
            exchange_item_id=processing.exchange_item_id,
            exchange_quantity=processing.exchange_quantity,
            processing_fee=processing.processing_fee,
            processed_at=return_record.processed_at,
            processing_notes=processing.processing_notes,
            expected_refund_time="3-5 business days" if "refund" in processing.processing_action else None,
            requires_customer_action=processing.requires_customer_action,
            customer_action_required=processing.customer_action_required
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Process return error", return_id=return_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process return"
        )

@app.get("/api/v1/returns/{return_id}/tracking")
async def track_return(
    return_id: str,
    current_user: dict = Depends(require_permissions(["returns:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Track return progress"""
    try:
        # Get return record
        return_stmt = select(Return).where(Return.return_id == return_id)
        return_result = await db.execute(return_stmt)
        return_record = return_result.scalar_one_or_none()
        
        if not return_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return not found"
            )
        
        # Get status history
        history_stmt = select(ReturnStatusHistory).where(
            ReturnStatusHistory.return_id == return_record.id
        ).order_by(ReturnStatusHistory.changed_at)
        history_result = await db.execute(history_stmt)
        status_events = history_result.scalars().all()
        
        # Build tracking events
        events = []
        for event in status_events:
            events.append({
                "timestamp": event.changed_at.isoformat(),
                "status": event.new_status,
                "location": event.location or "Processing Center",
                "description": event.status_reason or "Status updated",
                "notes": event.notes,
                "tracking_number": event.tracking_number,
                "carrier": event.carrier
            })
        
        # Determine current location based on status
        location_mapping = {
            ReturnStatus.REQUESTED: "Request Submitted",
            ReturnStatus.APPROVED: "Approval Center",
            ReturnStatus.PICKUP_SCHEDULED: "Customer Address",
            ReturnStatus.PICKED_UP: "In Transit",
            ReturnStatus.IN_TRANSIT: "Distribution Center",
            ReturnStatus.RECEIVED: "Return Processing Center",
            ReturnStatus.INSPECTED: "Quality Control",
            ReturnStatus.PROCESSED: "Processing Complete",
            ReturnStatus.REFUNDED: "Refund Processed",
            ReturnStatus.EXCHANGED: "Exchange Processed",
            ReturnStatus.DISPOSED: "Disposal Complete"
        }
        
        current_location = location_mapping.get(return_record.status, "Processing Center")
        
        # Calculate estimated completion
        estimated_completion = None
        if return_record.status in [ReturnStatus.RECEIVED, ReturnStatus.INSPECTED]:
            estimated_completion = datetime.utcnow() + timedelta(days=2)
        
        return {
            "return_id": return_id,
            "tracking_number": return_record.tracking_number or f"QTYRET{return_id}",
            "current_status": return_record.status,
            "current_location": current_location,
            "carrier": return_record.carrier,
            "events": events,
            "estimated_processing_completion": estimated_completion.isoformat() if estimated_completion else None,
            "last_updated": return_record.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Track return error", return_id=return_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track return"
        )

# Additional endpoints can be implemented as needed
# - Disposal record management
# - Analytics and summary reports
# - Batch processing operations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)