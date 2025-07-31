from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import TypeAdapter

from src.database import get_db
from src.schemas.document_schema import DocumentUploadInput, DocumentOut
from src.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    input_data: DocumentUploadInput = Depends(),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo no válido")
    
    service = DocumentService(db)
    document = await service.create_document(file.filename, input_data)
    return TypeAdapter(DocumentOut).validate_python(document, from_attributes=True)

@router.get("/filter", response_model=List[DocumentOut])
async def list_documents(
    client_id: Optional[str] = Query(None),
    envio_id: Optional[str] = Query(None),
    document_type_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    documents = await service.list_documents(client_id, envio_id, document_type_id)
    return [TypeAdapter(DocumentOut).validate_python(doc, from_attributes=True) for doc in documents]

@router.get("/{document_id}", response_model=DocumentOut)
async def get_document_by_id(document_id: int, db: AsyncSession = Depends(get_db)):
    service = DocumentService(db)
    try:
        document = await service.get_by_id(document_id)
        return TypeAdapter(DocumentOut).validate_python(document, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    service = DocumentService(db)
    try:
        await service.soft_delete(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None
