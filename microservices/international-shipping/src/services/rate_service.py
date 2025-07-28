from src.models.models import Rate, ClientRatebook
from src.schemas.rate_schema import RateCreate, RateUpdate, RateOut
from src.schemas.datatables_schema import ListRequest
from src.services.base_service import BaseService
from sqlalchemy import update, select
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


class RateService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Rate)

    async def create_rate(self, data: RateCreate) -> Rate:
        now = datetime.utcnow()
        new_rate = Rate(
            operator_id=data.operator_id,
            service_id=data.service_id,
            name=data.name,
            weight_min=data.weight_min,
            weight_max=data.weight_max,
            fixed_fee=data.fixed_fee,
            percentage=data.percentage,
            created_at=now,
            updated_at=now,
        )
        self.db.add(new_rate)
        await self.db.commit()
        await self.db.refresh(new_rate)
        return new_rate

    async def update_rate(self, rate_id: int, data: RateUpdate) -> RateOut:
        rate = await self.get_by_id(rate_id)

        for field, value in data.dict(exclude_unset=True).items():
            setattr(rate, field, value)

        rate.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(rate)

        await self.propagate_rate_update(rate)
        return RateOut.model_validate(rate)

    async def delete_rate(self, rate_id: int) -> None:
        deleted_rate = await self.soft_delete(rate_id)
        await self.propagate_rate_deletion(rate_id, deleted_rate.deleted_at)

    async def propagate_rate_update(self, rate: Rate):
        """Actualizar ClientRatebook que dependen de esta tarifa."""
        await self.db.execute(
            update(ClientRatebook)
            .where(
                ClientRatebook.rate_id == rate.id,
                ClientRatebook.deleted_at.is_(None),
                ClientRatebook.dependent == True
            )
            .values(
                operator_id=rate.operator_id,
                service_id=rate.service_id,
                name=rate.name,
                weight_min=rate.weight_min,
                weight_max=rate.weight_max,
                fixed_fee=rate.fixed_fee,
                percentage=rate.percentage,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()

    async def propagate_rate_deletion(self, rate_id: int, deleted_at: datetime):
        await self.db.execute(
            update(ClientRatebook)
            .where(
                ClientRatebook.rate_id == rate_id,
                ClientRatebook.deleted_at.is_(None),
                ClientRatebook.dependent == True
            )
            .values(deleted_at=deleted_at)
        )
        await self.db.commit()


    async def assign_rate_to_client(self, rate_id: int, client_id: int, warehouse_id: int) -> ClientRatebook:
        now = datetime.utcnow()

        # Verificar que la tarifa exista
        rate = await self.db.scalar(
            select(Rate).where(Rate.id == rate_id, Rate.deleted_at.is_(None))
        )
        if not rate:
            raise ValueError(f"La tarifa con id: {rate_id} no existe")

        # Evitar duplicado
        existing = await self.db.scalar(
            select(ClientRatebook).where(
                ClientRatebook.rate_id == rate_id,
                ClientRatebook.client_id == client_id,
                ClientRatebook.warehouse_id == warehouse_id,
                ClientRatebook.deleted_at.is_(None),
                ClientRatebook.dependent == True
            )
        )
        if existing:
            raise ValueError("Ya existe una tarifa asignada a este cliente y bodega")

        client_rate = ClientRatebook(
            client_id=client_id,
            warehouse_id=warehouse_id,
            rate_id=rate.id,
            catalog_id=None,
            operator_id=rate.operator_id,
            service_id=rate.service_id,
            name=rate.name,
            weight_min=rate.weight_min,
            weight_max=rate.weight_max,
            fixed_fee=rate.fixed_fee,
            percentage=rate.percentage,
            dependent=True,
            created_at=now,
            updated_at=now
        )

        self.db.add(client_rate)
        await self.db.commit()
        await self.db.refresh(client_rate)
        return client_rate