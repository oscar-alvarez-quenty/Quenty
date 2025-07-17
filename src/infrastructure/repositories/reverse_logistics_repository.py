from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from src.domain.entities.reverse_logistics import (
    ReturnRequest, ReverseLogisticsCenter, ReturnPolicy
)
from src.infrastructure.models.reverse_logistics_models import (
    ReturnRequestModel, ReturnItemModel, ReverseLogisticsCenterModel,
    ReturnPolicyModel, InspectionReportModel
)
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money


class ReverseLogisticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_return_request(self, return_request: ReturnRequest) -> ReturnRequest:
        """Crear nueva solicitud de devolución"""
        return_model = ReturnRequestModel(
            return_id=return_request.return_id,
            original_guide_id=return_request.original_guide_id.value,
            customer_id=return_request.customer_id.value,
            return_reason=return_request.return_reason.value,
            customer_comments=return_request.customer_comments,
            status=return_request.status.value,
            created_at=return_request.created_at,
            updated_at=return_request.updated_at,
            return_shipping_guide=return_request.return_shipping_guide.value if return_request.return_shipping_guide else None,
            expected_return_value_amount=return_request.expected_return_value.amount,
            expected_return_value_currency=return_request.expected_return_value.currency,
            approved_at=return_request.approved_at,
            approved_by=return_request.approved_by,
            rejection_reason=return_request.rejection_reason,
            return_deadline=return_request.return_deadline,
            refund_amount_amount=return_request.refund_amount.amount,
            refund_amount_currency=return_request.refund_amount.currency,
            refund_method=return_request.refund_method.value if return_request.refund_method else None,
            refund_processed_at=return_request.refund_processed_at,
            pickup_scheduled_at=return_request.pickup_scheduled_at,
            received_at=return_request.received_at,
            customer_contact_info=str(return_request.customer_contact_info)
        )
        
        self.session.add(return_model)
        await self.session.commit()
        await self.session.refresh(return_model)
        
        return return_request

    async def get_return_request(self, return_id: str) -> Optional[ReturnRequest]:
        """Obtener solicitud de devolución por ID"""
        stmt = (
            select(ReturnRequestModel)
            .options(
                selectinload(ReturnRequestModel.return_items),
                selectinload(ReturnRequestModel.inspection_report)
            )
            .where(ReturnRequestModel.return_id == return_id)
        )
        
        result = await self.session.execute(stmt)
        return_model = result.scalar_one_or_none()
        
        if return_model:
            return self._return_model_to_entity(return_model)
        return None

    async def update_return_request(self, return_request: ReturnRequest) -> ReturnRequest:
        """Actualizar solicitud de devolución"""
        stmt = (
            update(ReturnRequestModel)
            .where(ReturnRequestModel.return_id == return_request.return_id)
            .values(
                status=return_request.status.value,
                updated_at=return_request.updated_at,
                return_shipping_guide=return_request.return_shipping_guide.value if return_request.return_shipping_guide else None,
                expected_return_value_amount=return_request.expected_return_value.amount,
                expected_return_value_currency=return_request.expected_return_value.currency,
                approved_at=return_request.approved_at,
                approved_by=return_request.approved_by,
                rejection_reason=return_request.rejection_reason,
                return_deadline=return_request.return_deadline,
                refund_amount_amount=return_request.refund_amount.amount,
                refund_amount_currency=return_request.refund_amount.currency,
                refund_method=return_request.refund_method.value if return_request.refund_method else None,
                refund_processed_at=return_request.refund_processed_at,
                pickup_scheduled_at=return_request.pickup_scheduled_at,
                received_at=return_request.received_at,
                customer_contact_info=str(return_request.customer_contact_info)
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return return_request

    async def get_returns_by_customer(self, customer_id: CustomerId) -> List[ReturnRequest]:
        """Obtener devoluciones por cliente"""
        stmt = (
            select(ReturnRequestModel)
            .options(selectinload(ReturnRequestModel.return_items))
            .where(ReturnRequestModel.customer_id == customer_id.value)
            .order_by(ReturnRequestModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        return_models = result.scalars().all()
        
        return [self._return_model_to_entity(model) for model in return_models]

    async def get_returns_by_status(self, status: str) -> List[ReturnRequest]:
        """Obtener devoluciones por estado"""
        stmt = (
            select(ReturnRequestModel)
            .options(selectinload(ReturnRequestModel.return_items))
            .where(ReturnRequestModel.status == status)
            .order_by(ReturnRequestModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        return_models = result.scalars().all()
        
        return [self._return_model_to_entity(model) for model in return_models]

    async def get_overdue_returns(self) -> List[ReturnRequest]:
        """Obtener devoluciones vencidas"""
        now = datetime.now()
        
        stmt = (
            select(ReturnRequestModel)
            .options(selectinload(ReturnRequestModel.return_items))
            .where(
                and_(
                    ReturnRequestModel.return_deadline < now,
                    ReturnRequestModel.status.in_(['approved', 'in_transit'])
                )
            )
        )
        
        result = await self.session.execute(stmt)
        return_models = result.scalars().all()
        
        return [self._return_model_to_entity(model) for model in return_models]

    async def get_pending_inspection_returns(self, center_id: Optional[str] = None) -> List[ReturnRequest]:
        """Obtener devoluciones pendientes de inspección"""
        conditions = [ReturnRequestModel.status == 'received']
        
        stmt = (
            select(ReturnRequestModel)
            .options(selectinload(ReturnRequestModel.return_items))
            .where(and_(*conditions))
            .order_by(ReturnRequestModel.received_at)
        )
        
        result = await self.session.execute(stmt)
        return_models = result.scalars().all()
        
        return [self._return_model_to_entity(model) for model in return_models]

    # Return Item methods
    async def add_return_item(self, return_id: str, return_item_data: Dict[str, Any]) -> bool:
        """Agregar item a devolución"""
        item_model = ReturnItemModel(
            item_id=return_item_data["item_id"],
            return_id=return_id,
            product_id=return_item_data["product_id"],
            product_name=return_item_data["product_name"],
            quantity_returned=return_item_data["quantity_returned"],
            unit_price_amount=return_item_data["unit_price"].amount,
            unit_price_currency=return_item_data["unit_price"].currency,
            return_reason=return_item_data["return_reason"].value,
            condition_description=return_item_data["condition_description"],
            photos_urls=",".join(return_item_data.get("photos_urls", [])),
            inspection_notes=return_item_data.get("inspection_notes"),
            disposition_action=return_item_data.get("disposition_action").value if return_item_data.get("disposition_action") else None
        )
        
        self.session.add(item_model)
        await self.session.commit()
        
        return True

    async def get_return_items(self, return_id: str) -> List[Dict[str, Any]]:
        """Obtener items de devolución"""
        stmt = select(ReturnItemModel).where(ReturnItemModel.return_id == return_id)
        result = await self.session.execute(stmt)
        item_models = result.scalars().all()
        
        return [self._return_item_model_to_dict(model) for model in item_models]

    # Logistics Center methods
    async def create_logistics_center(self, center: ReverseLogisticsCenter) -> ReverseLogisticsCenter:
        """Crear centro logístico"""
        center_model = ReverseLogisticsCenterModel(
            center_id=center.center_id,
            name=center.name,
            address=center.address,
            capacity=center.capacity,
            created_at=center.created_at,
            is_active=center.is_active,
            current_inventory=str(center.current_inventory),
            processing_queue=",".join(center.processing_queue),
            staff_assignments=str(center.staff_assignments),
            operational_hours=str(center.operational_hours)
        )
        
        self.session.add(center_model)
        await self.session.commit()
        await self.session.refresh(center_model)
        
        return center

    async def get_logistics_center(self, center_id: str) -> Optional[ReverseLogisticsCenter]:
        """Obtener centro logístico por ID"""
        stmt = select(ReverseLogisticsCenterModel).where(
            ReverseLogisticsCenterModel.center_id == center_id
        )
        result = await self.session.execute(stmt)
        center_model = result.scalar_one_or_none()
        
        if center_model:
            return self._center_model_to_entity(center_model)
        return None

    async def update_logistics_center(self, center: ReverseLogisticsCenter) -> ReverseLogisticsCenter:
        """Actualizar centro logístico"""
        stmt = (
            update(ReverseLogisticsCenterModel)
            .where(ReverseLogisticsCenterModel.center_id == center.center_id)
            .values(
                name=center.name,
                address=center.address,
                capacity=center.capacity,
                is_active=center.is_active,
                current_inventory=str(center.current_inventory),
                processing_queue=",".join(center.processing_queue),
                staff_assignments=str(center.staff_assignments),
                operational_hours=str(center.operational_hours)
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return center

    async def get_active_logistics_centers(self) -> List[ReverseLogisticsCenter]:
        """Obtener centros logísticos activos"""
        stmt = (
            select(ReverseLogisticsCenterModel)
            .where(ReverseLogisticsCenterModel.is_active == True)
            .order_by(ReverseLogisticsCenterModel.name)
        )
        
        result = await self.session.execute(stmt)
        center_models = result.scalars().all()
        
        return [self._center_model_to_entity(model) for model in center_models]

    # Return Policy methods
    async def create_return_policy(self, policy: ReturnPolicy) -> ReturnPolicy:
        """Crear política de devoluciones"""
        policy_model = ReturnPolicyModel(
            policy_id=policy.policy_id,
            name=policy.name,
            description=policy.description,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
            is_active=policy.is_active,
            return_window_days=policy.return_window_days,
            eligible_reasons=",".join([r.value for r in policy.eligible_reasons]),
            excluded_categories=",".join(policy.excluded_categories),
            minimum_condition_required=policy.minimum_condition_required,
            restocking_fee_percentage=policy.restocking_fee_percentage,
            who_pays_shipping=policy.who_pays_shipping,
            refund_processing_days=policy.refund_processing_days,
            exchange_allowed=policy.exchange_allowed,
            partial_returns_allowed=policy.partial_returns_allowed
        )
        
        self.session.add(policy_model)
        await self.session.commit()
        await self.session.refresh(policy_model)
        
        return policy

    async def get_return_policy(self, policy_id: str) -> Optional[ReturnPolicy]:
        """Obtener política de devoluciones por ID"""
        stmt = select(ReturnPolicyModel).where(ReturnPolicyModel.policy_id == policy_id)
        result = await self.session.execute(stmt)
        policy_model = result.scalar_one_or_none()
        
        if policy_model:
            return self._policy_model_to_entity(policy_model)
        return None

    async def get_active_return_policy(self) -> Optional[ReturnPolicy]:
        """Obtener política de devoluciones activa"""
        stmt = (
            select(ReturnPolicyModel)
            .where(ReturnPolicyModel.is_active == True)
            .order_by(ReturnPolicyModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        policy_model = result.scalar_one_or_none()
        
        if policy_model:
            return self._policy_model_to_entity(policy_model)
        return None

    async def update_return_policy(self, policy: ReturnPolicy) -> ReturnPolicy:
        """Actualizar política de devoluciones"""
        stmt = (
            update(ReturnPolicyModel)
            .where(ReturnPolicyModel.policy_id == policy.policy_id)
            .values(
                name=policy.name,
                description=policy.description,
                updated_at=policy.updated_at,
                is_active=policy.is_active,
                return_window_days=policy.return_window_days,
                eligible_reasons=",".join([r.value for r in policy.eligible_reasons]),
                excluded_categories=",".join(policy.excluded_categories),
                minimum_condition_required=policy.minimum_condition_required,
                restocking_fee_percentage=policy.restocking_fee_percentage,
                who_pays_shipping=policy.who_pays_shipping,
                refund_processing_days=policy.refund_processing_days,
                exchange_allowed=policy.exchange_allowed,
                partial_returns_allowed=policy.partial_returns_allowed
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return policy

    async def search_returns(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[ReturnRequest]:
        """Buscar devoluciones con filtros"""
        conditions = []
        
        if filters.get('customer_id'):
            conditions.append(ReturnRequestModel.customer_id == filters['customer_id'])
        
        if filters.get('status'):
            conditions.append(ReturnRequestModel.status == filters['status'])
        
        if filters.get('return_reason'):
            conditions.append(ReturnRequestModel.return_reason == filters['return_reason'])
        
        if filters.get('start_date'):
            conditions.append(ReturnRequestModel.created_at >= filters['start_date'])
        
        if filters.get('end_date'):
            conditions.append(ReturnRequestModel.created_at <= filters['end_date'])
        
        if filters.get('original_guide_id'):
            conditions.append(ReturnRequestModel.original_guide_id == filters['original_guide_id'])
        
        stmt = (
            select(ReturnRequestModel)
            .options(selectinload(ReturnRequestModel.return_items))
            .where(and_(*conditions) if conditions else True)
            .order_by(ReturnRequestModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return_models = result.scalars().all()
        
        return [self._return_model_to_entity(model) for model in return_models]

    async def get_return_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Obtener analytics de devoluciones"""
        # Obtener todas las devoluciones en el período
        stmt = (
            select(ReturnRequestModel)
            .where(
                and_(
                    ReturnRequestModel.created_at >= start_date,
                    ReturnRequestModel.created_at <= end_date
                )
            )
        )
        
        result = await self.session.execute(stmt)
        return_models = result.scalars().all()
        
        # Calcular métricas
        total_returns = len(return_models)
        approved_returns = len([r for r in return_models if r.status == 'approved'])
        refunded_returns = len([r for r in return_models if r.status == 'refunded'])
        
        # Calcular monto total de reembolsos
        total_refund_amount = sum(
            r.refund_amount_amount for r in return_models 
            if r.refund_amount_amount and r.status == 'refunded'
        )
        
        # Analizar razones de devolución
        reason_counts = {}
        for return_model in return_models:
            reason = return_model.return_reason
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_returns": total_returns,
            "approved_returns": approved_returns,
            "refunded_returns": refunded_returns,
            "approval_rate": (approved_returns / total_returns * 100) if total_returns > 0 else 0,
            "refund_rate": (refunded_returns / approved_returns * 100) if approved_returns > 0 else 0,
            "total_refund_amount": total_refund_amount,
            "average_refund": total_refund_amount / refunded_returns if refunded_returns > 0 else 0,
            "reason_distribution": reason_counts
        }

    def _return_model_to_entity(self, model: ReturnRequestModel) -> ReturnRequest:
        """Convertir modelo de devolución a entidad"""
        from src.domain.entities.reverse_logistics import ReturnReason, ReturnStatus, RefundMethod
        
        return_request = ReturnRequest(
            return_id=model.return_id,
            original_guide_id=GuideId(model.original_guide_id),
            customer_id=CustomerId(model.customer_id),
            return_reason=ReturnReason(model.return_reason),
            customer_comments=model.customer_comments
        )
        
        # Asignar propiedades adicionales
        return_request.status = ReturnStatus(model.status)
        return_request.created_at = model.created_at
        return_request.updated_at = model.updated_at
        return_request.expected_return_value = Money(
            model.expected_return_value_amount,
            model.expected_return_value_currency
        )
        return_request.approved_at = model.approved_at
        return_request.approved_by = model.approved_by
        return_request.rejection_reason = model.rejection_reason
        return_request.return_deadline = model.return_deadline
        return_request.refund_amount = Money(
            model.refund_amount_amount,
            model.refund_amount_currency
        )
        return_request.refund_processed_at = model.refund_processed_at
        return_request.pickup_scheduled_at = model.pickup_scheduled_at
        return_request.received_at = model.received_at
        
        if model.return_shipping_guide:
            return_request.return_shipping_guide = GuideId(model.return_shipping_guide)
        
        if model.refund_method:
            return_request.refund_method = RefundMethod(model.refund_method)
        
        # Parsear información de contacto
        if model.customer_contact_info:
            import json
            try:
                return_request.customer_contact_info = json.loads(model.customer_contact_info)
            except:
                return_request.customer_contact_info = {}
        
        # Cargar items de devolución
        if hasattr(model, 'return_items') and model.return_items:
            from src.domain.entities.reverse_logistics import ReturnItem, DispositionAction
            return_items = []
            for item_model in model.return_items:
                return_item = ReturnItem(
                    item_id=item_model.item_id,
                    product_id=item_model.product_id,
                    product_name=item_model.product_name,
                    quantity_returned=item_model.quantity_returned,
                    unit_price=Money(item_model.unit_price_amount, item_model.unit_price_currency),
                    return_reason=ReturnReason(item_model.return_reason),
                    condition_description=item_model.condition_description,
                    photos_urls=item_model.photos_urls.split(',') if item_model.photos_urls else []
                )
                return_item.inspection_notes = item_model.inspection_notes
                if item_model.disposition_action:
                    return_item.disposition_action = DispositionAction(item_model.disposition_action)
                
                return_items.append(return_item)
            
            return_request.return_items = return_items
        
        return return_request

    def _return_item_model_to_dict(self, model: ReturnItemModel) -> Dict[str, Any]:
        """Convertir modelo de item a diccionario"""
        from src.domain.entities.reverse_logistics import ReturnReason, DispositionAction
        
        return {
            "item_id": model.item_id,
            "product_id": model.product_id,
            "product_name": model.product_name,
            "quantity_returned": model.quantity_returned,
            "unit_price": Money(model.unit_price_amount, model.unit_price_currency),
            "return_reason": ReturnReason(model.return_reason),
            "condition_description": model.condition_description,
            "photos_urls": model.photos_urls.split(',') if model.photos_urls else [],
            "inspection_notes": model.inspection_notes,
            "disposition_action": DispositionAction(model.disposition_action) if model.disposition_action else None
        }

    def _center_model_to_entity(self, model: ReverseLogisticsCenterModel) -> ReverseLogisticsCenter:
        """Convertir modelo de centro a entidad"""
        center = ReverseLogisticsCenter(
            center_id=model.center_id,
            name=model.name,
            address=model.address,
            capacity=model.capacity
        )
        
        # Asignar propiedades
        center.created_at = model.created_at
        center.is_active = model.is_active
        
        # Parsear inventario actual
        if model.current_inventory:
            import json
            try:
                center.current_inventory = json.loads(model.current_inventory)
            except:
                center.current_inventory = {}
        
        # Parsear cola de procesamiento
        if model.processing_queue:
            center.processing_queue = model.processing_queue.split(',')
        
        # Parsear asignaciones de personal
        if model.staff_assignments:
            import json
            try:
                center.staff_assignments = json.loads(model.staff_assignments)
            except:
                center.staff_assignments = {}
        
        # Parsear horarios operacionales
        if model.operational_hours:
            import json
            try:
                center.operational_hours = json.loads(model.operational_hours)
            except:
                center.operational_hours = {}
        
        return center

    def _policy_model_to_entity(self, model: ReturnPolicyModel) -> ReturnPolicy:
        """Convertir modelo de política a entidad"""
        from src.domain.entities.reverse_logistics import ReturnReason
        
        policy = ReturnPolicy(
            policy_id=model.policy_id,
            name=model.name,
            description=model.description
        )
        
        # Asignar propiedades
        policy.created_at = model.created_at
        policy.updated_at = model.updated_at
        policy.is_active = model.is_active
        policy.return_window_days = model.return_window_days
        policy.minimum_condition_required = model.minimum_condition_required
        policy.restocking_fee_percentage = model.restocking_fee_percentage
        policy.who_pays_shipping = model.who_pays_shipping
        policy.refund_processing_days = model.refund_processing_days
        policy.exchange_allowed = model.exchange_allowed
        policy.partial_returns_allowed = model.partial_returns_allowed
        
        # Parsear razones elegibles
        if model.eligible_reasons:
            policy.eligible_reasons = [
                ReturnReason(reason) for reason in model.eligible_reasons.split(',')
            ]
        
        # Parsear categorías excluidas
        if model.excluded_categories:
            policy.excluded_categories = model.excluded_categories.split(',')
        
        return policy