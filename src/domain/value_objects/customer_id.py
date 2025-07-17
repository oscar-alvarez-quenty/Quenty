from uuid import UUID, uuid4
from dataclasses import dataclass

@dataclass(frozen=True)
class CustomerId:
    value: UUID
    
    @classmethod
    def generate(cls) -> "CustomerId":
        return cls(uuid4())
    
    @classmethod
    def from_string(cls, value: str) -> "CustomerId":
        return cls(UUID(value))
    
    def __str__(self) -> str:
        return str(self.value)