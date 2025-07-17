from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from src.domain.entities.cash_on_delivery import CashOnDelivery, CODAttempt, CODStatus
from src.domain.entities.commission import Commission, CommissionCalculation
from src.domain.value_objects.money import Money
from src.domain.value_objects.customer_id import CustomerId
from src.domain.events.payment_events import (
    InvoiceGenerated, PaymentProcessed, PaymentFailed, 
    CommissionCalculated, CommissionPaid, CODCollected, CODFailed
)


class Invoice:
    def __init__(
        self,
        invoice_id: str,
        customer_id: CustomerId,
        amount: Money,
        due_date: datetime
    ):
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.amount = amount
        self.due_date = due_date
        self.created_at = datetime.now()
        self.paid_at: Optional[datetime] = None
        self.status = "pending"  # pending, paid, overdue, cancelled
        self.items: List[Dict[str, Any]] = []
        self.tax_amount = Money(0, amount.currency)
        self.discount_amount = Money(0, amount.currency)
        self.total_amount = amount
        self.payment_terms_days = 30

    def add_item(self, description: str, quantity: int, unit_price: Money) -> None:
        """Agregar item a la factura"""
        item = {
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": Money(unit_price.amount * quantity, unit_price.currency)
        }
        self.items.append(item)
        self._recalculate_total()

    def apply_discount(self, discount: Money) -> None:
        """Aplicar descuento a la factura"""
        if discount.amount > self.amount.amount:
            raise ValueError("El descuento no puede ser mayor al subtotal")
        
        self.discount_amount = discount
        self._recalculate_total()

    def apply_tax(self, tax_rate: float) -> None:
        """Aplicar impuesto a la factura"""
        subtotal = self.amount.amount - self.discount_amount.amount
        self.tax_amount = Money(subtotal * tax_rate, self.amount.currency)
        self._recalculate_total()

    def mark_as_paid(self, payment_date: datetime) -> None:
        """Marcar factura como pagada"""
        if self.status != "pending":
            raise ValueError("Solo se pueden marcar como pagadas facturas pendientes")
        
        self.status = "paid"
        self.paid_at = payment_date

    def is_overdue(self) -> bool:
        """Verificar si la factura está vencida"""
        return datetime.now() > self.due_date and self.status == "pending"

    def _recalculate_total(self) -> None:
        """Recalcular total de la factura"""
        subtotal = sum(item["total"].amount for item in self.items)
        self.total_amount = Money(
            subtotal - self.discount_amount.amount + self.tax_amount.amount,
            self.amount.currency
        )


class Payment:
    def __init__(
        self,
        payment_id: str,
        customer_id: CustomerId,
        amount: Money,
        payment_method: str
    ):
        self.payment_id = payment_id
        self.customer_id = customer_id
        self.amount = amount
        self.payment_method = payment_method  # credit_card, bank_transfer, cash, etc.
        self.status = "pending"  # pending, completed, failed, refunded
        self.created_at = datetime.now()
        self.processed_at: Optional[datetime] = None
        self.gateway_transaction_id: Optional[str] = None
        self.gateway_response: Optional[Dict[str, Any]] = None
        self.failure_reason: Optional[str] = None
        self.refunded_amount = Money(0, amount.currency)
        self.fees = Money(0, amount.currency)

    def mark_as_completed(
        self,
        gateway_transaction_id: str,
        gateway_response: Dict[str, Any],
        fees: Money
    ) -> None:
        """Marcar pago como completado"""
        self.status = "completed"
        self.processed_at = datetime.now()
        self.gateway_transaction_id = gateway_transaction_id
        self.gateway_response = gateway_response
        self.fees = fees

    def mark_as_failed(self, failure_reason: str, gateway_response: Dict[str, Any]) -> None:
        """Marcar pago como fallido"""
        self.status = "failed"
        self.failure_reason = failure_reason
        self.gateway_response = gateway_response

    def process_refund(self, refund_amount: Money, reason: str) -> None:
        """Procesar reembolso"""
        if self.status != "completed":
            raise ValueError("Solo se pueden reembolsar pagos completados")
        
        if refund_amount.amount > self.amount.amount:
            raise ValueError("El reembolso no puede ser mayor al pago original")
        
        self.refunded_amount = Money(
            self.refunded_amount.amount + refund_amount.amount,
            self.refunded_amount.currency
        )
        
        if self.refunded_amount.amount >= self.amount.amount:
            self.status = "refunded"


