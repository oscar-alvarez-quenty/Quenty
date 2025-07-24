from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict, Any
import consul
import httpx
import os
import logging
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from .models import Product, InventoryItem, StockMovement, Order, OrderItem, Base, StockMovementType
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
logger = structlog.get_logger("order-service")

class Settings(BaseSettings):
    service_name: str = "order-service"
    database_url: str = "postgresql+asyncpg://order:order_pass@order-db:5432/order_db"
    redis_url: str = "redis://redis:6379/2"
    consul_host: str = "consul"
    consul_port: int = 8500
    auth_service_url: str = "http://auth-service:8003"

    class Config:
        env_file = ".env"

settings = Settings()

# HTTP Bearer for token extraction
security = HTTPBearer()

app = FastAPI(
    title="Order Service", 
    description="Microservice for order and inventory management",
    version="2.0.0"
)
# Prometheus metrics
order_service_operations_total = Counter(
    'order_service_operations_total',
    'Total number of order-service operations',
    ['operation', 'status']
)
order_service_request_duration = Histogram(
    'order_service_request_duration_seconds',
    'Duration of order-service requests in seconds',
    ['method', 'endpoint']
)
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['service', 'method', 'endpoint', 'status']
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

# Pydantic models for API
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    category: str
    price: float
    cost: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    company_id: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    sku: str
    category: str
    price: float
    cost: Optional[float]
    weight: Optional[float]
    dimensions: Optional[Dict[str, float]]
    active: bool
    created_at: datetime
    updated_at: datetime
    company_id: str

class InventoryCreate(BaseModel):
    product_id: int
    quantity: int
    reserved_quantity: Optional[int] = 0
    min_stock_level: Optional[int] = 0
    max_stock_level: Optional[int] = None
    location: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None

class InventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    reserved_quantity: int
    min_stock_level: int
    max_stock_level: Optional[int]
    location: Optional[str]
    batch_number: Optional[str]
    expiry_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class StockMovementCreate(BaseModel):
    product_id: int
    movement_type: str
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: str

