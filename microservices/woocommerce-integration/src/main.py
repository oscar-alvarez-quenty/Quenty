"""
WooCommerce Integration Service
FastAPI application for integrating WooCommerce stores with Quenty
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Header, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
import structlog
import os
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .models.entities import Base, Store, Order, OrderStatus
from .models.database import get_db, init_db
from .api.woocommerce_client import WooCommerceClient
from .webhooks.webhook_handler import WooCommerceWebhookHandler
from .services.order_service import OrderService
from .services.product_service import ProductService
from .services.notification_service import NotificationService
from .services.sync_service import SyncService
from .utils.carrier_integration import CarrierIntegrationClient
from .utils.encryption import encrypt_data, decrypt_data
from .utils.exceptions import WebhookValidationError

# Configure logging
logger = structlog.get_logger()

# Global services
order_service = None
product_service = None
notification_service = None
sync_service = None
webhook_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Initialize services and database on startup
    """
    logger.info("Starting WooCommerce Integration Service...")
    
    # Initialize database
    await init_db()
    
    # Initialize carrier client
    carrier_client = CarrierIntegrationClient(
        base_url=os.getenv("CARRIER_SERVICE_URL", "http://carrier-integration-service:8009"),
        api_key=os.getenv("CARRIER_SERVICE_API_KEY")
    )
    
    # Initialize services
    global order_service, product_service, notification_service, sync_service, webhook_handler
    
    order_service = OrderService(carrier_client)
    product_service = ProductService()
    notification_service = NotificationService()
    sync_service = SyncService(order_service, product_service)
    
    webhook_handler = WooCommerceWebhookHandler(
        order_service=order_service,
        product_service=product_service,
        notification_service=notification_service
    )
    
    logger.info("WooCommerce Integration Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down WooCommerce Integration Service...")


app = FastAPI(
    title="WooCommerce Integration Service",
    description="Integrates WooCommerce stores with Quenty logistics platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Health Check =============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "woocommerce-integration",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check endpoint"""
    try:
        # Check database connection
        result = await db.execute("SELECT 1")
        
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


# ============= Store Management =============

@app.post("/api/v1/stores", status_code=status.HTTP_201_CREATED)
async def register_store(
    store_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new WooCommerce store
    
    Args:
        store_data: Store configuration including URL and credentials
    """
    try:
        # Validate required fields
        required_fields = ['id', 'name', 'url', 'consumer_key', 'consumer_secret']
        for field in required_fields:
            if field not in store_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Check if store already exists
        existing = await db.get(Store, store_data['id'])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Store {store_data['id']} already exists"
            )
        
        # Create WooCommerce client to verify credentials
        wc_client = WooCommerceClient(
            store_url=store_data['url'],
            consumer_key=store_data['consumer_key'],
            consumer_secret=store_data['consumer_secret']
        )
        
        # Verify credentials
        if not await wc_client.verify_credentials():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid WooCommerce credentials"
            )
        
        # Get store info
        store_info = await wc_client.get_store_info()
        
        # Encrypt consumer secret
        encrypted_secret = encrypt_data(store_data['consumer_secret'])
        
        # Create store record
        store = Store(
            id=store_data['id'],
            name=store_data['name'],
            url=store_data['url'],
            consumer_key=store_data['consumer_key'],
            consumer_secret=encrypted_secret,
            webhook_secret=store_data.get('webhook_secret'),
            active=True,
            version=store_data.get('version', 'wc/v3'),
            timezone=store_info.get('timezone'),
            currency=store_info.get('currency'),
            metadata={
                'woocommerce_version': store_info.get('woocommerce_version'),
                'wordpress_version': store_info.get('wordpress_version')
            }
        )
        
        db.add(store)
        await db.commit()
        
        # Register with order service
        order_service.register_store(store.id, wc_client)
        
        # Close client
        await wc_client.close()
        
        logger.info(f"Store registered: {store.id}")
        
        return {
            "id": store.id,
            "name": store.name,
            "url": store.url,
            "status": "registered",
            "store_info": store_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register store: {str(e)}"
        )


@app.get("/api/v1/stores")
async def list_stores(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all registered stores"""
    try:
        from sqlalchemy import select
        
        query = select(Store)
        if active_only:
            query = query.where(Store.active == True)
        
        result = await db.execute(query)
        stores = result.scalars().all()
        
        return {
            "stores": [
                {
                    "id": store.id,
                    "name": store.name,
                    "url": store.url,
                    "active": store.active,
                    "currency": store.currency,
                    "last_sync": store.last_sync.isoformat() if store.last_sync else None
                }
                for store in stores
            ],
            "total": len(stores)
        }
    except Exception as e:
        logger.error(f"Failed to list stores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============= Webhook Endpoints =============

@app.post("/webhooks/woocommerce/{store_id}")
async def receive_webhook(
    store_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_wc_webhook_topic: Optional[str] = Header(None),
    x_wc_webhook_signature: Optional[str] = Header(None),
    x_wc_webhook_id: Optional[str] = Header(None),
    x_wc_webhook_resource: Optional[str] = Header(None),
    x_wc_webhook_event: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Receive webhooks from WooCommerce
    
    Headers:
        X-WC-Webhook-Topic: Event topic (e.g., order.created)
        X-WC-Webhook-Signature: HMAC signature for validation
        X-WC-Webhook-ID: Webhook ID
        X-WC-Webhook-Resource: Resource type (order, product, etc.)
        X-WC-Webhook-Event: Event type (created, updated, deleted)
    """
    try:
        # Get store
        store = await db.get(Store, store_id)
        if not store or not store.active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store {store_id} not found or inactive"
            )
        
        # Get webhook payload
        payload = await request.json()
        
        # Log webhook receipt
        logger.info(
            "webhook_received",
            store_id=store_id,
            topic=x_wc_webhook_topic,
            webhook_id=x_wc_webhook_id
        )
        
        # Process webhook in background
        background_tasks.add_task(
            webhook_handler.process_webhook,
            store_id=store_id,
            topic=x_wc_webhook_topic,
            webhook_id=x_wc_webhook_id,
            payload=payload,
            signature=x_wc_webhook_signature,
            secret=store.webhook_secret or "",
            db=db
        )
        
        return {"status": "received", "webhook_id": x_wc_webhook_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============= Order Management =============

@app.get("/api/v1/stores/{store_id}/orders")
async def get_orders(
    store_id: str,
    status: Optional[OrderStatus] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get orders for a store"""
    try:
        from sqlalchemy import select
        
        query = select(Order).where(Order.store_id == store_id)
        
        if status:
            query = query.where(Order.status == status)
        
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return {
            "orders": [
                {
                    "id": order.id,
                    "wc_order_id": order.wc_order_id,
                    "wc_order_number": order.wc_order_number,
                    "status": order.status.value,
                    "customer_email": order.customer_email,
                    "total": float(order.total),
                    "currency": order.currency,
                    "tracking_number": order.tracking_number,
                    "created_at": order.date_created.isoformat() if order.date_created else None
                }
                for order in orders
            ],
            "total": len(orders),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to get orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)