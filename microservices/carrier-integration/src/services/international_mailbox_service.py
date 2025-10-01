"""
International Mailbox Service
Manages virtual mailboxes and international shipping through Pasarex and Aeropost
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    CarrierType, InternationalMailbox, PackagePrealert,
    PackageConsolidation, CustomsDeclaration, ImportCostCalculation
)
from ..carriers.pasarex import PasarexClient
from ..carriers.aeropost import AeropostClient
from ..error_handlers import CarrierException
from .exchange_rate_service import ExchangeRateService

logger = structlog.get_logger()


class InternationalMailboxService:
    """Service for managing international mailbox operations"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.pasarex_client = PasarexClient()
        self.aeropost_client = AeropostClient()
        self.exchange_service = ExchangeRateService(self.db)
    
    async def assign_mailbox(self, customer_id: str, carrier: str, 
                            customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign a virtual mailbox to a customer
        
        Args:
            customer_id: Customer identifier
            carrier: PASAREX or AEROPOST
            customer_data: Customer information
            
        Returns:
            Mailbox assignment details
        """
        try:
            # Check if customer already has a mailbox with this carrier
            existing = self.db.query(InternationalMailbox).filter(
                InternationalMailbox.customer_id == customer_id,
                InternationalMailbox.carrier == CarrierType[carrier],
                InternationalMailbox.status == "active"
            ).first()
            
            if existing:
                return {
                    "mailbox_id": existing.mailbox_id,
                    "mailbox_number": existing.mailbox_number,
                    "miami_address": existing.miami_address,
                    "spain_address": existing.spain_address,
                    "status": existing.status,
                    "existing": True
                }
            
            # Assign new mailbox based on carrier
            if carrier.upper() == "PASAREX":
                result = await self.pasarex_client.assign_mailbox(customer_data)
                
                # Save to database
                mailbox = InternationalMailbox(
                    customer_id=customer_id,
                    carrier=CarrierType.PASAREX,
                    mailbox_id=result["mailbox_id"],
                    mailbox_number=result["mailbox_id"],
                    miami_address=result["usa_address"],
                    spain_address=result["spain_address"],
                    status="active"
                )
                
            elif carrier.upper() == "AEROPOST":
                result = await self.aeropost_client.assign_po_box(customer_data)
                
                # Save to database
                mailbox = InternationalMailbox(
                    customer_id=customer_id,
                    carrier=CarrierType.AEROPOST,
                    mailbox_id=result["po_box_id"],
                    mailbox_number=result["po_box_number"],
                    miami_address=result["miami_address"],
                    status="active",
                    membership_type=result.get("membership_type", "standard")
                )
            else:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            self.db.add(mailbox)
            self.db.commit()
            
            logger.info(f"Mailbox assigned for customer {customer_id} with {carrier}")
            
            return {
                "mailbox_id": mailbox.mailbox_id,
                "mailbox_number": mailbox.mailbox_number,
                "miami_address": mailbox.miami_address,
                "spain_address": mailbox.spain_address if carrier == "PASAREX" else None,
                "status": mailbox.status,
                "carrier": carrier,
                "created_at": mailbox.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to assign mailbox: {str(e)}")
            raise
    
    async def get_prealerts(self, customer_id: str, carrier: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get pre-alert packages for a customer
        
        Args:
            customer_id: Customer identifier
            carrier: Optional carrier filter
            
        Returns:
            List of pre-alerted packages
        """
        try:
            all_prealerts = []
            
            # Get mailboxes for customer
            query = self.db.query(InternationalMailbox).filter(
                InternationalMailbox.customer_id == customer_id,
                InternationalMailbox.status == "active"
            )
            
            if carrier:
                query = query.filter(InternationalMailbox.carrier == CarrierType[carrier])
            
            mailboxes = query.all()
            
            for mailbox in mailboxes:
                if mailbox.carrier == CarrierType.PASAREX:
                    prealerts = await self.pasarex_client.get_prealerts(customer_id)
                elif mailbox.carrier == CarrierType.AEROPOST:
                    prealerts = await self.aeropost_client.get_packages(customer_id)
                else:
                    continue
                
                # Save prealerts to database
                for prealert in prealerts:
                    # Check if prealert already exists
                    existing = self.db.query(PackagePrealert).filter(
                        PackagePrealert.tracking_number == prealert["tracking_number"],
                        PackagePrealert.mailbox_id == mailbox.mailbox_id
                    ).first()
                    
                    if not existing:
                        db_prealert = PackagePrealert(
                            mailbox_id=mailbox.mailbox_id,
                            carrier=mailbox.carrier,
                            tracking_number=prealert["tracking_number"],
                            origin_carrier=prealert.get("carrier"),
                            description=prealert["description"],
                            declared_value=prealert["value"],
                            weight_lb=prealert["weight_lb"],
                            dimensions=prealert.get("dimensions"),
                            category=prealert.get("category", "GENERAL"),
                            status=prealert["status"],
                            expected_arrival=prealert.get("expected_arrival")
                        )
                        self.db.add(db_prealert)
                    
                    prealert["carrier"] = mailbox.carrier.value
                    all_prealerts.append(prealert)
            
            self.db.commit()
            
            return all_prealerts
            
        except Exception as e:
            logger.error(f"Failed to get prealerts: {str(e)}")
            return []
    
    async def consolidate_packages(self, customer_id: str, package_ids: List[str], 
                                  carrier: str) -> Dict[str, Any]:
        """
        Request consolidation of multiple packages
        
        Args:
            customer_id: Customer identifier
            package_ids: List of package IDs
            carrier: PASAREX or AEROPOST
            
        Returns:
            Consolidation details
        """
        try:
            if carrier.upper() == "PASAREX":
                result = await self.pasarex_client.consolidate_packages(customer_id, package_ids)
            elif carrier.upper() == "AEROPOST":
                result = await self.aeropost_client.consolidate_packages(customer_id, package_ids)
            else:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            # Save consolidation to database
            consolidation = PackageConsolidation(
                consolidation_id=result["consolidation_id"],
                customer_id=customer_id,
                carrier=CarrierType[carrier],
                package_ids=package_ids,
                master_tracking=result.get("master_tracking"),
                status=result["status"],
                packages_count=result["packages_count"],
                total_weight_lb=result.get("total_weight_lb", 0),
                volumetric_weight=result.get("volumetric_weight"),
                billable_weight=result.get("billable_weight"),
                estimated_cost=result.get("estimated_cost"),
                savings_amount=result.get("savings", 0)
            )
            
            self.db.add(consolidation)
            self.db.commit()
            
            logger.info(f"Consolidation created: {consolidation.consolidation_id}")
            
            return {
                "consolidation_id": consolidation.consolidation_id,
                "status": consolidation.status,
                "packages_count": consolidation.packages_count,
                "estimated_cost": consolidation.estimated_cost,
                "savings": consolidation.savings_amount,
                "carrier": carrier
            }
            
        except Exception as e:
            logger.error(f"Failed to consolidate packages: {str(e)}")
            raise
    
    async def calculate_import_costs(self, package_data: Dict[str, Any], 
                                    carrier: str) -> Dict[str, Any]:
        """
        Calculate import costs for a package
        
        Args:
            package_data: Package information
            carrier: PASAREX or AEROPOST
            
        Returns:
            Import cost breakdown
        """
        try:
            # Get current TRM
            trm = await self.exchange_service.get_current_trm()
            
            if carrier.upper() == "PASAREX":
                costs = await self.pasarex_client.calculate_import_costs(package_data)
            elif carrier.upper() == "AEROPOST":
                costs = await self.aeropost_client.calculate_import_costs(package_data)
            else:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            # Save calculation to database
            calculation = ImportCostCalculation(
                package_id=package_data.get("package_id", "TEMP"),
                carrier=CarrierType[carrier],
                product_value=costs["product_value"],
                shipping_cost=costs["shipping_cost"],
                customs_duty=costs["customs_duty"],
                vat=costs["vat"],
                handling_fee=costs["handling_fee"],
                insurance=costs.get("insurance", 0),
                total_cost=costs["total_cost"],
                currency=costs["currency"],
                exchange_rate=costs.get("exchange_rate", trm["rate"]),
                duty_rate=costs["breakdown"]["duty_rate"],
                vat_rate=costs["breakdown"]["vat_rate"],
                category=costs["breakdown"]["category"]
            )
            
            self.db.add(calculation)
            self.db.commit()
            
            return costs
            
        except Exception as e:
            logger.error(f"Failed to calculate import costs: {str(e)}")
            raise
    
    async def declare_content(self, package_id: str, declaration: Dict[str, Any], 
                             carrier: str) -> Dict[str, Any]:
        """
        Declare package content for customs
        
        Args:
            package_id: Package identifier
            declaration: Content declaration
            carrier: PASAREX or AEROPOST
            
        Returns:
            Declaration confirmation
        """
        try:
            if carrier.upper() == "PASAREX":
                result = await self.pasarex_client.declare_content(package_id, declaration)
            elif carrier.upper() == "AEROPOST":
                result = await self.aeropost_client.declare_content(package_id, declaration)
            else:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            # Save declaration to database
            customs_declaration = CustomsDeclaration(
                package_id=package_id,
                declaration_id=result["declaration_id"],
                carrier=CarrierType[carrier],
                items=declaration["items"],
                total_value=declaration["total_value"],
                currency=declaration.get("currency", "USD"),
                invoice_number=declaration.get("invoice_number"),
                purchase_date=declaration.get("purchase_date"),
                merchant=declaration.get("merchant"),
                customs_form_id=result.get("customs_form_id"),
                status="declared"
            )
            
            self.db.add(customs_declaration)
            self.db.commit()
            
            logger.info(f"Content declared for package {package_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to declare content: {str(e)}")
            raise
    
    async def request_additional_services(self, package_id: str, service_type: str, 
                                         options: Dict[str, Any], carrier: str) -> Dict[str, Any]:
        """
        Request additional services for a package
        
        Args:
            package_id: Package identifier
            service_type: Type of service (REPACK, PHOTOS, etc.)
            options: Service options
            carrier: PASAREX or AEROPOST
            
        Returns:
            Service request confirmation
        """
        try:
            if carrier.upper() == "PASAREX":
                if service_type == "REPACK":
                    result = await self.pasarex_client.request_repack(package_id, options)
                else:
                    raise ValueError(f"Unsupported service type for Pasarex: {service_type}")
                    
            elif carrier.upper() == "AEROPOST":
                if service_type == "PHOTOS":
                    result = await self.aeropost_client.request_photos(package_id)
                else:
                    raise ValueError(f"Unsupported service type for Aeropost: {service_type}")
            else:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            logger.info(f"Additional service requested: {service_type} for package {package_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to request additional service: {str(e)}")
            raise
    
    async def track_international_package(self, tracking_number: str, carrier: str) -> Dict[str, Any]:
        """
        Track international package
        
        Args:
            tracking_number: Package tracking number
            carrier: PASAREX or AEROPOST
            
        Returns:
            Tracking information
        """
        try:
            if carrier.upper() == "PASAREX":
                tracking = await self.pasarex_client.track_package(tracking_number)
            elif carrier.upper() == "AEROPOST":
                tracking = await self.aeropost_client.track_package(tracking_number)
            else:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            return {
                "tracking_number": tracking.tracking_number,
                "carrier": tracking.carrier,
                "status": tracking.status,
                "current_location": tracking.current_location,
                "events": [
                    {
                        "date": event.date.isoformat(),
                        "status": event.status,
                        "description": event.description,
                        "location": event.location
                    }
                    for event in tracking.events
                ],
                "estimated_delivery": tracking.estimated_delivery.isoformat() if tracking.estimated_delivery else None,
                "delivered_date": tracking.delivered_date.isoformat() if tracking.delivered_date else None
            }
            
        except Exception as e:
            logger.error(f"Failed to track package: {str(e)}")
            raise
    
    async def process_international_return(self, package_id: str, reason: str, 
                                          carrier: str) -> Dict[str, Any]:
        """
        Process international return request
        
        Args:
            package_id: Package identifier
            reason: Return reason
            carrier: PASAREX or AEROPOST
            
        Returns:
            Return request details
        """
        try:
            # This would need implementation in the carrier clients
            # For now, return a placeholder
            
            return {
                "return_id": f"RET-{package_id}",
                "package_id": package_id,
                "status": "return_requested",
                "reason": reason,
                "carrier": carrier,
                "instructions": "Return label will be sent via email",
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process return: {str(e)}")
            raise
    
    async def get_mailbox_summary(self, customer_id: str) -> Dict[str, Any]:
        """
        Get summary of customer's international mailboxes
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            Mailbox summary with package counts and costs
        """
        try:
            mailboxes = self.db.query(InternationalMailbox).filter(
                InternationalMailbox.customer_id == customer_id,
                InternationalMailbox.status == "active"
            ).all()
            
            summary = {
                "customer_id": customer_id,
                "mailboxes": [],
                "total_packages": 0,
                "total_pending_value": 0
            }
            
            for mailbox in mailboxes:
                # Get package count
                packages = self.db.query(PackagePrealert).filter(
                    PackagePrealert.mailbox_id == mailbox.mailbox_id,
                    PackagePrealert.status != "delivered"
                ).all()
                
                mailbox_data = {
                    "carrier": mailbox.carrier.value,
                    "mailbox_number": mailbox.mailbox_number,
                    "miami_address": mailbox.miami_address,
                    "spain_address": mailbox.spain_address,
                    "package_count": len(packages),
                    "total_value": sum(p.declared_value for p in packages)
                }
                
                summary["mailboxes"].append(mailbox_data)
                summary["total_packages"] += len(packages)
                summary["total_pending_value"] += mailbox_data["total_value"]
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get mailbox summary: {str(e)}")
            return {
                "customer_id": customer_id,
                "error": str(e)
            }