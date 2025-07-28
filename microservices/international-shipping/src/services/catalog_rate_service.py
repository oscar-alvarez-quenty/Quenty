from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from datetime import datetime

from src.models.models import CatalogRate, Rate
from src.schemas.catalog_schema import CatalogRateWithRateOut, RateOut
from src.services.base_service import BaseService


class CatalogRateService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CatalogRate)

    async def assign(self, catalog_id: int, rate_id: int, now: datetime):
        exists = await self.db.scalar(
            select(CatalogRate).where(
                CatalogRate.catalog_id == catalog_id,
                CatalogRate.rate_id == rate_id,
                CatalogRate.deleted_at.is_(None)
            )
        )
        if not exists:
            self.db.add(CatalogRate(
                catalog_id=catalog_id,
                rate_id=rate_id,
                created_at=now,
                updated_at=now
            ))
            await self.db.commit()

    async def soft_delete(self, catalog_id: int, rate_id: int, deleted_at: datetime):
        await self.db.execute(
            update(CatalogRate)
            .where(
                CatalogRate.catalog_id == catalog_id,
                CatalogRate.rate_id == rate_id,
                CatalogRate.deleted_at.is_(None)
            )
            .values(deleted_at=deleted_at, updated_at=deleted_at)
        )
        await self.db.commit()

    async def soft_delete_by_catalog(self, catalog_id: int, deleted_at: datetime):
        await self.db.execute(
            update(CatalogRate)
            .where(
                CatalogRate.catalog_id == catalog_id,
                CatalogRate.deleted_at.is_(None)
            )
            .values(deleted_at=deleted_at, updated_at=deleted_at)
        )
        await self.db.commit()

    async def get_with_rate_info(self, catalog_id: int) -> list[CatalogRateWithRateOut]:
        result = await self.db.execute(
            select(CatalogRate, Rate)
            .join(Rate, CatalogRate.rate_id == Rate.id)
            .where(CatalogRate.catalog_id == catalog_id)
        )
        rows = result.all()
        return [
            CatalogRateWithRateOut(
                id=cr.id,
                catalog_id=cr.catalog_id,
                rate=RateOut.model_validate(rate, from_attributes=True)
            )
            for cr, rate in rows
        ]
