"""Servicios de dominio para la gestión de pagos.

Este módulo contiene la lógica de negocio para procesar pagos,
incluye integración con pasarelas de pago, billeteras digitales,
y diferentes métodos de pago disponibles.
"""

from decimal import Decimal
from typing import Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from src.domain.entities.wallet import Wallet
from src.domain.entities.microcredit import Microcredit, MicrocreditStatus
from src.domain.value_objects.customer_id import CustomerId


class PaymentMethod(Enum):
    """Métodos de pago disponibles en la plataforma.
    
    Attributes:
        CASH: Pago en efectivo (contraentrega)
        CREDIT_CARD: Tarjeta de crédito
        DEBIT_CARD: Tarjeta débito
        PSE: Pago Seguro En Línea
        WALLET: Billetera digital de la plataforma
    """
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PSE = "pse"
    WALLET = "wallet"

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

@dataclass
class PaymentResult:
    """Resultado del procesamiento de un pago.
    
    Contiene toda la información relevante sobre el
    resultado de una transacción de pago.
    
    Attributes:
        success: Indica si el pago fue exitoso
        transaction_id: ID único de la transacción
        amount: Monto procesado
        status: Estado final del pago
        message: Mensaje descriptivo del resultado
    """
    success: bool
    transaction_id: str
    amount: Decimal
    status: PaymentStatus
    message: str = ""

class PaymentService:
    """Servicio de dominio para la gestión de pagos.
    
    Coordina el procesamiento de pagos a través de diferentes
    métodos y proveedores, incluyendo validaciones de negocio.
    
    Attributes:
        payment_gateway: Gateway de pago externo (inyectado)
    """
    
    def __init__(self):
        """Inicializa el servicio de pagos.
        
        En implementación real se inyectaría la pasarela de pago.
        """
        self.payment_gateway = None  # Se inyectaría el gateway de pago
    
    async def process_payment(self, amount: Decimal, method: PaymentMethod, 
                            customer_id: CustomerId, **kwargs) -> PaymentResult:
        """Procesa un pago inmediato.
        
        Valida el monto y procesa el pago según el método seleccionado,
        ya sea a través de billetera digital o pasarela externa.
        
        Args:
            amount: Monto a procesar
            method: Método de pago seleccionado
            customer_id: ID del cliente que realiza el pago
            **kwargs: Argumentos adicionales según el método
            
        Returns:
            PaymentResult: Resultado del procesamiento
        """
        
        if amount <= 0:
            return PaymentResult(
                success=False,
                transaction_id="",
                amount=amount,
                status=PaymentStatus.FAILED,
                message="Invalid amount"
            )
        
        try:
            if method == PaymentMethod.WALLET:
                return await self._process_wallet_payment(amount, customer_id)
            else:
                return await self._process_external_payment(amount, method, **kwargs)
        
        except Exception as e:
            return PaymentResult(
                success=False,
                transaction_id="",
                amount=amount,
                status=PaymentStatus.FAILED,
                message=str(e)
            )
    
    async def _process_wallet_payment(self, amount: Decimal, customer_id: CustomerId) -> PaymentResult:
        """Procesa pago usando la billetera del cliente.
        
        Args:
            amount: Monto a debitar de la billetera
            customer_id: ID del cliente propietario de la billetera
            
        Returns:
            PaymentResult: Resultado del procesamiento
        """
        # This would interact with wallet repository
        # For now, simulate the process
        
        transaction_id = f"WAL_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            amount=amount,
            status=PaymentStatus.COMPLETED,
            message="Payment processed successfully"
        )
    
    async def _process_external_payment(self, amount: Decimal, method: PaymentMethod, 
                                      **kwargs) -> PaymentResult:
        """Procesa pago a través de pasarela externa.
        
        Integra con proveedores como Epayco, dLocal u otros
        para procesar pagos con tarjeta o PSE.
        
        Args:
            amount: Monto a procesar
            method: Método de pago externo
            **kwargs: Parámetros específicos del proveedor
            
        Returns:
            PaymentResult: Resultado del procesamiento
        """
        # This would integrate with payment providers like Epayco, dLocal
        
        transaction_id = f"EXT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate external payment processing
        success = True  # In reality, this would call the payment gateway
        
        return PaymentResult(
            success=success,
            transaction_id=transaction_id,
            amount=amount,
            status=PaymentStatus.COMPLETED if success else PaymentStatus.FAILED,
            message="Payment processed successfully" if success else "Payment failed"
        )
    
    async def process_cash_on_delivery(self, amount: Decimal, delivery_method: str = "cash") -> PaymentResult:
        """Procesa pago contraentrega.
        
        Registra un pago pendiente que será cobrado
        al momento de la entrega del paquete.
        
        Args:
            amount: Monto a cobrar en la entrega
            delivery_method: Método de cobro (efectivo por defecto)
            
        Returns:
            PaymentResult: Resultado con estado pendiente
        """
        
        transaction_id = f"COD_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            amount=amount,
            status=PaymentStatus.PENDING,
            message="Cash on delivery payment registered"
        )
    
    def calculate_credit_limit(self, customer_id: CustomerId, payment_history: list, 
                             shipment_count: int) -> Decimal:
        """Calcula el límite de crédito del cliente.
        
        Basado en historial de pagos y volumen de envíos
        para determinar la capacidad crediticia.
        
        Args:
            customer_id: ID del cliente
            payment_history: Historial de pagos del cliente
            shipment_count: Número total de envíos realizados
            
        Returns:
            Decimal: Límite de crédito calculado (máximo 2M COP)
        """
        
        base_limit = Decimal('100000')  # 100k COP base
        
        # Increase limit based on shipment volume
        volume_bonus = min(shipment_count * Decimal('5000'), Decimal('500000'))
        
        # Increase limit based on payment history
        payment_bonus = Decimal('0')
        if payment_history:
            on_time_rate = sum(1 for p in payment_history if p.get('on_time', False)) / len(payment_history)
            payment_bonus = base_limit * Decimal(str(on_time_rate))
        
        total_limit = base_limit + volume_bonus + payment_bonus
        return min(total_limit, Decimal('2000000'))  # Max 2M COP
    
    async def process_refund(self, transaction_id: str, amount: Decimal, 
                           reason: str = "") -> PaymentResult:
        """Procesa un reembolso de pago.
        
        Reintegra fondos al cliente por cancelaciones
        o problemas en el servicio.
        
        Args:
            transaction_id: ID de la transacción original
            amount: Monto a reembolsar
            reason: Motivo del reembolso
            
        Returns:
            PaymentResult: Resultado del reembolso
        """
        
        refund_id = f"REF_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # This would integrate with payment gateway for refund
        
        return PaymentResult(
            success=True,
            transaction_id=refund_id,
            amount=amount,
            status=PaymentStatus.REFUNDED,
            message=f"Refund processed for transaction {transaction_id}"
        )