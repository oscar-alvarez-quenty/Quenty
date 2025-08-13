from pydantic import BaseModel, Field
from typing import List

class LabelRequest(BaseModel):
    envio_ids: List[int] = Field(..., example=[101, 102, 103])
    format_type: int = Field(..., ge=1, le=2, example=1)
