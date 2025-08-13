from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from typing import Literal


class SignatureOut(BaseModel):
    id: int
    client_id: str
    image_base64: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResponsibilityLetterRequest(BaseModel):
    envio_id: str = Field(..., example="ABC123")
    language: Literal["esp", "ing"] = Field(default="esp", example="esp")