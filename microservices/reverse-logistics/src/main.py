from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict, Any
import consul
from datetime import datetime, date, timedelta
from enum import Enum

logger = structlog.get_logger()

class Settings(BaseSettings):
    service_name: str = "reverse-logistics-service"
    database_url: str = "postgresql+asyncpg://reverse_logistics:reverse_logistics_pass@reverse-logistics-db:5432/reverse_logistics_db"
    redis_url: str = "redis://redis:6379/7"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="Reverse Logistics Service",
    description="Microservice for returns, exchanges, and reverse logistics management",
    version="2.0.0"
)

# Enums
class ReturnStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PICKUP_SCHEDULED = "pickup_scheduled"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTED = "inspected"
    PROCESSED = "processed"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    DISPOSED = "disposed"

class ReturnReason(str, Enum):
    DAMAGED = "damaged"
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    SIZE_ISSUE = "size_issue"
    CHANGE_OF_MIND = "change_of_mind"
    DUPLICATE_ORDER = "duplicate_order"
    LATE_DELIVERY = "late_delivery"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"

class ReturnType(str, Enum):
    RETURN = "return"
    EXCHANGE = "exchange"
    REPAIR = "repair"
    WARRANTY_CLAIM = "warranty_claim"

class DisposalMethod(str, Enum):
    RESELL = "resell"
    REFURBISH = "refurbish"
    DONATE = "donate"
    RECYCLE = "recycle"
    DESTROY = "destroy"

class InspectionResult(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"
    UNUSABLE = "unusable"

# Pydantic models
class ReturnRequest(BaseModel):
    original_order_id: str
    customer_id: str
    return_type: ReturnType
    return_reason: ReturnReason
    items: List[Dict[str, Any]]  # item_id, quantity, reason_details
    description: str
    photos: Optional[List[str]] = None  # URLs to photos
    preferred_resolution: str  # "refund", "exchange", "store_credit"
    return_address: Optional[str] = None  # If different from delivery address

class ReturnResponse(BaseModel):
    return_id: str
    original_order_id: str
    customer_id: str
    return_type: ReturnType
    status: ReturnStatus
    return_reason: ReturnReason
    items: List[Dict[str, Any]]
    description: str
    preferred_resolution: str
    return_authorization_number: str
    estimated_refund_amount: float
    pickup_address: Optional[str] = None
    return_shipping_cost: float
    estimated_pickup_date: Optional[date] = None
    estimated_processing_time: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

class InspectionReport(BaseModel):
    return_id: str
    item_id: str
    inspector_id: str
    inspection_date: datetime
    condition: InspectionResult
    photos: List[str]
    notes: str
    resale_value: Optional[float] = None
    recommended_action: str
    defects_found: List[str]

class ReturnProcessing(BaseModel):
    processing_action: str  # "approve_full_refund", "approve_partial_refund", "approve_exchange", "reject"
    refund_amount: Optional[float] = None
    exchange_item_id: Optional[str] = None
    processing_notes: str
    requires_customer_action: bool = False
    customer_action_required: Optional[str] = None

class DisposalRecord(BaseModel):
    return_id: str
    item_id: str
    disposal_method: DisposalMethod
    disposal_date: date
    disposal_value: float
    disposal_cost: float
    disposal_partner: Optional[str] = None
    environmental_impact: Optional[Dict[str, str]] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.post("/api/v1/returns", response_model=ReturnResponse)
async def create_return_request(return_request: ReturnRequest):
    # Mock implementation
    return_id = f"RET-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    authorization_number = f"RMA{return_id}"
    
    # Calculate estimated refund based on return reason
    refund_multiplier = {
        ReturnReason.DAMAGED: 1.0,
        ReturnReason.DEFECTIVE: 1.0,
        ReturnReason.WRONG_ITEM: 1.0,
        ReturnReason.NOT_AS_DESCRIBED: 1.0,
        ReturnReason.CHANGE_OF_MIND: 0.9,  # 10% restocking fee
        ReturnReason.SIZE_ISSUE: 0.95,
        ReturnReason.OTHER: 0.95
    }
    
    # Mock original order value
    original_value = 1500.0
    estimated_refund = original_value * refund_multiplier.get(return_request.return_reason, 0.9)
    
    # Calculate return shipping cost
    return_shipping_cost = 0.0 if return_request.return_reason in [
        ReturnReason.DAMAGED, ReturnReason.DEFECTIVE, ReturnReason.WRONG_ITEM
    ] else 50.0
    
    return ReturnResponse(
        return_id=return_id,
        original_order_id=return_request.original_order_id,
        customer_id=return_request.customer_id,
        return_type=return_request.return_type,
        status=ReturnStatus.REQUESTED,
        return_reason=return_request.return_reason,
        items=return_request.items,
        description=return_request.description,
        preferred_resolution=return_request.preferred_resolution,
        return_authorization_number=authorization_number,
        estimated_refund_amount=estimated_refund,
        return_shipping_cost=return_shipping_cost,
        estimated_pickup_date=date.today() + timedelta(days=2),
        estimated_processing_time="3-5 business days",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )

@app.get("/api/v1/returns/{return_id}", response_model=ReturnResponse)
async def get_return(return_id: str):
    # Mock implementation
    if return_id.startswith("RET-"):
        return ReturnResponse(
            return_id=return_id,
            original_order_id="ORD-20250120001",
            customer_id="CUST-001",
            return_type=ReturnType.RETURN,
            status=ReturnStatus.INSPECTED,
            return_reason=ReturnReason.DEFECTIVE,
            items=[
                {
                    "item_id": "ITEM-001",
                    "quantity": 1,
                    "reason_details": "Screen not working properly"
                }
            ],
            description="The device screen is flickering and unresponsive",
            preferred_resolution="refund",
            return_authorization_number=f"RMA{return_id}",
            estimated_refund_amount=1500.0,
            pickup_address="123 Customer St, Mexico City",
            return_shipping_cost=0.0,
            estimated_pickup_date=date.today() - timedelta(days=3),
            estimated_processing_time="3-5 business days",
            created_at=datetime.utcnow() - timedelta(days=5),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=25)
        )
    else:
        raise HTTPException(status_code=404, detail="Return not found")

