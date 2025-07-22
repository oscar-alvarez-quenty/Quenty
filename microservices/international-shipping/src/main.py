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
    service_name: str = "international-shipping-service"
    database_url: str = "postgresql+asyncpg://intl_shipping:intl_shipping_pass@international-shipping-db:5432/intl_shipping_db"
    redis_url: str = "redis://redis:6379/4"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="International Shipping Service",
    description="Microservice for international shipping and customs management",
    version="2.0.0"
)

# Enums
class ShipmentStatus(str, Enum):
    PENDING = "pending"
    CUSTOMS_CLEARANCE = "customs_clearance"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    HELD = "held"
    RETURNED = "returned"

class ShippingMethod(str, Enum):
    AIR_EXPRESS = "air_express"
    AIR_STANDARD = "air_standard"
    SEA_FREIGHT = "sea_freight"
    LAND_FREIGHT = "land_freight"

class CustomsStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADDITIONAL_DOCS_REQUIRED = "additional_docs_required"

class IncoTerms(str, Enum):
    EXW = "EXW"  # Ex Works
    FCA = "FCA"  # Free Carrier
    CPT = "CPT"  # Carriage Paid To
    CIP = "CIP"  # Carriage and Insurance Paid To
    DAP = "DAP"  # Delivered at Place
    DPU = "DPU"  # Delivered at Place Unloaded
    DDP = "DDP"  # Delivered Duty Paid

# Pydantic models
class InternationalShipment(BaseModel):
    sender_id: str
    recipient_name: str
    recipient_company: Optional[str] = None
    recipient_address: str
    recipient_city: str
    recipient_state: str
    recipient_postal_code: str
    recipient_country: str
    recipient_phone: str
    recipient_email: str
    shipping_method: ShippingMethod
    incoterms: IncoTerms
    packages: List[Dict[str, Any]]  # weight_kg, dimensions, description, value_usd
    total_value_usd: float
    currency: str = "USD"
    customs_declaration: Dict[str, str]
    insurance_required: bool = False
    priority_handling: bool = False

class ShipmentResponse(BaseModel):
    shipment_id: str
    tracking_number: str
    sender_id: str
    recipient_country: str
    status: ShipmentStatus
    shipping_method: ShippingMethod
    incoterms: IncoTerms
    total_value_usd: float
    customs_status: CustomsStatus
    estimated_delivery_date: date
    actual_delivery_date: Optional[date] = None
    shipping_cost_usd: float
    customs_fees_usd: float
    total_cost_usd: float
    created_at: datetime
    updated_at: datetime

class CustomsDocument(BaseModel):
    document_type: str  # commercial_invoice, packing_list, certificate_origin, etc.
    document_url: Optional[str] = None
    document_data: Optional[Dict] = None
    issued_date: date
    expiry_date: Optional[date] = None

class ShipmentTracking(BaseModel):
    tracking_number: str
    current_location: str
    current_country: str
    status: ShipmentStatus
    events: List[Dict[str, Any]]
    estimated_arrival: Optional[datetime] = None
    customs_cleared: bool
    last_updated: datetime

