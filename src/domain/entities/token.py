from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
from uuid import UUID, uuid4

class TokenType(Enum):
    CITY = "city"
    FRANCHISE = "franchise"
    PERFORMANCE = "performance"
    LOYALTY = "loyalty"

class TokenStatus(Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    BURNED = "burned"
    SUSPENDED = "suspended"

class DistributionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class CityToken:
    id: UUID = field(default_factory=uuid4)
    city_code: str = ""
    city_name: str = ""
    total_supply: Decimal = Decimal('1000000')  # 1M tokens per city
    circulating_supply: Decimal = Decimal('0')
    token_price: Decimal = Decimal('1000')  # Price in COP
    franchise_allocation: Decimal = Decimal('0.60')  # 60% for franchises
    utility_allocation: Decimal = Decimal('0.30')   # 30% for utilities distribution
    reserve_allocation: Decimal = Decimal('0.10')   # 10% reserve
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_distribution: Optional[datetime] = None
    
    def mint_tokens(self, amount: Decimal) -> None:
        """Acuña nuevos tokens"""
        if self.circulating_supply + amount > self.total_supply:
            raise ValueError("Cannot mint more tokens than total supply")
        
        self.circulating_supply += amount
    
    def burn_tokens(self, amount: Decimal) -> None:
        """Quema tokens del suministro circulante"""
        if amount > self.circulating_supply:
            raise ValueError("Cannot burn more tokens than circulating supply")
        
        self.circulating_supply -= amount
    
    def get_available_for_distribution(self) -> Decimal:
        """Obtiene la cantidad disponible para distribución"""
        return self.total_supply - self.circulating_supply
    
    def calculate_franchise_tokens(self) -> Decimal:
        """Calcula tokens asignados a franquicias"""
        return self.total_supply * self.franchise_allocation
    
    def calculate_utility_tokens(self) -> Decimal:
        """Calcula tokens para distribución de utilidades"""
        return self.total_supply * self.utility_allocation

@dataclass
class TokenHolder:
    id: UUID = field(default_factory=uuid4)
    holder_id: UUID = None  # Customer, Franchise, etc.
    holder_type: str = ""   # customer, franchise, employee
    city_token_id: UUID = None
    token_balance: Decimal = Decimal('0')
    locked_balance: Decimal = Decimal('0')
    total_earned: Decimal = Decimal('0')
    total_spent: Decimal = Decimal('0')
    status: TokenStatus = TokenStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_transaction: Optional[datetime] = None
    
    def get_available_balance(self) -> Decimal:
        """Obtiene el balance disponible (no bloqueado)"""
        return self.token_balance - self.locked_balance
    
    def lock_tokens(self, amount: Decimal, reason: str = "") -> None:
        """Bloquea una cantidad de tokens"""
        if amount > self.get_available_balance():
            raise ValueError("Insufficient available tokens to lock")
        
        self.locked_balance += amount
    
    def unlock_tokens(self, amount: Decimal) -> None:
        """Desbloquea tokens"""
        if amount > self.locked_balance:
            raise ValueError("Cannot unlock more tokens than locked")
        
        self.locked_balance -= amount
    
    def add_tokens(self, amount: Decimal, reason: str = "") -> None:
        """Agrega tokens al balance"""
        self.token_balance += amount
        self.total_earned += amount
        self.last_transaction = datetime.utcnow()
    
    def spend_tokens(self, amount: Decimal, reason: str = "") -> None:
        """Gasta tokens del balance disponible"""
        if amount > self.get_available_balance():
            raise ValueError("Insufficient available tokens")
        
        self.token_balance -= amount
        self.total_spent += amount
        self.last_transaction = datetime.utcnow()

@dataclass
class TokenTransaction:
    id: UUID = field(default_factory=uuid4)
    from_holder_id: Optional[UUID] = None
    to_holder_id: UUID = None
    city_token_id: UUID = None
    transaction_type: str = ""  # mint, transfer, burn, reward, utility_distribution
    amount: Decimal = Decimal('0')
    reference_id: Optional[UUID] = None  # Order, Commission, etc.
    description: str = ""
    transaction_hash: str = ""  # Blockchain hash if applicable
    status: str = "completed"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def generate_hash(self) -> str:
        """Genera un hash único para la transacción"""
        import hashlib
        data = f"{self.id}_{self.from_holder_id}_{self.to_holder_id}_{self.amount}_{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

@dataclass
class UtilityDistribution:
    id: UUID = field(default_factory=uuid4)
    city_token_id: UUID = None
    period: str = ""  # YYYY-MM
    total_utility_amount: Decimal = Decimal('0')  # In COP
    total_tokens_distributed: Decimal = Decimal('0')
    distribution_rate: Decimal = Decimal('0')  # COP per token
    eligible_holders: List[UUID] = field(default_factory=list)
    distributions: Dict[UUID, Decimal] = field(default_factory=dict)  # holder_id -> amount
    status: DistributionStatus = DistributionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def calculate_distribution_rate(self, total_participating_tokens: Decimal) -> None:
        """Calcula la tasa de distribución por token"""
        if total_participating_tokens <= 0:
            raise ValueError("Total participating tokens must be positive")
        
        self.distribution_rate = self.total_utility_amount / total_participating_tokens
    
    def add_holder_distribution(self, holder_id: UUID, token_amount: Decimal) -> None:
        """Agrega la distribución para un holder específico"""
        utility_amount = token_amount * self.distribution_rate
        self.distributions[holder_id] = utility_amount
        self.total_tokens_distributed += token_amount
    
    def process_distribution(self) -> None:
        """Procesa la distribución"""
        if self.status != DistributionStatus.PENDING:
            raise ValueError("Only pending distributions can be processed")
        
        self.status = DistributionStatus.PROCESSING
        self.processed_at = datetime.utcnow()
    
    def complete_distribution(self) -> None:
        """Completa la distribución"""
        if self.status != DistributionStatus.PROCESSING:
            raise ValueError("Only processing distributions can be completed")
        
        self.status = DistributionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def fail_distribution(self, reason: str = "") -> None:
        """Marca la distribución como fallida"""
        if self.status != DistributionStatus.PROCESSING:
            raise ValueError("Only processing distributions can be marked as failed")
        
        self.status = DistributionStatus.FAILED

@dataclass
class SmartContract:
    id: UUID = field(default_factory=uuid4)
    contract_address: str = ""
    contract_type: str = ""  # city_token, utility_distribution, governance
    city_token_id: Optional[UUID] = None
    abi: str = ""  # Contract ABI as JSON string
    bytecode: str = ""
    deployment_transaction: str = ""
    deployed_at: Optional[datetime] = None
    is_active: bool = False
    gas_limit: int = 500000
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def deploy(self, deployment_transaction: str) -> None:
        """Marca el contrato como desplegado"""
        self.deployment_transaction = deployment_transaction
        self.deployed_at = datetime.utcnow()
        self.is_active = True
    
    def deactivate(self, reason: str = "") -> None:
        """Desactiva el contrato"""
        self.is_active = False