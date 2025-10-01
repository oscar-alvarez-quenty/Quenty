"""
International Mailbox API Endpoints
Handles virtual mailbox operations for Pasarex and Aeropost
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import structlog

from ..database import get_db
from ..services.international_mailbox_service import InternationalMailboxService
from ..models import CarrierType

logger = structlog.get_logger()

router = APIRouter(prefix="/international-mailbox", tags=["International Mailbox"])


class MailboxAssignRequest(BaseModel):
    """Request model for mailbox assignment"""
    customer_id: str
    carrier: str  # PASAREX or AEROPOST
    full_name: str
    email: str
    phone: str
    document_type: str = "CC"
    document_number: str


class ConsolidationRequest(BaseModel):
    """Request model for package consolidation"""
    customer_id: str
    package_ids: List[str]
    carrier: str


class ImportCostRequest(BaseModel):
    """Request model for import cost calculation"""
    value: float
    weight_lb: float
    category: str = "GENERAL"
    carrier: str
    has_electronics: bool = False
    origin: str = "USA"


class ContentDeclarationRequest(BaseModel):
    """Request model for content declaration"""
    package_id: str
    carrier: str
    items: List[Dict[str, Any]]
    total_value: float
    currency: str = "USD"
    invoice_number: Optional[str] = None
    purchase_date: Optional[str] = None
    merchant: Optional[str] = None


class AdditionalServiceRequest(BaseModel):
    """Request model for additional services"""
    package_id: str
    carrier: str
    service_type: str  # REPACK, PHOTOS, etc.
    options: Dict[str, Any] = {}


@router.post("/assign", response_model=Dict[str, Any])
async def assign_mailbox(
    request: MailboxAssignRequest,
    db=Depends(get_db)
):
    """
    Assign a virtual mailbox to a customer
    
    Supports:
    - Pasarex: Miami and Madrid addresses
    - Aeropost: Miami PO Box
    """
    try:
        service = InternationalMailboxService(db)
        
        customer_data = {
            "customer_id": request.customer_id,
            "full_name": request.full_name,
            "email": request.email,
            "phone": request.phone,
            "document_type": request.document_type,
            "document_number": request.document_number
        }
        
        result = await service.assign_mailbox(
            customer_id=request.customer_id,
            carrier=request.carrier,
            customer_data=customer_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to assign mailbox: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/prealerts/{customer_id}")
async def get_prealerts(
    customer_id: str,
    carrier: Optional[str] = Query(None, description="Filter by carrier"),
    db=Depends(get_db)
):
    """
    Get pre-alert packages for a customer
    
    Returns packages that have been pre-alerted but not yet shipped
    """
    try:
        service = InternationalMailboxService(db)
        prealerts = await service.get_prealerts(customer_id, carrier)
        
        return {
            "customer_id": customer_id,
            "prealerts": prealerts,
            "count": len(prealerts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get prealerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/consolidate", response_model=Dict[str, Any])
async def consolidate_packages(
    request: ConsolidationRequest,
    db=Depends(get_db)
):
    """
    Request consolidation of multiple packages
    
    Combines multiple packages into a single shipment for cost savings
    """
    try:
        service = InternationalMailboxService(db)
        result = await service.consolidate_packages(
            customer_id=request.customer_id,
            package_ids=request.package_ids,
            carrier=request.carrier
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to consolidate packages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/calculate-import-costs", response_model=Dict[str, Any])
async def calculate_import_costs(
    request: ImportCostRequest,
    db=Depends(get_db)
):
    """
    Calculate import costs including duties and taxes
    
    Provides breakdown of:
    - Product value
    - Shipping cost
    - Customs duty
    - VAT (19% in Colombia)
    - Handling fees
    - Total cost in COP
    """
    try:
        service = InternationalMailboxService(db)
        
        package_data = {
            "value": request.value,
            "weight_lb": request.weight_lb,
            "category": request.category,
            "has_electronics": request.has_electronics,
            "origin": request.origin
        }
        
        costs = await service.calculate_import_costs(package_data, request.carrier)
        
        return costs
        
    except Exception as e:
        logger.error(f"Failed to calculate import costs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/declare-content", response_model=Dict[str, Any])
async def declare_content(
    request: ContentDeclarationRequest,
    db=Depends(get_db)
):
    """
    Declare package content for customs
    
    Required for customs clearance and accurate duty calculation
    """
    try:
        service = InternationalMailboxService(db)
        
        declaration = {
            "items": request.items,
            "total_value": request.total_value,
            "currency": request.currency,
            "invoice_number": request.invoice_number,
            "purchase_date": request.purchase_date,
            "merchant": request.merchant
        }
        
        result = await service.declare_content(
            package_id=request.package_id,
            declaration=declaration,
            carrier=request.carrier
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to declare content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/additional-services", response_model=Dict[str, Any])
async def request_additional_services(
    request: AdditionalServiceRequest,
    db=Depends(get_db)
):
    """
    Request additional services for a package
    
    Available services:
    - REPACK: Repackaging to reduce volume
    - PHOTOS: Photos of package content
    - INSURANCE: Additional insurance coverage
    """
    try:
        service = InternationalMailboxService(db)
        
        result = await service.request_additional_services(
            package_id=request.package_id,
            service_type=request.service_type,
            options=request.options,
            carrier=request.carrier
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to request additional service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/track/{tracking_number}")
async def track_international_package(
    tracking_number: str,
    carrier: str = Query(..., description="PASAREX or AEROPOST"),
    db=Depends(get_db)
):
    """
    Track international package
    
    Provides tracking from origin to final delivery
    """
    try:
        service = InternationalMailboxService(db)
        tracking = await service.track_international_package(tracking_number, carrier)
        
        return tracking
        
    except Exception as e:
        logger.error(f"Failed to track package: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/return/{package_id}", response_model=Dict[str, Any])
async def process_return(
    package_id: str,
    reason: str,
    carrier: str,
    db=Depends(get_db)
):
    """
    Process international return request
    
    Initiates return process for packages that need to be sent back
    """
    try:
        service = InternationalMailboxService(db)
        
        result = await service.process_international_return(
            package_id=package_id,
            reason=reason,
            carrier=carrier
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process return: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/summary/{customer_id}")
async def get_mailbox_summary(
    customer_id: str,
    db=Depends(get_db)
):
    """
    Get summary of customer's international mailboxes
    
    Returns overview of all mailboxes, packages, and pending values
    """
    try:
        service = InternationalMailboxService(db)
        summary = await service.get_mailbox_summary(customer_id)
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get mailbox summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/import-calculator")
async def import_calculator_info():
    """
    Get information about import cost calculation
    
    Provides details on how duties and taxes are calculated
    """
    return {
        "info": "Colombian Import Cost Calculator",
        "tax_rates": {
            "vat": 0.19,  # 19% IVA
            "duty_rates": {
                "GENERAL": 0.15,
                "TECHNOLOGY": 0.05,
                "CLOTHING": 0.15,
                "BOOKS": 0.00,
                "MEDICINE": 0.00
            }
        },
        "thresholds": {
            "duty_free_limit_usd": 200,
            "description": "Packages under $200 USD are generally exempt from duties"
        },
        "categories": [
            "GENERAL",
            "TECHNOLOGY",
            "CLOTHING",
            "BOOKS",
            "MEDICINE",
            "SPORTS",
            "TOYS",
            "COSMETICS"
        ],
        "notes": [
            "Final cost includes product value + shipping + duties + VAT",
            "Exchange rate is updated daily from Banco de la República",
            "Some products may have additional restrictions or requirements"
        ]
    }