from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

router = APIRouter()

@router.get("/")
async def list_products(
    store_id: Optional[int] = Query(None),
    limit: int = Query(10, le=100),
    offset: int = Query(0)
):
    return {"products": [], "total": 0}

@router.get("/{product_id}")
async def get_product(product_id: int):
    return {"id": product_id, "name": "Sample Product"}

@router.post("/sync")
async def sync_products(store_id: int):
    return {"status": "syncing", "store_id": store_id}