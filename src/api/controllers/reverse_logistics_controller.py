from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_session
from src.infrastructure.repositories.reverse_logistics_repository import ReverseLogisticsRepository
from src.domain.services.reverse_logistics_service import ReverseLogisticsService
from src.domain.entities.reverse_logistics import ReturnReason, RefundMethod
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money
from src.infrastructure.logging.log_messages import LogCodes, QuantyLogger
from src.api.schemas.reverse_logistics_schemas import (
    ReturnRequestCreate, ReturnItemAdd, ReturnApprove, ReturnReject,
    ReturnReceive, InspectionConduct, RefundProcess, InventoryProcess,
    ReturnEligibilityCheck, ReturnPolicyUpdate, ReturnRequestResponse,
    ReturnItemResponse, InspectionReportResponse, LogisticsCenterResponse,
    ReturnPolicyResponse, ReturnAnalyticsResponse, QualityIssueResponse,
    ReturnEligibilityResponse, InventoryProcessingResponse
)

router = APIRouter()
logger = QuantyLogger()

@router.post("/return-requests", response_model=ReturnRequestResponse)
async def create_return_request(
    request: ReturnRequestCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear nueva solicitud de devolución"""
    try:
        returns_service = ReverseLogisticsService()
        
        # Crear cliente mock
        from src.domain.entities.customer import Customer, CustomerType
        customer = Customer(
            customer_id=CustomerId(request.customer_id),
            name="Customer",
            email="customer@test.com",
            phone="123456789",
            customer_type=CustomerType.SMALL
        )
        
        return_request = returns_service.create_return_request(
            original_guide_id=GuideId(request.original_guide_id),
            customer=customer,
            return_reason=ReturnReason(request.return_reason),
            customer_comments=request.customer_comments,
            contact_info=request.contact_info
        )
        
        # Guardar en repositorio
        returns_repo = ReverseLogisticsRepository(session)
        saved_return = await returns_repo.create_return_request(return_request)
        
        logger.log_info(
            LogCodes.RETURN_REQUEST_CREATED,
            f"Return request created: {return_request.return_id}",
            {"return_id": return_request.return_id, "customer_id": request.customer_id}
        )
        
        return ReturnRequestResponse(
            return_id=saved_return.return_id,
            original_guide_id=saved_return.original_guide_id.value,
            customer_id=saved_return.customer_id.value,
            return_reason=saved_return.return_reason.value,
            status=saved_return.status.value,
            created_at=saved_return.created_at,
            expected_return_value={
                "amount": saved_return.expected_return_value.amount,
                "currency": saved_return.expected_return_value.currency
            },
            items_count=len(saved_return.return_items),
            is_within_deadline=saved_return.is_within_deadline(),
            refund_processed=saved_return.refund_processed_at is not None
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error creating return request: {str(e)}",
            {"error": str(e), "customer_id": request.customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/items")
async def add_return_item(
    return_id: str,
    request: ReturnItemAdd,
    session: AsyncSession = Depends(get_session)
):
    """Agregar item a devolución"""
    try:
        returns_service = ReverseLogisticsService()
        
        success = returns_service.add_item_to_return(
            return_id=return_id,
            product_id=request.product_id,
            product_name=request.product_name,
            quantity=request.quantity,
            unit_price=Money(request.unit_price_amount, request.unit_price_currency),
            item_reason=ReturnReason(request.item_reason),
            condition_description=request.condition_description,
            photos_urls=request.photos_urls
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to add item to return")
        
        logger.log_info(
            LogCodes.RETURN_ITEM_ADDED,
            f"Return item added: {request.product_id}",
            {"return_id": return_id, "product_id": request.product_id}
        )
        
        return {"success": True, "message": "Item added to return successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error adding return item: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/eligibility")
async def check_return_eligibility(
    return_id: str,
    request: ReturnEligibilityCheck,
    session: AsyncSession = Depends(get_session)
):
    """Evaluar elegibilidad de devolución"""
    try:
        returns_service = ReverseLogisticsService()
        
        eligibility = returns_service.evaluate_return_eligibility(
            return_id=return_id,
            order_date=request.order_date,
            delivery_date=request.delivery_date,
            product_categories=request.product_categories
        )
        
        return eligibility
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error checking return eligibility: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/approve")
async def approve_return_request(
    return_id: str,
    request: ReturnApprove,
    session: AsyncSession = Depends(get_session)
):
    """Aprobar solicitud de devolución"""
    try:
        returns_service = ReverseLogisticsService()
        
        success = returns_service.approve_return(
            return_id=return_id,
            approved_by=request.approved_by,
            pickup_date=request.pickup_date
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to approve return request")
        
        logger.log_info(
            LogCodes.RETURN_REQUEST_APPROVED,
            f"Return request approved: {return_id}",
            {"return_id": return_id, "approved_by": request.approved_by}
        )
        
        return {"success": True, "message": "Return request approved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error approving return request: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/reject")
async def reject_return_request(
    return_id: str,
    request: ReturnReject,
    session: AsyncSession = Depends(get_session)
):
    """Rechazar solicitud de devolución"""
    try:
        returns_service = ReverseLogisticsService()
        
        success = returns_service.reject_return(
            return_id=return_id,
            rejection_reason=request.rejection_reason,
            rejected_by=request.rejected_by
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to reject return request")
        
        logger.log_warning(
            LogCodes.RETURN_REQUEST_REJECTED,
            f"Return request rejected: {return_id}",
            {"return_id": return_id, "reason": request.rejection_reason}
        )
        
        return {"success": True, "message": "Return request rejected"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error rejecting return request: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/receive")
async def receive_return(
    return_id: str,
    request: ReturnReceive,
    session: AsyncSession = Depends(get_session)
):
    """Recibir devolución en centro logístico"""
    try:
        returns_service = ReverseLogisticsService()
        
        success = returns_service.receive_return(
            return_id=return_id,
            center_id=request.center_id,
            received_by=request.received_by,
            packages_count=request.packages_count,
            initial_condition=request.initial_condition
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Unable to receive return")
        
        logger.log_info(
            LogCodes.RETURN_RECEIVED,
            f"Return received: {return_id}",
            {"return_id": return_id, "center_id": request.center_id}
        )
        
        return {"success": True, "message": "Return received successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error receiving return: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/inspect", response_model=InspectionReportResponse)
async def conduct_inspection(
    return_id: str,
    request: InspectionConduct,
    session: AsyncSession = Depends(get_session)
):
    """Realizar inspección de items devueltos"""
    try:
        returns_service = ReverseLogisticsService()
        
        inspection_report = returns_service.conduct_inspection(
            return_id=return_id,
            inspector_id=request.inspector_id,
            item_inspections=request.item_inspections
        )
        
        logger.log_info(
            LogCodes.RETURN_INSPECTED,
            f"Return inspection completed: {return_id}",
            {"return_id": return_id, "inspector": request.inspector_id}
        )
        
        return InspectionReportResponse(
            inspection_id=inspection_report.inspection_id,
            inspector_id=inspection_report.inspector_id,
            inspection_date=inspection_report.inspection_date,
            overall_result=inspection_report.overall_result.value,
            approved_items=len([i for i in inspection_report.items_inspected if i.get("result") == "approved"]),
            rejected_items=len([i for i in inspection_report.items_inspected if i.get("result") == "rejected"]),
            refund_amount={
                "amount": inspection_report.refund_amount.amount,
                "currency": inspection_report.refund_amount.currency
            }
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error conducting inspection: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/refund")
async def process_refund(
    return_id: str,
    request: RefundProcess,
    session: AsyncSession = Depends(get_session)
):
    """Procesar reembolso de devolución"""
    try:
        returns_service = ReverseLogisticsService()
        
        transaction_reference = returns_service.process_refund(
            return_id=return_id,
            refund_method=RefundMethod(request.refund_method),
            processed_by=request.processed_by
        )
        
        logger.log_info(
            LogCodes.RETURN_REFUNDED,
            f"Return refund processed: {return_id}",
            {"return_id": return_id, "reference": transaction_reference}
        )
        
        return {
            "success": True,
            "transaction_reference": transaction_reference,
            "message": "Refund processed successfully"
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error processing refund: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/return-requests/{return_id}/process-inventory")
async def process_returned_inventory(
    return_id: str,
    request: InventoryProcess,
    session: AsyncSession = Depends(get_session)
):
    """Procesar inventario devuelto"""
    try:
        returns_service = ReverseLogisticsService()
        
        processing_summary = returns_service.process_returned_inventory(
            return_id=return_id,
            center_id=request.center_id,
            processed_by=request.processed_by
        )
        
        logger.log_info(
            LogCodes.RETURN_INVENTORY_PROCESSED,
            f"Return inventory processed: {return_id}",
            {"return_id": return_id, "restocked": processing_summary["restocked"]}
        )
        
        return {
            "success": True,
            "processing_summary": processing_summary,
            "message": "Inventory processed successfully"
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error processing returned inventory: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/return-requests/{return_id}", response_model=ReturnRequestResponse)
async def get_return_request(
    return_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener solicitud de devolución por ID"""
    try:
        returns_repo = ReverseLogisticsRepository(session)
        return_request = await returns_repo.get_return_request(return_id)
        
        if not return_request:
            raise HTTPException(status_code=404, detail="Return request not found")
        
        return ReturnRequestResponse(
            return_id=return_request.return_id,
            original_guide_id=return_request.original_guide_id.value,
            customer_id=return_request.customer_id.value,
            return_reason=return_request.return_reason.value,
            status=return_request.status.value,
            created_at=return_request.created_at,
            expected_return_value={
                "amount": return_request.expected_return_value.amount,
                "currency": return_request.expected_return_value.currency
            },
            items_count=len(return_request.return_items),
            is_within_deadline=return_request.is_within_deadline(),
            refund_processed=return_request.refund_processed_at is not None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving return request: {str(e)}",
            {"error": str(e), "return_id": return_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/return-requests/customer/{customer_id}", response_model=List[ReturnRequestResponse])
async def get_returns_by_customer(
    customer_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener devoluciones por cliente"""
    try:
        returns_repo = ReverseLogisticsRepository(session)
        returns = await returns_repo.get_returns_by_customer(CustomerId(customer_id))
        
        return [
            ReturnRequestResponse(
                return_id=return_request.return_id,
                original_guide_id=return_request.original_guide_id.value,
                customer_id=return_request.customer_id.value,
                return_reason=return_request.return_reason.value,
                status=return_request.status.value,
                created_at=return_request.created_at,
                expected_return_value={
                    "amount": return_request.expected_return_value.amount,
                    "currency": return_request.expected_return_value.currency
                },
                items_count=len(return_request.return_items),
                is_within_deadline=return_request.is_within_deadline(),
                refund_processed=return_request.refund_processed_at is not None
            )
            for return_request in returns
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving returns by customer: {str(e)}",
            {"error": str(e), "customer_id": customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/return-requests/status/{status}", response_model=List[ReturnRequestResponse])
async def get_returns_by_status(
    status: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener devoluciones por estado"""
    try:
        returns_repo = ReverseLogisticsRepository(session)
        returns = await returns_repo.get_returns_by_status(status)
        
        return [
            ReturnRequestResponse(
                return_id=return_request.return_id,
                original_guide_id=return_request.original_guide_id.value,
                customer_id=return_request.customer_id.value,
                return_reason=return_request.return_reason.value,
                status=return_request.status.value,
                created_at=return_request.created_at,
                expected_return_value={
                    "amount": return_request.expected_return_value.amount,
                    "currency": return_request.expected_return_value.currency
                },
                items_count=len(return_request.return_items),
                is_within_deadline=return_request.is_within_deadline(),
                refund_processed=return_request.refund_processed_at is not None
            )
            for return_request in returns
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving returns by status: {str(e)}",
            {"error": str(e), "status": status}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/return-requests/overdue", response_model=List[ReturnRequestResponse])
async def get_overdue_returns(
    session: AsyncSession = Depends(get_session)
):
    """Obtener devoluciones vencidas"""
    try:
        returns_repo = ReverseLogisticsRepository(session)
        returns = await returns_repo.get_overdue_returns()
        
        return [
            ReturnRequestResponse(
                return_id=return_request.return_id,
                original_guide_id=return_request.original_guide_id.value,
                customer_id=return_request.customer_id.value,
                return_reason=return_request.return_reason.value,
                status=return_request.status.value,
                created_at=return_request.created_at,
                expected_return_value={
                    "amount": return_request.expected_return_value.amount,
                    "currency": return_request.expected_return_value.currency
                },
                items_count=len(return_request.return_items),
                is_within_deadline=return_request.is_within_deadline(),
                refund_processed=return_request.refund_processed_at is not None
            )
            for return_request in returns
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving overdue returns: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logistics-centers", response_model=List[LogisticsCenterResponse])
async def get_logistics_centers(
    session: AsyncSession = Depends(get_session)
):
    """Obtener centros logísticos activos"""
    try:
        returns_repo = ReverseLogisticsRepository(session)
        centers = await returns_repo.get_active_logistics_centers()
        
        return [
            LogisticsCenterResponse(
                center_id=center.center_id,
                name=center.name,
                address=center.address,
                capacity=center.capacity,
                current_inventory_count=sum(center.current_inventory.values()),
                capacity_utilization=(sum(center.current_inventory.values()) / center.capacity * 100) if center.capacity > 0 else 0,
                processing_queue_size=len(center.processing_queue),
                is_active=center.is_active
            )
            for center in centers
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving logistics centers: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logistics-centers/{center_id}/status")
async def get_center_status(
    center_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener estado del centro logístico"""
    try:
        returns_service = ReverseLogisticsService()
        
        center_status = returns_service.get_center_status(center_id)
        
        return center_status
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving center status: {str(e)}",
            {"error": str(e), "center_id": center_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/return-analytics", response_model=ReturnAnalyticsResponse)
async def get_return_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    customer_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Obtener analytics de devoluciones"""
    try:
        returns_service = ReverseLogisticsService()
        
        customer_filter = CustomerId(customer_id) if customer_id else None
        
        analytics = returns_service.get_return_analytics(
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_filter
        )
        
        return ReturnAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving return analytics: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quality-issues/{product_id}")
async def detect_quality_issues(
    product_id: str,
    lookback_days: int = Query(30),
    session: AsyncSession = Depends(get_session)
):
    """Detectar problemas de calidad basado en patrones de devolución"""
    try:
        returns_service = ReverseLogisticsService()
        
        quality_issue = returns_service.detect_quality_issues(
            product_id=product_id,
            lookback_days=lookback_days
        )
        
        if not quality_issue:
            return {"quality_issue_detected": False, "message": "No quality issues detected"}
        
        return {
            "quality_issue_detected": True,
            "quality_issue": QualityIssueResponse(**quality_issue)
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error detecting quality issues: {str(e)}",
            {"error": str(e), "product_id": product_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/return-policy", response_model=ReturnPolicyResponse)
async def get_active_return_policy(
    session: AsyncSession = Depends(get_session)
):
    """Obtener política de devoluciones activa"""
    try:
        returns_repo = ReverseLogisticsRepository(session)
        policy = await returns_repo.get_active_return_policy()
        
        if not policy:
            raise HTTPException(status_code=404, detail="No active return policy found")
        
        return ReturnPolicyResponse(
            policy_id=policy.policy_id,
            name=policy.name,
            description=policy.description,
            is_active=policy.is_active,
            return_window_days=policy.return_window_days,
            eligible_reasons=[reason.value for reason in policy.eligible_reasons],
            excluded_categories=policy.excluded_categories,
            restocking_fee_percentage=policy.restocking_fee_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.RETURN_REQUEST_ERROR,
            f"Error retrieving return policy: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))