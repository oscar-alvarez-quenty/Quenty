from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timedelta

from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class ReturnReason(Enum):
    DEFECTIVE_PRODUCT = "defective_product"
    WRONG_ITEM = "wrong_item"
    DAMAGED_IN_TRANSIT = "damaged_in_transit"
    NOT_AS_DESCRIBED = "not_as_described"
    CUSTOMER_CHANGE_MIND = "customer_change_mind"
    SIZE_ISSUE = "size_issue"
    QUALITY_ISSUE = "quality_issue"
    DELIVERY_DELAY = "delivery_delay"
    DUPLICATE_ORDER = "duplicate_order"
    MERCHANT_ERROR = "merchant_error"


class ReturnStatus(Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTED = "inspected"
    PROCESSED = "processed"
    REFUNDED = "refunded"
    EXCHANGED = "exchanged"
    CANCELLED = "cancelled"


class InspectionResult(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIAL_APPROVAL = "partial_approval"
    REQUIRES_ADDITIONAL_INFO = "requires_additional_info"


class RefundMethod(Enum):
    ORIGINAL_PAYMENT = "original_payment"
    WALLET_CREDIT = "wallet_credit"
    BANK_TRANSFER = "bank_transfer"
    STORE_CREDIT = "store_credit"
    CASH = "cash"


class DispositionAction(Enum):
    RESTOCK = "restock"
    REPAIR = "repair"
    REFURBISH = "refurbish"
    DISCOUNT_SALE = "discount_sale"
    DONATE = "donate"
    RECYCLE = "recycle"
    DISPOSE = "dispose"


@dataclass
class ReturnItem:
    item_id: str
    product_id: str
    product_name: str
    quantity_returned: int
    unit_price: Money
    return_reason: ReturnReason
    condition_description: str
    photos_urls: List[str] = None
    inspection_notes: Optional[str] = None
    disposition_action: Optional[DispositionAction] = None


@dataclass
class InspectionReport:
    inspection_id: str
    inspector_id: str
    inspection_date: datetime
    overall_result: InspectionResult
    items_inspected: List[Dict[str, Any]]  # item_id -> inspection details
    refund_amount: Money
    exchange_items: List[str] = None
    notes: Optional[str] = None
    photos_urls: List[str] = None


class ReturnRequest:
    def __init__(
        self,
        return_id: str,
        original_guide_id: GuideId,
        customer_id: CustomerId,
        return_reason: ReturnReason,
        customer_comments: str
    ):
        self.return_id = return_id
        self.original_guide_id = original_guide_id
        self.customer_id = customer_id
        self.return_reason = return_reason
        self.customer_comments = customer_comments
        self.status = ReturnStatus.REQUESTED
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.return_items: List[ReturnItem] = []
        self.return_shipping_guide: Optional[GuideId] = None
        self.expected_return_value: Money = Money(0, "COP")
        self.approved_at: Optional[datetime] = None
        self.approved_by: Optional[str] = None
        self.rejection_reason: Optional[str] = None
        self.return_deadline: Optional[datetime] = None
        self.inspection_report: Optional[InspectionReport] = None
        self.refund_amount: Money = Money(0, "COP")
        self.refund_method: Optional[RefundMethod] = None
        self.refund_processed_at: Optional[datetime] = None
        self.pickup_scheduled_at: Optional[datetime] = None
        self.received_at: Optional[datetime] = None
        self.customer_contact_info: Dict[str, str] = {}

    def add_return_item(
        self,
        item_id: str,
        product_id: str,
        product_name: str,
        quantity: int,
        unit_price: Money,
        item_reason: ReturnReason,
        condition_description: str,
        photos_urls: List[str] = None
    ) -> None:
        """Agregar item a devolver"""
        return_item = ReturnItem(
            item_id=item_id,
            product_id=product_id,
            product_name=product_name,
            quantity_returned=quantity,
            unit_price=unit_price,
            return_reason=item_reason,
            condition_description=condition_description,
            photos_urls=photos_urls or []
        )
        
        self.return_items.append(return_item)
        
        # Actualizar valor esperado de devolución
        item_value = Money(unit_price.amount * quantity, unit_price.currency)
        self.expected_return_value = Money(
            self.expected_return_value.amount + item_value.amount,
            self.expected_return_value.currency
        )
        
        self.updated_at = datetime.now()

    def approve_return(
        self,
        approved_by: str,
        return_deadline_days: int = 15,
        pickup_date: Optional[datetime] = None
    ) -> None:
        """Aprobar solicitud de devolución"""
        if self.status != ReturnStatus.REQUESTED:
            raise ValueError("Solo se pueden aprobar solicitudes pendientes")
        
        self.status = ReturnStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.return_deadline = datetime.now() + timedelta(days=return_deadline_days)
        
        if pickup_date:
            self.pickup_scheduled_at = pickup_date
        
        self.updated_at = datetime.now()

    def reject_return(
        self,
        rejection_reason: str,
        rejected_by: str
    ) -> None:
        """Rechazar solicitud de devolución"""
        if self.status != ReturnStatus.REQUESTED:
            raise ValueError("Solo se pueden rechazar solicitudes pendientes")
        
        self.status = ReturnStatus.REJECTED
        self.rejection_reason = rejection_reason
        self.updated_at = datetime.now()

    def mark_in_transit(self, return_shipping_guide: GuideId) -> None:
        """Marcar devolución como en tránsito"""
        if self.status != ReturnStatus.APPROVED:
            raise ValueError("Solo se pueden enviar devoluciones aprobadas")
        
        self.status = ReturnStatus.IN_TRANSIT
        self.return_shipping_guide = return_shipping_guide
        self.updated_at = datetime.now()

    def mark_received(self) -> None:
        """Marcar devolución como recibida"""
        if self.status != ReturnStatus.IN_TRANSIT:
            raise ValueError("Solo se pueden recibir devoluciones en tránsito")
        
        self.status = ReturnStatus.RECEIVED
        self.received_at = datetime.now()
        self.updated_at = datetime.now()

    def complete_inspection(
        self,
        inspection_report: InspectionReport
    ) -> None:
        """Completar inspección de items devueltos"""
        if self.status != ReturnStatus.RECEIVED:
            raise ValueError("Solo se pueden inspeccionar devoluciones recibidas")
        
        self.status = ReturnStatus.INSPECTED
        self.inspection_report = inspection_report
        self.refund_amount = inspection_report.refund_amount
        
        # Actualizar disposición de items
        for item in self.return_items:
            item_inspection = next(
                (i for i in inspection_report.items_inspected if i["item_id"] == item.item_id),
                None
            )
            if item_inspection:
                item.inspection_notes = item_inspection.get("notes")
                item.disposition_action = item_inspection.get("disposition_action")
        
        self.updated_at = datetime.now()

    def process_refund(
        self,
        refund_method: RefundMethod,
        processed_by: str
    ) -> None:
        """Procesar reembolso"""
        if self.status != ReturnStatus.INSPECTED:
            raise ValueError("Solo se pueden procesar reembolsos de devoluciones inspeccionadas")
        
        if self.inspection_report.overall_result not in [
            InspectionResult.APPROVED, 
            InspectionResult.PARTIAL_APPROVAL
        ]:
            raise ValueError("El reembolso requiere inspección aprobada")
        
        self.status = ReturnStatus.REFUNDED
        self.refund_method = refund_method
        self.refund_processed_at = datetime.now()
        self.updated_at = datetime.now()

    def cancel_return(self, cancellation_reason: str) -> None:
        """Cancelar devolución"""
        if self.status in [ReturnStatus.REFUNDED, ReturnStatus.EXCHANGED]:
            raise ValueError("No se puede cancelar una devolución ya procesada")
        
        self.status = ReturnStatus.CANCELLED
        self.rejection_reason = cancellation_reason
        self.updated_at = datetime.now()

    def is_within_deadline(self) -> bool:
        """Verificar si la devolución está dentro del plazo"""
        if not self.return_deadline:
            return True
        
        return datetime.now() <= self.return_deadline

    def calculate_refund_amount(self) -> Money:
        """Calcular monto de reembolso basado en inspección"""
        if not self.inspection_report:
            return Money(0, self.expected_return_value.currency)
        
        return self.inspection_report.refund_amount

    def get_return_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la devolución"""
        return {
            "return_id": self.return_id,
            "original_guide_id": self.original_guide_id.value,
            "customer_id": self.customer_id.value,
            "status": self.status.value,
            "return_reason": self.return_reason.value,
            "items_count": len(self.return_items),
            "expected_value": {
                "amount": self.expected_return_value.amount,
                "currency": self.expected_return_value.currency
            },
            "refund_amount": {
                "amount": self.refund_amount.amount,
                "currency": self.refund_amount.currency
            } if self.refund_amount else None,
            "created_at": self.created_at,
            "approved_at": self.approved_at,
            "return_deadline": self.return_deadline,
            "is_within_deadline": self.is_within_deadline(),
            "refund_processed": self.refund_processed_at is not None
        }


class ReverseLogisticsCenter:
    def __init__(
        self,
        center_id: str,
        name: str,
        address: str,
        capacity: int
    ):
        self.center_id = center_id
        self.name = name
        self.address = address
        self.capacity = capacity
        self.created_at = datetime.now()
        self.is_active = True
        self.current_inventory: Dict[str, int] = {}  # product_id -> quantity
        self.processing_queue: List[str] = []  # return_ids
        self.staff_assignments: Dict[str, str] = {}  # staff_id -> role
        self.operational_hours: Dict[str, str] = {
            "monday": "08:00-18:00",
            "tuesday": "08:00-18:00",
            "wednesday": "08:00-18:00",
            "thursday": "08:00-18:00",
            "friday": "08:00-18:00",
            "saturday": "08:00-14:00",
            "sunday": "closed"
        }

    def add_to_processing_queue(self, return_id: str) -> None:
        """Agregar devolución a cola de procesamiento"""
        if return_id not in self.processing_queue:
            self.processing_queue.append(return_id)

    def remove_from_processing_queue(self, return_id: str) -> bool:
        """Remover devolución de cola de procesamiento"""
        if return_id in self.processing_queue:
            self.processing_queue.remove(return_id)
            return True
        return False

    def add_to_inventory(self, product_id: str, quantity: int) -> None:
        """Agregar producto al inventario"""
        current_qty = self.current_inventory.get(product_id, 0)
        self.current_inventory[product_id] = current_qty + quantity

    def remove_from_inventory(self, product_id: str, quantity: int) -> bool:
        """Remover producto del inventario"""
        current_qty = self.current_inventory.get(product_id, 0)
        if current_qty >= quantity:
            self.current_inventory[product_id] = current_qty - quantity
            return True
        return False

    def get_queue_size(self) -> int:
        """Obtener tamaño de cola de procesamiento"""
        return len(self.processing_queue)

    def is_at_capacity(self) -> bool:
        """Verificar si el centro está a capacidad"""
        total_inventory = sum(self.current_inventory.values())
        return total_inventory >= self.capacity

    def get_center_summary(self) -> Dict[str, Any]:
        """Obtener resumen del centro"""
        total_inventory = sum(self.current_inventory.values())
        
        return {
            "center_id": self.center_id,
            "name": self.name,
            "address": self.address,
            "capacity": self.capacity,
            "current_inventory_count": total_inventory,
            "capacity_utilization": (total_inventory / self.capacity * 100) if self.capacity > 0 else 0,
            "processing_queue_size": self.get_queue_size(),
            "is_active": self.is_active,
            "is_at_capacity": self.is_at_capacity()
        }


class ReturnPolicy:
    def __init__(
        self,
        policy_id: str,
        name: str,
        description: str
    ):
        self.policy_id = policy_id
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.is_active = True
        self.return_window_days = 30
        self.eligible_reasons: List[ReturnReason] = []
        self.excluded_categories: List[str] = []
        self.minimum_condition_required = "good"
        self.restocking_fee_percentage = 0.0
        self.who_pays_shipping = "customer"  # "customer", "merchant", "split"
        self.refund_processing_days = 5
        self.exchange_allowed = True
        self.partial_returns_allowed = True

    def add_eligible_reason(self, reason: ReturnReason) -> None:
        """Agregar razón elegible para devolución"""
        if reason not in self.eligible_reasons:
            self.eligible_reasons.append(reason)
            self.updated_at = datetime.now()

    def exclude_category(self, category: str) -> None:
        """Excluir categoría de productos de devoluciones"""
        if category not in self.excluded_categories:
            self.excluded_categories.append(category)
            self.updated_at = datetime.now()

    def is_return_eligible(
        self,
        reason: ReturnReason,
        product_category: str,
        days_since_delivery: int,
        order_date: datetime
    ) -> bool:
        """Verificar si una devolución es elegible"""
        if not self.is_active:
            return False
        
        # Verificar ventana de tiempo
        if days_since_delivery > self.return_window_days:
            return False
        
        # Verificar razón elegible
        if self.eligible_reasons and reason not in self.eligible_reasons:
            return False
        
        # Verificar categoría excluida
        if product_category in self.excluded_categories:
            return False
        
        return True

    def calculate_refund_amount(
        self,
        original_amount: Money,
        condition_score: float  # 0.0 a 1.0
    ) -> Money:
        """Calcular monto de reembolso basado en condición"""
        base_amount = original_amount.amount
        
        # Aplicar descuento por condición
        condition_adjustment = base_amount * condition_score
        
        # Aplicar tarifa de restock si aplica
        restocking_fee = condition_adjustment * (self.restocking_fee_percentage / 100)
        
        final_amount = condition_adjustment - restocking_fee
        
        return Money(max(0, final_amount), original_amount.currency)

    def get_policy_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la política"""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "is_active": self.is_active,
            "return_window_days": self.return_window_days,
            "eligible_reasons": [r.value for r in self.eligible_reasons],
            "excluded_categories": self.excluded_categories,
            "restocking_fee_percentage": self.restocking_fee_percentage,
            "who_pays_shipping": self.who_pays_shipping,
            "refund_processing_days": self.refund_processing_days,
            "exchange_allowed": self.exchange_allowed,
            "partial_returns_allowed": self.partial_returns_allowed
        }