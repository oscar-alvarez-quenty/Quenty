from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class StoreConfig(BaseModel):
    name: str
    url: str
    api_key: str
    api_secret: str
    webhook_secret: Optional[str] = None

@router.get("/")
async def list_stores():
    return {"stores": []}

@router.post("/")
async def create_store(store: StoreConfig):
    return {"id": 1, "name": store.name, "url": store.url}

@router.get("/{store_id}")
async def get_store(store_id: int):
    return {"id": store_id, "name": "Sample Store"}

@router.delete("/{store_id}")
async def delete_store(store_id: int):
    return {"status": "deleted", "store_id": store_id}