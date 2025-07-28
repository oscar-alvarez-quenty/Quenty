from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class CatalogCreate(BaseModel):
    name: str

class CatalogUpdate(BaseModel):
    name: Optional[str]

class CatalogOut(CatalogCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CatalogListResponse(BaseModel):
    records_total: int
    records_filtered: int
    data: List[CatalogOut]

class AssignRateInput(BaseModel):
    rate_id: int
    assign: bool  # True = asignar, False = desasignar


class RateOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CatalogRateWithRateOut(BaseModel):
    id: int  # ID de la asignación en CatalogRate
    catalog_id: int
    rate: RateOut