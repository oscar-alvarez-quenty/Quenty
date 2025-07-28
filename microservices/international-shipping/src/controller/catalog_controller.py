from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.catalog_service import CatalogService
from src.schemas.catalog_schema import (
    CatalogCreate, CatalogRateWithRateOut, CatalogUpdate, CatalogOut, CatalogListResponse, AssignRateInput
)
from src.schemas.datatables_schema import ListRequest
from pydantic import TypeAdapter
from typing import List

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.post("/", response_model=CatalogListResponse)
async def list_catalogs(
    request: ListRequest, 
    db: AsyncSession = Depends(get_db)):
    service = CatalogService(db)
    total, filtered, catalogs = await service.list_datatables(request)
    data = [TypeAdapter(CatalogOut).validate_python(cat, from_attributes=True) for cat in catalogs]
    return CatalogListResponse(
        records_total=total,
        records_filtered=filtered,
        data=data
    )


@router.get("/{catalog_id}", response_model=CatalogOut)
async def get_catalog(catalog_id: int, db: AsyncSession = Depends(get_db)):
    service = CatalogService(db)
    try:
        catalog = await service.get_by_id(catalog_id)
        return TypeAdapter(CatalogOut).validate_python(catalog, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/create", response_model=CatalogOut)
async def create_catalog(data: CatalogCreate, db: AsyncSession = Depends(get_db)):
    service = CatalogService(db)
    catalog = await service.create_catalog(data)
    return TypeAdapter(CatalogOut).validate_python(catalog, from_attributes=True)


@router.put("/{catalog_id}", response_model=CatalogOut)
async def update_catalog(catalog_id: int, data: CatalogUpdate, db: AsyncSession = Depends(get_db)):
    service = CatalogService(db)
    try:
        catalog = await service.update_catalog(catalog_id, data)
        return TypeAdapter(CatalogOut).validate_python(catalog, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{catalog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog(catalog_id: int, db: AsyncSession = Depends(get_db)):
    service = CatalogService(db)
    try:
        await service.delete_catalog(catalog_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None


@router.post("/{catalog_id}/assign-rate")
async def assign_single_rate_to_catalog(
    catalog_id: int,
    data: AssignRateInput,
    db: AsyncSession = Depends(get_db),
):
    service = CatalogService(db)
    if data.assign:
        await service.assign_single_rate_to_catalog(catalog_id, data.rate_id)
        message  = "Tarifa asignada correctamente"
    else:
        await service.remove_rate_from_catalog(catalog_id, data.rate_id)
        message  = "Tarifa desasignada correctamente"
    return {"message": message}


@router.get("/{catalog_id}/assigned-rates", response_model=List[CatalogRateWithRateOut])
async def list_assigned_rates(catalog_id: int, db: AsyncSession = Depends(get_db)):
    service = CatalogService(db)
    return await service.get_assigned_rates(catalog_id)


