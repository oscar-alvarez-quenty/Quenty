from uuid import UUID, uuid4
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderId:
    value: UUID
    
    @classmethod
    def generate(cls) -> "OrderId":
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, value: str) -> "OrderId":
        return cls(UUID(value))
    
    def __str__(self) -> str:
        return str(self.value)