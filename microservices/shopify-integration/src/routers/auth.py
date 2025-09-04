from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AuthRequest(BaseModel):
    store_url: str
    api_key: str
    api_secret: str

@router.post("/connect")
async def connect_store(auth_data: AuthRequest):
    return {"status": "connected", "store_url": auth_data.store_url}

@router.get("/stores")
async def list_connected_stores():
    return {"stores": []}