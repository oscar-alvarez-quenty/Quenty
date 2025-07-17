import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Phone:
    number: str
    country_code: str = "+57"  # Colombia por defecto
    
    def __post_init__(self):
        # Limpiar el número (remover espacios, guiones, paréntesis)
        clean_number = re.sub(r'[\s\-\(\)]', '', self.number)
        object.__setattr__(self, 'number', clean_number)
        
        if not self._is_valid_phone():
            raise ValueError(f"Invalid phone number format: {self.number}")
    
    def _is_valid_phone(self) -> bool:
        """Valida el formato del teléfono según el código de país"""
        if self.country_code == "+57":  # Colombia
            # Móvil: 10 dígitos empezando con 3
            # Fijo: 7-10 dígitos
            return bool(re.match(r'^3\d{9}$', self.number)) or bool(re.match(r'^\d{7,10}$', self.number))
        elif self.country_code == "+1":  # USA/Canada
            # 10 dígitos
            return bool(re.match(r'^\d{10}$', self.number))
        elif self.country_code == "+52":  # México
            # 10 dígitos
            return bool(re.match(r'^\d{10}$', self.number))
        else:
            # Formato genérico: 7-15 dígitos
            return bool(re.match(r'^\d{7,15}$', self.number))
    
    def get_full_number(self) -> str:
        """Retorna el número completo con código de país"""
        return f"{self.country_code}{self.number}"
    
    def get_formatted_number(self) -> str:
        """Retorna el número formateado según el país"""
        if self.country_code == "+57":  # Colombia
            if len(self.number) == 10:  # Móvil
                return f"{self.number[:3]} {self.number[3:6]} {self.number[6:]}"
            elif len(self.number) == 7:  # Fijo Bogotá
                return f"{self.number[:3]} {self.number[3:]}"
        elif self.country_code == "+1":  # USA
            if len(self.number) == 10:
                return f"({self.number[:3]}) {self.number[3:6]}-{self.number[6:]}"
        
        # Formato por defecto
        return self.number
    
    def is_mobile(self) -> bool:
        """Verifica si es un número móvil"""
        if self.country_code == "+57":  # Colombia
            return self.number.startswith('3') and len(self.number) == 10
        elif self.country_code == "+1":  # USA/Canada
            # En USA/Canada todos los números de 10 dígitos pueden ser móviles
            return len(self.number) == 10
        
        return False
    
    def is_landline(self) -> bool:
        """Verifica si es un número fijo"""
        return not self.is_mobile()
    
    def get_country_name(self) -> str:
        """Obtiene el nombre del país"""
        country_map = {
            "+57": "Colombia",
            "+1": "United States",
            "+52": "Mexico",
            "+34": "Spain",
            "+33": "France",
            "+44": "United Kingdom"
        }
        return country_map.get(self.country_code, "Unknown")
    
    def __str__(self) -> str:
        return self.get_full_number()