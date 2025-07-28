from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from src.services.base_service import BaseService
from datetime import datetime

from src.models.models import ClientRatebook
from src.schemas.client_ratebook_schema import ClientRatebookOut


class ClientRatebookService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ClientRatebook)

    async def get_dependent_clients_by_catalog(self, catalog_id: int) -> list[tuple[int, int]]:
        result = await self.db.execute(
            select(ClientRatebook.client_id, ClientRatebook.warehouse_id)
            .where(
                ClientRatebook.catalog_id == catalog_id,
                ClientRatebook.deleted_at.is_(None),
                ClientRatebook.dependent == True
            )
            .distinct()
        )
        return result.fetchall()

    async def expand_rate_to_clients(self, catalog_id: int, rate_id: int, clients_bodegas: list[tuple[int, int]], now: datetime):
        for client_id, warehouse_id in clients_bodegas:
            exists = await self.db.scalar(
                select(ClientRatebook)
                .where(
                    ClientRatebook.catalog_id == catalog_id,
                    ClientRatebook.rate_id == rate_id,
                    ClientRatebook.client_id == client_id,
                    ClientRatebook.warehouse_id == warehouse_id,
                    ClientRatebook.deleted_at.is_(None),
                    ClientRatebook.dependent == True
                )
            )
            if not exists:
                self.db.add(ClientRatebook(
                    catalog_id=catalog_id,
                    rate_id=rate_id,
                    client_id=client_id,
                    warehouse_id=warehouse_id,
                    dependent=True,
                    created_at=now,
                    updated_at=now
                ))
        await self.db.commit()

    async def soft_delete_by_catalog(self, catalog_id: int, deleted_at: datetime):
        await self.db.execute(
            update(ClientRatebook)
            .where(
                ClientRatebook.catalog_id == catalog_id,
                ClientRatebook.deleted_at.is_(None),
                ClientRatebook.dependent == True
            )
            .values(deleted_at=deleted_at, updated_at=deleted_at)
        )
        await self.db.commit()

    async def soft_delete_by_catalog_and_rate(self, catalog_id: int, rate_id: int, deleted_at: datetime):
        await self.db.execute(
            update(ClientRatebook)
            .where(
                ClientRatebook.catalog_id == catalog_id,
                ClientRatebook.rate_id == rate_id,
                ClientRatebook.deleted_at.is_(None),
                ClientRatebook.dependent == True
            )
            .values(deleted_at=deleted_at, updated_at=deleted_at)
        )
        await self.db.commit()

    async def list_by_client_and_warehouse(self, client_id: int, warehouse_id: int) -> list[ClientRatebook]:
        result = await self.db.execute(
            select(ClientRatebook).where(
                ClientRatebook.client_id == client_id,
                ClientRatebook.warehouse_id == warehouse_id,
                ClientRatebook.deleted_at.is_(None)
            )
        )
        return result.scalars().all()

    async def update_client_rate(self, ratebook_id: int, data: dict) -> ClientRatebook:
        rate = await self.get_by_id(ratebook_id)
        for key, value in data.items():
            setattr(rate, key, value)
        rate.updated_at = datetime.utcnow()
        rate.dependent = False
        await self.db.commit()
        await self.db.refresh(rate)
        return rate

    async def create_client_rate(self, data: dict) -> ClientRatebook:
        now = datetime.utcnow()
        new_rate = ClientRatebook(
            client_id=data["client_id"],
            warehouse_id=data["warehouse_id"],
            operator_id=data.get("operator_id"),
            service_id=data.get("service_id"),
            name=data.get("name"),
            weight_min=data.get("weight_min"),
            weight_max=data.get("weight_max"),
            fixed_fee=data.get("fixed_fee"),
            percentage=data.get("percentage"),
            dependent=False,
            created_at=now,
            updated_at=now
        )
        self.db.add(new_rate)
        await self.db.commit()
        await self.db.refresh(new_rate)
        return new_rate
    

    async def find_matching_rate(
        self, client_id: str, warehouse_id: str, operator_id: str, service_id: str, weight: float) -> ClientRatebook:
        stmt = select(ClientRatebook).where(
            ClientRatebook.client_id == client_id,
            ClientRatebook.warehouse_id == warehouse_id,
            ClientRatebook.operator_id == operator_id,
            ClientRatebook.service_id == service_id,
            ClientRatebook.weight_min <= weight,
            ClientRatebook.weight_max > weight,
            ClientRatebook.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        rate = result.scalar_one_or_none()
        if not rate:
            fecha_defecto = datetime(2025, 1, 1)
            rate = ClientRatebookOut(
                id=0,
                client_id=client_id,
                warehouse_id=warehouse_id,
                catalog_id=None,
                rate_id=None,
                dependent=False,
                operator_id=operator_id,
                service_id=service_id,
                name="Tarifa por defecto",
                weight_min=0,
                weight_max=500,
                fixed_fee=30,
                percentage=True,
                created_at=fecha_defecto,
                updated_at=fecha_defecto,
                deleted_at=None
            )
        return rate
