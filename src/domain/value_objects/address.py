from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "Colombia"
    
    def __post_init__(self):
        if not self.street or not self.street.strip():
            raise ValueError("Street cannot be empty")
        
        if not self.city or not self.city.strip():
            raise ValueError("City cannot be empty")
        
        if not self.state or not self.state.strip():
            raise ValueError("State cannot be empty")
        
        if self.postal_code and not self._is_valid_postal_code():
            raise ValueError(f"Invalid postal code format for {self.country}")
    
    def _is_valid_postal_code(self) -> bool:
        """Valida el código postal según el país"""
        if self.country.lower() == "colombia":
            # Colombia: 6 dígitos
            return bool(re.match(r'^\d{6}$', self.postal_code))
        elif self.country.lower() == "usa":
            # USA: 5 dígitos o 5+4 formato
            return bool(re.match(r'^\d{5}(-\d{4})?$', self.postal_code))
        elif self.country.lower() == "mexico":
            # México: 5 dígitos
            return bool(re.match(r'^\d{5}$', self.postal_code))
        else:
            # Formato genérico: alfanumérico, 3-10 caracteres
            return bool(re.match(r'^[A-Za-z0-9\s-]{3,10}$', self.postal_code))
    
    def get_full_address(self) -> str:
        """Retorna la dirección completa como string"""
        parts = [self.street, self.city, self.state]
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(parts)
    
    def is_international(self) -> bool:
        """Verifica si es una dirección internacional (fuera de Colombia)"""
        return self.country.lower() != "colombia"