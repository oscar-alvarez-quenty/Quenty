from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.order import Order
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.customer_id import CustomerId

class OrderRepository(ABC):
    
    @abstractmethod
    async def save(self, order: Order) -> Order:
        pass
    
    @abstractmethod
    async def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        pass
    
    @abstractmethod
    async def find_by_customer_id(self, customer_id: CustomerId) -> List[Order]:
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Order]:
        pass
    
    @abstractmethod
    async def delete(self, order_id: OrderId) -> bool:
        pass