@app.get("/api/v1/returns")
async def list_returns(
    customer_id: Optional[str] = None,
    status: Optional[ReturnStatus] = None,
    return_type: Optional[ReturnType] = None,
    return_reason: Optional[ReturnReason] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    # Mock implementation
    returns = [
        {
            "return_id": "RET-20250122001",
            "original_order_id": "ORD-20250120001",
            "customer_id": "CUST-001",
            "status": "inspected",
            "return_reason": "defective",
            "estimated_refund_amount": 1500.0,
            "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat()
        },
        {
            "return_id": "RET-20250121001",
            "original_order_id": "ORD-20250118001",
            "customer_id": "CUST-002",
            "status": "processed",
            "return_reason": "change_of_mind",
            "estimated_refund_amount": 675.0,
            "created_at": (datetime.utcnow() - timedelta(days=4)).isoformat()
        }
    ]
    return {
        "returns": returns,
        "total": len(returns),
        "limit": limit,
        "offset": offset
    }

@app.put("/api/v1/returns/{return_id}/approve")
async def approve_return(return_id: str, approval_notes: Optional[str] = None):
    # Mock implementation
    return {
        "return_id": return_id,
        "status": ReturnStatus.APPROVED,
        "approved_at": datetime.utcnow(),
        "approval_notes": approval_notes,
        "next_steps": "Return shipping label will be emailed to customer",
        "pickup_scheduled_for": (date.today() + timedelta(days=2)).isoformat()
    }

@app.put("/api/v1/returns/{return_id}/reject")
async def reject_return(return_id: str, rejection_reason: str):
    # Mock implementation
    return {
        "return_id": return_id,
        "status": ReturnStatus.REJECTED,
        "rejected_at": datetime.utcnow(),
        "rejection_reason": rejection_reason,
        "appeal_deadline": (date.today() + timedelta(days=7)).isoformat()
    }

@app.post("/api/v1/returns/{return_id}/schedule-pickup")
async def schedule_return_pickup(return_id: str, pickup_date: date, time_window: str):
    # Mock implementation
    return {
        "return_id": return_id,
        "status": ReturnStatus.PICKUP_SCHEDULED,
        "pickup_date": pickup_date.isoformat(),
        "time_window": time_window,
        "pickup_id": f"PU-{return_id}",
        "tracking_number": f"QTYRET{return_id}",
        "scheduled_at": datetime.utcnow()
    }

@app.post("/api/v1/returns/{return_id}/inspection")
async def create_inspection_report(return_id: str, inspection: InspectionReport):
    # Mock implementation
    return {
        "return_id": return_id,
        "inspection_id": f"INSP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "inspection_completed": True,
        "overall_condition": inspection.condition,
        "recommended_action": inspection.recommended_action,
        "status": ReturnStatus.INSPECTED,
        "processing_recommendation": "approve_full_refund" if inspection.condition in [
            InspectionResult.EXCELLENT, InspectionResult.GOOD
        ] else "approve_partial_refund"
    }

@app.post("/api/v1/returns/{return_id}/process")
async def process_return(return_id: str, processing: ReturnProcessing):
    # Mock implementation
    status_mapping = {
        "approve_full_refund": ReturnStatus.REFUNDED,
        "approve_partial_refund": ReturnStatus.REFUNDED,
        "approve_exchange": ReturnStatus.EXCHANGED,
        "reject": ReturnStatus.REJECTED
    }
    
    return {
        "return_id": return_id,
        "processing_action": processing.processing_action,
        "status": status_mapping.get(processing.processing_action, ReturnStatus.PROCESSED),
        "refund_amount": processing.refund_amount,
        "exchange_item_id": processing.exchange_item_id,
        "processed_at": datetime.utcnow(),
        "processing_notes": processing.processing_notes,
        "expected_refund_time": "3-5 business days" if "refund" in processing.processing_action else None
    }

@app.get("/api/v1/returns/{return_id}/tracking")
async def track_return(return_id: str):
    # Mock implementation
    return {
        "return_id": return_id,
        "tracking_number": f"QTYRET{return_id}",
        "current_status": ReturnStatus.IN_TRANSIT,
        "current_location": "Return Processing Center",
        "events": [
            {
                "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "status": "pickup_scheduled",
                "location": "Customer Address",
                "description": "Return pickup scheduled"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "status": "picked_up",
                "location": "Customer Address",
                "description": "Package picked up from customer"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "status": "in_transit",
                "location": "Distribution Center",
                "description": "Return package in transit to processing center"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "received",
                "location": "Return Processing Center",
                "description": "Package received at processing center"
            }
        ],
        "estimated_processing_completion": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        "last_updated": datetime.utcnow()
    }

@app.post("/api/v1/returns/{return_id}/dispose")
async def dispose_returned_item(return_id: str, disposal: DisposalRecord):
    # Mock implementation
    return {
        "return_id": return_id,
        "disposal_id": f"DISP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "disposal_method": disposal.disposal_method,
        "disposal_completed": True,
        "disposal_value": disposal.disposal_value,
        "disposal_cost": disposal.disposal_cost,
        "net_recovery": disposal.disposal_value - disposal.disposal_cost,
        "environmental_impact": disposal.environmental_impact,
        "completed_at": datetime.utcnow()
    }

@app.get("/api/v1/returns/analytics/summary")
async def get_returns_summary(
    date_from: date = Query(...),
    date_to: date = Query(...)
):
    # Mock implementation
    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "total_returns": 245,
        "return_rate": 8.5,  # percentage
        "returns_by_reason": {
            "defective": 45,
            "damaged": 38,
            "change_of_mind": 52,
            "wrong_item": 25,
            "not_as_described": 35,
            "other": 50
        },
        "returns_by_status": {
            "processed": 189,
            "in_process": 34,
            "pending": 22
        },
        "financial_impact": {
            "total_refunds_issued": 125000.50,
            "total_processing_costs": 8750.25,
            "recovery_value": 45600.75,
            "net_cost": 88149.00
        },
        "processing_metrics": {
            "average_processing_time_days": 4.2,
            "customer_satisfaction_score": 4.1,
            "first_call_resolution_rate": 78.5
        }
    }

