from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class InventoryUpdate(BaseModel):
    product_id: int
    quantity: int
    location_id: Optional[int] = None

@router.get("/levels")
async def get_inventory_levels(product_id: int):
    return {"product_id": product_id, "quantity": 100}

@router.post("/update")
async def update_inventory(update: InventoryUpdate):
    return {"status": "updated", "product_id": update.product_id}