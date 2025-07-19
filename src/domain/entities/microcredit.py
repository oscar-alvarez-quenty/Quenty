"""Entidades de dominio para la gestión de microcréditos.

Este módulo contiene las entidades para manejar préstamos de microcrédito
para clientes, incluyendo aprobación, desembolso, pagos y scoring crediticio.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class ApplicationStatus(Enum):
    """Estados de una solicitud de microcrédito.
    
    Attributes:
        SUBMITTED: Solicitud enviada
        UNDER_REVIEW: Solicitud en revisión
        APPROVED: Solicitud aprobada
        REJECTED: Solicitud rechazada
    """
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class MicrocreditStatus(Enum):
    """Estados posibles de un microcrédito.
    
    Attributes:
        PENDING: Solicitud pendiente de evaluación
        APPROVED: Solicitud aprobada pendiente de desembolso
        REJECTED: Solicitud rechazada
        ACTIVE: Crédito activo con saldo pendiente
        PAID: Crédito pagado en su totalidad
        OVERDUE: Crédito vencido sin pagar
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentStatus(Enum):
    """Estados de procesamiento de pagos.
    
    Attributes:
        PENDING: Pago pendiente de procesamiento
        PROCESSING: Pago en proceso
        COMPLETED: Pago completado exitosamente
        FAILED: Pago fallido
        REFUNDED: Pago reembolsado
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class RefundMethod(Enum):
    """Métodos de reembolso disponibles.
    
    Attributes:
        ORIGINAL_METHOD: Mismo método de pago original
        WALLET: Billetera digital de la plataforma
        BANK_TRANSFER: Transferencia bancaria
    """
    ORIGINAL_METHOD = "original_method"
    WALLET = "wallet"
    BANK_TRANSFER = "bank_transfer"

@dataclass
class Microcredit:
    """Microcrédito para financiar envíos de clientes.
    
    Permite a clientes acceder a financiamiento de corto plazo
    para cubrir costos de envío, con evaluación de crédito
    basada en historial de pagos y volumen de envíos.
    
    Attributes:
        id: Identificador único del microcrédito
        customer_id: ID del cliente solicitante
        requested_amount: Monto solicitado por el cliente
        approved_amount: Monto aprobado tras evaluación
        interest_rate: Tasa de interés aplicada (por defecto 5%)
        term_days: Plazo en días para el pago (por defecto 30)
        status: Estado actual del microcrédito
        credit_score: Puntaje crediticio del cliente
        application_date: Fecha de solicitud
        approval_date: Fecha de aprobación o rechazo
        disbursement_date: Fecha de desembolso
        due_date: Fecha de vencimiento
        paid_date: Fecha de pago completo
        outstanding_balance: Saldo pendiente por pagar
    """
    id: UUID = field(default_factory=uuid4)
    customer_id: CustomerId = None
    requested_amount: Decimal = Decimal('0.00')
    approved_amount: Decimal = Decimal('0.00')
    interest_rate: Decimal = Decimal('0.05')  # 5% default
    term_days: int = 30
    status: MicrocreditStatus = MicrocreditStatus.PENDING
    credit_score: int = 0
    application_date: datetime = field(default_factory=datetime.utcnow)
    approval_date: Optional[datetime] = None
    disbursement_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    outstanding_balance: Decimal = Decimal('0.00')
    
    def approve(self, approved_amount: Decimal) -> None:
        """Aprueba una solicitud de microcrédito.
        
        Establece el monto aprobado (puede ser menor al solicitado)
        y cambia el estado a APPROVED para permitir el desembolso.
        
        Args:
            approved_amount: Monto aprobado para el microcrédito
            
        Raises:
            ValueError: Si no está en estado pendiente o monto inválido
        """
        if self.status != MicrocreditStatus.PENDING:
            raise ValueError("Solo se pueden aprobar microcréditos pendientes")
        
        if approved_amount <= 0:
            raise ValueError("El monto aprobado debe ser positivo")
        
        if approved_amount > self.requested_amount:
            raise ValueError("El monto aprobado no puede exceder el solicitado")
        
        self.approved_amount = approved_amount
        self.status = MicrocreditStatus.APPROVED
        self.approval_date = datetime.utcnow()
    
    def reject(self) -> None:
        """Rechaza una solicitud de microcrédito.
        
        Marca la solicitud como rechazada, impidiendo
        cualquier procesamiento posterior.
        
        Raises:
            ValueError: Si no está en estado pendiente
        """
        if self.status != MicrocreditStatus.PENDING:
            raise ValueError("Solo se pueden rechazar microcréditos pendientes")
        
        self.status = MicrocreditStatus.REJECTED
        self.approval_date = datetime.utcnow()
    
    def disburse(self) -> None:
        """Desembolsa el microcrédito aprobado.
        
        Activa el crédito, calcula el saldo total con intereses
        y establece la fecha de vencimiento según el plazo.
        
        Raises:
            ValueError: Si no está aprobado
        """
        if self.status != MicrocreditStatus.APPROVED:
            raise ValueError("Solo se pueden desembolsar microcréditos aprobados")
        
        self.status = MicrocreditStatus.ACTIVE
        self.disbursement_date = datetime.utcnow()
        self.due_date = self.disbursement_date + timedelta(days=self.term_days)
        
        # Calcular monto total con intereses
        interest_amount = self.approved_amount * self.interest_rate
        self.outstanding_balance = self.approved_amount + interest_amount
    
    def make_payment(self, amount: Decimal) -> None:
        """Registra un pago al microcrédito.
        
        Reduce el saldo pendiente y marca como pagado
        si se cancela completamente la deuda.
        
        Args:
            amount: Monto del pago a realizar
            
        Raises:
            ValueError: Si el microcrédito no está activo o monto inválido
        """
        if self.status not in [MicrocreditStatus.ACTIVE, MicrocreditStatus.OVERDUE]:
            raise ValueError("No se puede pagar un microcrédito inactivo")
        
        if amount <= 0:
            raise ValueError("El monto del pago debe ser positivo")
        
        # Ajustar pago si excede el saldo pendiente
        if amount > self.outstanding_balance:
            amount = self.outstanding_balance
        
        self.outstanding_balance -= amount
        
        # Marcar como pagado si se cancela completamente
        if self.outstanding_balance == 0:
            self.status = MicrocreditStatus.PAID
            self.paid_date = datetime.utcnow()
    
    def check_overdue(self) -> None:
        """Verifica y actualiza el estado si el crédito está vencido.
        
        Debe ejecutarse periódicamente para mantener actualizados
        los estados de microcréditos que han pasado su fecha de vencimiento.
        """
        if (self.status == MicrocreditStatus.ACTIVE and 
            self.due_date and 
            datetime.utcnow() > self.due_date):
            self.status = MicrocreditStatus.OVERDUE
    
    def calculate_credit_score(self, payment_history: list, shipment_count: int) -> int:
        """Calcula el puntaje crediticio del cliente.
        
        Algoritmo basado en historial de pagos y volumen de envíos
        para determinar la capacidad crediticia del cliente.
        
        Args:
            payment_history: Lista de pagos previos del cliente
            shipment_count: Número total de envíos realizados
            
        Returns:
            int: Puntaje crediticio entre 300 y 850
        """
        # Algoritmo simple de scoring basado en historial y volumen
        base_score = 300
        
        # Agregar puntos por volumen de envíos (máx 200 puntos)
        volume_score = min(shipment_count * 2, 200)
        
        # Agregar puntos por buen historial de pagos (máx 300 puntos)
        payment_score = 0
        if payment_history:
            on_time_payments = sum(1 for p in payment_history if p.get('on_time', False))
            payment_score = min((on_time_payments / len(payment_history)) * 300, 300)
        
        total_score = base_score + volume_score + payment_score
        self.credit_score = min(int(total_score), 850)
        return self.credit_score


@dataclass
class MicrocreditApplication:
    """Solicitud de microcrédito.
    
    Representa una solicitud de microcrédito con toda la información
    necesaria para su evaluación y procesamiento.
    
    Attributes:
        id: Identificador único de la aplicación
        customer_id: ID del cliente solicitante
        requested_amount: Monto solicitado
        purpose: Propósito del crédito
        status: Estado de la aplicación
        monthly_income: Ingreso mensual del solicitante
        employment_type: Tipo de empleo
        business_description: Descripción del negocio
        submitted_at: Fecha de envío
        reviewed_at: Fecha de revisión
        decision_date: Fecha de decisión
        decision_reason: Razón de la decisión
        credit_score: Puntaje crediticio calculado
        risk_level: Nivel de riesgo evaluado
    """
    id: UUID = field(default_factory=uuid4)
    customer_id: CustomerId = None
    requested_amount: Money = field(default_factory=lambda: Money(Decimal('0'), 'COP'))
    purpose: str = ""
    status: ApplicationStatus = ApplicationStatus.SUBMITTED
    monthly_income: Optional[Money] = None
    employment_type: str = "self_employed"
    business_description: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    decision_reason: Optional[str] = None
    credit_score: Optional[int] = None
    risk_level: Optional[str] = None
    
    def start_review(self) -> None:
        """Inicia el proceso de revisión de la aplicación."""
        if self.status != ApplicationStatus.SUBMITTED:
            raise ValueError("Solo se pueden revisar aplicaciones enviadas")
        self.status = ApplicationStatus.UNDER_REVIEW
        self.reviewed_at = datetime.utcnow()
    
    def approve(self, reason: str = "") -> None:
        """Aprueba la aplicación."""
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError("Solo se pueden aprobar aplicaciones en revisión")
        self.status = ApplicationStatus.APPROVED
        self.decision_date = datetime.utcnow()
        self.decision_reason = reason
    
    def reject(self, reason: str) -> None:
        """Rechaza la aplicación."""
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError("Solo se pueden rechazar aplicaciones en revisión")
        self.status = ApplicationStatus.REJECTED
        self.decision_date = datetime.utcnow()
        self.decision_reason = reason


@dataclass
class CreditProfile:
    """Perfil crediticio del cliente.
    
    Contiene información histórica y actual sobre el comportamiento
    crediticio del cliente para evaluar su capacidad de pago.
    
    Attributes:
        customer_id: ID del cliente
        credit_limit: Límite de crédito actual
        current_debt: Deuda actual
        payment_history: Historial de pagos
        first_credit_date: Fecha del primer crédito
        total_credits_taken: Total de créditos tomados
        on_time_payment_rate: Tasa de pagos a tiempo
        average_payment_delay_days: Promedio de días de retraso
        last_updated: Última actualización del perfil
    """
    customer_id: CustomerId = None
    credit_limit: Money = field(default_factory=lambda: Money(Decimal('0'), 'COP'))
    current_debt: Money = field(default_factory=lambda: Money(Decimal('0'), 'COP'))
    payment_history: list = field(default_factory=list)
    first_credit_date: Optional[datetime] = None
    total_credits_taken: int = 0
    on_time_payment_rate: float = 0.0
    average_payment_delay_days: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def recent_applications_count(self, since_date: datetime) -> int:
        """Cuenta las aplicaciones recientes desde una fecha."""
        recent_apps = [
            h for h in self.payment_history 
            if h.get('application_date') and h['application_date'] >= since_date
        ]
        return len(recent_apps)
    
    def update_payment_metrics(self) -> None:
        """Actualiza las métricas de pago basado en el historial."""
        if not self.payment_history:
            return
        
        on_time_count = sum(1 for p in self.payment_history if p.get('on_time', False))
        self.on_time_payment_rate = on_time_count / len(self.payment_history)
        
        total_delay_days = sum(p.get('delay_days', 0) for p in self.payment_history)
        delayed_payments = sum(1 for p in self.payment_history if p.get('delay_days', 0) > 0)
        
        if delayed_payments > 0:
            self.average_payment_delay_days = total_delay_days / delayed_payments
        else:
            self.average_payment_delay_days = 0.0
        
        self.last_updated = datetime.utcnow()


@dataclass
class MicrocreditPayment:
    """Pago de microcrédito.
    
    Representa un pago realizado para un microcrédito,
    incluyendo información sobre el método y estado.
    
    Attributes:
        id: Identificador único del pago
        microcredit_id: ID del microcrédito
        amount: Monto del pago
        payment_date: Fecha del pago
        due_date: Fecha de vencimiento
        status: Estado del pago
        payment_method: Método de pago utilizado
        transaction_id: ID de transacción externa
        late_fee: Cargo por pago tardío
        days_overdue: Días de retraso
    """
    id: UUID = field(default_factory=uuid4)
    microcredit_id: UUID = None
    amount: Money = field(default_factory=lambda: Money(Decimal('0'), 'COP'))
    payment_date: Optional[datetime] = None
    due_date: datetime = field(default_factory=datetime.utcnow)
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    late_fee: Money = field(default_factory=lambda: Money(Decimal('0'), 'COP'))
    days_overdue: int = 0
    
    def process_payment(self, transaction_id: str, method: str) -> None:
        """Procesa el pago."""
        self.status = PaymentStatus.COMPLETED
        self.payment_date = datetime.utcnow()
        self.transaction_id = transaction_id
        self.payment_method = method
        
        if self.payment_date > self.due_date:
            self.days_overdue = (self.payment_date - self.due_date).days
            self.late_fee = self._calculate_late_fee()
    
    def _calculate_late_fee(self) -> Money:
        """Calcula el cargo por pago tardío."""
        base_fee = Decimal('10000')  # 10k COP base
        daily_fee = Decimal('1000')  # 1k COP por día
        total_fee = base_fee + (daily_fee * self.days_overdue)
        return Money(total_fee, self.amount.currency)
    
    def fail_payment(self, reason: str) -> None:
        """Marca el pago como fallido."""
        self.status = PaymentStatus.FAILED


@dataclass
class PaymentSchedule:
    """Cronograma de pagos de microcrédito.
    
    Define el plan de pagos para un microcrédito,
    incluyendo fechas y montos de cada cuota.
    
    Attributes:
        microcredit_id: ID del microcrédito
        total_amount: Monto total a pagar
        installments: Lista de cuotas programadas
        created_at: Fecha de creación del cronograma
    """
    microcredit_id: UUID = None
    total_amount: Money = field(default_factory=lambda: Money(Decimal('0'), 'COP'))
    installments: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def generate_installments(self, principal: Money, interest_rate: Decimal, 
                            term_months: int) -> None:
        """Genera las cuotas del cronograma de pagos.
        
        Args:
            principal: Monto principal del préstamo
            interest_rate: Tasa de interés mensual
            term_months: Plazo en meses
        """
        self.installments = []
        
        # Cálculo de cuota fija mensual
        if interest_rate > 0:
            monthly_rate = interest_rate / 12
            monthly_payment = principal.amount * (
                (monthly_rate * (1 + monthly_rate) ** term_months) /
                ((1 + monthly_rate) ** term_months - 1)
            )
        else:
            monthly_payment = principal.amount / term_months
        
        remaining_balance = principal.amount
        
        for i in range(term_months):
            due_date = datetime.utcnow() + timedelta(days=30 * (i + 1))
            
            interest_payment = remaining_balance * (interest_rate / 12)
            principal_payment = monthly_payment - interest_payment
            remaining_balance -= principal_payment
            
            installment = {
                'number': i + 1,
                'due_date': due_date,
                'amount': Money(monthly_payment, principal.currency),
                'principal': Money(principal_payment, principal.currency),
                'interest': Money(interest_payment, principal.currency),
                'balance': Money(max(remaining_balance, Decimal('0')), principal.currency)
            }
            
            self.installments.append(installment)
        
        self.total_amount = Money(
            monthly_payment * term_months,
            principal.currency
        )
    
    def get_next_installment(self) -> Optional[dict]:
        """Obtiene la próxima cuota por pagar."""
        now = datetime.utcnow()
        for installment in self.installments:
            if installment['due_date'] > now and not installment.get('paid', False):
                return installment
        return None
    
    def mark_installment_paid(self, installment_number: int) -> None:
        """Marca una cuota como pagada."""
        for installment in self.installments:
            if installment['number'] == installment_number:
                installment['paid'] = True
                installment['paid_date'] = datetime.utcnow()
                break