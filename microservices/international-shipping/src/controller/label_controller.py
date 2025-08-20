from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from src.schemas.label_schema import LabelRequest
from src.services.label_service import LabelService
from src.core.auth import get_current_user

router = APIRouter(prefix="/labels", tags=["labels"])

@router.post("/generate-labels")
async def generate_labels_endpoint(request: LabelRequest
    ,current_user = Depends(get_current_user)
    ):
    try:
        pdf_bytes = await LabelService.generate_labels(request.envio_ids, request.format_type)
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=labels.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF labels: {e}")
