# src/routes/client_ratebook_controller.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.client_ratebook_service import ClientRatebookService
from src.schemas.client_ratebook_schema import (
    ClientRatebookMatchRequest,
    ClientRatebookOut,
    ClientRatebookCreate,
    ClientRatebookUpdate
)
from pydantic import TypeAdapter

router = APIRouter(prefix="/client-ratebook", tags=["client-ratebook"])


@router.get("/{client_id}/{warehouse_id}", response_model=list[ClientRatebookOut])
async def list_client_rates(client_id: str, warehouse_id: str, db: AsyncSession = Depends(get_db)):
    service = ClientRatebookService(db)
    rates = await service.list_by_client_and_warehouse(client_id, warehouse_id)
    return [TypeAdapter(ClientRatebookOut).validate_python(r, from_attributes=True) for r in rates]


@router.get("/detail/{ratebook_id}", response_model=ClientRatebookOut)
async def get_client_rate(ratebook_id: int, db: AsyncSession = Depends(get_db)):
    service = ClientRatebookService(db)
    try:
        rate = await service.get_by_id(ratebook_id)
        return TypeAdapter(ClientRatebookOut).validate_python(rate, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{ratebook_id}", response_model=ClientRatebookOut)
async def update_client_rate(ratebook_id: int, data: ClientRatebookUpdate, db: AsyncSession = Depends(get_db)):
    service = ClientRatebookService(db)
    try:
        rate = await service.update_client_rate(ratebook_id, data.dict(exclude_unset=True))
        return TypeAdapter(ClientRatebookOut).validate_python(rate, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{ratebook_id}", status_code=204)
async def delete_client_rate(ratebook_id: int, db: AsyncSession = Depends(get_db)):
    service = ClientRatebookService(db)
    try:
        await service.soft_delete(ratebook_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None


@router.post("/", response_model=ClientRatebookOut)
async def create_client_rate(data: ClientRatebookCreate, db: AsyncSession = Depends(get_db)):
    service = ClientRatebookService(db)
    rate = await service.create_client_rate(data.dict())
    return TypeAdapter(ClientRatebookOut).validate_python(rate, from_attributes=True)


@router.post("/match", response_model=ClientRatebookOut)
async def match_client_rate(data: ClientRatebookMatchRequest, db: AsyncSession = Depends(get_db)):
    service = ClientRatebookService(db)
    try:
        rate = await service.find_matching_rate(
            client_id=data.client_id,
            warehouse_id=data.warehouse_id,
            operator_id=data.operator_id,
            service_id=data.service_id,
            weight=data.weight
        )
        return TypeAdapter(ClientRatebookOut).validate_python(rate, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
