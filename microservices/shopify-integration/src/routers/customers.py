from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

router = APIRouter()

@router.get("/")
async def list_customers(
    store_id: Optional[int] = Query(None),
    limit: int = Query(10, le=100),
    offset: int = Query(0)
):
    return {"customers": [], "total": 0}

@router.get("/{customer_id}")
async def get_customer(customer_id: int):
    return {"id": customer_id, "email": "customer@example.com"}

@router.post("/sync")
async def sync_customers(store_id: int):
    return {"status": "syncing", "store_id": store_id}