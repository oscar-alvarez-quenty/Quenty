from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
import logging
from ..database import get_db
from ..models import MercadoLibreAccount, MercadoLibreProduct, ListingStatus
from ..services.product_sync import ProductSyncService
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def list_products(
    account_id: int,
    status: Optional[str] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List products for an account"""
    try:
        query = select(MercadoLibreProduct).where(
            MercadoLibreProduct.account_id == account_id
        )
        
        if status:
            status_enum = ListingStatus[status.upper()]
            query = query.where(MercadoLibreProduct.status == status_enum)
        
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        return {
            "products": [
                {
                    "id": p.id,
                    "meli_item_id": p.meli_item_id,
                    "title": p.title,
                    "price": p.price,
                    "available_quantity": p.available_quantity,
                    "status": p.status.value,
                    "permalink": p.permalink,
                    "thumbnail": p.thumbnail
                }
                for p in products
            ],
            "total": len(products),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}")
async def get_product(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get product details"""
    try:
        result = await db.execute(
            select(MercadoLibreProduct).where(
                MercadoLibreProduct.meli_item_id == item_id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "id": product.id,
            "meli_item_id": product.meli_item_id,
            "title": product.title,
            "category_id": product.category_id,
            "price": product.price,
            "currency_id": product.currency_id,
            "available_quantity": product.available_quantity,
            "sold_quantity": product.sold_quantity,
            "status": product.status.value,
            "condition": product.condition,
            "permalink": product.permalink,
            "pictures": product.pictures,
            "attributes": product.attributes,
            "shipping": product.shipping,
            "created_at": product.date_created,
            "updated_at": product.last_updated
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_product(
    product_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Create a new product listing on MercadoLibre"""
    try:
        # Get account
        account_id = product_data.get("account_id")
        if not account_id:
            raise HTTPException(status_code=400, detail="account_id is required")
        
        result = await db.execute(
            select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        service = ProductSyncService(db)
        result = await service.publish_product_to_meli(account, product_data)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{item_id}")
async def update_product(
    item_id: str,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Update product listing"""
    try:
        # Get product
        result = await db.execute(
            select(MercadoLibreProduct).where(
                MercadoLibreProduct.meli_item_id == item_id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == product.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = ProductSyncService(db)
        result = await service.update_product_on_meli(account, item_id, updates)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{item_id}/stock")
async def update_stock(
    item_id: str,
    quantity: int,
    db: AsyncSession = Depends(get_db)
):
    """Update product stock"""
    try:
        # Get product
        result = await db.execute(
            select(MercadoLibreProduct).where(
                MercadoLibreProduct.meli_item_id == item_id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == product.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = ProductSyncService(db)
        result = await service.update_stock_on_meli(account, item_id, quantity)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{item_id}/pause")
async def pause_product(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Pause product listing"""
    return await _change_product_status(item_id, "pause", db)


@router.post("/{item_id}/activate")
async def activate_product(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Activate product listing"""
    return await _change_product_status(item_id, "activate", db)


@router.post("/{item_id}/close")
async def close_product(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Close product listing"""
    return await _change_product_status(item_id, "close", db)


async def _change_product_status(item_id: str, action: str, db: AsyncSession):
    """Helper function to change product status"""
    try:
        # Get product
        result = await db.execute(
            select(MercadoLibreProduct).where(
                MercadoLibreProduct.meli_item_id == item_id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == product.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = ProductSyncService(db)
        
        if action == "pause":
            result = await service.pause_product(account, item_id)
        elif action == "activate":
            result = await service.activate_product(account, item_id)
        elif action == "close":
            result = await service.close_product(account, item_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to {action} product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_products(
    account_id: int,
    background_tasks: BackgroundTasks,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Sync products from MercadoLibre"""
    try:
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Schedule background sync
        background_tasks.add_task(
            sync_products_task,
            account_id,
            status_filter
        )
        
        return {
            "message": "Product sync started",
            "account_id": account_id
        }
        
    except Exception as e:
        logger.error(f"Failed to start product sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def sync_products_task(account_id: int, status_filter: Optional[str] = None):
    """Background task to sync products"""
    from ..database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account:
                service = ProductSyncService(db)
                await service.sync_products_from_meli(account, status_filter)
        except Exception as e:
            logger.error(f"Product sync task failed: {e}")