from pydantic import BaseModel
from datetime import datetime
from typing import List
from typing import Optional

class RateCreate(BaseModel):
    operator_id: str
    service_id: str
    name: str
    weight_min: float
    weight_max: float
    fixed_fee: float
    percentage: bool

class RateOut(RateCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RateListResponse(BaseModel):
    records_total: int
    records_filtered: int
    data: List[RateOut]

class RateUpdate(BaseModel):
    operator_id: Optional[str]
    service_id: Optional[str]
    name: Optional[str]
    weight_min: Optional[float]
    weight_max: Optional[float]
    fixed_fee: Optional[float]
    percentage: Optional[bool]

class AssignRateToClientInput(BaseModel):
    rate_id: int
    client_id: int
    warehouse_id: int