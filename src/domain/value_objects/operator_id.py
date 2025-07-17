from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class OperatorId:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Operator ID cannot be empty")
        if len(self.value) > 50:
            raise ValueError("Operator ID cannot exceed 50 characters")

    @classmethod
    def generate(cls) -> "OperatorId":
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value