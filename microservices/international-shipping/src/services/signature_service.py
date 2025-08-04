from src.models.models import ClientSignature
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from src.services.base_service import BaseService

class SignatureService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ClientSignature)

    async def create_or_update_signature(self, client_id: str, image_base64: str) -> ClientSignature:
        stmt = select(ClientSignature).where(ClientSignature.client_id == client_id, ClientSignature.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        existing = result.scalars().first()

        if existing:
            existing.image_base64 = image_base64
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            signature = ClientSignature(
                client_id=client_id,
                image_base64=image_base64,
            )
            self.db.add(signature)
            await self.db.commit()
            await self.db.refresh(signature)
            return signature


    async def get_by_client_id(self, client_id: str) -> ClientSignature:
        stmt = select(ClientSignature).where(ClientSignature.client_id == client_id, ClientSignature.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        signature = result.scalars().first()
        if not signature:
            raise ValueError("Signature not found")
        return signature