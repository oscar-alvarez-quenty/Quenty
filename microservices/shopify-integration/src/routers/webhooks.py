from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.post("/order/created")
async def handle_order_created(request: Request):
    return {"status": "received"}

@router.post("/order/updated")
async def handle_order_updated(request: Request):
    return {"status": "received"}

@router.post("/product/created")
async def handle_product_created(request: Request):
    return {"status": "received"}

@router.post("/product/updated")
async def handle_product_updated(request: Request):
    return {"status": "received"}