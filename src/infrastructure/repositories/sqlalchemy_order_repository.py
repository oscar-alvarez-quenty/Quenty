from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.repositories.order_repository import OrderRepository
from src.domain.entities.order import Order
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId
from src.infrastructure.models.order_model import OrderModel
from src.infrastructure.mappers.order_mapper import OrderMapper

class SQLAlchemyOrderRepository(OrderRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = OrderMapper()
    
    async def save(self, order: Order) -> Order:
        model = self.mapper.to_model(order)
        
        # Check if order exists
        existing = await self.session.get(OrderModel, order.id.value)
        if existing:
            # Update existing order
            for key, value in model.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            model = existing
        else:
            # Add new order
            self.session.add(model)
        
        await self.session.commit()
        await self.session.refresh(model)
        return self.mapper.to_entity(model)
    
    async def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        model = await self.session.get(OrderModel, order_id.value)
        return self.mapper.to_entity(model) if model else None
    
    async def find_by_customer_id(self, customer_id: CustomerId) -> List[Order]:
        stmt = select(OrderModel).where(OrderModel.customer_id == customer_id.value)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Order]:
        stmt = select(OrderModel).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self.mapper.to_entity(model) for model in models]
    
    async def delete(self, order_id: OrderId) -> bool:
        model = await self.session.get(OrderModel, order_id.value)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False