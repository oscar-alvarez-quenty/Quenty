# src/schemas/client_ratebook_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClientRatebookBase(BaseModel):
    operator_id: Optional[str]
    service_id: Optional[str]
    name: Optional[str]
    weight_min: Optional[float]
    weight_max: Optional[float]
    fixed_fee: Optional[float]
    percentage: Optional[bool]

class ClientRatebookCreate(ClientRatebookBase):
    client_id: int
    warehouse_id: int

class ClientRatebookUpdate(ClientRatebookBase):
    pass

class ClientRatebookOut(ClientRatebookBase):
    id: int
    client_id: int
    warehouse_id: int
    catalog_id: Optional[int]
    rate_id: Optional[int]
    dependent: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True

class ClientRatebookMatchRequest(BaseModel):
    client_id: str
    warehouse_id: str
    operator_id: str
    service_id: str
    weight: float