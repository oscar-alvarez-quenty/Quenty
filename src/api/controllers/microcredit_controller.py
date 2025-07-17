from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_session
from src.infrastructure.repositories.microcredit_repository import MicrocreditRepository
from src.domain.services.microcredit_service import MicrocreditService
from src.domain.entities.microcredit import ApplicationStatus, MicrocreditStatus, RefundMethod
from src.domain.entities.customer import Customer, CustomerType
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money
from src.infrastructure.logging.log_messages import LogCodes, QuantyLogger
from src.api.schemas.microcredit_schemas import (
    MicrocreditApplicationCreate, ApplicationEvaluate, ApplicationApprove,
    ApplicationReject, MicrocreditDisburse, PaymentProcess, CreditLimitUpdate,
    MicrocreditApplicationResponse, MicrocreditResponse, CreditProfileResponse,
    PaymentResponse, CreditScoringResponse, PaymentScheduleResponse,
    MicrocreditAnalyticsResponse
)

router = APIRouter()
logger = QuantyLogger()

@router.post("/microcredit-applications", response_model=MicrocreditApplicationResponse)
async def submit_microcredit_application(
    request: MicrocreditApplicationCreate,
    session: AsyncSession = Depends(get_session)
):
    """Enviar solicitud de microcrédito"""
    try:
        microcredit_service = MicrocreditService()
        
        # Crear cliente mock
        customer = Customer(
            customer_id=CustomerId(request.customer_id),
            name="Customer",
            email="customer@test.com",
            phone="123456789",
            customer_type=CustomerType.SMALL
        )
        
        monthly_income = None
        if request.monthly_income_amount and request.monthly_income_currency:
            monthly_income = Money(request.monthly_income_amount, request.monthly_income_currency)
        
        application = microcredit_service.submit_application(
            customer=customer,
            requested_amount=Money(request.requested_amount, request.requested_currency),
            purpose=request.purpose,
            monthly_income=monthly_income,
            employment_type=request.employment_type,
            business_description=request.business_description
        )
        
        # Guardar en repositorio
        microcredit_repo = MicrocreditRepository(session)
        saved_application = await microcredit_repo.create_application(application)
        
        logger.log_info(
            LogCodes.MICROCREDIT_APPLICATION_SUBMITTED,
            f"Microcredit application submitted: {application.application_id}",
            {"application_id": application.application_id, "customer_id": request.customer_id}
        )
        
        return MicrocreditApplicationResponse(
            application_id=saved_application.application_id,
            customer_id=saved_application.customer_id.value,
            requested_amount={
                "amount": saved_application.requested_amount.amount,
                "currency": saved_application.requested_amount.currency
            },
            purpose=saved_application.purpose,
            status=saved_application.status.value,
            created_at=saved_application.created_at,
            credit_score=saved_application.credit_score,
            risk_assessment=saved_application.risk_assessment,
            rejection_reasons=saved_application.rejection_reasons
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_APPLICATION_ERROR,
            f"Error submitting microcredit application: {str(e)}",
            {"error": str(e), "customer_id": request.customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/microcredit-applications/{application_id}/evaluate", response_model=CreditScoringResponse)
async def evaluate_microcredit_application(
    application_id: str,
    request: ApplicationEvaluate,
    session: AsyncSession = Depends(get_session)
):
    """Evaluar solicitud de microcrédito"""
    try:
        microcredit_service = MicrocreditService()
        
        # Crear cliente mock
        customer = Customer(
            customer_id=CustomerId("customer_id"),
            name="Customer",
            email="customer@test.com",
            phone="123456789",
            customer_type=CustomerType.SMALL
        )
        
        scoring_result = microcredit_service.evaluate_application(
            application_id=application_id,
            customer=customer
        )
        
        logger.log_info(
            LogCodes.MICROCREDIT_APPLICATION_EVALUATED,
            f"Microcredit application evaluated: {application_id}",
            {"application_id": application_id, "score": scoring_result["credit_score"]}
        )
        
        return CreditScoringResponse(
            application_id=application_id,
            credit_score=scoring_result["credit_score"],
            risk_level=scoring_result["risk_level"],
            recommendation=scoring_result["recommendation"],
            scoring_factors=scoring_result["scoring_factors"],
            model_version=scoring_result["model_version"]
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_APPLICATION_ERROR,
            f"Error evaluating microcredit application: {str(e)}",
            {"error": str(e), "application_id": application_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/microcredit-applications/{application_id}/approve", response_model=MicrocreditResponse)
async def approve_microcredit_application(
    application_id: str,
    request: ApplicationApprove,
    session: AsyncSession = Depends(get_session)
):
    """Aprobar solicitud de microcrédito"""
    try:
        microcredit_service = MicrocreditService()
        
        microcredit = microcredit_service.approve_application(
            application_id=application_id,
            approved_amount=Money(request.approved_amount, request.approved_currency),
            interest_rate=request.interest_rate,
            term_months=request.term_months,
            approved_by=request.approved_by
        )
        
        # Guardar en repositorio
        microcredit_repo = MicrocreditRepository(session)
        saved_microcredit = await microcredit_repo.create_microcredit(microcredit)
        
        logger.log_info(
            LogCodes.MICROCREDIT_APPLICATION_APPROVED,
            f"Microcredit application approved: {application_id}",
            {"application_id": application_id, "microcredit_id": microcredit.microcredit_id}
        )
        
        return MicrocreditResponse(
            microcredit_id=saved_microcredit.microcredit_id,
            customer_id=saved_microcredit.customer_id.value,
            principal_amount={
                "amount": saved_microcredit.principal_amount.amount,
                "currency": saved_microcredit.principal_amount.currency
            },
            interest_rate=saved_microcredit.interest_rate,
            term_months=saved_microcredit.term_months,
            status=saved_microcredit.status.value,
            created_at=saved_microcredit.created_at,
            disbursement_date=saved_microcredit.disbursement_date,
            outstanding_balance={
                "amount": saved_microcredit.outstanding_balance.amount,
                "currency": saved_microcredit.outstanding_balance.currency
            },
            total_paid={
                "amount": saved_microcredit.total_paid.amount,
                "currency": saved_microcredit.total_paid.currency
            },
            payments_count=len(saved_microcredit.payments)
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_APPLICATION_ERROR,
            f"Error approving microcredit application: {str(e)}",
            {"error": str(e), "application_id": application_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/microcredit-applications/{application_id}/reject")
async def reject_microcredit_application(
    application_id: str,
    request: ApplicationReject,
    session: AsyncSession = Depends(get_session)
):
    """Rechazar solicitud de microcrédito"""
    try:
        microcredit_service = MicrocreditService()
        
        microcredit_service.reject_application(
            application_id=application_id,
            rejection_reasons=request.rejection_reasons,
            rejected_by=request.rejected_by
        )
        
        logger.log_warning(
            LogCodes.MICROCREDIT_APPLICATION_REJECTED,
            f"Microcredit application rejected: {application_id}",
            {"application_id": application_id, "reasons": request.rejection_reasons}
        )
        
        return {"success": True, "message": "Application rejected successfully"}
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_APPLICATION_ERROR,
            f"Error rejecting microcredit application: {str(e)}",
            {"error": str(e), "application_id": application_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/microcredits/{microcredit_id}/disburse")
async def disburse_microcredit(
    microcredit_id: str,
    request: MicrocreditDisburse,
    session: AsyncSession = Depends(get_session)
):
    """Desembolsar microcrédito"""
    try:
        microcredit_service = MicrocreditService()
        
        reference_number = microcredit_service.disburse_microcredit(
            microcredit_id=microcredit_id,
            disbursement_method=request.disbursement_method
        )
        
        logger.log_info(
            LogCodes.MICROCREDIT_DISBURSED,
            f"Microcredit disbursed: {microcredit_id}",
            {"microcredit_id": microcredit_id, "reference": reference_number}
        )
        
        return {
            "success": True,
            "reference_number": reference_number,
            "message": "Microcredit disbursed successfully"
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_DISBURSEMENT_ERROR,
            f"Error disbursing microcredit: {str(e)}",
            {"error": str(e), "microcredit_id": microcredit_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/microcredits/{microcredit_id}/payments", response_model=PaymentResponse)
async def process_microcredit_payment(
    microcredit_id: str,
    request: PaymentProcess,
    session: AsyncSession = Depends(get_session)
):
    """Procesar pago de microcrédito"""
    try:
        microcredit_service = MicrocreditService()
        
        payment = microcredit_service.process_payment(
            microcredit_id=microcredit_id,
            payment_amount=Money(request.payment_amount, request.payment_currency),
            payment_method=request.payment_method,
            reference_number=request.reference_number
        )
        
        # Guardar en repositorio
        microcredit_repo = MicrocreditRepository(session)
        saved_payment = await microcredit_repo.create_payment(payment)
        
        logger.log_info(
            LogCodes.MICROCREDIT_PAYMENT_PROCESSED,
            f"Microcredit payment processed: {payment.payment_id}",
            {"payment_id": payment.payment_id, "microcredit_id": microcredit_id}
        )
        
        return PaymentResponse(
            payment_id=saved_payment.payment_id,
            microcredit_id=saved_payment.microcredit_id,
            amount={
                "amount": saved_payment.amount.amount,
                "currency": saved_payment.amount.currency
            },
            payment_date=saved_payment.payment_date,
            payment_method=saved_payment.payment_method,
            status=saved_payment.status.value,
            is_late_payment=saved_payment.is_late_payment,
            days_late=saved_payment.days_late
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_PAYMENT_ERROR,
            f"Error processing microcredit payment: {str(e)}",
            {"error": str(e), "microcredit_id": microcredit_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/microcredit-applications/{application_id}", response_model=MicrocreditApplicationResponse)
async def get_microcredit_application(
    application_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener solicitud de microcrédito por ID"""
    try:
        microcredit_repo = MicrocreditRepository(session)
        application = await microcredit_repo.get_application(application_id)
        
        if not application:
            raise HTTPException(status_code=404, detail="Microcredit application not found")
        
        return MicrocreditApplicationResponse(
            application_id=application.application_id,
            customer_id=application.customer_id.value,
            requested_amount={
                "amount": application.requested_amount.amount,
                "currency": application.requested_amount.currency
            },
            purpose=application.purpose,
            status=application.status.value,
            created_at=application.created_at,
            credit_score=application.credit_score,
            risk_assessment=application.risk_assessment,
            rejection_reasons=application.rejection_reasons
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_APPLICATION_ERROR,
            f"Error retrieving microcredit application: {str(e)}",
            {"error": str(e), "application_id": application_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/microcredits/{microcredit_id}", response_model=MicrocreditResponse)
async def get_microcredit(
    microcredit_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener microcrédito por ID"""
    try:
        microcredit_repo = MicrocreditRepository(session)
        microcredit = await microcredit_repo.get_microcredit(microcredit_id)
        
        if not microcredit:
            raise HTTPException(status_code=404, detail="Microcredit not found")
        
        return MicrocreditResponse(
            microcredit_id=microcredit.microcredit_id,
            customer_id=microcredit.customer_id.value,
            principal_amount={
                "amount": microcredit.principal_amount.amount,
                "currency": microcredit.principal_amount.currency
            },
            interest_rate=microcredit.interest_rate,
            term_months=microcredit.term_months,
            status=microcredit.status.value,
            created_at=microcredit.created_at,
            disbursement_date=microcredit.disbursement_date,
            outstanding_balance={
                "amount": microcredit.outstanding_balance.amount,
                "currency": microcredit.outstanding_balance.currency
            },
            total_paid={
                "amount": microcredit.total_paid.amount,
                "currency": microcredit.total_paid.currency
            },
            payments_count=len(microcredit.payments)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_ERROR,
            f"Error retrieving microcredit: {str(e)}",
            {"error": str(e), "microcredit_id": microcredit_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}/credit-profile", response_model=CreditProfileResponse)
async def get_customer_credit_profile(
    customer_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener perfil crediticio del cliente"""
    try:
        microcredit_repo = MicrocreditRepository(session)
        profile = await microcredit_repo.get_credit_profile(CustomerId(customer_id))
        
        if not profile:
            raise HTTPException(status_code=404, detail="Credit profile not found")
        
        return CreditProfileResponse(
            customer_id=profile.customer_id.value,
            credit_score=profile.credit_score,
            credit_limit={
                "amount": profile.credit_limit.amount,
                "currency": profile.credit_limit.currency
            },
            current_debt={
                "amount": profile.current_debt.amount,
                "currency": profile.current_debt.currency
            },
            payment_history_score=profile.payment_history_score,
            risk_category=profile.risk_category,
            created_at=profile.created_at,
            last_updated_score=profile.last_updated_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_ERROR,
            f"Error retrieving credit profile: {str(e)}",
            {"error": str(e), "customer_id": customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}/microcredits", response_model=List[MicrocreditResponse])
async def get_customer_microcredits(
    customer_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener microcréditos por cliente"""
    try:
        microcredit_repo = MicrocreditRepository(session)
        microcredits = await microcredit_repo.get_microcredits_by_customer(CustomerId(customer_id))
        
        return [
            MicrocreditResponse(
                microcredit_id=microcredit.microcredit_id,
                customer_id=microcredit.customer_id.value,
                principal_amount={
                    "amount": microcredit.principal_amount.amount,
                    "currency": microcredit.principal_amount.currency
                },
                interest_rate=microcredit.interest_rate,
                term_months=microcredit.term_months,
                status=microcredit.status.value,
                created_at=microcredit.created_at,
                disbursement_date=microcredit.disbursement_date,
                outstanding_balance={
                    "amount": microcredit.outstanding_balance.amount,
                    "currency": microcredit.outstanding_balance.currency
                },
                total_paid={
                    "amount": microcredit.total_paid.amount,
                    "currency": microcredit.total_paid.currency
                },
                payments_count=len(microcredit.payments)
            )
            for microcredit in microcredits
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_ERROR,
            f"Error retrieving customer microcredits: {str(e)}",
            {"error": str(e), "customer_id": customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/microcredits/{microcredit_id}/payments", response_model=List[PaymentResponse])
async def get_microcredit_payments(
    microcredit_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener pagos de microcrédito"""
    try:
        microcredit_repo = MicrocreditRepository(session)
        payments = await microcredit_repo.get_payments_by_microcredit(microcredit_id)
        
        return [
            PaymentResponse(
                payment_id=payment.payment_id,
                microcredit_id=payment.microcredit_id,
                amount={
                    "amount": payment.amount.amount,
                    "currency": payment.amount.currency
                },
                payment_date=payment.payment_date,
                payment_method=payment.payment_method,
                status=payment.status.value,
                is_late_payment=payment.is_late_payment,
                days_late=payment.days_late
            )
            for payment in payments
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_ERROR,
            f"Error retrieving microcredit payments: {str(e)}",
            {"error": str(e), "microcredit_id": microcredit_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/microcredits/overdue", response_model=List[MicrocreditResponse])
async def get_overdue_microcredits(
    session: AsyncSession = Depends(get_session)
):
    """Obtener microcréditos vencidos"""
    try:
        microcredit_repo = MicrocreditRepository(session)
        microcredits = await microcredit_repo.get_overdue_microcredits()
        
        return [
            MicrocreditResponse(
                microcredit_id=microcredit.microcredit_id,
                customer_id=microcredit.customer_id.value,
                principal_amount={
                    "amount": microcredit.principal_amount.amount,
                    "currency": microcredit.principal_amount.currency
                },
                interest_rate=microcredit.interest_rate,
                term_months=microcredit.term_months,
                status=microcredit.status.value,
                created_at=microcredit.created_at,
                disbursement_date=microcredit.disbursement_date,
                outstanding_balance={
                    "amount": microcredit.outstanding_balance.amount,
                    "currency": microcredit.outstanding_balance.currency
                },
                total_paid={
                    "amount": microcredit.total_paid.amount,
                    "currency": microcredit.total_paid.currency
                },
                payments_count=len(microcredit.payments)
            )
            for microcredit in microcredits
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_ERROR,
            f"Error retrieving overdue microcredits: {str(e)}",
            {"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/customers/{customer_id}/credit-limit")
async def update_customer_credit_limit(
    customer_id: str,
    request: CreditLimitUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Actualizar límite de crédito del cliente"""
    try:
        microcredit_service = MicrocreditService()
        
        microcredit_service.update_credit_limit(
            customer_id=CustomerId(customer_id),
            new_limit=Money(request.new_limit_amount, request.new_limit_currency),
            reason=request.reason,
            approved_by=request.approved_by
        )
        
        logger.log_info(
            LogCodes.CREDIT_LIMIT_UPDATED,
            f"Credit limit updated for customer: {customer_id}",
            {"customer_id": customer_id, "new_limit": request.new_limit_amount}
        )
        
        return {"success": True, "message": "Credit limit updated successfully"}
        
    except Exception as e:
        logger.log_error(
            LogCodes.MICROCREDIT_ERROR,
            f"Error updating credit limit: {str(e)}",
            {"error": str(e), "customer_id": customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))