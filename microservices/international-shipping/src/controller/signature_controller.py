from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import base64

from src.database import get_db
from src.services.signature_service import SignatureService
from src.schemas.signature_schema import SignatureOut
from src.core.auth import get_current_user

router = APIRouter(prefix="/signatures", tags=["signatures"])

@router.post("/", response_model=SignatureOut)
async def upload_signature(
    client_id: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if image.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Only PNG images are allowed")

    image_bytes = await image.read()
    image_base64 = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

    service = SignatureService(db)
    result = await service.create_or_update_signature(client_id, image_base64)
    return result
