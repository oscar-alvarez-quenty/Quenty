"""Entidades de dominio para la gestión de billeteras digitales.

Este módulo contiene las entidades para manejar billeteras de clientes,
transacciones financieras, saldos, límites de crédito y historial de movimientos.
"""

from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List
from uuid import UUID, uuid4
from src.domain.value_objects.customer_id import CustomerId


@dataclass
class WalletTransaction:
    """Representa una transacción individual en la billetera.
    
    Cada transacción registra un movimiento de fondos, ya sea crédito
    (ingreso de dinero) o débito (salida de dinero), con su respectiva
    descripción y fecha.
    
    Attributes:
        id: Identificador único de la transacción
        amount: Monto de la transacción
        transaction_type: Tipo de transacción (credit/debit)
        description: Descripción del motivo de la transacción
        created_at: Fecha y hora de creación de la transacción
    """
    id: UUID = field(default_factory=uuid4)
    amount: Decimal = Decimal('0.00')
    transaction_type: str = ""  # debit, credit
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Wallet:
    """Billetera digital de un cliente para gestionar fondos.
    
    La billetera permite a los clientes mantener un saldo para pagar
    envíos, manejar límites de crédito y llevar un historial completo
    de todas las transacciones financieras.
    
    Attributes:
        id: Identificador único de la billetera
        customer_id: ID del cliente propietario de la billetera
        balance: Saldo actual de la billetera
        credit_limit: Límite de crédito disponible
        is_active: Indica si la billetera está activa
        created_at: Fecha y hora de creación
        updated_at: Fecha y hora de última actualización
        transactions: Lista de todas las transacciones realizadas
    """
    id: UUID = field(default_factory=uuid4)
    customer_id: CustomerId = None
    balance: Decimal = Decimal('0.00')
    credit_limit: Decimal = Decimal('0.00')
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    transactions: List[WalletTransaction] = field(default_factory=list)
    
    def add_funds(self, amount: Decimal, description: str = "") -> None:
        """Agrega fondos a la billetera.
        
        Registra una transacción de crédito y actualiza el saldo
        de la billetera con el monto especificado.
        
        Args:
            amount: Monto a agregar (debe ser positivo)
            description: Descripción del motivo del crédito
            
        Raises:
            ValueError: Si el monto no es positivo
            BusinessRuleException: Si la billetera está inactiva
        """
        if amount <= 0:
            raise ValueError("El monto debe ser positivo")
        
        if not self.is_active:
            raise ValueError("No se pueden agregar fondos a una billetera inactiva")
        
        transaction = WalletTransaction(
            amount=amount,
            transaction_type="credit",
            description=description
        )
        self.transactions.append(transaction)
        self.balance += amount
        self.updated_at = datetime.utcnow()
    
    def debit_funds(self, amount: Decimal, description: str = "") -> None:
        """Debita fondos de la billetera.
        
        Registra una transacción de débito y reduce el saldo de la billetera.
        Considera tanto el saldo actual como el límite de crédito disponible.
        
        Args:
            amount: Monto a debitar (debe ser positivo)
            description: Descripción del motivo del débito
            
        Raises:
            ValueError: Si el monto no es positivo o fondos insuficientes
            BusinessRuleException: Si la billetera está inactiva
        """
        if amount <= 0:
            raise ValueError("El monto debe ser positivo")
        
        if not self.is_active:
            raise ValueError("No se pueden debitar fondos de una billetera inactiva")
        
        available_balance = self.balance + self.credit_limit
        if amount > available_balance:
            raise ValueError("Fondos insuficientes")
        
        transaction = WalletTransaction(
            amount=amount,
            transaction_type="debit",
            description=description
        )
        self.transactions.append(transaction)
        self.balance -= amount
        self.updated_at = datetime.utcnow()
    
    def get_available_balance(self) -> Decimal:
        """Obtiene el saldo total disponible incluyendo crédito.
        
        Calcula la suma del saldo actual más el límite de crédito
        disponible para determinar cuánto puede gastar el cliente.
        
        Returns:
            Decimal: Saldo total disponible para transacciones
        """
        return self.balance + self.credit_limit
    
    def has_overdue_balance(self) -> bool:
        """Verifica si la billetera tiene saldo vencido.
        
        Un saldo negativo indica que el cliente está usando crédito
        y debe realizar pagos para regularizar su situación.
        
        Returns:
            bool: True si el saldo es negativo (vencido)
        """
        return self.balance < Decimal('0.00')