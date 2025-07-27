from sqlalchemy import update, select, func, asc, desc, or_, cast, String
from sqlalchemy.orm import selectinload
from src.models.models import ClientRatebook, Rate 
from src.schemas.datatables_schema import ListRequest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from src.schemas.rate_schema import RateCreate, RateUpdate, RateOut


class RateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_rate_by_id(self, rate_id: int):
        stmt = select(Rate).where(Rate.id == rate_id, Rate.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        rate = result.scalar_one_or_none()

        if not rate:
            raise ValueError(f"Rate {rate_id} not found")

        return rate


    async def list_rates(self, params: ListRequest):
        # Base query sin eliminados
        query = select(Rate).where(Rate.deleted_at.is_(None))

        # 🔍 Búsqueda global usando solo columnas searchable
        search_term = params.search.value.strip().lower() if params.search and params.search.value else None
        if search_term:
            conditions = []
            for col in params.columns:
                if col.searchable:
                    model_attr = getattr(Rate, col.data, None)
                    if model_attr is not None:
                        # UPPER para case-insensitive search
                        conditions.append(func.lower(cast(model_attr, String)).ilike(f"%{search_term}%"))

            if conditions:
                query = query.where(or_(*conditions))

        # Total filtrado
        filtered_stmt = query.with_only_columns(func.count()).order_by(None)
        filtered_result = await self.db.execute(filtered_stmt)
        filtered = filtered_result.scalar_one()

        # 🔃 Orden dinámico
        order_index = params.order[0].column if params.order else 0
        order_field = params.columns[order_index].data
        reverse = params.order[0].dir.lower() == "desc" if params.order else False

        order_column = getattr(Rate, order_field, None)
        if order_column is not None:
            query = query.order_by(desc(order_column) if reverse else asc(order_column))

        # 📄 Paginación
        query = query.offset(params.start).limit(params.length)
        result = await self.db.execute(query)
        paginated = result.scalars().all()

        # Total sin filtros
        total_stmt = select(func.count()).select_from(Rate).where(Rate.deleted_at.is_(None))
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()

        return total, filtered, paginated
    

    async def create_rate(self, data: RateCreate):
        new_rate = Rate(
            operator_id=data.operator_id,
            service_id=data.service_id,
            name=data.name,
            weight_min=data.weight_min,
            weight_max=data.weight_max,
            fixed_fee=data.fixed_fee,
            percentage=data.percentage,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(new_rate)
        await self.db.commit()
        await self.db.refresh(new_rate)
        return new_rate
    

    async def update_rate(self, rate_id: int, data: RateUpdate) -> RateOut:
        rate = await self.get_rate_by_id(rate_id)

        for field, value in data.dict(exclude_unset=True).items():
            setattr(rate, field, value)

        rate.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(rate)
        rate = await self.get_rate_by_id(rate_id)

        # Propaga los cambios a ClientRatebook si es dependiente
        await self.propagate_rate_update(rate)

        return RateOut.model_validate(rate)
    

    async def delete_rate(self, rate_id: int) -> None:
        rate = await self.get_rate_by_id(rate_id)
        now = datetime.utcnow()

        # Marcar la tarifa como eliminada (soft delete)
        rate.deleted_at = now
        rate.updated_at = now
        await self.db.commit()

        # Propagar la eliminación a ClientRatebook
        await self.propagate_rate_deletion(rate_id, now)
    

    async def propagate_rate_update(self, rate: Rate):
        """Actualiza los registros ClientRatebook que dependen de esta tarifa."""
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


    async def propagate_rate_deletion(self, rate_id: int, deleted_at: datetime) -> None:
        stmt = (
            update(ClientRatebook)
            .where(
                ClientRatebook.rate_id == rate_id,
                ClientRatebook.deleted_at.is_(None),
                ClientRatebook.dependent.is_(True)
            )
            .values(deleted_at=deleted_at)
            .execution_options(synchronize_session="fetch")
        )
        await self.db.execute(stmt)
        await self.db.commit()

    
