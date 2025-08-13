from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from src.services.base_service import BaseService
from src.models.models import DocumentType
from src.schemas.document_type_schema import DocumentTypeCreate, DocumentTypeUpdate

class DocumentTypeService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, DocumentType)

    async def create_document_type(self, data: DocumentTypeCreate) -> DocumentType:
        document_type = DocumentType(
            code=data.code,
            name=data.name,
            description=data.description,
            created_at=datetime.utcnow(),
        )
        self.db.add(document_type)
        await self.db.commit()
        await self.db.refresh(document_type)
        return document_type

    async def update_document_type(self, document_type_id: int, data: DocumentTypeUpdate) -> DocumentType:
        document_type = await self.get_by_id(document_type_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(document_type, field, value)
        await self.db.commit()
        await self.db.refresh(document_type)
        return document_type
