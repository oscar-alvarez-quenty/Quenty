from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from ..database import get_db
from ..models import MercadoLibreAccount, MercadoLibreOrder, OrderStatus
from ..services.order_service import OrderService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def list_orders(
    account_id: int,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List orders for an account"""
    try:
        query = select(MercadoLibreOrder).where(
            MercadoLibreOrder.account_id == account_id
        )
        
        if status:
            status_enum = OrderStatus[status.upper()]
            query = query.where(MercadoLibreOrder.status == status_enum)
        
        if date_from:
            query = query.where(MercadoLibreOrder.date_created >= date_from)
        
        if date_to:
            query = query.where(MercadoLibreOrder.date_created <= date_to)
        
        query = query.offset(offset).limit(limit).order_by(MercadoLibreOrder.date_created.desc())
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return {
            "orders": [
                {
                    "id": o.id,
                    "meli_order_id": o.meli_order_id,
                    "status": o.status.value,
                    "total_amount": o.total_amount,
                    "currency_id": o.currency_id,
                    "buyer": o.buyer,
                    "date_created": o.date_created,
                    "date_closed": o.date_closed
                }
                for o in orders
            ],
            "total": len(orders),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get order details"""
    try:
        # Try to find by ID or MercadoLibre order ID
        result = await db.execute(
            select(MercadoLibreOrder).where(
                (MercadoLibreOrder.id == order_id) |
                (MercadoLibreOrder.meli_order_id == order_id)
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            # Try to fetch from MercadoLibre
            account_id = 1  # You might want to pass this as a parameter
            result = await db.execute(
                select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            
            if account:
                service = OrderService(db)
                result = await service.get_order_details(account, order_id)
                
                if result["success"]:
                    order = result["order"]
                else:
                    raise HTTPException(status_code=404, detail="Order not found")
            else:
                raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "id": order.id if hasattr(order, 'id') else None,
            "meli_order_id": order.meli_order_id if hasattr(order, 'meli_order_id') else order.get("id"),
            "status": order.status.value if hasattr(order, 'status') else order.get("status"),
            "total_amount": order.total_amount if hasattr(order, 'total_amount') else order.get("total_amount"),
            "currency_id": order.currency_id if hasattr(order, 'currency_id') else order.get("currency_id"),
            "buyer": order.buyer if hasattr(order, 'buyer') else order.get("buyer"),
            "seller": order.seller if hasattr(order, 'seller') else order.get("seller"),
            "order_items": order.order_items if hasattr(order, 'order_items') else order.get("order_items"),
            "shipping": order.shipping if hasattr(order, 'shipping') else order.get("shipping"),
            "payments": order.payments if hasattr(order, 'payments') else order.get("payments"),
            "date_created": order.date_created if hasattr(order, 'date_created') else order.get("date_created"),
            "date_closed": order.date_closed if hasattr(order, 'date_closed') else order.get("date_closed")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/shipping-label")
async def get_shipping_label(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get shipping label for an order"""
    try:
        # Get order
        result = await db.execute(
            select(MercadoLibreOrder).where(
                MercadoLibreOrder.meli_order_id == order_id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not order.shipping or not order.shipping.get("id"):
            raise HTTPException(status_code=400, detail="Order has no shipping information")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == order.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = OrderService(db)
        result = await service.get_shipping_label(account, order.shipping["id"])
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get shipping label: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/messages")
async def send_message(
    order_id: str,
    message_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Send message to buyer about an order"""
    try:
        # Get order
        result = await db.execute(
            select(MercadoLibreOrder).where(
                MercadoLibreOrder.meli_order_id == order_id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == order.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = OrderService(db)
        result = await service.send_message_to_buyer(
            account,
            order_id,
            message_data.get("message", ""),
            message_data.get("attachments")
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/messages")
async def get_messages(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get messages for an order"""
    try:
        # Get order
        result = await db.execute(
            select(MercadoLibreOrder).where(
                MercadoLibreOrder.meli_order_id == order_id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == order.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = OrderService(db)
        result = await service.get_order_messages(account, order_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_orders(
    account_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Sync orders from MercadoLibre"""
    try:
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        service = OrderService(db)
        result = await service.sync_orders(account, date_from, date_to, status_filter)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to sync orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/note")
async def add_order_note(
    order_id: str,
    note: str,
    db: AsyncSession = Depends(get_db)
):
    """Add internal note to order"""
    try:
        # Get order
        result = await db.execute(
            select(MercadoLibreOrder).where(
                MercadoLibreOrder.meli_order_id == order_id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == order.account_id
            )
        )
        account = result.scalar_one_or_none()
        
        service = OrderService(db)
        result = await service.add_order_note(account, order_id, note)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add note: {e}")
        raise HTTPException(status_code=500, detail=str(e))