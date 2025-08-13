from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from pydantic.config import ConfigDict

class CatalogCreate(BaseModel):
    name: str

class CatalogUpdate(BaseModel):
    name: Optional[str]

class CatalogOut(CatalogCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CatalogListResponse(BaseModel):
    records_total: int
    records_filtered: int
    data: List[CatalogOut]

class AssignRateInput(BaseModel):
    rate_id: int
    assign: bool  # True = asignar, False = desasignar


class RateOut(BaseModel):
    id: int
    operator_id: str
    service_id: str
    name: str
    weight_min: float
    weight_max: float
    fixed_fee: float
    percentage: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CatalogRateWithRateOut(BaseModel):
    rate_id: int  # ID de la asignación en CatalogRate
    catalog_id: int
    rate: RateOut