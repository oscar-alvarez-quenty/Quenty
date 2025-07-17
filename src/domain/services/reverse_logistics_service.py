from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from src.domain.entities.reverse_logistics import (
    ReturnRequest, ReturnItem, InspectionReport, ReverseLogisticsCenter,
    ReturnPolicy, ReturnReason, ReturnStatus, InspectionResult,
    RefundMethod, DispositionAction
)
from src.domain.entities.customer import Customer
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money
from src.domain.events.reverse_logistics_events import (
    ReturnRequested, ReturnApproved, ReturnRejected, ReturnReceived,
    ReturnInspectionCompleted, ReturnRefundProcessed, InventoryRestocked,
    ReturnCancelled, QualityControlAlert
)


class ReverseLogisticsService:
    def __init__(self):
        self.return_requests: Dict[str, ReturnRequest] = {}
        self.logistics_centers: Dict[str, ReverseLogisticsCenter] = {}
        self.return_policies: Dict[str, ReturnPolicy] = {}
        self._domain_events: List = []
        
        # Inicializar políticas y centros predeterminados
        self._initialize_default_policies()
        self._initialize_default_centers()

    def create_return_request(
        self,
        original_guide_id: GuideId,
        customer: Customer,
        return_reason: ReturnReason,
        customer_comments: str,
        contact_info: Dict[str, str]
    ) -> ReturnRequest:
        """Crear solicitud de devolución"""
        return_id = str(uuid.uuid4())
        
        return_request = ReturnRequest(
            return_id=return_id,
            original_guide_id=original_guide_id,
            customer_id=customer.customer_id,
            return_reason=return_reason,
            customer_comments=customer_comments
        )
        
        return_request.customer_contact_info = contact_info
        
        self.return_requests[return_id] = return_request
        
        self._add_domain_event(
            ReturnRequested(
                return_id=return_id,
                customer_id=customer.customer_id.value,
                original_guide_id=original_guide_id.value,
                return_reason=return_reason.value,
                items_count=0,  # Se actualizará cuando se agreguen items
                expected_value={"amount": 0, "currency": "COP"},
                requested_at=datetime.now()
            )
        )
        
        return return_request

    def add_item_to_return(
        self,
        return_id: str,
        product_id: str,
        product_name: str,
        quantity: int,
        unit_price: Money,
        item_reason: ReturnReason,
        condition_description: str,
        photos_urls: List[str] = None
    ) -> bool:
        """Agregar item a solicitud de devolución"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        if return_request.status != ReturnStatus.REQUESTED:
            raise ValueError("Solo se pueden agregar items a solicitudes pendientes")
        
        item_id = str(uuid.uuid4())
        return_request.add_return_item(
            item_id=item_id,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            item_reason=item_reason,
            condition_description=condition_description,
            photos_urls=photos_urls
        )
        
        return True

    def evaluate_return_eligibility(
        self,
        return_id: str,
        order_date: datetime,
        delivery_date: datetime,
        product_categories: List[str]
    ) -> Dict[str, Any]:
        """Evaluar elegibilidad de devolución"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        # Obtener política aplicable (en implementación real sería más sofisticado)
        active_policy = next(
            (policy for policy in self.return_policies.values() if policy.is_active),
            None
        )
        
        if not active_policy:
            return {
                "eligible": False,
                "reason": "No hay política de devoluciones activa",
                "policy_id": None
            }
        
        days_since_delivery = (datetime.now() - delivery_date).days
        
        eligibility_results = []
        overall_eligible = True
        
        for category in product_categories:
            is_eligible = active_policy.is_return_eligible(
                reason=return_request.return_reason,
                product_category=category,
                days_since_delivery=days_since_delivery,
                order_date=order_date
            )
            
            eligibility_results.append({
                "category": category,
                "eligible": is_eligible,
                "reason": None if is_eligible else "Fuera de política"
            })
            
            if not is_eligible:
                overall_eligible = False
        
        return {
            "eligible": overall_eligible,
            "policy_id": active_policy.policy_id,
            "policy_name": active_policy.name,
            "days_since_delivery": days_since_delivery,
            "return_window_days": active_policy.return_window_days,
            "category_results": eligibility_results
        }

    def approve_return(
        self,
        return_id: str,
        approved_by: str,
        pickup_date: Optional[datetime] = None
    ) -> bool:
        """Aprobar solicitud de devolución"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        return_request.approve_return(
            approved_by=approved_by,
            pickup_date=pickup_date
        )
        
        self._add_domain_event(
            ReturnApproved(
                return_id=return_id,
                customer_id=return_request.customer_id.value,
                approved_by=approved_by,
                return_deadline=return_request.return_deadline,
                pickup_scheduled=pickup_date is not None,
                pickup_date=pickup_date,
                approved_at=datetime.now()
            )
        )
        
        return True

    def reject_return(
        self,
        return_id: str,
        rejection_reason: str,
        rejected_by: str
    ) -> bool:
        """Rechazar solicitud de devolución"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        return_request.reject_return(rejection_reason, rejected_by)
        
        self._add_domain_event(
            ReturnRejected(
                return_id=return_id,
                customer_id=return_request.customer_id.value,
                rejection_reason=rejection_reason,
                rejected_by=rejected_by,
                rejected_at=datetime.now()
            )
        )
        
        return True

    def receive_return(
        self,
        return_id: str,
        center_id: str,
        received_by: str,
        packages_count: int,
        initial_condition: str = "pending_inspection"
    ) -> bool:
        """Recibir devolución en centro logístico"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        center = self.logistics_centers.get(center_id)
        if not center:
            raise ValueError(f"Centro logístico {center_id} no encontrado")
        
        return_request.mark_received()
        center.add_to_processing_queue(return_id)
        
        self._add_domain_event(
            ReturnReceived(
                return_id=return_id,
                received_at_center=center_id,
                received_by=received_by,
                packages_count=packages_count,
                initial_condition=initial_condition,
                received_at=datetime.now()
            )
        )
        
        return True

    def conduct_inspection(
        self,
        return_id: str,
        inspector_id: str,
        item_inspections: List[Dict[str, Any]]
    ) -> InspectionReport:
        """Realizar inspección de items devueltos"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        inspection_id = str(uuid.uuid4())
        
        # Calcular resultado general y monto de reembolso
        approved_items = 0
        rejected_items = 0
        total_refund = Money(0, return_request.expected_return_value.currency)
        
        # Obtener política para cálculo de reembolso
        active_policy = next(
            (policy for policy in self.return_policies.values() if policy.is_active),
            None
        )
        
        for inspection in item_inspections:
            if inspection["result"] == "approved":
                approved_items += 1
                # Calcular reembolso basado en condición
                if active_policy:
                    item_refund = active_policy.calculate_refund_amount(
                        Money(inspection["original_price"], total_refund.currency),
                        inspection.get("condition_score", 1.0)
                    )
                    total_refund = Money(
                        total_refund.amount + item_refund.amount,
                        total_refund.currency
                    )
            else:
                rejected_items += 1
        
        # Determinar resultado general
        if approved_items == len(item_inspections):
            overall_result = InspectionResult.APPROVED
        elif approved_items > 0:
            overall_result = InspectionResult.PARTIAL_APPROVAL
        else:
            overall_result = InspectionResult.REJECTED
        
        inspection_report = InspectionReport(
            inspection_id=inspection_id,
            inspector_id=inspector_id,
            inspection_date=datetime.now(),
            overall_result=overall_result,
            items_inspected=item_inspections,
            refund_amount=total_refund,
            notes=f"Inspección completada: {approved_items} aprobados, {rejected_items} rechazados"
        )
        
        return_request.complete_inspection(inspection_report)
        
        self._add_domain_event(
            ReturnInspectionCompleted(
                return_id=return_id,
                inspection_id=inspection_id,
                inspector_id=inspector_id,
                overall_result=overall_result.value,
                approved_items=approved_items,
                rejected_items=rejected_items,
                refund_amount={
                    "amount": total_refund.amount,
                    "currency": total_refund.currency
                },
                completed_at=datetime.now()
            )
        )
        
        return inspection_report

    def process_refund(
        self,
        return_id: str,
        refund_method: RefundMethod,
        processed_by: str
    ) -> str:
        """Procesar reembolso de devolución"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        return_request.process_refund(refund_method, processed_by)
        
        transaction_reference = f"REF_{return_id[:8]}_{datetime.now().strftime('%Y%m%d%H%M')}"
        
        self._add_domain_event(
            ReturnRefundProcessed(
                return_id=return_id,
                customer_id=return_request.customer_id.value,
                refund_amount={
                    "amount": return_request.refund_amount.amount,
                    "currency": return_request.refund_amount.currency
                },
                refund_method=refund_method.value,
                transaction_reference=transaction_reference,
                processed_by=processed_by,
                processed_at=datetime.now()
            )
        )
        
        return transaction_reference

    def process_returned_inventory(
        self,
        return_id: str,
        center_id: str,
        processed_by: str
    ) -> Dict[str, Any]:
        """Procesar inventario devuelto"""
        return_request = self.return_requests.get(return_id)
        if not return_request:
            raise ValueError(f"Solicitud de devolución {return_id} no encontrada")
        
        center = self.logistics_centers.get(center_id)
        if not center:
            raise ValueError(f"Centro logístico {center_id} no encontrado")
        
        if not return_request.inspection_report:
            raise ValueError("Se requiere inspección completada")
        
        processing_summary = {
            "restocked": 0,
            "refurbished": 0,
            "disposed": 0,
            "total_value_restocked": Money(0, "COP")
        }
        
        for item in return_request.return_items:
            if item.disposition_action == DispositionAction.RESTOCK:
                center.add_to_inventory(item.product_id, item.quantity_returned)
                processing_summary["restocked"] += item.quantity_returned
                
                item_value = Money(
                    item.unit_price.amount * item.quantity_returned,
                    item.unit_price.currency
                )
                processing_summary["total_value_restocked"] = Money(
                    processing_summary["total_value_restocked"].amount + item_value.amount,
                    processing_summary["total_value_restocked"].currency
                )
                
                self._add_domain_event(
                    InventoryRestocked(
                        center_id=center_id,
                        return_id=return_id,
                        product_id=item.product_id,
                        quantity_restocked=item.quantity_returned,
                        condition="good",
                        restocked_by=processed_by,
                        restocked_at=datetime.now()
                    )
                )
            
            elif item.disposition_action == DispositionAction.REFURBISH:
                processing_summary["refurbished"] += item.quantity_returned
            
            elif item.disposition_action in [DispositionAction.DISPOSE, DispositionAction.RECYCLE]:
                processing_summary["disposed"] += item.quantity_returned
        
        # Remover de cola de procesamiento
        center.remove_from_processing_queue(return_id)
        
        return processing_summary

    def get_return_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        customer_id: Optional[CustomerId] = None
    ) -> Dict[str, Any]:
        """Obtener analytics de devoluciones"""
        # Filtrar devoluciones por período
        period_returns = [
            return_req for return_req in self.return_requests.values()
            if start_date <= return_req.created_at <= end_date
        ]
        
        if customer_id:
            period_returns = [
                return_req for return_req in period_returns
                if return_req.customer_id == customer_id
            ]
        
        # Calcular métricas
        total_returns = len(period_returns)
        approved_returns = len([r for r in period_returns if r.status == ReturnStatus.APPROVED])
        completed_returns = len([r for r in period_returns if r.status == ReturnStatus.REFUNDED])
        
        total_refund_amount = sum(
            r.refund_amount.amount for r in period_returns 
            if r.refund_amount and r.refund_amount.amount > 0
        )
        
        # Análisis de razones
        reason_counts = {}
        for return_req in period_returns:
            reason = return_req.return_reason.value
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        top_reasons = sorted(
            reason_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_returns": total_returns,
            "approved_returns": approved_returns,
            "completed_returns": completed_returns,
            "approval_rate": (approved_returns / total_returns * 100) if total_returns > 0 else 0,
            "completion_rate": (completed_returns / approved_returns * 100) if approved_returns > 0 else 0,
            "total_refund_amount": total_refund_amount,
            "average_refund": total_refund_amount / completed_returns if completed_returns > 0 else 0,
            "top_return_reasons": [{"reason": r[0], "count": r[1]} for r in top_reasons],
            "customer_filter": customer_id.value if customer_id else None
        }

    def detect_quality_issues(
        self,
        product_id: str,
        lookback_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Detectar problemas de calidad basado en patrones de devolución"""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        # Buscar devoluciones del producto
        product_returns = []
        for return_req in self.return_requests.values():
            if return_req.created_at >= cutoff_date:
                for item in return_req.return_items:
                    if item.product_id == product_id:
                        product_returns.append({
                            "return_id": return_req.return_id,
                            "reason": item.return_reason,
                            "quantity": item.quantity_returned,
                            "date": return_req.created_at
                        })
        
        if len(product_returns) < 3:  # Umbral mínimo
            return None
        
        # Analizar patrones
        total_returns = len(product_returns)
        reason_distribution = {}
        
        for return_item in product_returns:
            reason = return_item["reason"].value
            reason_distribution[reason] = reason_distribution.get(reason, 0) + 1
        
        # Detectar si hay concentración alta en razones problemáticas
        quality_reasons = [
            ReturnReason.DEFECTIVE_PRODUCT.value,
            ReturnReason.DAMAGED_IN_TRANSIT.value,
            ReturnReason.NOT_AS_DESCRIBED.value,
            ReturnReason.QUALITY_ISSUE.value
        ]
        
        quality_issues_count = sum(
            reason_distribution.get(reason, 0) for reason in quality_reasons
        )
        
        quality_issue_rate = quality_issues_count / total_returns
        
        if quality_issue_rate > 0.6:  # Más del 60% son problemas de calidad
            alert_id = str(uuid.uuid4())
            
            self._add_domain_event(
                QualityControlAlert(
                    alert_id=alert_id,
                    center_id="main_center",  # En implementación real sería dinámico
                    product_id=product_id,
                    issue_type="high_return_rate",
                    affected_returns=[r["return_id"] for r in product_returns],
                    alert_severity="high" if quality_issue_rate > 0.8 else "medium",
                    detected_at=datetime.now()
                )
            )
            
            return {
                "alert_id": alert_id,
                "product_id": product_id,
                "total_returns": total_returns,
                "quality_issue_rate": quality_issue_rate,
                "lookback_days": lookback_days,
                "reason_distribution": reason_distribution,
                "recommended_action": "investigate_product_quality"
            }
        
        return None

    def get_center_status(self, center_id: str) -> Dict[str, Any]:
        """Obtener estado del centro logístico"""
        center = self.logistics_centers.get(center_id)
        if not center:
            raise ValueError(f"Centro logístico {center_id} no encontrado")
        
        # Calcular métricas adicionales
        processing_queue = center.processing_queue
        queue_analytics = {
            "urgent_returns": 0,
            "overdue_returns": 0,
            "average_wait_time_hours": 0
        }
        
        for return_id in processing_queue:
            return_req = self.return_requests.get(return_id)
            if return_req:
                # Calcular tiempo en cola
                if return_req.received_at:
                    wait_time = (datetime.now() - return_req.received_at).total_seconds() / 3600
                    queue_analytics["average_wait_time_hours"] += wait_time
                    
                    if wait_time > 48:  # Más de 48 horas
                        queue_analytics["overdue_returns"] += 1
                
                # Verificar urgencia
                if return_req.return_deadline and return_req.return_deadline <= datetime.now() + timedelta(days=2):
                    queue_analytics["urgent_returns"] += 1
        
        if processing_queue:
            queue_analytics["average_wait_time_hours"] /= len(processing_queue)
        
        center_summary = center.get_center_summary()
        center_summary.update(queue_analytics)
        
        return center_summary

    def _initialize_default_policies(self) -> None:
        """Inicializar políticas de devolución predeterminadas"""
        default_policy = ReturnPolicy(
            policy_id="default_return_policy",
            name="Política General de Devoluciones",
            description="Política estándar para devoluciones de productos"
        )
        
        # Configurar política
        default_policy.return_window_days = 30
        default_policy.eligible_reasons = [
            ReturnReason.DEFECTIVE_PRODUCT,
            ReturnReason.WRONG_ITEM,
            ReturnReason.DAMAGED_IN_TRANSIT,
            ReturnReason.NOT_AS_DESCRIBED,
            ReturnReason.SIZE_ISSUE,
            ReturnReason.QUALITY_ISSUE
        ]
        default_policy.excluded_categories = ["perishable", "custom", "digital"]
        default_policy.restocking_fee_percentage = 10.0
        
        self.return_policies[default_policy.policy_id] = default_policy

    def _initialize_default_centers(self) -> None:
        """Inicializar centros logísticos predeterminados"""
        main_center = ReverseLogisticsCenter(
            center_id="main_center",
            name="Centro Principal de Devoluciones",
            address="Bogotá, Colombia",
            capacity=10000
        )
        
        self.logistics_centers[main_center.center_id] = main_center

    def _add_domain_event(self, event) -> None:
        """Agregar evento de dominio"""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Obtener eventos de dominio pendientes"""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Limpiar eventos de dominio después de publicarlos"""
        self._domain_events.clear()