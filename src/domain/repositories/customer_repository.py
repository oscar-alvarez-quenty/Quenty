from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email

class CustomerRepository(ABC):
    
    @abstractmethod
    async def save(self, customer: Customer) -> Customer:
        pass
    
    @abstractmethod
    async def find_by_id(self, customer_id: CustomerId) -> Optional[Customer]:
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[Customer]:
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        pass
    
    @abstractmethod
    async def delete(self, customer_id: CustomerId) -> bool:
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        pass