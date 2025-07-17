from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class PackageDimensions:
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    weight_kg: Decimal
    
    def __post_init__(self):
        if any(dim <= 0 for dim in [self.length_cm, self.width_cm, self.height_cm, self.weight_kg]):
            raise ValueError("All dimensions must be positive")
    
    def calculate_volumetric_weight(self) -> Decimal:
        # Volumetric weight formula: L x W x H / 5000
        volume = self.length_cm * self.width_cm * self.height_cm
        return volume / Decimal('5000')
    
    def get_billable_weight(self) -> Decimal:
        # Use the higher of actual weight or volumetric weight
        return max(self.weight_kg, self.calculate_volumetric_weight())