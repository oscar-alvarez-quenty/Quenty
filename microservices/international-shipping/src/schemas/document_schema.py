from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from fastapi import Form


class DocumentUploadInput:
    def __init__(
        self,
        client_id: str = Form(...),
        user_id: str = Form(...),
        envio_id: Optional[str] = Form(None),
        document_type_id: int = Form(...)
    ):
        self.client_id = client_id
        self.user_id = user_id
        self.envio_id = envio_id
        self.document_type_id = document_type_id


class DocumentOut(BaseModel):
    id: int
    name: str
    unique_name: str
    extension: str
    storage_url: str
    client_id: str
    user_id: str
    envio_id: Optional[str]
    document_type_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
