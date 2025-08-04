from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from src.database import get_db
from src.services.responsibility_letter_service import ResponsibilityLetterService
from src.schemas.signature_schema import ResponsibilityLetterRequest

router = APIRouter(prefix="/letters", tags=["letters"])

@router.post("/responsibility/pdf")
async def get_responsibility_letter_pdf(
    request: ResponsibilityLetterRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        pdf_bytes = await ResponsibilityLetterService.generate_pdf(
            envio_id=request.envio_id,
            language=request.language,
            db=db
        )
        return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
            # "Content-Disposition": f"inline; filename=carta_responsabilidad_{request.envio_id}.pdf"
            "Content-Disposition": f"attachment; filename=carta_responsabilidad_{request.envio_id}.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
