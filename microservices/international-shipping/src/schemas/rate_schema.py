from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from typing import Optional
from pydantic.config import ConfigDict

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
    model_config = ConfigDict(from_attributes=True)

class RateListResponse(BaseModel):
    records_total: int
    records_filtered: int
    data: List[RateOut]

class RateUpdate(BaseModel):
    operator_id: Optional[str] = Field(default=None)
    service_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    weight_min: Optional[float] = Field(default=None)
    weight_max: Optional[float] = Field(default=None)
    fixed_fee: Optional[float] = Field(default=None)
    percentage: Optional[bool] = Field(default=None)

class AssignRateToClientInput(BaseModel):
    rate_id: int
    client_id: int
    warehouse_id: int