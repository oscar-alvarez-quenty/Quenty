from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from io import BytesIO

from src.schemas.label_schema import LabelRequest
from src.services.label_service import LabelService

router = APIRouter(prefix="/api/v1/labels", tags=["labels"])

@router.post("/generate-labels")
async def generate_labels_endpoint(request: LabelRequest):
    try:
        pdf_bytes = await LabelService.generate_labels(request.envio_ids, request.format_type)
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=labels.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF labels: {e}")
