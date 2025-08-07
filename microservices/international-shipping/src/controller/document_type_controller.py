from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import TypeAdapter

from src.database import get_db
from src.schemas.document_type_schema import (
    DocumentTypeCreate,
    DocumentTypeUpdate,
    DocumentTypeOut,
    DocumentTypeListResponse,
)
from src.schemas.datatables_schema import ListRequest
from src.services.document_type_service import DocumentTypeService
from src.core.auth import get_current_user

router = APIRouter(prefix="/document-types", tags=["document-types"])

@router.get("/{document_type_id}", response_model=DocumentTypeOut)
async def get_document_type_by_id(document_type_id: int, db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    service = DocumentTypeService(db)
    try:
        doc_type = await service.get_by_id(document_type_id)
        return TypeAdapter(DocumentTypeOut).validate_python(doc_type, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=DocumentTypeListResponse)
async def list_document_types(request: ListRequest, db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    service = DocumentTypeService(db)
    total, filtered, document_types = await service.list_datatables(request)
    data = [TypeAdapter(DocumentTypeOut).validate_python(dt, from_attributes=True) for dt in document_types]
    return DocumentTypeListResponse(records_total=total, records_filtered=filtered, data=data)

@router.get("/{document_type_id}", response_model=DocumentTypeOut)
async def get_document_type(document_type_id: int, db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    service = DocumentTypeService(db)
    try:
        document_type = await service.get_by_id(document_type_id)
        return TypeAdapter(DocumentTypeOut).validate_python(document_type, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/create", response_model=DocumentTypeOut)
async def create_document_type(data: DocumentTypeCreate, db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    service = DocumentTypeService(db)
    document_type = await service.create_document_type(data)
    return TypeAdapter(DocumentTypeOut).validate_python(document_type, from_attributes=True)

@router.put("/{document_type_id}", response_model=DocumentTypeOut)
async def update_document_type(document_type_id: int, data: DocumentTypeUpdate, db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    service = DocumentTypeService(db)
    try:
        document_type = await service.update_document_type(document_type_id, data)
        return TypeAdapter(DocumentTypeOut).validate_python(document_type, from_attributes=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{document_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_type(document_type_id: int, db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)):
    service = DocumentTypeService(db)
    try:
        await service.soft_delete(document_type_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None
