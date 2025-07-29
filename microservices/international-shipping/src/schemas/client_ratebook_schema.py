from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic.config import ConfigDict


class ClientRatebookBase(BaseModel):
    operator_id: Optional[str] = Field(default=None)
    service_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    weight_min: Optional[float] = Field(default=None)
    weight_max: Optional[float] = Field(default=None)
    fixed_fee: Optional[float] = Field(default=None)
    percentage: Optional[bool] = Field(default=None)

class ClientRatebookCreate(ClientRatebookBase):
    client_id: str
    warehouse_id: str

class ClientRatebookUpdate(ClientRatebookBase):
    pass

class ClientRatebookOut(ClientRatebookBase):
    id: int
    client_id: str
    warehouse_id: str
    catalog_id: Optional[int]
    rate_id: Optional[int]
    dependent: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ClientRatebookMatchRequest(BaseModel):
    client_id: str
    warehouse_id: str
    operator_id: str
    service_id: str
    weight: float