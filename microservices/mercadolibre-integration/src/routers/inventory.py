from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime
import logging
from ..database import get_db
from ..models import MercadoLibreAccount, MercadoLibreProduct, MercadoLibreInventory
from ..services.product_sync import ProductSyncService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def list_inventory(
    account_id: int,
    low_stock_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List inventory for all products"""
    try:
        query = select(MercadoLibreInventory).join(
            MercadoLibreProduct
        ).where(
            MercadoLibreProduct.account_id == account_id
        )
        
        if low_stock_only:
            query = query.where(MercadoLibreInventory.available_quantity < 10)
        
        result = await db.execute(query)
        inventory = result.scalars().all()
        
        # Get product details
        inventory_data = []
        for inv in inventory:
            product_result = await db.execute(
                select(MercadoLibreProduct).where(
                    MercadoLibreProduct.id == inv.product_id
                )
            )
            product = product_result.scalar_one_or_none()
            
            if product:
                inventory_data.append({
                    "product_id": product.id,
                    "meli_item_id": product.meli_item_id,
                    "title": product.title,
                    "available_quantity": inv.available_quantity,
                    "reserved_quantity": inv.reserved_quantity,
                    "sold_quantity": inv.sold_quantity,
                    "last_sync": inv.last_sync,
                    "sync_status": inv.sync_status
                })
        
        return {
            "inventory": inventory_data,
            "total": len(inventory_data)
        }
    except Exception as e:
        logger.error(f"Failed to list inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_inventory(
    account_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Sync inventory levels from MercadoLibre"""
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
            sync_inventory_task,
            account_id
        )
        
        return {
            "message": "Inventory sync started",
            "account_id": account_id
        }
        
    except Exception as e:
        logger.error(f"Failed to start inventory sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-update")
async def bulk_update_stock(
    updates: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db)
):
    """Bulk update stock levels"""
    try:
        results = {
            "success": [],
            "failed": []
        }
        
        for update in updates:
            item_id = update.get("item_id")
            quantity = update.get("quantity")
            
            if not item_id or quantity is None:
                results["failed"].append({
                    "item_id": item_id,
                    "error": "Missing item_id or quantity"
                })
                continue
            
            # Get product
            result = await db.execute(
                select(MercadoLibreProduct).where(
                    MercadoLibreProduct.meli_item_id == item_id
                )
            )
            product = result.scalar_one_or_none()
            
            if not product:
                results["failed"].append({
                    "item_id": item_id,
                    "error": "Product not found"
                })
                continue
            
            # Get account
            result = await db.execute(
                select(MercadoLibreAccount).where(
                    MercadoLibreAccount.id == product.account_id
                )
            )
            account = result.scalar_one_or_none()
            
            if not account:
                results["failed"].append({
                    "item_id": item_id,
                    "error": "Account not found"
                })
                continue
            
            # Update stock
            service = ProductSyncService(db)
            update_result = await service.update_stock_on_meli(account, item_id, quantity)
            
            if update_result["success"]:
                results["success"].append({
                    "item_id": item_id,
                    "new_quantity": quantity
                })
            else:
                results["failed"].append({
                    "item_id": item_id,
                    "error": update_result.get("error")
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to bulk update stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/low-stock-alerts")
async def get_low_stock_alerts(
    account_id: int,
    threshold: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get products with low stock"""
    try:
        query = select(MercadoLibreInventory).join(
            MercadoLibreProduct
        ).where(
            MercadoLibreProduct.account_id == account_id,
            MercadoLibreInventory.available_quantity < threshold
        )
        
        result = await db.execute(query)
        low_stock = result.scalars().all()
        
        alerts = []
        for inv in low_stock:
            product_result = await db.execute(
                select(MercadoLibreProduct).where(
                    MercadoLibreProduct.id == inv.product_id
                )
            )
            product = product_result.scalar_one_or_none()
            
            if product:
                alerts.append({
                    "meli_item_id": product.meli_item_id,
                    "title": product.title,
                    "current_stock": inv.available_quantity,
                    "threshold": threshold,
                    "sold_quantity": inv.sold_quantity,
                    "status": product.status.value
                })
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "threshold": threshold
        }
    except Exception as e:
        logger.error(f"Failed to get low stock alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def sync_inventory_task(account_id: int):
    """Background task to sync inventory"""
    from ..database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Get account
            result = await db.execute(
                select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account:
                # Get all products
                result = await db.execute(
                    select(MercadoLibreProduct).where(
                        MercadoLibreProduct.account_id == account_id
                    )
                )
                products = result.scalars().all()
                
                service = ProductSyncService(db)
                
                # Sync each product's inventory
                for product in products:
                    try:
                        from ..services.meli_client import MercadoLibreClient
                        client = MercadoLibreClient(access_token=account.access_token)
                        item = await client.get_item(product.meli_item_id)
                        
                        # Update inventory
                        inv_result = await db.execute(
                            select(MercadoLibreInventory).where(
                                MercadoLibreInventory.product_id == product.id
                            )
                        )
                        inventory = inv_result.scalar_one_or_none()
                        
                        if inventory:
                            inventory.available_quantity = item.get("available_quantity", 0)
                            inventory.sold_quantity = item.get("sold_quantity", 0)
                            inventory.last_sync = datetime.utcnow()
                            inventory.sync_status = "synced"
                        else:
                            inventory = MercadoLibreInventory(
                                product_id=product.id,
                                available_quantity=item.get("available_quantity", 0),
                                sold_quantity=item.get("sold_quantity", 0),
                                last_sync=datetime.utcnow(),
                                sync_status="synced"
                            )
                            db.add(inventory)
                        
                    except Exception as e:
                        logger.error(f"Failed to sync inventory for {product.meli_item_id}: {e}")
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Inventory sync task failed: {e}")