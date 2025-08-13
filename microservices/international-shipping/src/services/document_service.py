import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from src.services.base_service import BaseService
from typing import Optional, List
from src.models.models import Document
from src.schemas.document_schema import DocumentUploadInput
from sqlalchemy import select


class DocumentService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Document)

    async def create_document(self, file_name: str, input_data: DocumentUploadInput) -> Document:
        ext = file_name.split('.')[-1]
        original_name = file_name
        unique_name = str(uuid.uuid4())
        storage_url = f"https://fake-storage.local/{unique_name}.{ext}"

        doc = Document(
            name=original_name,
            unique_name=unique_name,
            extension=ext,
            storage_url=storage_url,
            client_id=input_data.client_id,
            user_id=input_data.user_id,
            envio_id=input_data.envio_id,
            document_type_id=input_data.document_type_id,
            created_at=datetime.utcnow(),
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_documents(
        self,
        client_id: Optional[str] = None,
        envio_id: Optional[str] = None,
        document_type_id: Optional[int] = None,
    ) -> List[Document]:
        stmt = select(Document).where(Document.deleted_at.is_(None))

        if client_id:
            stmt = stmt.where(Document.client_id == client_id)
        if envio_id:
            stmt = stmt.where(Document.envio_id == envio_id)
        if document_type_id:
            stmt = stmt.where(Document.document_type_id == document_type_id)

        result = await self.db.execute(stmt)
        return result.scalars().all()