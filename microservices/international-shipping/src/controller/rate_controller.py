from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession 
from src.services.rate_service import RateService
from src.schemas.datatables_schema import ListRequest
from src.schemas.rate_schema import RateListResponse, RateOut, RateCreate, RateUpdate
from pydantic import TypeAdapter
from src.database import get_db

router = APIRouter(prefix="/rates", tags=["rates"])

@router.get("/{rate_id}", response_model=RateOut)
async def get_rate(rate_id: int, db: AsyncSession = Depends(get_db)):
    service = RateService(db)
    try:
        rate = await service.get_by_id(rate_id)
        return TypeAdapter(RateOut).validate_python(rate, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=RateListResponse)
async def list_rates(
    request: ListRequest,
    db: AsyncSession = Depends(get_db),
    # current_user=Depends(require_permissions("rates:list"))
):
    service = RateService(db)
    total, filtered, rates = await service.list_datatables(request)
    print(f"Total rates: {total}, Filtered rates: {filtered}")
    print(f"{rates}")

    # Mapear a Pydantic
    data = [TypeAdapter(RateOut).validate_python(r, from_attributes=True) for r in rates]

    return RateListResponse(
        records_total=total,
        records_filtered=filtered,
        data=data
    )


@router.post("/create", response_model=RateOut)
async def create_rate(
    rate_data: RateCreate,
    db: AsyncSession = Depends(get_db),
    # current_user=Depends(require_permissions("rates:create"))
):
    service = RateService(db)
    new_rate = await service.create_rate(rate_data)
    return TypeAdapter(RateOut).validate_python(new_rate, from_attributes=True)


@router.put("/{rate_id}", response_model=RateOut)
async def update_rate(
    rate_id: int,
    data: RateUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = RateService(db)
    try:
        return await service.update_rate(rate_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(rate_id: int, db: AsyncSession = Depends(get_db)):
    service = RateService(db)
    try:
        await service.delete_rate(rate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None