class PaymentAggregate:
    def __init__(self, customer_id: CustomerId):
        self.customer_id = customer_id
        self.invoices: List[Invoice] = []
        self.payments: List[Payment] = []
        self.cod_transactions: List[CashOnDelivery] = []
        self.commissions: List[Commission] = []
        self.credit_limit = Money(0, "COP")
        self.available_credit = Money(0, "COP")
        self.total_outstanding = Money(0, "COP")
        self._domain_events: List = []

    def generate_invoice(
        self,
        invoice_id: str,
        items: List[Dict[str, Any]],
        due_date: datetime,
        tax_rate: float = 0.19
    ) -> Invoice:
        """Generar nueva factura"""
        # Calcular total de items
        total_amount = Money(0, "COP")
        for item in items:
            item_total = Money(
                item["quantity"] * item["unit_price"].amount,
                item["unit_price"].currency
            )
            total_amount = Money(
                total_amount.amount + item_total.amount,
                total_amount.currency
            )

        invoice = Invoice(
            invoice_id=invoice_id,
            customer_id=self.customer_id,
            amount=total_amount,
            due_date=due_date
        )
        
        # Agregar items
        for item in items:
            invoice.add_item(
                description=item["description"],
                quantity=item["quantity"],
                unit_price=item["unit_price"]
            )
        
        # Aplicar impuesto
        invoice.apply_tax(tax_rate)
        
        self.invoices.append(invoice)
        self._update_outstanding_balance()
        
        self._add_domain_event(
            InvoiceGenerated(
                invoice_id=invoice_id,
                customer_id=self.customer_id.value,
                amount=invoice.total_amount.amount,
                due_date=due_date,
                items_count=len(items)
            )
        )
        
        return invoice

    def process_payment(
        self,
        payment_id: str,
        amount: Money,
        payment_method: str,
        gateway_transaction_id: str,
        gateway_response: Dict[str, Any],
        fees: Money = None
    ) -> Payment:
        """Procesar pago"""
        if fees is None:
            fees = Money(0, amount.currency)

        payment = Payment(
            payment_id=payment_id,
            customer_id=self.customer_id,
            amount=amount,
            payment_method=payment_method
        )
        
        payment.mark_as_completed(gateway_transaction_id, gateway_response, fees)
        self.payments.append(payment)
        
        # Aplicar pago a facturas pendientes (FIFO)
        self._apply_payment_to_invoices(amount)
        
        self._add_domain_event(
            PaymentProcessed(
                payment_id=payment_id,
                customer_id=self.customer_id.value,
                amount=amount.amount,
                payment_method=payment_method,
                gateway_transaction_id=gateway_transaction_id
            )
        )
        
        return payment

    def process_failed_payment(
        self,
        payment_id: str,
        amount: Money,
        payment_method: str,
        failure_reason: str,
        gateway_response: Dict[str, Any]
    ) -> Payment:
        """Procesar pago fallido"""
        payment = Payment(
            payment_id=payment_id,
            customer_id=self.customer_id,
            amount=amount,
            payment_method=payment_method
        )
        
        payment.mark_as_failed(failure_reason, gateway_response)
        self.payments.append(payment)
        
        self._add_domain_event(
            PaymentFailed(
                payment_id=payment_id,
                customer_id=self.customer_id.value,
                amount=amount.amount,
                payment_method=payment_method,
                failure_reason=failure_reason
            )
        )
        
        return payment

    def create_cod_transaction(
        self,
        cod_id: str,
        order_id: str,
        recipient_name: str,
        amount_to_collect: Money
    ) -> CashOnDelivery:
        """Crear transacción de pago contra entrega"""
        cod = CashOnDelivery(
            cod_id=cod_id,
            order_id=order_id,
            customer_id=self.customer_id.value,
            recipient_name=recipient_name,
            amount_to_collect=amount_to_collect
        )
        
        self.cod_transactions.append(cod)
        return cod

    def process_cod_collection(
        self,
        cod_id: str,
        collected_amount: Money,
        payment_method: str,
        operator_id: str,
        evidence_url: Optional[str] = None
    ) -> None:
        """Procesar cobro de pago contra entrega"""
        cod = next((c for c in self.cod_transactions if c.cod_id == cod_id), None)
        if not cod:
            raise ValueError(f"Transacción COD {cod_id} no encontrada")
        
        from src.domain.entities.cash_on_delivery import CODPaymentMethod
        payment_method_enum = CODPaymentMethod(payment_method)
        
        attempt = cod.add_collection_attempt(
            amount_attempted=cod.amount_to_collect,
            payment_method=payment_method_enum,
            collected_amount=collected_amount,
            operator_id=operator_id,
            evidence_url=evidence_url
        )
        
        if cod.status == CODStatus.COLLECTED:
            self._add_domain_event(
                CODCollected(
                    cod_id=cod_id,
                    order_id=cod.order_id,
                    customer_id=self.customer_id.value,
                    collected_amount=collected_amount.amount,
                    payment_method=payment_method,
                    operator_id=operator_id
                )
            )
        elif cod.status == CODStatus.FAILED:
            self._add_domain_event(
                CODFailed(
                    cod_id=cod_id,
                    order_id=cod.order_id,
                    customer_id=self.customer_id.value,
                    failure_reason="Máximo de intentos alcanzado",
                    attempts_made=len(cod.collection_attempts)
                )
            )

    def calculate_commission(
        self,
        commission_id: str,
        transaction_id: str,
        base_amount: Money,
        commission_rate: float,
        commission_type: str
    ) -> Commission:
        """Calcular comisión"""
        commission = Commission(
            commission_id=commission_id,
            agent_id="",  # Se asignará según el contexto
            transaction_id=transaction_id,
            base_amount=base_amount,
            commission_rate=commission_rate,
            commission_type=commission_type
        )
        
        calculation = CommissionCalculation(
            calculation_date=datetime.now(),
            base_amount=base_amount,
            rate=commission_rate,
            commission_amount=Money(base_amount.amount * commission_rate, base_amount.currency),
            taxes=Money(0, base_amount.currency),
            net_commission=Money(base_amount.amount * commission_rate, base_amount.currency)
        )
        
        commission.add_calculation(calculation)
        self.commissions.append(commission)
        
        self._add_domain_event(
            CommissionCalculated(
                commission_id=commission_id,
                transaction_id=transaction_id,
                agent_id=commission.agent_id,
                commission_amount=calculation.commission_amount.amount,
                commission_rate=commission_rate
            )
        )
        
        return commission

    def set_credit_limit(self, credit_limit: Money) -> None:
        """Establecer límite de crédito"""
        self.credit_limit = credit_limit
        self._update_available_credit()

    def get_outstanding_balance(self) -> Money:
        """Obtener saldo pendiente"""
        return self.total_outstanding

    def get_available_credit(self) -> Money:
        """Obtener crédito disponible"""
        return self.available_credit

    def has_overdue_invoices(self) -> bool:
        """Verificar si hay facturas vencidas"""
        return any(invoice.is_overdue() for invoice in self.invoices)

    def get_overdue_amount(self) -> Money:
        """Obtener monto total vencido"""
        overdue_amount = Money(0, "COP")
        for invoice in self.invoices:
            if invoice.is_overdue():
                overdue_amount = Money(
                    overdue_amount.amount + invoice.total_amount.amount,
                    overdue_amount.currency
                )
        return overdue_amount

    def get_payment_history(self, days: int = 30) -> List[Payment]:
        """Obtener historial de pagos"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [p for p in self.payments if p.created_at >= cutoff_date]

    def get_commission_summary(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Obtener resumen de comisiones por período"""
        period_commissions = [
            c for c in self.commissions 
            if period_start <= c.created_at <= period_end
        ]
        
        total_commission = Money(0, "COP")
        total_transactions = len(period_commissions)
        
        for commission in period_commissions:
            if commission.calculations:
                latest_calc = commission.calculations[-1]
                total_commission = Money(
                    total_commission.amount + latest_calc.commission_amount.amount,
                    total_commission.currency
                )
        
        return {
            "period_start": period_start,
            "period_end": period_end,
            "total_commission": total_commission,
            "total_transactions": total_transactions,
            "average_commission": Money(
                total_commission.amount / total_transactions if total_transactions > 0 else 0,
                total_commission.currency
            )
        }

    def _apply_payment_to_invoices(self, payment_amount: Money) -> None:
        """Aplicar pago a facturas pendientes (FIFO)"""
        remaining_amount = payment_amount.amount
        
        # Ordenar facturas por fecha de vencimiento (más antiguas primero)
        pending_invoices = [i for i in self.invoices if i.status == "pending"]
        pending_invoices.sort(key=lambda x: x.due_date)
        
        for invoice in pending_invoices:
            if remaining_amount <= 0:
                break
            
            if remaining_amount >= invoice.total_amount.amount:
                # Pago completo de la factura
                invoice.mark_as_paid(datetime.now())
                remaining_amount -= invoice.total_amount.amount
            else:
                # Pago parcial - por simplicidad, no manejamos pagos parciales
                # En una implementación real, se podría crear un crédito o nota
                break
        
        self._update_outstanding_balance()

    def _update_outstanding_balance(self) -> None:
        """Actualizar saldo pendiente"""
        outstanding = Money(0, "COP")
        for invoice in self.invoices:
            if invoice.status == "pending":
                outstanding = Money(
                    outstanding.amount + invoice.total_amount.amount,
                    outstanding.currency
                )
        
        self.total_outstanding = outstanding
        self._update_available_credit()

    def _update_available_credit(self) -> None:
        """Actualizar crédito disponible"""
        self.available_credit = Money(
            max(0, self.credit_limit.amount - self.total_outstanding.amount),
            self.credit_limit.currency
        )

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()