from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "COP"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code (e.g., COP, USD)")
        
        # Redondear a 2 decimales
        object.__setattr__(self, 'amount', self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def add(self, other: "Money") -> "Money":
        """Suma dos cantidades de dinero"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        """Resta dos cantidades de dinero"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")
        
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Result would be negative")
        
        return Money(result_amount, self.currency)
    
    def multiply(self, factor: Union[Decimal, float, int]) -> "Money":
        """Multiplica por un factor"""
        if isinstance(factor, (float, int)):
            factor = Decimal(str(factor))
        
        if factor < 0:
            raise ValueError("Cannot multiply by negative factor")
        
        return Money(self.amount * factor, self.currency)
    
    def divide(self, divisor: Union[Decimal, float, int]) -> "Money":
        """Divide por un divisor"""
        if isinstance(divisor, (float, int)):
            divisor = Decimal(str(divisor))
        
        if divisor <= 0:
            raise ValueError("Cannot divide by zero or negative number")
        
        return Money(self.amount / divisor, self.currency)
    
    def percentage(self, percent: Union[Decimal, float, int]) -> "Money":
        """Calcula un porcentaje de la cantidad"""
        if isinstance(percent, (float, int)):
            percent = Decimal(str(percent))
        
        return self.multiply(percent / Decimal('100'))
    
    def is_zero(self) -> bool:
        """Verifica si la cantidad es cero"""
        return self.amount == Decimal('0.00')
    
    def is_greater_than(self, other: "Money") -> bool:
        """Compara si es mayor que otra cantidad"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        
        return self.amount > other.amount
    
    def is_less_than(self, other: "Money") -> bool:
        """Compara si es menor que otra cantidad"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        
        return self.amount < other.amount
    
    def equals(self, other: "Money") -> bool:
        """Compara si es igual a otra cantidad"""
        return self.currency == other.currency and self.amount == other.amount
    
    def format(self, symbol: bool = True) -> str:
        """Formatea la cantidad como string"""
        symbols = {
            "COP": "$",
            "USD": "$",
            "EUR": "€",
            "GBP": "£"
        }
        
        if symbol and self.currency in symbols:
            return f"{symbols[self.currency]}{self.amount:,.2f}"
        else:
            return f"{self.amount:,.2f} {self.currency}"
    
    def to_cents(self) -> int:
        """Convierte a centavos (para APIs de pago)"""
        return int(self.amount * 100)
    
    @classmethod
    def from_cents(cls, cents: int, currency: str = "COP") -> "Money":
        """Crea Money desde centavos"""
        amount = Decimal(cents) / Decimal('100')
        return cls(amount, currency)
    
    @classmethod
    def zero(cls, currency: str = "COP") -> "Money":
        """Crea una cantidad de dinero en cero"""
        return cls(Decimal('0.00'), currency)
    
    def __str__(self) -> str:
        return self.format()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Money):
            return False
        return self.equals(other)
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, Money):
            raise TypeError("Cannot compare Money with non-Money")
        return self.is_less_than(other)
    
    def __gt__(self, other) -> bool:
        if not isinstance(other, Money):
            raise TypeError("Cannot compare Money with non-Money")
        return self.is_greater_than(other)
    
    def __add__(self, other) -> "Money":
        if not isinstance(other, Money):
            raise TypeError("Cannot add non-Money to Money")
        return self.add(other)
    
    def __sub__(self, other) -> "Money":
        if not isinstance(other, Money):
            raise TypeError("Cannot subtract non-Money from Money")
        return self.subtract(other)