from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_session
from src.infrastructure.repositories.pickup_repository import PickupRepository
from src.domain.services.pickup_service import PickupService
from src.domain.entities.pickup import PickupStatus, PickupType
from src.domain.entities.customer import Customer, CustomerType
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.infrastructure.logging.log_messages import LogCodes, QuantyLogger
from src.api.schemas.pickup_schemas import (
    PickupRequestCreate, PickupSchedule, PickupReschedule, PickupCancel,
    PickupComplete, PickupFail, PickupRouteCreate, PickupRequestResponse,
    PickupRouteResponse, PickupMetricsResponse, PickupSummaryResponse
)

router = APIRouter()
logger = QuantyLogger()

@router.post("/pickups", response_model=PickupRequestResponse)
async def create_pickup_request(
    request: PickupRequestCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear nueva solicitud de recolección"""
    try:
        pickup_repo = PickupRepository(session)
        pickup_service = PickupService()
        
        # Crear cliente mock (en implementación real vendría del servicio de clientes)
        customer = Customer(
            customer_id=CustomerId(request.customer_id),
            name="Customer",
            email="customer@test.com",
            phone=request.contact_phone,
            customer_type=CustomerType.MEDIUM  # Por defecto
        )
        
        pickup_request = pickup_service.request_pickup(
            pickup_id=f"pickup_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            guide_id=GuideId(request.guide_id),
            customer=customer,
            pickup_address=request.pickup_address,
            contact_name=request.contact_name,
            contact_phone=request.contact_phone,
            preferred_date=request.preferred_date,
            special_instructions=request.special_instructions
        )
        
        # Guardar en repositorio
        saved_pickup = await pickup_repo.create_pickup_request(pickup_request)
        
        logger.log_info(
            LogCodes.PICKUP_CREATED,
            f"Pickup request created: {saved_pickup.pickup_id}",
            {"pickup_id": saved_pickup.pickup_id, "customer_id": request.customer_id}
        )
        
        return PickupResponse(
            pickup_id=saved_pickup.pickup_id,
            guide_id=saved_pickup.guide_id.value,
            customer_id=saved_pickup.customer_id.value,
            pickup_type=saved_pickup.pickup_type.value,
            pickup_address=saved_pickup.pickup_address,
            contact_name=saved_pickup.contact_name,
            contact_phone=saved_pickup.contact_phone,
            status=saved_pickup.status.value,
            created_at=saved_pickup.created_at,
            updated_at=saved_pickup.updated_at,
            scheduled_date=saved_pickup.scheduled_date,
            assigned_operator_id=saved_pickup.assigned_operator_id,
            assigned_point_id=saved_pickup.assigned_point_id,
            priority=saved_pickup.priority,
            estimated_packages=saved_pickup.estimated_packages,
            is_overdue=saved_pickup.is_overdue(),
            can_be_rescheduled=saved_pickup.can_be_rescheduled()
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error creating pickup request: {str(e)}",
            {"error": str(e), "customer_id": request.customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pickups/{pickup_id}", response_model=PickupResponse)
async def get_pickup_request(
    pickup_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener solicitud de recolección por ID"""
    try:
        pickup_repo = PickupRepository(session)
        pickup_request = await pickup_repo.get_pickup_request(pickup_id)
        
        if not pickup_request:
            raise HTTPException(status_code=404, detail="Pickup request not found")
        
        return PickupResponse(
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
            priority=pickup_request.priority,
            estimated_packages=pickup_request.estimated_packages,
            is_overdue=pickup_request.is_overdue(),
            can_be_rescheduled=pickup_request.can_be_rescheduled()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error retrieving pickup request: {str(e)}",
            {"error": str(e), "pickup_id": pickup_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/pickups/{pickup_id}", response_model=PickupResponse)
async def update_pickup_request(
    pickup_id: str,
    request: PickupRequestUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Actualizar solicitud de recolección"""
    try:
        pickup_repo = PickupRepository(session)
        pickup_request = await pickup_repo.get_pickup_request(pickup_id)
        
        if not pickup_request:
            raise HTTPException(status_code=404, detail="Pickup request not found")
        
        # Actualizar campos si se proporcionan
        if request.status:
            pickup_request.status = PickupStatus(request.status)
        if request.scheduled_date:
            pickup_request.scheduled_date = request.scheduled_date
        if request.assigned_operator_id:
            pickup_request.assigned_operator_id = request.assigned_operator_id
        if request.assigned_point_id:
            pickup_request.assigned_point_id = request.assigned_point_id
        if request.special_instructions:
            pickup_request.special_instructions = request.special_instructions
        if request.priority:
            pickup_request.priority = request.priority
        
        pickup_request.updated_at = datetime.now()
        
        updated_pickup = await pickup_repo.update_pickup_request(pickup_request)
        
        logger.log_info(
            LogCodes.PICKUP_UPDATED,
            f"Pickup request updated: {pickup_id}",
            {"pickup_id": pickup_id}
        )
        
        return PickupResponse(
            pickup_id=updated_pickup.pickup_id,
            guide_id=updated_pickup.guide_id.value,
            customer_id=updated_pickup.customer_id.value,
            pickup_type=updated_pickup.pickup_type.value,
            pickup_address=updated_pickup.pickup_address,
            contact_name=updated_pickup.contact_name,
            contact_phone=updated_pickup.contact_phone,
            status=updated_pickup.status.value,
            created_at=updated_pickup.created_at,
            updated_at=updated_pickup.updated_at,
            scheduled_date=updated_pickup.scheduled_date,
            assigned_operator_id=updated_pickup.assigned_operator_id,
            assigned_point_id=updated_pickup.assigned_point_id,
            priority=updated_pickup.priority,
            estimated_packages=updated_pickup.estimated_packages,
            is_overdue=updated_pickup.is_overdue(),
            can_be_rescheduled=updated_pickup.can_be_rescheduled()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error updating pickup request: {str(e)}",
            {"error": str(e), "pickup_id": pickup_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pickups/schedule")
async def schedule_pickup(
    request: PickupScheduleRequest,
    session: AsyncSession = Depends(get_session)
):
    """Programar recolección directa"""
    try:
        pickup_service = PickupService()
        
        success = pickup_service.schedule_direct_pickup(
            pickup_id=request.pickup_id,
            preferred_date=request.preferred_date,
            time_preference=request.time_preference
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to schedule pickup at requested time")
        
        logger.log_info(
            LogCodes.PICKUP_SCHEDULED,
            f"Pickup scheduled: {request.pickup_id}",
            {"pickup_id": request.pickup_id, "date": request.preferred_date.isoformat()}
        )
        
        return {"success": True, "message": "Pickup scheduled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error scheduling pickup: {str(e)}",
            {"error": str(e), "pickup_id": request.pickup_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pickups/complete")
async def complete_pickup(
    request: PickupCompletionRequest,
    session: AsyncSession = Depends(get_session)
):
    """Completar recolección"""
    try:
        pickup_service = PickupService()
        
        success = pickup_service.complete_pickup(
            pickup_id=request.pickup_id,
            operator_id=request.operator_id,
            completion_notes=request.completion_notes,
            packages_collected=request.packages_collected,
            evidence_urls=request.evidence_urls or []
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to complete pickup")
        
        logger.log_info(
            LogCodes.PICKUP_COMPLETED,
            f"Pickup completed: {request.pickup_id}",
            {"pickup_id": request.pickup_id, "operator_id": request.operator_id}
        )
        
        return {"success": True, "message": "Pickup completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error completing pickup: {str(e)}",
            {"error": str(e), "pickup_id": request.pickup_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pickups/fail")
async def fail_pickup(
    request: PickupFailureRequest,
    session: AsyncSession = Depends(get_session)
):
    """Registrar fallo en recolección"""
    try:
        pickup_service = PickupService()
        
        success = pickup_service.fail_pickup(
            pickup_id=request.pickup_id,
            operator_id=request.operator_id,
            failure_reason=request.failure_reason,
            failure_notes=request.failure_notes,
            evidence_urls=request.evidence_urls or []
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to register pickup failure")
        
        logger.log_warning(
            LogCodes.PICKUP_FAILED,
            f"Pickup failed: {request.pickup_id}",
            {"pickup_id": request.pickup_id, "operator_id": request.operator_id, "reason": request.failure_reason}
        )
        
        return {"success": True, "message": "Pickup failure registered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error registering pickup failure: {str(e)}",
            {"error": str(e), "pickup_id": request.pickup_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pickups/reschedule")
async def reschedule_pickup(
    request: PickupRescheduleRequest,
    session: AsyncSession = Depends(get_session)
):
    """Reprogramar recolección"""
    try:
        pickup_service = PickupService()
        
        success = pickup_service.reschedule_pickup(
            pickup_id=request.pickup_id,
            new_date=request.new_date,
            reschedule_reason=request.reschedule_reason,
            time_preference=request.time_preference
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to reschedule pickup")
        
        logger.log_info(
            LogCodes.PICKUP_RESCHEDULED,
            f"Pickup rescheduled: {request.pickup_id}",
            {"pickup_id": request.pickup_id, "new_date": request.new_date.isoformat()}
        )
        
        return {"success": True, "message": "Pickup rescheduled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error rescheduling pickup: {str(e)}",
            {"error": str(e), "pickup_id": request.pickup_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pickups/customer/{customer_id}", response_model=List[PickupResponse])
async def get_pickups_by_customer(
    customer_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener recolecciones por cliente"""
    try:
        pickup_repo = PickupRepository(session)
        pickups = await pickup_repo.get_pickups_by_customer(CustomerId(customer_id))
        
        return [
            PickupResponse(
                pickup_id=pickup.pickup_id,
                guide_id=pickup.guide_id.value,
                customer_id=pickup.customer_id.value,
                pickup_type=pickup.pickup_type.value,
                pickup_address=pickup.pickup_address,
                contact_name=pickup.contact_name,
                contact_phone=pickup.contact_phone,
                status=pickup.status.value,
                created_at=pickup.created_at,
                updated_at=pickup.updated_at,
                scheduled_date=pickup.scheduled_date,
                assigned_operator_id=pickup.assigned_operator_id,
                assigned_point_id=pickup.assigned_point_id,
                priority=pickup.priority,
                estimated_packages=pickup.estimated_packages,
                is_overdue=pickup.is_overdue(),
                can_be_rescheduled=pickup.can_be_rescheduled()
            )
            for pickup in pickups
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error retrieving pickups by customer: {str(e)}",
            {"error": str(e), "customer_id": customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pickups/operator/{operator_id}", response_model=List[PickupResponse])
async def get_pickups_by_operator(
    operator_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Obtener recolecciones por operador"""
    try:
        pickup_repo = PickupRepository(session)
        pickups = await pickup_repo.get_pickups_by_operator(operator_id, start_date, end_date)
        
        return [
            PickupResponse(
                pickup_id=pickup.pickup_id,
                guide_id=pickup.guide_id.value,
                customer_id=pickup.customer_id.value,
                pickup_type=pickup.pickup_type.value,
                pickup_address=pickup.pickup_address,
                contact_name=pickup.contact_name,
                contact_phone=pickup.contact_phone,
                status=pickup.status.value,
                created_at=pickup.created_at,
                updated_at=pickup.updated_at,
                scheduled_date=pickup.scheduled_date,
                assigned_operator_id=pickup.assigned_operator_id,
                assigned_point_id=pickup.assigned_point_id,
                priority=pickup.priority,
                estimated_packages=pickup.estimated_packages,
                is_overdue=pickup.is_overdue(),
                can_be_rescheduled=pickup.can_be_rescheduled()
            )
            for pickup in pickups
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error retrieving pickups by operator: {str(e)}",
            {"error": str(e), "operator_id": operator_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pickups/overdue", response_model=List[PickupResponse])
async def get_overdue_pickups(
    session: AsyncSession = Depends(get_session)
):
    """Obtener recolecciones vencidas"""
    try:
        pickup_repo = PickupRepository(session)
        pickups = await pickup_repo.get_overdue_pickups()
        
        return [
            PickupResponse(
                pickup_id=pickup.pickup_id,
                guide_id=pickup.guide_id.value,
                customer_id=pickup.customer_id.value,
                pickup_type=pickup.pickup_type.value,
                pickup_address=pickup.pickup_address,
                contact_name=pickup.contact_name,
                contact_phone=pickup.contact_phone,
                status=pickup.status.value,
                created_at=pickup.created_at,
                updated_at=pickup.updated_at,
                scheduled_date=pickup.scheduled_date,
                assigned_operator_id=pickup.assigned_operator_id,
                assigned_point_id=pickup.assigned_point_id,
                priority=pickup.priority,
                estimated_packages=pickup.estimated_packages,
                is_overdue=pickup.is_overdue(),
                can_be_rescheduled=pickup.can_be_rescheduled()
            )
            for pickup in pickups
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error retrieving overdue pickups: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pickup-routes", response_model=PickupRouteResponse)
async def create_pickup_route(
    request: PickupRouteCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear ruta de recolecciones"""
    try:
        pickup_service = PickupService()
        
        route_id = f"route_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        pickup_route = pickup_service.create_pickup_route(
            route_id=route_id,
            operator_id=request.operator_id,
            date=request.date,
            pickup_ids=request.pickup_ids
        )
        
        # Guardar en repositorio
        pickup_repo = PickupRepository(session)
        saved_route = await pickup_repo.create_pickup_route(pickup_route)
        
        logger.log_info(
            LogCodes.ROUTE_CREATED,
            f"Pickup route created: {route_id}",
            {"route_id": route_id, "operator_id": request.operator_id, "pickups": len(request.pickup_ids)}
        )
        
        route_summary = saved_route.get_route_summary()
        
        return PickupRouteResponse(
            route_id=route_summary["route_id"],
            operator_id=route_summary["operator_id"],
            scheduled_date=route_summary["scheduled_date"],
            status=route_summary["status"],
            total_pickups=route_summary["total_pickups"],
            completed_pickups=route_summary["completed_pickups"],
            failed_pickups=route_summary["failed_pickups"],
            success_rate=route_summary["success_rate"],
            estimated_duration_hours=route_summary["estimated_duration_hours"]
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error creating pickup route: {str(e)}",
            {"error": str(e), "operator_id": request.operator_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pickup-metrics", response_model=PickupMetricsResponse)
async def get_pickup_metrics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    operator_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Obtener métricas de recolecciones"""
    try:
        pickup_service = PickupService()
        
        metrics = pickup_service.get_pickup_metrics(
            start_date=start_date,
            end_date=end_date,
            operator_id=operator_id
        )
        
        return PickupMetricsResponse(**metrics)
        
    except Exception as e:
        logger.log_error(
            LogCodes.PICKUP_ERROR,
            f"Error retrieving pickup metrics: {str(e)}",
            {"error": str(e), "operator_id": operator_id}
        )
        raise HTTPException(status_code=500, detail=str(e))