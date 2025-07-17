from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from src.domain.entities.pickup import PickupRequest, PickupRoute
from src.infrastructure.models.pickup_models import (
    PickupRequestModel, PickupRouteModel, PickupAttemptModel
)
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId


class PickupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_pickup_request(self, pickup_request: PickupRequest) -> PickupRequest:
        """Crear nueva solicitud de recolección"""
        pickup_model = PickupRequestModel(
            pickup_id=pickup_request.pickup_id,
            guide_id=pickup_request.guide_id.value,
            customer_id=pickup_request.customer_id.value,
            pickup_type=pickup_request.pickup_type.value,
            pickup_address=pickup_request.pickup_address,
            contact_name=pickup_request.contact_name,
            contact_phone=pickup_request.contact_phone,
            status=pickup_request.status.value,
            created_at=pickup_request.created_at,
            updated_at=pickup_request.updated_at,
            scheduled_date=pickup_request.scheduled_date,
            assigned_operator_id=pickup_request.assigned_operator_id,
            assigned_point_id=pickup_request.assigned_point_id,
            special_instructions=pickup_request.special_instructions,
            completed_at=pickup_request.completed_at,
            max_attempts=pickup_request.max_attempts,
            priority=pickup_request.priority,
            estimated_packages=pickup_request.estimated_packages,
            total_weight_kg=pickup_request.total_weight_kg,
            requires_special_handling=pickup_request.requires_special_handling
        )
        
        self.session.add(pickup_model)
        await self.session.commit()
        await self.session.refresh(pickup_model)
        
        return self._model_to_entity(pickup_model)

    async def get_pickup_request(self, pickup_id: str) -> Optional[PickupRequest]:
        """Obtener solicitud de recolección por ID"""
        stmt = (
            select(PickupRequestModel)
            .options(selectinload(PickupRequestModel.pickup_attempts))
            .where(PickupRequestModel.pickup_id == pickup_id)
        )
        result = await self.session.execute(stmt)
        pickup_model = result.scalar_one_or_none()
        
        if pickup_model:
            return self._model_to_entity(pickup_model)
        return None

    async def update_pickup_request(self, pickup_request: PickupRequest) -> PickupRequest:
        """Actualizar solicitud de recolección"""
        stmt = (
            update(PickupRequestModel)
            .where(PickupRequestModel.pickup_id == pickup_request.pickup_id)
            .values(
                status=pickup_request.status.value,
                updated_at=pickup_request.updated_at,
                scheduled_date=pickup_request.scheduled_date,
                assigned_operator_id=pickup_request.assigned_operator_id,
                assigned_point_id=pickup_request.assigned_point_id,
                special_instructions=pickup_request.special_instructions,
                completed_at=pickup_request.completed_at,
                priority=pickup_request.priority,
                estimated_packages=pickup_request.estimated_packages,
                total_weight_kg=pickup_request.total_weight_kg,
                requires_special_handling=pickup_request.requires_special_handling
            )
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return pickup_request

    async def get_pickups_by_customer(self, customer_id: CustomerId) -> List[PickupRequest]:
        """Obtener recolecciones por cliente"""
        stmt = (
            select(PickupRequestModel)
            .options(selectinload(PickupRequestModel.pickup_attempts))
            .where(PickupRequestModel.customer_id == customer_id.value)
            .order_by(PickupRequestModel.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        pickup_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in pickup_models]

    async def get_pickups_by_operator(
        self, 
        operator_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PickupRequest]:
        """Obtener recolecciones por operador"""
        conditions = [PickupRequestModel.assigned_operator_id == operator_id]
        
        if start_date:
            conditions.append(PickupRequestModel.scheduled_date >= start_date)
        if end_date:
            conditions.append(PickupRequestModel.scheduled_date <= end_date)
        
        stmt = (
            select(PickupRequestModel)
            .options(selectinload(PickupRequestModel.pickup_attempts))
            .where(and_(*conditions))
            .order_by(PickupRequestModel.scheduled_date)
        )
        
        result = await self.session.execute(stmt)
        pickup_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in pickup_models]

    async def get_pickups_by_status(
        self, 
        status: str,
        limit: Optional[int] = None
    ) -> List[PickupRequest]:
        """Obtener recolecciones por estado"""
        stmt = (
            select(PickupRequestModel)
            .options(selectinload(PickupRequestModel.pickup_attempts))
            .where(PickupRequestModel.status == status)
            .order_by(PickupRequestModel.created_at.desc())
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.session.execute(stmt)
        pickup_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in pickup_models]

    async def get_overdue_pickups(self) -> List[PickupRequest]:
        """Obtener recolecciones vencidas"""
        now = datetime.now()
        
        stmt = (
            select(PickupRequestModel)
            .options(selectinload(PickupRequestModel.pickup_attempts))
            .where(
                and_(
                    PickupRequestModel.scheduled_date < now,
                    PickupRequestModel.status.in_(['confirmed', 'in_progress'])
                )
            )
        )
        
        result = await self.session.execute(stmt)
        pickup_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in pickup_models]

    async def create_pickup_route(self, pickup_route: PickupRoute) -> PickupRoute:
        """Crear nueva ruta de recolecciones"""
        route_model = PickupRouteModel(
            route_id=pickup_route.route_id,
            operator_id=pickup_route.operator_id,
            scheduled_date=pickup_route.scheduled_date,
            status=pickup_route.status,
            started_at=pickup_route.started_at,
            completed_at=pickup_route.completed_at,
            total_distance_km=pickup_route.total_distance_km,
            estimated_duration_hours=pickup_route.estimated_duration_hours
        )
        
        self.session.add(route_model)
        await self.session.commit()
        await self.session.refresh(route_model)
        
        return pickup_route

    async def get_pickup_route(self, route_id: str) -> Optional[PickupRoute]:
        """Obtener ruta por ID"""
        stmt = select(PickupRouteModel).where(PickupRouteModel.route_id == route_id)
        result = await self.session.execute(stmt)
        route_model = result.scalar_one_or_none()
        
        if route_model:
            return self._route_model_to_entity(route_model)
        return None

    async def get_routes_by_operator(
        self, 
        operator_id: str,
        date: Optional[datetime] = None
    ) -> List[PickupRoute]:
        """Obtener rutas por operador"""
        conditions = [PickupRouteModel.operator_id == operator_id]
        
        if date:
            conditions.append(PickupRouteModel.scheduled_date == date.date())
        
        stmt = (
            select(PickupRouteModel)
            .where(and_(*conditions))
            .order_by(PickupRouteModel.scheduled_date.desc())
        )
        
        result = await self.session.execute(stmt)
        route_models = result.scalars().all()
        
        return [self._route_model_to_entity(model) for model in route_models]

    async def delete_pickup_request(self, pickup_id: str) -> bool:
        """Eliminar solicitud de recolección"""
        stmt = delete(PickupRequestModel).where(PickupRequestModel.pickup_id == pickup_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    async def search_pickups(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[PickupRequest]:
        """Buscar recolecciones con filtros"""
        conditions = []
        
        if filters.get('customer_id'):
            conditions.append(PickupRequestModel.customer_id == filters['customer_id'])
        
        if filters.get('status'):
            conditions.append(PickupRequestModel.status == filters['status'])
        
        if filters.get('operator_id'):
            conditions.append(PickupRequestModel.assigned_operator_id == filters['operator_id'])
        
        if filters.get('start_date'):
            conditions.append(PickupRequestModel.created_at >= filters['start_date'])
        
        if filters.get('end_date'):
            conditions.append(PickupRequestModel.created_at <= filters['end_date'])
        
        if filters.get('pickup_type'):
            conditions.append(PickupRequestModel.pickup_type == filters['pickup_type'])
        
        if filters.get('priority'):
            conditions.append(PickupRequestModel.priority == filters['priority'])
        
        stmt = (
            select(PickupRequestModel)
            .options(selectinload(PickupRequestModel.pickup_attempts))
            .where(and_(*conditions) if conditions else True)
            .order_by(PickupRequestModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        pickup_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in pickup_models]

    def _model_to_entity(self, model: PickupRequestModel) -> PickupRequest:
        """Convertir modelo a entidad"""
        from src.domain.entities.pickup import PickupStatus, PickupType
        
        pickup_request = PickupRequest(
            pickup_id=model.pickup_id,
            guide_id=GuideId(model.guide_id),
            customer_id=CustomerId(model.customer_id),
            pickup_type=PickupType(model.pickup_type),
            pickup_address=model.pickup_address,
            contact_name=model.contact_name,
            contact_phone=model.contact_phone
        )
        
        # Asignar propiedades adicionales
        pickup_request.status = PickupStatus(model.status)
        pickup_request.created_at = model.created_at
        pickup_request.updated_at = model.updated_at
        pickup_request.scheduled_date = model.scheduled_date
        pickup_request.assigned_operator_id = model.assigned_operator_id
        pickup_request.assigned_point_id = model.assigned_point_id
        pickup_request.special_instructions = model.special_instructions
        pickup_request.completed_at = model.completed_at
        pickup_request.max_attempts = model.max_attempts
        pickup_request.priority = model.priority
        pickup_request.estimated_packages = model.estimated_packages
        pickup_request.total_weight_kg = model.total_weight_kg
        pickup_request.requires_special_handling = model.requires_special_handling
        
        # Convertir intentos de recolección
        if hasattr(model, 'pickup_attempts') and model.pickup_attempts:
            from src.domain.entities.pickup import PickupAttempt
            pickup_request.pickup_attempts = [
                PickupAttempt(
                    attempt_id=attempt.attempt_id,
                    attempted_at=attempt.attempted_at,
                    status=attempt.status,
                    notes=attempt.notes,
                    attempted_by=attempt.attempted_by,
                    failure_reason=attempt.failure_reason,
                    evidence_urls=attempt.evidence_urls.split(',') if attempt.evidence_urls else []
                )
                for attempt in model.pickup_attempts
            ]
        
        return pickup_request

    def _route_model_to_entity(self, model: PickupRouteModel) -> PickupRoute:
        """Convertir modelo de ruta a entidad"""
        pickup_route = PickupRoute(
            route_id=model.route_id,
            operator_id=model.operator_id,
            scheduled_date=model.scheduled_date
        )
        
        pickup_route.status = model.status
        pickup_route.started_at = model.started_at
        pickup_route.completed_at = model.completed_at
        pickup_route.total_distance_km = model.total_distance_km
        pickup_route.estimated_duration_hours = model.estimated_duration_hours
        
        return pickup_route