@app.get("/api/v1/returns/inventory/disposition")
async def get_disposition_inventory():
    # Mock implementation
    return {
        "pending_disposition": [
            {
                "return_id": "RET-20250120001",
                "item_id": "ITEM-001",
                "condition": "good",
                "estimated_value": 750.0,
                "recommendation": "resell",
                "days_in_inventory": 5
            },
            {
                "return_id": "RET-20250118001",
                "item_id": "ITEM-002",
                "condition": "damaged",
                "estimated_value": 100.0,
                "recommendation": "recycle",
                "days_in_inventory": 12
            }
        ],
        "disposition_options": {
            "resell": {"count": 15, "estimated_value": 12500.0},
            "refurbish": {"count": 8, "estimated_value": 4200.0},
            "donate": {"count": 3, "estimated_value": 450.0},
            "recycle": {"count": 5, "estimated_value": 125.0},
            "destroy": {"count": 2, "estimated_value": 0.0}
        }
    }

@app.post("/api/v1/returns/batch-process")
async def batch_process_returns(return_ids: List[str], processing_action: str):
    # Mock implementation
    processed_returns = []
    for return_id in return_ids:
        processed_returns.append({
            "return_id": return_id,
            "action": processing_action,
            "status": "completed",
            "processed_at": datetime.utcnow()
        })
    
    return {
        "batch_id": f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "processed_count": len(processed_returns),
        "processing_action": processing_action,
        "results": processed_returns,
        "batch_completed_at": datetime.utcnow()
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="reverse-logistics-service",
            port=8007,
            check=consul.Check.http(
                url="http://reverse-logistics-service:8007/health",
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
    uvicorn.run(app, host="0.0.0.0", port=8007)