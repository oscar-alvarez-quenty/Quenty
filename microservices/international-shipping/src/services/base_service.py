from typing import Type, Any
from sqlalchemy import select, update, func, or_, cast, String, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta
from datetime import datetime
from src.schemas.datatables_schema import ListRequest

class BaseService:
    def __init__(self, db: AsyncSession, model: Type[DeclarativeMeta]):
        self.db = db
        self.model = model

    async def get_by_id(self, entity_id: Any):
        stmt = select(self.model).where(self.model.id == entity_id, self.model.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        instance = result.scalar_one_or_none()
        if not instance:
            raise ValueError(f"{self.model.__name__} {entity_id} not found")
        return instance

    async def soft_delete(self, entity_id: Any):
        now = datetime.utcnow()
        instance = await self.get_by_id(entity_id)
        instance.deleted_at = now
        instance.updated_at = now
        await self.db.commit()
        return instance

    async def list_datatables(self, params: ListRequest):
        query = select(self.model).where(self.model.deleted_at.is_(None))

        # Search filter
        search_term = params.search.value.strip().lower() if params.search and params.search.value else None
        if search_term:
            conditions = []
            for col in params.columns:
                if col.searchable:
                    attr = getattr(self.model, col.data, None)
                    if attr is not None:
                        conditions.append(func.lower(cast(attr, String)).ilike(f"%{search_term}%"))
            if conditions:
                query = query.where(or_(*conditions))

        # Filtered count
        filtered_stmt = query.with_only_columns(func.count()).order_by(None)
        filtered_result = await self.db.execute(filtered_stmt)
        filtered = filtered_result.scalar_one()

        # Ordering
        order_index = params.order[0].column if params.order else 0
        order_field = params.columns[order_index].data
        reverse = params.order[0].dir.lower() == "desc" if params.order else False
        order_column = getattr(self.model, order_field, None)
        if order_column:
            query = query.order_by(desc(order_column) if reverse else asc(order_column))

        # Pagination
        query = query.offset(params.start).limit(params.length)
        result = await self.db.execute(query)
        data = result.scalars().all()

        # Total count
        total_stmt = select(func.count()).select_from(self.model).where(self.model.deleted_at.is_(None))
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()

        return total, filtered, data
