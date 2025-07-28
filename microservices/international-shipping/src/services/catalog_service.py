from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.schemas.catalog_schema import CatalogCreate, CatalogRateWithRateOut, CatalogUpdate
from src.services.base_service import BaseService
from src.services.catalog_rate_service import CatalogRateService
from src.services.client_ratebook_service import ClientRatebookService
from src.models.models import Catalog

class CatalogService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Catalog)
        self.catalog_rate_service = CatalogRateService(db)
        self.client_ratebook_service = ClientRatebookService(db)

    async def create_catalog(self, data: CatalogCreate) -> Catalog:
        now = datetime.utcnow()
        catalog = Catalog(
            name=data.name,
            created_at=now,
            updated_at=now,
        )
        self.db.add(catalog)
        await self.db.commit()
        await self.db.refresh(catalog)
        return catalog


    async def update_catalog(self, catalog_id: int, data: CatalogUpdate) -> Catalog:
        catalog = await self.get_by_id(catalog_id)
        for field, value in data.dict(exclude_unset=True).items():
            setattr(catalog, field, value)
        catalog.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(catalog)
        return catalog


    async def delete_catalog(self, catalog_id: int):
        now = datetime.utcnow()
        catalog = await self.soft_delete(catalog_id)
        
        await self.catalog_rate_service.soft_delete_by_catalog(catalog_id, now)
        await self.client_ratebook_service.soft_delete_by_catalog(catalog_id, now)

        return catalog


    async def assign_single_rate_to_catalog(self, catalog_id: int, rate_id: int):
        now = datetime.utcnow()
        await self.catalog_rate_service.assign(catalog_id, rate_id, now)

        # Propagar a clientes dependientes
        dependents = await self.client_ratebook_service.get_dependent_clients_by_catalog(catalog_id)
        await self.client_ratebook_service.expand_rate_to_clients(catalog_id, rate_id, dependents, now)


    async def remove_rate_from_catalog(self, catalog_id: int, rate_id: int):
        now = datetime.utcnow()
        await self.catalog_rate_service.soft_delete(catalog_id, rate_id, now)
        await self.client_ratebook_service.soft_delete_by_catalog_and_rate(catalog_id, rate_id, now)

    async def get_assigned_rates(self, catalog_id: int) -> list[CatalogRateWithRateOut]:
        return await self.catalog_rate_service.get_with_rate_info(catalog_id)
