from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from pydantic.config import ConfigDict

class DocumentTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

class DocumentTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class DocumentTypeOut(DocumentTypeCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentTypeListResponse(BaseModel):
    records_total: int
    records_filtered: int
    data: List[DocumentTypeOut]
