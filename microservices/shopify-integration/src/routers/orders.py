from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

router = APIRouter()

@router.get("/")
async def list_orders(
    store_id: Optional[int] = Query(None),
    limit: int = Query(10, le=100),
    offset: int = Query(0)
):
    return {"orders": [], "total": 0}

@router.get("/{order_id}")
async def get_order(order_id: int):
    return {"id": order_id, "status": "pending"}

@router.post("/sync")
async def sync_orders(store_id: int):
    return {"status": "syncing", "store_id": store_id}