class ShippingQuote(BaseModel):
    origin_country: str
    destination_country: str
    packages: List[Dict[str, float]]  # weight_kg, dimensions
    shipping_method: ShippingMethod
    incoterms: IncoTerms
    total_value_usd: float
    insurance_required: bool = False

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.post("/api/v1/shipments/international", response_model=ShipmentResponse)
async def create_international_shipment(shipment: InternationalShipment):
    # Mock implementation
    shipment_id = f"INTL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    tracking_number = f"QTY{shipment_id}"
    
    # Calculate shipping costs based on method and destination
    base_cost = 50.0 if shipment.shipping_method == ShippingMethod.SEA_FREIGHT else 150.0
    weight_cost = sum(pkg["weight_kg"] * 5 for pkg in shipment.packages)
    shipping_cost = base_cost + weight_cost
    
    # Estimate customs fees (mock calculation)
    customs_fees = shipment.total_value_usd * 0.15  # 15% import duty
    
    # Estimate delivery date
    transit_days = {
        ShippingMethod.AIR_EXPRESS: 3,
        ShippingMethod.AIR_STANDARD: 7,
        ShippingMethod.SEA_FREIGHT: 30,
        ShippingMethod.LAND_FREIGHT: 14
    }
    estimated_delivery = date.today() + timedelta(days=transit_days[shipment.shipping_method])
    
    return ShipmentResponse(
        shipment_id=shipment_id,
        tracking_number=tracking_number,
        sender_id=shipment.sender_id,
        recipient_country=shipment.recipient_country,
        status=ShipmentStatus.PENDING,
        shipping_method=shipment.shipping_method,
        incoterms=shipment.incoterms,
        total_value_usd=shipment.total_value_usd,
        customs_status=CustomsStatus.PENDING,
        estimated_delivery_date=estimated_delivery,
        shipping_cost_usd=round(shipping_cost, 2),
        customs_fees_usd=round(customs_fees, 2),
        total_cost_usd=round(shipping_cost + customs_fees, 2),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/v1/shipments/international/{shipment_id}", response_model=ShipmentResponse)
async def get_international_shipment(shipment_id: str):
    # Mock implementation
    if shipment_id.startswith("INTL-"):
        return ShipmentResponse(
            shipment_id=shipment_id,
            tracking_number=f"QTY{shipment_id}",
            sender_id="CUST-001",
            recipient_country="USA",
            status=ShipmentStatus.IN_TRANSIT,
            shipping_method=ShippingMethod.AIR_EXPRESS,
            incoterms=IncoTerms.DDP,
            total_value_usd=2500.0,
            customs_status=CustomsStatus.APPROVED,
            estimated_delivery_date=date.today() + timedelta(days=2),
            shipping_cost_usd=275.50,
            customs_fees_usd=375.0,
            total_cost_usd=650.50,
            created_at=datetime.utcnow() - timedelta(days=3),
            updated_at=datetime.utcnow()
        )
    else:
        raise HTTPException(status_code=404, detail="Shipment not found")

@app.get("/api/v1/shipments/international")
async def list_international_shipments(
    sender_id: Optional[str] = None,
    status: Optional[ShipmentStatus] = None,
    destination_country: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    # Mock implementation
    shipments = [
        {
            "shipment_id": "INTL-20250122001",
            "tracking_number": "QTYINTL-20250122001",
            "destination_country": "USA",
            "status": "in_transit",
            "shipping_method": "air_express",
            "estimated_delivery": (date.today() + timedelta(days=2)).isoformat()
        },
        {
            "shipment_id": "INTL-20250121001",
            "tracking_number": "QTYINTL-20250121001",
            "destination_country": "Canada",
            "status": "customs_clearance",
            "shipping_method": "air_standard",
            "estimated_delivery": (date.today() + timedelta(days=5)).isoformat()
        }
    ]
    return {
        "shipments": shipments,
        "total": len(shipments),
        "limit": limit,
        "offset": offset
    }

@app.post("/api/v1/shipments/international/quote")
async def get_shipping_quote(quote_request: ShippingQuote):
    # Mock implementation
    base_rates = {
        ShippingMethod.AIR_EXPRESS: {"base": 100, "per_kg": 15},
        ShippingMethod.AIR_STANDARD: {"base": 50, "per_kg": 10},
        ShippingMethod.SEA_FREIGHT: {"base": 30, "per_kg": 2},
        ShippingMethod.LAND_FREIGHT: {"base": 40, "per_kg": 5}
    }
    
    rate = base_rates[quote_request.shipping_method]
    total_weight = sum(pkg["weight_kg"] for pkg in quote_request.packages)
    shipping_cost = rate["base"] + (total_weight * rate["per_kg"])
    
    # Estimate customs based on destination
    customs_rate = 0.10 if quote_request.destination_country == "Canada" else 0.15
    estimated_customs = quote_request.total_value_usd * customs_rate
    
    insurance_cost = quote_request.total_value_usd * 0.01 if quote_request.insurance_required else 0
    
    transit_days = {
        ShippingMethod.AIR_EXPRESS: 3,
        ShippingMethod.AIR_STANDARD: 7,
        ShippingMethod.SEA_FREIGHT: 30,
        ShippingMethod.LAND_FREIGHT: 14
    }
    
    return {
        "quote_id": f"QUOTE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "shipping_cost_usd": round(shipping_cost, 2),
        "estimated_customs_usd": round(estimated_customs, 2),
        "insurance_cost_usd": round(insurance_cost, 2),
        "total_cost_usd": round(shipping_cost + estimated_customs + insurance_cost, 2),
        "estimated_transit_days": transit_days[quote_request.shipping_method],
        "valid_until": (date.today() + timedelta(days=7)).isoformat()
    }

@app.get("/api/v1/shipments/international/{shipment_id}/tracking")
async def track_international_shipment(shipment_id: str):
    # Mock implementation
    return ShipmentTracking(
        tracking_number=f"QTY{shipment_id}",
        current_location="Los Angeles International Airport",
        current_country="USA",
        status=ShipmentStatus.IN_TRANSIT,
        events=[
            {
                "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "location": "Mexico City, Mexico",
                "description": "Package picked up",
                "status": "picked_up"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "location": "Mexico City International Airport",
                "description": "Departed from origin facility",
                "status": "departed"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "location": "US Customs",
                "description": "Customs clearance completed",
                "status": "customs_cleared"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "location": "Los Angeles International Airport",
                "description": "Arrived at destination facility",
                "status": "arrived"
            }
        ],
        estimated_arrival=datetime.utcnow() + timedelta(days=1),
        customs_cleared=True,
        last_updated=datetime.utcnow()
    )

@app.post("/api/v1/shipments/international/{shipment_id}/customs/documents")
async def upload_customs_documents(shipment_id: str, documents: List[CustomsDocument]):
    # Mock implementation
    return {
        "shipment_id": shipment_id,
        "documents_received": len(documents),
        "customs_status": CustomsStatus.UNDER_REVIEW,
        "estimated_clearance_time": "24-48 hours",
        "document_ids": [f"DOC-{i:03d}" for i in range(len(documents))]
    }

@app.put("/api/v1/shipments/international/{shipment_id}/customs/status")
async def update_customs_status(shipment_id: str, status: CustomsStatus, notes: Optional[str] = None):
    # Mock implementation
    return {
        "shipment_id": shipment_id,
        "customs_status": status,
        "updated_at": datetime.utcnow(),
        "notes": notes,
        "next_action": "Shipment will proceed to delivery" if status == CustomsStatus.APPROVED else "Additional documentation required"
    }

@app.get("/api/v1/shipments/international/restrictions")
async def get_shipping_restrictions(
    origin_country: str = Query(...),
    destination_country: str = Query(...),
    product_category: Optional[str] = None
):
    # Mock implementation
    return {
        "origin_country": origin_country,
        "destination_country": destination_country,
        "restrictions": [
            {
                "category": "electronics",
                "restriction_type": "declaration_required",
                "description": "Electronic devices require detailed declaration"
            },
            {
                "category": "food_products",
                "restriction_type": "permit_required",
                "description": "Food products require import permit"
            }
        ],
        "prohibited_items": ["weapons", "hazardous_materials", "currency"],
        "documentation_required": [
            "commercial_invoice",
            "packing_list",
            "certificate_of_origin"
        ],
        "estimated_customs_processing": "2-4 business days"
    }

@app.post("/api/v1/shipments/international/{shipment_id}/insurance")
async def add_shipment_insurance(shipment_id: str, coverage_amount_usd: float):
    # Mock implementation
    premium = coverage_amount_usd * 0.01  # 1% premium
    return {
        "shipment_id": shipment_id,
        "insurance_id": f"INS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "coverage_amount_usd": coverage_amount_usd,
        "premium_usd": round(premium, 2),
        "coverage_start": date.today().isoformat(),
        "coverage_end": (date.today() + timedelta(days=60)).isoformat(),
        "terms": "Covers loss or damage during international transit"
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="international-shipping-service",
            port=8004,
            check=consul.Check.http(
                url="http://international-shipping-service:8004/health",
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
    uvicorn.run(app, host="0.0.0.0", port=8004)