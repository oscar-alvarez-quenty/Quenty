from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SyncRequest(BaseModel):
    store_id: int
    sync_type: str  # products, orders, customers, all

@router.post("/start")
async def start_sync(sync_request: SyncRequest):
    return {"status": "started", "store_id": sync_request.store_id, "sync_type": sync_request.sync_type}

@router.get("/status/{store_id}")
async def get_sync_status(store_id: int):
    return {"store_id": store_id, "status": "idle"}

@router.post("/stop/{store_id}")
async def stop_sync(store_id: int):
    return {"store_id": store_id, "status": "stopped"}