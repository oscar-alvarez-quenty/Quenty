from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .config import settings
from .database import get_db, init_database, engine, AsyncSessionLocal
from .models import MercadoLibreAccount, TokenStatus, ListingStatus, OrderStatus, QuestionStatus
from .services.meli_client import MercadoLibreClient
from .services.product_sync import ProductSyncService
from .services.order_service import OrderService
from .services.question_service import QuestionService
from .routers import auth, products, orders, questions, webhooks, inventory
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse
import time

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Prometheus metrics
api_requests = Counter('meli_api_requests_total', 'Total API requests')
sync_operations = Counter('meli_sync_operations_total', 'Total sync operations')
webhook_events = Counter('meli_webhook_events_total', 'Total webhook events')
response_time = Histogram('meli_response_time_seconds', 'Response time in seconds')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting MercadoLibre Integration Service...")
    await init_database()
    logger.info("Database initialized")
    
    yield
    
    logger.info("Shutting down MercadoLibre Integration Service...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="MercadoLibre marketplace integration for Quenty platform",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(questions.router, prefix="/questions", tags=["Questions"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "site": settings.meli_site_id,
        "site_config": settings.site_config
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database
        result = await db.execute(select(MercadoLibreAccount).limit(1))
        
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    """List all connected MercadoLibre accounts"""
    api_requests.inc()
    
    result = await db.execute(
        select(MercadoLibreAccount).where(MercadoLibreAccount.is_active == True)
    )
    accounts = result.scalars().all()
    
    return {
        "accounts": [
            {
                "id": acc.id,
                "user_id": acc.user_id,
                "nickname": acc.nickname,
                "email": acc.email,
                "site_id": acc.site_id,
                "token_status": acc.token_status.value,
                "reputation": acc.reputation
            }
            for acc in accounts
        ]
    }


@app.get("/account/{account_id}/sync")
async def sync_account_data(
    account_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger full sync for an account"""
    api_requests.inc()
    sync_operations.inc()
    
    # Get account
    result = await db.execute(
        select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account.token_status != TokenStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="Account token is not active")
    
    # Schedule background sync tasks
    background_tasks.add_task(sync_products_task, account_id)
    background_tasks.add_task(sync_orders_task, account_id)
    background_tasks.add_task(sync_questions_task, account_id)
    
    return {
        "message": "Sync started",
        "account_id": account_id
    }


async def sync_products_task(account_id: int):
    """Background task to sync products"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account and account.token_status == TokenStatus.ACTIVE:
                service = ProductSyncService(db)
                await service.sync_products_from_meli(account)
                
        except Exception as e:
            logger.error(f"Product sync failed for account {account_id}: {e}")


async def sync_orders_task(account_id: int):
    """Background task to sync orders"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account and account.token_status == TokenStatus.ACTIVE:
                service = OrderService(db)
                await service.sync_orders(account)
                
        except Exception as e:
            logger.error(f"Order sync failed for account {account_id}: {e}")


async def sync_questions_task(account_id: int):
    """Background task to sync questions"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account and account.token_status == TokenStatus.ACTIVE:
                service = QuestionService(db)
                await service.sync_questions(account)
                
        except Exception as e:
            logger.error(f"Question sync failed for account {account_id}: {e}")


@app.get("/categories/{category_id}")
async def get_category_info(category_id: str):
    """Get category information and attributes"""
    api_requests.inc()
    
    try:
        client = MercadoLibreClient()
        category = await client.get_category(category_id)
        attributes = await client.get_category_attributes(category_id)
        
        return {
            "category": category,
            "attributes": attributes
        }
    except Exception as e:
        logger.error(f"Failed to get category {category_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict-category")
async def predict_category(title: str):
    """Predict category from product title"""
    api_requests.inc()
    
    try:
        client = MercadoLibreClient()
        prediction = await client.predict_category(title)
        
        return prediction
    except Exception as e:
        logger.error(f"Failed to predict category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_marketplace(
    query: str,
    category: Optional[str] = None,
    offset: int = 0,
    limit: int = 50
):
    """Search products in MercadoLibre marketplace"""
    api_requests.inc()
    
    try:
        client = MercadoLibreClient()
        results = await client.search_items(query, category, offset, limit)
        
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest())


@app.get("/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics for dashboard"""
    from sqlalchemy import func
    from .models import MercadoLibreProduct, MercadoLibreOrder, MercadoLibreQuestion
    
    try:
        # Count active products
        products_count = await db.execute(
            select(func.count(MercadoLibreProduct.id)).where(
                MercadoLibreProduct.status == ListingStatus.ACTIVE
            )
        )
        
        # Count pending orders
        orders_count = await db.execute(
            select(func.count(MercadoLibreOrder.id)).where(
                MercadoLibreOrder.status.in_([
                    OrderStatus.CONFIRMED,
                    OrderStatus.PAYMENT_IN_PROCESS
                ])
            )
        )
        
        # Count unanswered questions
        questions_count = await db.execute(
            select(func.count(MercadoLibreQuestion.id)).where(
                MercadoLibreQuestion.status == QuestionStatus.UNANSWERED
            )
        )
        
        # Calculate total sales
        total_sales = await db.execute(
            select(func.sum(MercadoLibreOrder.total_amount)).where(
                MercadoLibreOrder.status == OrderStatus.PAID
            )
        )
        
        return {
            "active_products": products_count.scalar() or 0,
            "pending_orders": orders_count.scalar() or 0,
            "unanswered_questions": questions_count.scalar() or 0,
            "total_sales": float(total_sales.scalar() or 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)