class OrderCreate(BaseModel):
    customer_id: str
    company_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    currency: Optional[str] = "USD"

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: str
    company_id: str
    status: str
    total_amount: float
    currency: str
    created_at: datetime
    updated_at: datetime

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Product endpoints
@app.get("/api/v1/products", response_model=Dict[str, Any])
async def get_products(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_products = [
            {
                "id": 1,
                "unique_id": "PROD-20250122001",
                "code": "SKU-001",
                "name": "Electronics Package",
                "description": "High-value electronics item",
                "price": 1299.99,
                "status": "active",
                "company_id": "COMP-001"
            },
            {
                "id": 2,
                "unique_id": "PROD-20250122002",
                "code": "SKU-002", 
                "name": "Clothing Item",
                "description": "Fashion apparel",
                "price": 49.99,
                "status": "active",
                "company_id": "COMP-001"
            }
        ]
        return {"products": mock_products, "total": len(mock_products), "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/products/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: int,
    current_user = Depends(require_permissions(["products:read"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "id": product_id,
            "unique_id": f"PROD-{10000000 + product_id - 1}",
            "code": f"SKU-{product_id}",
            "name": "Sample Product",
            "description": "A sample product for testing",
            "unit_measure": "PCS",
            "weight_kg": 1.5,
            "width_cm": 20.0,
            "height_cm": 15.0,
            "length_cm": 10.0,
            "is_packing": False,
            "packing_material": None,
            "packing_instructions": None,
            "price": 25.99,
            "company_id": "COMP-001",
            "category_id": 1,
            "status": "active",
            "reorder_point": 10,
            "created_at": datetime.utcnow() - timedelta(days=30),
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/products", response_model=Dict[str, Any])
async def create_product(
    product: ProductCreate, 
    current_user = Depends(require_permissions(["products:create"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        unique_id = f"PROD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "id": 16,  # Mock ID
            "unique_id": unique_id,
            "code": product.sku,
            "name": product.name,
            "description": product.description,
            "unit_measure": "PCS",
            "weight_kg": product.weight,
            "width_cm": product.dimensions.get("width") if product.dimensions else None,
            "height_cm": product.dimensions.get("height") if product.dimensions else None,
            "length_cm": product.dimensions.get("length") if product.dimensions else None,
            "is_packing": False,
            "packing_material": None,
            "packing_instructions": None,
            "price": product.price,
            "company_id": product.company_id,
            "category_id": 1,  # Mock category
            "status": "active",
            "reorder_point": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/products/{product_id}", response_model=Dict[str, Any])
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user = Depends(require_permissions(["products:update"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        current_product = await get_product(product_id, db)
        
        update_data = product_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in current_product:
                current_product[field] = value
        
        current_product["updated_at"] = datetime.utcnow()
        return current_product
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/v1/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user = Depends(require_permissions(["products:delete"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {"message": f"Product {product_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Order endpoints
@app.get("/api/v1/orders", response_model=Dict[str, Any])
async def get_orders(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_permissions(["orders:read"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_orders = [
            {
                "order_id": "ORD-20250122001",
                "customer_id": "CUST-001",
                "status": "in_transit",
                "order_type": "express",
                "total_amount": 15252.5,
                "estimated_delivery": "2025-07-23",
                "tracking_number": "QTYORD-20250122001"
            },
            {
                "order_id": "ORD-20250121001",
                "customer_id": "CUST-002",
                "status": "delivered",
                "order_type": "standard",
                "total_amount": 850.75,
                "actual_delivery": "2025-07-22",
                "tracking_number": "QTYORD-20250121001"
            }
        ]
        return {"orders": mock_orders, "total": len(mock_orders), "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/orders/{order_id}", response_model=Dict[str, Any])
async def get_order(
    order_id: str,
    current_user = Depends(require_permissions(["orders:read"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "order_id": order_id,
            "customer_id": "CUST-001",
            "order_type": "express",
            "status": "in_transit",
            "payment_status": "completed",
            "delivery_method": "home_delivery",
            "pickup_address": "123 Warehouse St, Mexico City",
            "delivery_address": {
                "street_address": "456 Customer Ave",
                "city": "Mexico City",
                "state": "CDMX",
                "postal_code": "01000",
                "country": "MX",
                "landmark": None,
                "special_instructions": None
            },
            "items": [
                {
                    "item_id": "ITEM-001",
                    "name": "Electronics Package",
                    "description": "Laptop and accessories",
                    "quantity": 1,
                    "weight_kg": 3.5,
                    "dimensions": {
                        "length": 40.0,
                        "width": 30.0,
                        "height": 10.0
                    },
                    "value": 15000.0,
                    "fragile": True,
                    "requires_special_handling": True
                }
            ],
            "total_weight_kg": 3.5,
            "total_value": 15000.0,
            "shipping_cost": 102.5,
            "insurance_cost": 150.0,
            "total_amount": 15252.5,
            "tracking_number": f"QTYORD-{order_id.split('-')[-1]}",
            "estimated_pickup_date": "2025-07-21",
            "estimated_delivery_date": "2025-07-23",
            "actual_pickup_date": "2025-07-21",
            "actual_delivery_date": None,
            "created_at": datetime.utcnow() - timedelta(days=2),
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/orders", response_model=Dict[str, Any])
async def create_order(
    order: OrderCreate,
    current_user = Depends(require_permissions(["orders:create"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        order_id = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        tracking_number = f"QTYORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate totals
        total_weight = sum(item.get("weight_kg", 0) for item in order.items)
        total_value = sum(item.get("value", 0) for item in order.items)
        shipping_cost = 65.0  # Base shipping cost
        insurance_cost = 0.0
        
        return {
            "order_id": order_id,
            "customer_id": order.customer_id,
            "order_type": "standard",
            "status": "pending",
            "payment_status": "pending",
            "delivery_method": "home_delivery",
            "pickup_address": "123 Warehouse St",
            "delivery_address": {
                "street_address": "456 Customer Ave",
                "city": "Mexico City", 
                "state": "CDMX",
                "postal_code": "01000",
                "country": "MX",
                "landmark": None,
                "special_instructions": None
            },
            "items": order.items,
            "total_weight_kg": total_weight,
            "total_value": total_value,
            "shipping_cost": shipping_cost,
            "insurance_cost": insurance_cost,
            "total_amount": total_value + shipping_cost + insurance_cost,
            "tracking_number": tracking_number,
            "estimated_pickup_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "estimated_delivery_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "actual_pickup_date": None,
            "actual_delivery_date": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str = Query(...),
    current_user = Depends(require_permissions(["orders:update"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "order_id": order_id,
            "status": status,
            "updated_at": datetime.utcnow(),
            "message": f"Order {order_id} status updated to {status}"
        }
    except Exception as e:
        logger.error(f"Error updating order {order_id} status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Inventory endpoints
@app.get("/api/v1/inventory", response_model=Dict[str, Any])
async def get_inventory(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_inventory = [
            {
                "product_id": 1,
                "product_name": "Electronics Package",
                "quantity_available": 150,
                "quantity_reserved": 25,
                "min_stock_level": 50,
                "max_stock_level": 500,
                "location": "Warehouse A",
                "status": "in_stock"
            },
            {
                "product_id": 2,
                "product_name": "Clothing Item",
                "quantity_available": 300,
                "quantity_reserved": 15,
                "min_stock_level": 100,
                "max_stock_level": 1000,
                "location": "Warehouse B", 
                "status": "in_stock"
            }
        ]
        return {"inventory": mock_inventory, "total": len(mock_inventory), "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error fetching inventory: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/products/low-stock", response_model=Dict[str, Any])
async def get_low_stock_products(
    current_user = Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_low_stock = [
            {
                "product_id": 3,
                "product_name": "Special Item",
                "current_stock": 5,
                "min_stock_level": 20,
                "reorder_quantity": 100,
                "status": "low_stock",
                "urgent": True
            }
        ]
        return {"low_stock_products": mock_low_stock, "total": len(mock_low_stock)}
    except Exception as e:
        logger.error(f"Error fetching low stock products: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/inventory/movements", response_model=Dict[str, Any])
async def get_stock_movements(
    product_id: Optional[str] = Query(None),
    current_user = Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "product_id": product_id or "movements",
            "warehouses": [
                {
                    "warehouse_id": 1,
                    "warehouse_name": "Main Warehouse",
                    "quantity_available": 150,
                    "quantity_reserved": 25,
                    "quantity_allocated": 10,
                    "status": "available"
                },
                {
                    "warehouse_id": 2,
                    "warehouse_name": "Distribution Center North",
                    "quantity_available": 75,
                    "quantity_reserved": 15,
                    "quantity_allocated": 5,
                    "status": "available"
                }
            ],
            "total_available": 225,
            "total_reserved": 40,
            "reorder_needed": False
        }
    except Exception as e:
        logger.error(f"Error fetching stock movements: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/inventory/movements", response_model=Dict[str, Any])
async def create_stock_movement(
    movement: StockMovementCreate,
    current_user = Depends(require_permissions(["inventory:update"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        movement_id = f"MOV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "movement_id": movement_id,
            "product_id": movement.product_id,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "reference_number": movement.reference_number,
            "notes": movement.notes,
            "created_by": movement.created_by,
            "created_at": datetime.utcnow(),
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Error creating stock movement: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    await create_tables()
    await register_with_consul()
    if INFO_MESSAGES and "ORD_I006" in INFO_MESSAGES:
        logger.info(
            INFO_MESSAGES["ORD_I006"]["message"].format(port=8002),
            **INFO_MESSAGES["ORD_I006"]
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