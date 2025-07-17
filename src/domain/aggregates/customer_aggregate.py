from typing import List, Optional
from dataclasses import dataclass, field
from src.domain.entities.customer import Customer
from src.domain.entities.wallet import Wallet, WalletTransaction
from src.domain.entities.microcredit import Microcredit
from src.domain.events.customer_events import (
    CustomerCreated, CustomerUpdated, CustomerKYCValidated, 
    WalletCredited, WalletDebited, MicrocreditRequested
)
from src.domain.events.base_event import DomainEvent
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.email import Email
from decimal import Decimal

@dataclass
class CustomerAggregate:
    """
    Agregado del Cliente que encapsula todas las entidades y reglas de negocio
    relacionadas con un cliente específico
    """
    customer: Customer
    wallet: Optional[Wallet] = None
    microcredits: List[Microcredit] = field(default_factory=list)
    _domain_events: List[DomainEvent] = field(default_factory=list)
    
    @classmethod
    def create_new_customer(cls, email: str, business_name: str, tax_id: str, 
                          phone: str, address: str) -> "CustomerAggregate":
        """Factory method para crear un nuevo cliente"""
        
        # Crear el cliente
        customer = Customer(
            email=Email(email),
            business_name=business_name,
            tax_id=tax_id,
            phone=phone,
            address=address
        )
        
        # Crear wallet automáticamente
        wallet = Wallet(customer_id=customer.id)
        
        # Crear el agregado
        aggregate = cls(customer=customer, wallet=wallet)
        
        # Registrar evento de dominio
        event = CustomerCreated(
            aggregate_id=customer.id.value,
            aggregate_type="customer",
            customer_id=str(customer.id.value),
            email=email,
            customer_type=customer.customer_type,
            business_name=business_name
        )
        aggregate._add_domain_event(event)
        
        return aggregate
    
    def update_profile(self, **kwargs) -> None:
        """Actualiza el perfil del cliente"""
        updated_fields = {}
        
        for field, value in kwargs.items():
            if hasattr(self.customer, field) and getattr(self.customer, field) != value:
                setattr(self.customer, field, value)
                updated_fields[field] = value
        
        if updated_fields:
            event = CustomerUpdated(
                aggregate_id=self.customer.id.value,
                aggregate_type="customer",
                customer_id=str(self.customer.id.value),
                updated_fields=updated_fields
            )
            self._add_domain_event(event)
    
    def validate_kyc(self, validation_method: str = "manual", validated_by: str = "system") -> None:
        """Valida el KYC del cliente"""
        if self.customer.kyc_validated:
            raise ValueError("Customer KYC is already validated")
        
        self.customer.validate_kyc()
        
        event = CustomerKYCValidated(
            aggregate_id=self.customer.id.value,
            aggregate_type="customer",
            customer_id=str(self.customer.id.value),
            validation_method=validation_method,
            validated_by=validated_by
        )
        self._add_domain_event(event)
    
    def add_funds_to_wallet(self, amount: Decimal, description: str = "") -> None:
        """Agrega fondos al wallet del cliente"""
        if not self.wallet:
            raise ValueError("Customer wallet not found")
        
        self.wallet.add_funds(amount, description)
        
        event = WalletCredited(
            aggregate_id=self.customer.id.value,
            aggregate_type="customer",
            wallet_id=str(self.wallet.id),
            customer_id=str(self.customer.id.value),
            amount=str(amount),
            transaction_type="credit",
            description=description
        )
        self._add_domain_event(event)
    
    def debit_from_wallet(self, amount: Decimal, description: str = "") -> None:
        """Debita fondos del wallet del cliente"""
        if not self.wallet:
            raise ValueError("Customer wallet not found")
        
        self.wallet.debit_funds(amount, description)
        
        event = WalletDebited(
            aggregate_id=self.customer.id.value,
            aggregate_type="customer",
            wallet_id=str(self.wallet.id),
            customer_id=str(self.customer.id.value),
            amount=str(amount),
            transaction_type="debit",
            description=description
        )
        self._add_domain_event(event)
    
    def request_microcredit(self, requested_amount: Decimal, payment_history: list = None, 
                          shipment_count: int = 0) -> Microcredit:
        """Solicita un microcrédito"""
        microcredit = Microcredit(
            customer_id=self.customer.id,
            requested_amount=requested_amount
        )
        
        # Calcular credit score
        microcredit.calculate_credit_score(payment_history or [], shipment_count)
        
        self.microcredits.append(microcredit)
        
        event = MicrocreditRequested(
            aggregate_id=self.customer.id.value,
            aggregate_type="customer",
            microcredit_id=str(microcredit.id),
            customer_id=str(self.customer.id.value),
            requested_amount=str(requested_amount),
            credit_score=microcredit.credit_score
        )
        self._add_domain_event(event)
        
        return microcredit
    
    def can_create_international_shipment(self) -> bool:
        """Verifica si puede crear envíos internacionales"""
        return self.customer.can_create_international_shipment()
    
    def can_use_credit(self) -> bool:
        """Verifica si puede usar crédito"""
        return self.customer.can_use_credit()
    
    def get_available_credit(self) -> Decimal:
        """Obtiene el crédito disponible"""
        if not self.wallet:
            return Decimal('0.00')
        return self.wallet.get_available_balance()
    
    def has_overdue_balance(self) -> bool:
        """Verifica si tiene saldo vencido"""
        if not self.wallet:
            return False
        return self.wallet.has_overdue_balance()
    
    def get_active_microcredits(self) -> List[Microcredit]:
        """Obtiene microcréditos activos"""
        return [mc for mc in self.microcredits if mc.status.value in ['active', 'overdue']]
    
    def get_total_debt(self) -> Decimal:
        """Calcula la deuda total incluyendo microcréditos"""
        wallet_debt = abs(min(self.wallet.balance, Decimal('0.00'))) if self.wallet else Decimal('0.00')
        microcredit_debt = sum(mc.outstanding_balance for mc in self.get_active_microcredits())
        return wallet_debt + microcredit_debt
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Agrega un evento de dominio"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Obtiene los eventos de dominio"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Limpia los eventos de dominio"""
        self._domain_events.clear()