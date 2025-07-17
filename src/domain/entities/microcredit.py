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