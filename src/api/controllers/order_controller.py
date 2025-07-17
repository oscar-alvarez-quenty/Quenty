from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.api.schemas.order_schemas import (
    OrderCreateRequest,
    OrderQuoteRequest,
    OrderResponse,
    OrderQuoteResponse,
    GuideResponse
)
from src.application.services.order_application_service import OrderApplicationService
from src.domain.services.order_service import OrderService
from src.infrastructure.database.database import get_db
from src.infrastructure.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from src.infrastructure.repositories.sqlalchemy_order_repository import SQLAlchemyOrderRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

async def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderApplicationService:
    customer_repo = SQLAlchemyCustomerRepository(db)
    order_repo = SQLAlchemyOrderRepository(db)
    order_service = OrderService(order_repo, customer_repo)
    return OrderApplicationService(order_service)

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        order = await service.create_order(request)
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        order = await service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/customer/{customer_id}", response_model=List[OrderResponse])
async def get_orders_by_customer(
    customer_id: str,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        orders = await service.get_orders_by_customer(customer_id)
        return [_order_to_response(order) for order in orders]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/quote", response_model=OrderQuoteResponse)
async def calculate_quote(
    request: OrderQuoteRequest,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        quote = service.calculate_shipping_quote(request)
        return OrderQuoteResponse(
            price=quote['price'],
            delivery_days=quote['delivery_days'],
            billable_weight=quote['billable_weight']
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{order_id}/quote", response_model=OrderResponse)
async def quote_order(
    order_id: str,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        order = await service.quote_order(order_id)
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: str,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        order = await service.confirm_order(order_id)
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: str,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        success = await service.cancel_order(order_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        return {"message": "Order cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{order_id}/guide", response_model=GuideResponse)
async def generate_guide(
    order_id: str,
    service: OrderApplicationService = Depends(get_order_service)
):
    try:
        guide = await service.generate_guide(order_id)
        return GuideResponse(
            id=str(guide.id.value),
            order_id=str(guide.order_id.value),
            customer_id=str(guide.customer_id.value),
            status=guide.status.value,
            logistics_operator=guide.logistics_operator,
            barcode=guide.barcode,
            qr_code=guide.qr_code,
            pickup_code=guide.pickup_code,
            created_at=guide.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

def _order_to_response(order) -> OrderResponse:
    return OrderResponse(
        id=str(order.id.value),
        customer_id=str(order.customer_id.value),
        recipient={
            "name": order.recipient.name,
            "phone": order.recipient.phone,
            "email": order.recipient.email,
            "address": order.recipient.address,
            "city": order.recipient.city,
            "country": order.recipient.country,
            "postal_code": order.recipient.postal_code
        },
        package_dimensions={
            "length_cm": order.package_dimensions.length_cm,
            "width_cm": order.package_dimensions.width_cm,
            "height_cm": order.package_dimensions.height_cm,
            "weight_kg": order.package_dimensions.weight_kg
        },
        declared_value=order.declared_value,
        service_type=order.service_type,
        status=order.status,
        origin_address=order.origin_address,
        origin_city=order.origin_city,
        notes=order.notes,
        quoted_price=order.quoted_price,
        estimated_delivery_days=order.estimated_delivery_days,
        created_at=order.created_at,
        updated_at=order.updated_at
    )