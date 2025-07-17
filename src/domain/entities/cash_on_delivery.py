from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

from src.domain.value_objects.money import Money


class CODStatus(Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class CODPaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    QR_CODE = "qr_code"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"


@dataclass
class CODAttempt:
    attempt_id: str
    attempted_at: datetime
    amount_attempted: Money
    payment_method: CODPaymentMethod
    status: str  # "success", "failed", "partial"
    collected_amount: Money
    failure_reason: Optional[str] = None
    evidence_url: Optional[str] = None  # Photo or receipt URL


class CashOnDelivery:
    def __init__(
        self,
        cod_id: str,
        order_id: str,
        customer_id: str,
        recipient_name: str,
        amount_to_collect: Money
    ):
        self.cod_id = cod_id
        self.order_id = order_id
        self.customer_id = customer_id
        self.recipient_name = recipient_name
        self.amount_to_collect = amount_to_collect
        self.status = CODStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.collected_amount = Money(0, amount_to_collect.currency)
        self.collection_attempts: list[CODAttempt] = []
        self.max_collection_attempts = 3
        self.instructions: Optional[str] = None
        self.collected_at: Optional[datetime] = None
        self.collected_by: Optional[str] = None  # Operator/messenger ID
        self.settlement_date: Optional[datetime] = None
        self.settlement_amount: Optional[Money] = None
        self.settlement_fee: Optional[Money] = None
        self.dispute_reason: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def add_collection_attempt(
        self,
        amount_attempted: Money,
        payment_method: CODPaymentMethod,
        collected_amount: Money,
        operator_id: str,
        evidence_url: Optional[str] = None
    ) -> CODAttempt:
        """Registrar intento de cobro"""
        if self.status != CODStatus.PENDING:
            raise ValueError("Solo se pueden agregar intentos a CODs pendientes")
        
        if len(self.collection_attempts) >= self.max_collection_attempts:
            raise ValueError("Se ha alcanzado el máximo de intentos de cobro")

        attempt = CODAttempt(
            attempt_id=f"att_{datetime.now().timestamp()}",
            attempted_at=datetime.now(),
            amount_attempted=amount_attempted,
            payment_method=payment_method,
            status="pending",
            collected_amount=collected_amount,
            evidence_url=evidence_url
        )

        # Determinar status del intento
        if collected_amount.amount == 0:
            attempt.status = "failed"
        elif collected_amount.amount >= amount_attempted.amount:
            attempt.status = "success"
        else:
            attempt.status = "partial"

        self.collection_attempts.append(attempt)
        self.collected_amount = Money(
            self.collected_amount.amount + collected_amount.amount,
            self.collected_amount.currency
        )

        # Actualizar status general si se completó el cobro
        if self.collected_amount.amount >= self.amount_to_collect.amount:
            self.status = CODStatus.COLLECTED
            self.collected_at = datetime.now()
            self.collected_by = operator_id
        elif len(self.collection_attempts) >= self.max_collection_attempts:
            self.status = CODStatus.FAILED

        self.updated_at = datetime.now()
        return attempt

    def mark_as_failed(self, reason: str) -> None:
        """Marcar COD como fallido"""
        if self.status != CODStatus.PENDING:
            raise ValueError("Solo se pueden marcar como fallidos CODs pendientes")
        
        self.status = CODStatus.FAILED
        self.dispute_reason = reason
        self.updated_at = datetime.now()

    def process_refund(self, refund_amount: Money, reason: str) -> None:
        """Procesar reembolso"""
        if self.status != CODStatus.COLLECTED:
            raise ValueError("Solo se pueden reembolsar CODs cobrados")
        
        if refund_amount.amount > self.collected_amount.amount:
            raise ValueError("El monto a reembolsar no puede ser mayor al cobrado")
        
        self.status = CODStatus.REFUNDED
        self.dispute_reason = reason
        self.updated_at = datetime.now()

    def initiate_dispute(self, reason: str) -> None:
        """Iniciar disputa"""
        if self.status not in [CODStatus.COLLECTED, CODStatus.FAILED]:
            raise ValueError("Solo se pueden disputar CODs cobrados o fallidos")
        
        self.status = CODStatus.DISPUTED
        self.dispute_reason = reason
        self.updated_at = datetime.now()

    def calculate_settlement(self, commission_rate: float = 0.03) -> Money:
        """Calcular monto de liquidación al cliente"""
        if self.status != CODStatus.COLLECTED:
            raise ValueError("Solo se puede calcular liquidación para CODs cobrados")
        
        commission = Money(
            self.collected_amount.amount * commission_rate,
            self.collected_amount.currency
        )
        
        settlement_amount = Money(
            self.collected_amount.amount - commission.amount,
            self.collected_amount.currency
        )
        
        self.settlement_fee = commission
        self.settlement_amount = settlement_amount
        
        return settlement_amount

    def process_settlement(self) -> None:
        """Procesar liquidación al cliente"""
        if not self.settlement_amount:
            raise ValueError("Debe calcular liquidación antes de procesarla")
        
        self.settlement_date = datetime.now()
        self.updated_at = datetime.now()

    def get_collection_rate(self) -> float:
        """Obtener tasa de cobro exitoso"""
        if not self.collection_attempts:
            return 0.0
        
        successful_attempts = len([a for a in self.collection_attempts if a.status == "success"])
        return successful_attempts / len(self.collection_attempts)

    def get_remaining_amount(self) -> Money:
        """Obtener monto restante por cobrar"""
        return Money(
            self.amount_to_collect.amount - self.collected_amount.amount,
            self.amount_to_collect.currency
        )

    def can_retry_collection(self) -> bool:
        """Verificar si se puede reintentar el cobro"""
        return (self.status == CODStatus.PENDING and 
                len(self.collection_attempts) < self.max_collection_attempts and
                self.get_remaining_amount().amount > 0)

    def set_instructions(self, instructions: str) -> None:
        """Establecer instrucciones especiales para el cobro"""
        self.instructions = instructions
        self.updated_at = datetime.now()

    def add_metadata(self, key: str, value: Any) -> None:
        """Agregar metadata adicional"""
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def get_collection_summary(self) -> Dict[str, Any]:
        """Obtener resumen del proceso de cobro"""
        return {
            "cod_id": self.cod_id,
            "order_id": self.order_id,
            "status": self.status.value,
            "amount_to_collect": {
                "amount": self.amount_to_collect.amount,
                "currency": self.amount_to_collect.currency
            },
            "collected_amount": {
                "amount": self.collected_amount.amount,
                "currency": self.collected_amount.currency
            },
            "remaining_amount": {
                "amount": self.get_remaining_amount().amount,
                "currency": self.get_remaining_amount().currency
            },
            "attempts_count": len(self.collection_attempts),
            "max_attempts": self.max_collection_attempts,
            "collection_rate": self.get_collection_rate(),
            "collected_at": self.collected_at,
            "settlement_amount": {
                "amount": self.settlement_amount.amount if self.settlement_amount else 0,
                "currency": self.settlement_amount.currency if self.settlement_amount else self.amount_to_collect.currency
            },
            "settlement_date": self.settlement_date
        }

    def __str__(self) -> str:
        return f"CashOnDelivery({self.cod_id}, {self.amount_to_collect}, {self.status.value})"