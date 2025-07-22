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
    service_name: str = "order-service"
    database_url: str = "postgresql+asyncpg://order:order_pass@order-db:5432/order_db"
    redis_url: str = "redis://redis:6379/2"
    consul_host: str = "consul"
    consul_port: int = 8500

settings = Settings()

app = FastAPI(
    title="Order Service",
    description="Microservice for order management and processing",
    version="2.0.0"
)

# Enums
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class OrderType(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    SAME_DAY = "same_day"
    SCHEDULED = "scheduled"
    PICKUP_ONLY = "pickup_only"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"

class DeliveryMethod(str, Enum):
    HOME_DELIVERY = "home_delivery"
    PICKUP_POINT = "pickup_point"
    FRANCHISE_PICKUP = "franchise_pickup"
    LOCKER = "locker"

# Pydantic models
class OrderItem(BaseModel):
    item_id: str
    name: str
    description: Optional[str] = None
    quantity: int = Field(ge=1)
    weight_kg: float
    dimensions: Dict[str, float]  # length, width, height in cm
    value: float
    fragile: bool = False
    requires_special_handling: bool = False

class DeliveryAddress(BaseModel):
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str = "MX"
    landmark: Optional[str] = None
    special_instructions: Optional[str] = None

class OrderCreate(BaseModel):
    customer_id: str
    order_type: OrderType
    delivery_method: DeliveryMethod
    pickup_address: str
    delivery_address: DeliveryAddress
    items: List[OrderItem] = Field(min_items=1)
    preferred_pickup_date: Optional[date] = None
    preferred_delivery_date: Optional[date] = None
    delivery_time_window: Optional[str] = None  # "09:00-12:00", "14:00-18:00"
    special_instructions: Optional[str] = None
    insurance_required: bool = False
    signature_required: bool = True

class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    order_type: OrderType
    status: OrderStatus
    payment_status: PaymentStatus
    delivery_method: DeliveryMethod
    pickup_address: str
    delivery_address: DeliveryAddress
    items: List[OrderItem]
    total_weight_kg: float
    total_value: float
    shipping_cost: float
    insurance_cost: float
    total_amount: float
    tracking_number: Optional[str] = None
    estimated_pickup_date: Optional[date] = None
    estimated_delivery_date: Optional[date] = None
    actual_pickup_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    delivery_address: Optional[DeliveryAddress] = None
    preferred_delivery_date: Optional[date] = None
    delivery_time_window: Optional[str] = None
    special_instructions: Optional[str] = None

class OrderTracking(BaseModel):
    order_id: str
    tracking_number: str
    current_status: OrderStatus
    current_location: str
    estimated_delivery: Optional[datetime] = None
    delivery_attempts: int
    events: List[Dict[str, Any]]
    last_updated: datetime

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.post("/api/v1/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    # Mock implementation
    order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    tracking_number = f"QTY{order_id}"
    
    # Calculate totals
    total_weight = sum(item.weight_kg * item.quantity for item in order.items)
    total_value = sum(item.value * item.quantity for item in order.items)
    
    # Calculate shipping cost based on weight and order type
    base_shipping = 50.0
    weight_factor = total_weight * 15.0
    type_multiplier = {
        OrderType.STANDARD: 1.0,
        OrderType.EXPRESS: 1.5,
        OrderType.SAME_DAY: 2.0,
        OrderType.SCHEDULED: 1.0,
        OrderType.PICKUP_ONLY: 0.5
    }
    shipping_cost = (base_shipping + weight_factor) * type_multiplier[order.order_type]
    
    # Calculate insurance cost
    insurance_cost = total_value * 0.01 if order.insurance_required else 0.0
    
    # Estimate dates
    pickup_days = 1 if order.order_type == OrderType.SAME_DAY else 2
    delivery_days = {
        OrderType.STANDARD: 3,
        OrderType.EXPRESS: 1,
        OrderType.SAME_DAY: 0,
        OrderType.SCHEDULED: 5,
        OrderType.PICKUP_ONLY: 0
    }
    
    estimated_pickup = date.today() + timedelta(days=pickup_days)
    estimated_delivery = estimated_pickup + timedelta(days=delivery_days[order.order_type])
    
    return OrderResponse(
        order_id=order_id,
        customer_id=order.customer_id,
        order_type=order.order_type,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        delivery_method=order.delivery_method,
        pickup_address=order.pickup_address,
        delivery_address=order.delivery_address,
        items=order.items,
        total_weight_kg=total_weight,
        total_value=total_value,
        shipping_cost=round(shipping_cost, 2),
        insurance_cost=round(insurance_cost, 2),
        total_amount=round(total_value + shipping_cost + insurance_cost, 2),
        tracking_number=tracking_number,
        estimated_pickup_date=estimated_pickup,
        estimated_delivery_date=estimated_delivery,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    # Mock implementation
    if order_id.startswith("ORD-"):
        return OrderResponse(
            order_id=order_id,
            customer_id="CUST-001",
            order_type=OrderType.EXPRESS,
            status=OrderStatus.IN_TRANSIT,
            payment_status=PaymentStatus.COMPLETED,
            delivery_method=DeliveryMethod.HOME_DELIVERY,
            pickup_address="123 Warehouse St, Mexico City",
            delivery_address=DeliveryAddress(
                street_address="456 Customer Ave",
                city="Mexico City",
                state="CDMX",
                postal_code="01000",
                country="MX"
            ),
            items=[
                OrderItem(
                    item_id="ITEM-001",
                    name="Electronics Package",
                    description="Laptop and accessories",
                    quantity=1,
                    weight_kg=3.5,
                    dimensions={"length": 40, "width": 30, "height": 10},
                    value=15000.0,
                    fragile=True,
                    requires_special_handling=True
                )
            ],
            total_weight_kg=3.5,
            total_value=15000.0,
            shipping_cost=102.50,
            insurance_cost=150.0,
            total_amount=15252.50,
            tracking_number=f"QTY{order_id}",
            estimated_pickup_date=date.today() - timedelta(days=1),
            estimated_delivery_date=date.today() + timedelta(days=1),
            actual_pickup_date=date.today() - timedelta(days=1),
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow()
        )
    else:
        raise HTTPException(status_code=404, detail="Order not found")

@app.get("/api/v1/orders")
async def list_orders(
    customer_id: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    order_type: Optional[OrderType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    # Mock implementation
    orders = [
        {
            "order_id": "ORD-20250122001",
            "customer_id": "CUST-001",
            "status": "in_transit",
            "order_type": "express",
            "total_amount": 15252.50,
            "estimated_delivery": (date.today() + timedelta(days=1)).isoformat(),
            "tracking_number": "QTYORD-20250122001"
        },
        {
            "order_id": "ORD-20250121001",
            "customer_id": "CUST-002",
            "status": "delivered",
            "order_type": "standard",
            "total_amount": 850.75,
            "actual_delivery": date.today().isoformat(),
            "tracking_number": "QTYORD-20250121001"
        }
    ]
    return {
        "orders": orders,
        "total": len(orders),
        "limit": limit,
        "offset": offset
    }

@app.put("/api/v1/orders/{order_id}")
async def update_order(order_id: str, update: OrderUpdate):
    # Mock implementation
    updated_fields = [k for k, v in update.dict().items() if v is not None]
    return {
        "order_id": order_id,
        "message": "Order updated successfully",
        "updated_fields": updated_fields,
        "updated_at": datetime.utcnow()
    }

@app.post("/api/v1/orders/{order_id}/confirm")
async def confirm_order(order_id: str):
    # Mock implementation
    return {
        "order_id": order_id,
        "status": OrderStatus.CONFIRMED,
        "payment_status": PaymentStatus.COMPLETED,
        "confirmed_at": datetime.utcnow(),
        "estimated_pickup": (date.today() + timedelta(days=1)).isoformat(),
        "message": "Order confirmed and scheduled for pickup"
    }

@app.post("/api/v1/orders/{order_id}/cancel")
async def cancel_order(order_id: str, reason: str):
    # Mock implementation
    return {
        "order_id": order_id,
        "status": OrderStatus.CANCELLED,
        "cancellation_reason": reason,
        "cancelled_at": datetime.utcnow(),
        "refund_status": "processing",
        "estimated_refund_time": "3-5 business days"
    }

@app.get("/api/v1/orders/{order_id}/tracking")
async def track_order(order_id: str):
    # Mock implementation
    return OrderTracking(
        order_id=order_id,
        tracking_number=f"QTY{order_id}",
        current_status=OrderStatus.IN_TRANSIT,
        current_location="Distribution Center - North",
        estimated_delivery=datetime.utcnow() + timedelta(hours=8),
        delivery_attempts=0,
        events=[
            {
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "status": "confirmed",
                "location": "Order Processing Center",
                "description": "Order confirmed and processing started"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "status": "picked_up",
                "location": "123 Warehouse St",
                "description": "Package picked up from sender"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                "status": "in_transit",
                "location": "Distribution Center - North",
                "description": "Package arrived at distribution center"
            }
        ],
        last_updated=datetime.utcnow()
    )

@app.post("/api/v1/orders/{order_id}/delivery-attempt")
async def record_delivery_attempt(order_id: str, attempt_notes: str, successful: bool = False):
    # Mock implementation
    return {
        "order_id": order_id,
        "attempt_number": 1,
        "attempted_at": datetime.utcnow(),
        "successful": successful,
        "notes": attempt_notes,
        "next_attempt_scheduled": None if successful else (date.today() + timedelta(days=1)).isoformat(),
        "status": OrderStatus.DELIVERED if successful else OrderStatus.OUT_FOR_DELIVERY
    }

@app.get("/api/v1/orders/analytics/summary")
async def get_orders_summary(
    date_from: date = Query(...),
    date_to: date = Query(...)
):
    # Mock implementation
    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "total_orders": 1247,
        "orders_by_status": {
            "pending": 45,
            "confirmed": 123,
            "in_transit": 234,
            "delivered": 789,
            "cancelled": 56
        },
        "orders_by_type": {
            "standard": 623,
            "express": 456,
            "same_day": 134,
            "scheduled": 34
        },
        "total_revenue": 2456789.50,
        "average_order_value": 1970.25,
        "delivery_performance": {
            "on_time_delivery_rate": 92.5,
            "average_delivery_time_hours": 28.5,
            "first_attempt_success_rate": 87.3
        }
    }

@app.post("/api/v1/orders/bulk")
async def create_bulk_orders(orders: List[OrderCreate]):
    # Mock implementation
    created_orders = []
    for idx, order in enumerate(orders):
        order_id = f"ORD-BULK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{idx:03d}"
        created_orders.append({
            "order_id": order_id,
            "customer_id": order.customer_id,
            "status": "pending",
            "tracking_number": f"QTY{order_id}"
        })
    
    return {
        "created_count": len(created_orders),
        "orders": created_orders,
        "batch_id": f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    }

@app.get("/api/v1/orders/{order_id}/invoice")
async def get_order_invoice(order_id: str):
    # Mock implementation
    return {
        "order_id": order_id,
        "invoice_number": f"INV-{order_id}",
        "invoice_date": date.today().isoformat(),
        "customer_details": {
            "customer_id": "CUST-001",
            "name": "John Doe",
            "email": "john.doe@example.com"
        },
        "items": [
            {
                "description": "Shipping Service - Express",
                "quantity": 1,
                "unit_price": 102.50,
                "total": 102.50
            },
            {
                "description": "Insurance Coverage",
                "quantity": 1,
                "unit_price": 150.00,
                "total": 150.00
            }
        ],
        "subtotal": 252.50,
        "tax": 40.40,
        "total": 292.90,
        "payment_status": "paid"
    }

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="order-service",
            port=8002,
            check=consul.Check.http(
                url="http://order-service:8002/health",
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
    uvicorn.run(app, host="0.0.0.0", port=8002)