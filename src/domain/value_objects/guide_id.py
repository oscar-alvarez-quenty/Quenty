import random
import string
from dataclasses import dataclass

@dataclass(frozen=True)
class GuideId:
    value: str
    
    @classmethod
    def generate(cls) -> "GuideId":
        # Generate a unique guide ID (e.g., QUE240001234)
        prefix = "QUE"
        year = "24"
        number = ''.join(random.choices(string.digits, k=7))
        return cls(f"{prefix}{year}{number}")
    
    @classmethod
    def from_string(cls, value: str) -> "GuideId":
        if not value.startswith("QUE"):
            raise ValueError("Invalid guide ID format")
        return cls(value)
    
    def __str__(self) -> str:
        return self.value