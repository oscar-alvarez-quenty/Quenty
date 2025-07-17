from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_session
from src.infrastructure.repositories.international_shipping_repository import InternationalShippingRepository
from src.domain.services.international_shipping_service import InternationalShippingService
from src.domain.entities.international_shipping import DocumentType, KYCStatus, CustomsStatus
from src.domain.entities.customer import Customer, CustomerType
from src.domain.value_objects.guide_id import GuideId
from src.domain.value_objects.customer_id import CustomerId
from src.domain.value_objects.money import Money
from src.infrastructure.logging.log_messages import LogCodes, QuantyLogger
from src.api.schemas.international_shipping_schemas import (
    InternationalShipmentCreate, KYCValidationStart, KYCDocumentSubmit,
    KYCValidationApprove, KYCValidationReject, CustomsDeclarationCreate,
    DocumentUpload, InternationalShipmentResponse, KYCValidationResponse,
    CustomsDeclarationResponse, InternationalDocumentResponse,
    ShipmentStatusResponse, ShipmentReadinessResponse, InternationalCostsResponse
)

router = APIRouter()
logger = QuantyLogger()

@router.post("/international-shipments", response_model=InternationalShipmentResponse)
async def create_international_shipment(
    request: InternationalShipmentCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear nuevo envío internacional"""
    try:
        shipping_service = InternationalShippingService()
        
        # Crear cliente mock
        customer = Customer(
            customer_id=CustomerId(request.customer_id),
            name="Customer",
            email="customer@test.com",
            phone="123456789",
            customer_type=CustomerType.MEDIUM
        )
        
        shipment = shipping_service.create_international_shipment(
            guide_id=GuideId(request.guide_id),
            customer=customer,
            destination_country=request.destination_country,
            declared_value=Money(request.declared_value_amount, request.declared_value_currency),
            product_description=request.product_description,
            product_category=request.product_category,
            weight_kg=request.weight_kg
        )
        
        # Guardar en repositorio
        shipping_repo = InternationalShippingRepository(session)
        saved_shipment = await shipping_repo.create_shipment(shipment)
        
        logger.log_info(
            LogCodes.INTERNATIONAL_SHIPMENT_CREATED,
            f"International shipment created: {shipment.shipment_id}",
            {"shipment_id": shipment.shipment_id, "destination": request.destination_country}
        )
        
        return InternationalShipmentResponse(
            shipment_id=saved_shipment.shipment_id,
            guide_id=saved_shipment.guide_id.value,
            customer_id=saved_shipment.customer_id.value,
            destination_country=saved_shipment.destination_country,
            declared_value={
                "amount": saved_shipment.declared_value.amount,
                "currency": saved_shipment.declared_value.currency
            },
            customs_status=saved_shipment.customs_status.value,
            compliance_status=saved_shipment.compliance_status,
            is_ready_for_shipping=saved_shipment.is_ready_for_shipping(),
            missing_documents=[doc.value for doc in saved_shipment.get_missing_documents()],
            created_at=saved_shipment.created_at,
            estimated_customs_clearance_date=saved_shipment.estimated_customs_clearance_date
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_SHIPMENT_ERROR,
            f"Error creating international shipment: {str(e)}",
            {"error": str(e), "guide_id": request.guide_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/international-shipments/{shipment_id}", response_model=InternationalShipmentResponse)
async def get_international_shipment(
    shipment_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener envío internacional por ID"""
    try:
        shipping_repo = InternationalShippingRepository(session)
        shipment = await shipping_repo.get_shipment(shipment_id)
        
        if not shipment:
            raise HTTPException(status_code=404, detail="International shipment not found")
        
        return InternationalShipmentResponse(
            shipment_id=shipment.shipment_id,
            guide_id=shipment.guide_id.value,
            customer_id=shipment.customer_id.value,
            destination_country=shipment.destination_country,
            declared_value={
                "amount": shipment.declared_value.amount,
                "currency": shipment.declared_value.currency
            },
            customs_status=shipment.customs_status.value,
            compliance_status=shipment.compliance_status,
            is_ready_for_shipping=shipment.is_ready_for_shipping(),
            missing_documents=[doc.value for doc in shipment.get_missing_documents()],
            created_at=shipment.created_at,
            estimated_customs_clearance_date=shipment.estimated_customs_clearance_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_SHIPMENT_ERROR,
            f"Error retrieving international shipment: {str(e)}",
            {"error": str(e), "shipment_id": shipment_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kyc-validations", response_model=KYCValidationResponse)
async def start_kyc_validation(
    request: KYCValidationStart,
    session: AsyncSession = Depends(get_session)
):
    """Iniciar validación KYC"""
    try:
        shipping_service = InternationalShippingService()
        
        kyc_validation = shipping_service.start_kyc_validation(
            customer_id=CustomerId(request.customer_id),
            provider=request.provider
        )
        
        # Guardar en repositorio
        shipping_repo = InternationalShippingRepository(session)
        saved_kyc = await shipping_repo.create_kyc_validation(kyc_validation)
        
        logger.log_info(
            LogCodes.KYC_VALIDATION_STARTED,
            f"KYC validation started: {kyc_validation.kyc_id}",
            {"kyc_id": kyc_validation.kyc_id, "customer_id": request.customer_id}
        )
        
        return KYCValidationResponse(
            kyc_id=saved_kyc.kyc_id,
            customer_id=saved_kyc.customer_id.value,
            provider=saved_kyc.provider,
            status=saved_kyc.status.value,
            created_at=saved_kyc.created_at,
            expiry_date=saved_kyc.expiry_date,
            validation_score=saved_kyc.validation_score,
            risk_level=saved_kyc.risk_level,
            is_valid_for_international_shipping=saved_kyc.is_valid_for_international_shipping()
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.KYC_VALIDATION_ERROR,
            f"Error starting KYC validation: {str(e)}",
            {"error": str(e), "customer_id": request.customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kyc-validations/{kyc_id}/documents")
async def submit_kyc_document(
    kyc_id: str,
    request: KYCDocumentSubmit,
    session: AsyncSession = Depends(get_session)
):
    """Enviar documento para validación KYC"""
    try:
        shipping_repo = InternationalShippingRepository(session)
        kyc_validation = await shipping_repo.get_kyc_validation(kyc_id)
        
        if not kyc_validation:
            raise HTTPException(status_code=404, detail="KYC validation not found")
        
        kyc_validation.submit_document(request.document_type, request.file_url)
        
        await shipping_repo.update_kyc_validation(kyc_validation)
        
        logger.log_info(
            LogCodes.KYC_DOCUMENT_SUBMITTED,
            f"KYC document submitted: {kyc_id}",
            {"kyc_id": kyc_id, "document_type": request.document_type}
        )
        
        return {"success": True, "message": "Document submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.KYC_VALIDATION_ERROR,
            f"Error submitting KYC document: {str(e)}",
            {"error": str(e), "kyc_id": kyc_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kyc-validations/{kyc_id}/approve")
async def approve_kyc_validation(
    kyc_id: str,
    request: KYCValidationApprove,
    session: AsyncSession = Depends(get_session)
):
    """Aprobar validación KYC"""
    try:
        shipping_repo = InternationalShippingRepository(session)
        kyc_validation = await shipping_repo.get_kyc_validation(kyc_id)
        
        if not kyc_validation:
            raise HTTPException(status_code=404, detail="KYC validation not found")
        
        kyc_validation.approve_kyc(
            approved_by=request.approved_by,
            validation_score=request.validation_score,
            risk_level=request.risk_level,
            expiry_months=request.expiry_months
        )
        
        await shipping_repo.update_kyc_validation(kyc_validation)
        
        logger.log_info(
            LogCodes.KYC_VALIDATION_APPROVED,
            f"KYC validation approved: {kyc_id}",
            {"kyc_id": kyc_id, "approved_by": request.approved_by}
        )
        
        return {"success": True, "message": "KYC validation approved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.KYC_VALIDATION_ERROR,
            f"Error approving KYC validation: {str(e)}",
            {"error": str(e), "kyc_id": kyc_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/kyc-validations/{kyc_id}/reject")
async def reject_kyc_validation(
    kyc_id: str,
    request: KYCValidationReject,
    session: AsyncSession = Depends(get_session)
):
    """Rechazar validación KYC"""
    try:
        shipping_repo = InternationalShippingRepository(session)
        kyc_validation = await shipping_repo.get_kyc_validation(kyc_id)
        
        if not kyc_validation:
            raise HTTPException(status_code=404, detail="KYC validation not found")
        
        kyc_validation.reject_kyc(request.rejection_reasons)
        
        await shipping_repo.update_kyc_validation(kyc_validation)
        
        logger.log_warning(
            LogCodes.KYC_VALIDATION_REJECTED,
            f"KYC validation rejected: {kyc_id}",
            {"kyc_id": kyc_id, "reasons": request.rejection_reasons}
        )
        
        return {"success": True, "message": "KYC validation rejected"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.KYC_VALIDATION_ERROR,
            f"Error rejecting KYC validation: {str(e)}",
            {"error": str(e), "kyc_id": kyc_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customs-declarations", response_model=CustomsDeclarationResponse)
async def create_customs_declaration(
    request: CustomsDeclarationCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crear declaración aduanera"""
    try:
        shipping_service = InternationalShippingService()
        
        declaration = shipping_service.create_customs_declaration(
            shipment_id=request.shipment_id,
            product_description=request.product_description,
            product_category=request.product_category,
            quantity=request.quantity,
            weight_kg=request.weight_kg,
            country_of_origin=request.country_of_origin
        )
        
        # Guardar en repositorio
        shipping_repo = InternationalShippingRepository(session)
        saved_declaration = await shipping_repo.create_customs_declaration(declaration)
        
        logger.log_info(
            LogCodes.CUSTOMS_DECLARATION_CREATED,
            f"Customs declaration created: {declaration.declaration_id}",
            {"declaration_id": declaration.declaration_id, "shipment_id": request.shipment_id}
        )
        
        return CustomsDeclarationResponse(
            declaration_id=saved_declaration.declaration_id,
            guide_id=saved_declaration.guide_id.value,
            declared_value={
                "amount": saved_declaration.declared_value.amount,
                "currency": saved_declaration.declared_value.currency
            },
            product_description=saved_declaration.product_description,
            product_category=saved_declaration.product_category,
            quantity=saved_declaration.quantity,
            weight_kg=saved_declaration.weight_kg,
            country_of_origin=saved_declaration.country_of_origin,
            hs_code=saved_declaration.hs_code
        )
        
    except Exception as e:
        logger.log_error(
            LogCodes.CUSTOMS_DECLARATION_ERROR,
            f"Error creating customs declaration: {str(e)}",
            {"error": str(e), "shipment_id": request.shipment_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/international-documents")
async def upload_international_document(
    shipment_id: str,
    document_type: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """Cargar documento internacional"""
    try:
        shipping_service = InternationalShippingService()
        
        # En implementación real, se subiría el archivo a almacenamiento
        file_url = f"/documents/{file.filename}"
        
        document = shipping_service.add_required_document(
            shipment_id=shipment_id,
            document_type=DocumentType(document_type),
            file_url=file_url,
            metadata={"original_filename": file.filename, "content_type": file.content_type}
        )
        
        # Guardar en repositorio
        shipping_repo = InternationalShippingRepository(session)
        saved_document = await shipping_repo.create_document(document)
        
        logger.log_info(
            LogCodes.INTERNATIONAL_DOCUMENT_UPLOADED,
            f"International document uploaded: {document.document_id}",
            {"document_id": document.document_id, "shipment_id": shipment_id, "type": document_type}
        )
        
        return {
            "success": True,
            "document_id": saved_document.document_id,
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_DOCUMENT_ERROR,
            f"Error uploading international document: {str(e)}",
            {"error": str(e), "shipment_id": shipment_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/international-shipments/{shipment_id}/customs-clearance")
async def start_customs_clearance(
    shipment_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Iniciar proceso de liberación aduanera"""
    try:
        shipping_service = InternationalShippingService()
        
        success = shipping_service.start_customs_clearance(shipment_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Shipment not ready for customs clearance")
        
        logger.log_info(
            LogCodes.CUSTOMS_CLEARANCE_STARTED,
            f"Customs clearance started: {shipment_id}",
            {"shipment_id": shipment_id}
        )
        
        return {"success": True, "message": "Customs clearance started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(
            LogCodes.CUSTOMS_CLEARANCE_ERROR,
            f"Error starting customs clearance: {str(e)}",
            {"error": str(e), "shipment_id": shipment_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/international-shipments/{shipment_id}/status", response_model=ShipmentStatusResponse)
async def get_shipment_status(
    shipment_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener estado completo del envío internacional"""
    try:
        shipping_service = InternationalShippingService()
        
        status_summary = shipping_service.get_shipment_status_summary(shipment_id)
        
        return ShipmentStatusResponse(**status_summary)
        
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_SHIPMENT_ERROR,
            f"Error retrieving shipment status: {str(e)}",
            {"error": str(e), "shipment_id": shipment_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/international-shipments/{shipment_id}/readiness")
async def check_shipment_readiness(
    shipment_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Verificar si envío está listo para ser enviado"""
    try:
        shipping_service = InternationalShippingService()
        
        readiness_status = shipping_service.check_shipment_readiness(shipment_id)
        
        return readiness_status
        
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_SHIPMENT_ERROR,
            f"Error checking shipment readiness: {str(e)}",
            {"error": str(e), "shipment_id": shipment_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/international-shipments/{shipment_id}/costs")
async def calculate_international_costs(
    shipment_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Calcular costos internacionales totales"""
    try:
        shipping_service = InternationalShippingService()
        
        costs = shipping_service.calculate_international_costs(shipment_id)
        
        return {
            "customs_fees": {
                "amount": costs["customs_fees"].amount,
                "currency": costs["customs_fees"].currency
            },
            "insurance": {
                "amount": costs["insurance"].amount,
                "currency": costs["insurance"].currency
            },
            "total": {
                "amount": costs["total"].amount,
                "currency": costs["total"].currency
            }
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_SHIPMENT_ERROR,
            f"Error calculating international costs: {str(e)}",
            {"error": str(e), "shipment_id": shipment_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/international-shipments/customer/{customer_id}", response_model=List[InternationalShipmentResponse])
async def get_shipments_by_customer(
    customer_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener envíos internacionales por cliente"""
    try:
        shipping_repo = InternationalShippingRepository(session)
        shipments = await shipping_repo.get_shipments_by_customer(CustomerId(customer_id))
        
        return [
            InternationalShipmentResponse(
                shipment_id=shipment.shipment_id,
                guide_id=shipment.guide_id.value,
                customer_id=shipment.customer_id.value,
                destination_country=shipment.destination_country,
                declared_value={
                    "amount": shipment.declared_value.amount,
                    "currency": shipment.declared_value.currency
                },
                customs_status=shipment.customs_status.value,
                compliance_status=shipment.compliance_status,
                is_ready_for_shipping=shipment.is_ready_for_shipping(),
                missing_documents=[doc.value for doc in shipment.get_missing_documents()],
                created_at=shipment.created_at,
                estimated_customs_clearance_date=shipment.estimated_customs_clearance_date
            )
            for shipment in shipments
        ]
        
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_SHIPMENT_ERROR,
            f"Error retrieving shipments by customer: {str(e)}",
            {"error": str(e), "customer_id": customer_id}
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shipping-restrictions/{destination_country}")
async def get_shipping_restrictions(
    destination_country: str,
    product_category: str,
    session: AsyncSession = Depends(get_session)
):
    """Obtener restricciones de envío por país y categoría"""
    try:
        shipping_service = InternationalShippingService()
        
        restrictions = shipping_service.get_shipping_restrictions(
            destination_country=destination_country,
            product_category=product_category
        )
        
        return {
            "destination_country": destination_country,
            "product_category": product_category,
            "restrictions": [
                {
                    "restriction_level": r.restriction_level.value,
                    "required_documents": [doc.value for doc in r.required_documents],
                    "max_value": {
                        "amount": r.max_value.amount,
                        "currency": r.max_value.currency
                    } if r.max_value else None,
                    "max_weight_kg": r.max_weight_kg,
                    "estimated_customs_days": r.estimated_customs_days
                }
                for r in restrictions
            ]
        }
        
    except Exception as e:
        logger.log_error(
            LogCodes.INTERNATIONAL_SHIPMENT_ERROR,
            f"Error retrieving shipping restrictions: {str(e)}",
            {"error": str(e), "destination": destination_country}
        )
        raise HTTPException(status_code=500, detail=str(e))