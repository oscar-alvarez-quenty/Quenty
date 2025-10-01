"""
Aeropost Integration Client
International courier service with Miami PO Box
"""

import httpx
import structlog
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import base64
from decimal import Decimal
import xml.etree.ElementTree as ET
from zeep import Client as SOAPClient
from zeep.transports import Transport

from ..schemas import (
    QuoteRequest, QuoteResponse,
    TrackingRequest, TrackingResponse, TrackingEvent,
    LabelRequest, LabelResponse
)
from ..credentials_manager import get_credential_manager
from ..error_handlers import CarrierException

logger = structlog.get_logger()


class AeropostClient:
    """Client for Aeropost international courier services"""

    def __init__(self, credentials: Dict[str, Any] = None, environment: str = None):
        # Load from environment variables if credentials not provided
        if credentials is None:
            credentials = self._load_from_env()

        self.credentials = credentials
        self.environment = environment or os.getenv('AEROPOST_ENVIRONMENT', 'sandbox')
        self.base_url = self._get_base_url()
        self.soap_url = self._get_soap_url()
        self.session_token = None

    def _load_from_env(self) -> Dict[str, Any]:
        """Load Aeropost credentials from environment variables"""
        return {
            'API_KEY': os.getenv('AEROPOST_API_KEY'),
            'API_SECRET': os.getenv('AEROPOST_API_SECRET'),
            'ACCOUNT_NUMBER': os.getenv('AEROPOST_ACCOUNT_NUMBER')
        }

    def _get_base_url(self) -> str:
        """Get Aeropost API base URL based on environment"""
        if self.environment == "sandbox":
            return "https://sandbox-api.aeropost.com/v3"
        return "https://api.aeropost.com/v3"

    def _get_soap_url(self) -> str:
        """Get Aeropost SOAP URL based on environment"""
        if self.environment == "sandbox":
            return "https://sandbox-services.aeropost.com/WSAeropost/AeropostService.asmx?wsdl"
        return "https://services.aeropost.com/WSAeropost/AeropostService.asmx?wsdl"
    
    def _get_auth_header(self) -> str:
        """Generate Basic Auth header"""
        api_key = self.credentials.get("API_KEY", "")
        api_secret = self.credentials.get("API_SECRET", "")
        credentials = f"{api_key}:{api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def assign_po_box(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign a PO Box in Miami to a customer
        
        Args:
            customer_data: Customer information
            
        Returns:
            PO Box assignment details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mailbox/assign",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json",
                        "X-API-Version": "3.0"
                    },
                    json={
                        "customer": {
                            "id": customer_data["customer_id"],
                            "email": customer_data["email"],
                            "name": customer_data["full_name"],
                            "phone": customer_data["phone"],
                            "id_type": customer_data.get("document_type", "CEDULA"),
                            "id_number": customer_data["document_number"],
                            "country": "CO"
                        },
                        "service_type": "STANDARD"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    po_box_data = response.json()
                    
                    return {
                        "po_box_id": po_box_data["po_box_id"],
                        "po_box_number": po_box_data["po_box_number"],
                        "customer_id": customer_data["customer_id"],
                        "miami_address": {
                            "name": f"{customer_data['full_name']} - AP{po_box_data['po_box_number']}",
                            "line1": po_box_data["address"]["line1"],
                            "line2": po_box_data["address"]["line2"],
                            "city": "Miami",
                            "state": "FL",
                            "postal_code": po_box_data["address"]["zip_code"],
                            "country": "USA",
                            "phone": po_box_data["address"]["phone"]
                        },
                        "status": "active",
                        "membership_type": po_box_data.get("membership_type", "STANDARD"),
                        "created_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to assign PO Box: {response.status_code}",
                        carrier="AEROPOST"
                    )
                    
        except Exception as e:
            logger.error("Failed to assign Aeropost PO Box", error=str(e))
            raise
    
    async def get_packages(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get packages in customer's PO Box
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of packages in Miami warehouse
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/packages",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "X-Customer-ID": customer_id
                    },
                    params={
                        "status": "all",
                        "location": "MIAMI"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    packages = response.json()["packages"]
                    
                    return [
                        {
                            "package_id": p["id"],
                            "tracking_number": p["tracking_number"],
                            "carrier": p["origin_carrier"],
                            "description": p["description"],
                            "value": p["declared_value"],
                            "weight_lb": p["weight_pounds"],
                            "dimensions": {
                                "length": p.get("length_inches"),
                                "width": p.get("width_inches"),
                                "height": p.get("height_inches")
                            },
                            "status": p["status"],
                            "received_date": p["received_date"],
                            "category": p.get("category", "GENERAL"),
                            "ready_to_ship": p.get("ready_to_ship", False)
                        }
                        for p in packages
                    ]
                else:
                    return []
                    
        except Exception as e:
            logger.error("Failed to get Aeropost packages", error=str(e))
            return []
    
    async def consolidate_packages(self, customer_id: str, package_ids: List[str]) -> Dict[str, Any]:
        """
        Request consolidation of multiple packages
        
        Args:
            customer_id: Customer identifier
            package_ids: List of package IDs to consolidate
            
        Returns:
            Consolidation order details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/consolidation",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    },
                    json={
                        "customer_id": customer_id,
                        "packages": package_ids,
                        "options": {
                            "remove_packaging": True,
                            "add_protection": True,
                            "combine_items": True
                        }
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    consolidation = response.json()
                    
                    return {
                        "consolidation_id": consolidation["consolidation_id"],
                        "master_tracking": consolidation["master_tracking_number"],
                        "status": consolidation["status"],
                        "packages_count": len(package_ids),
                        "total_weight_lb": consolidation["total_weight"],
                        "volumetric_weight": consolidation["volumetric_weight"],
                        "billable_weight": consolidation["billable_weight"],
                        "estimated_cost": consolidation["estimated_cost"],
                        "savings": consolidation.get("savings_amount", 0),
                        "created_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to create consolidation: {response.status_code}",
                        carrier="AEROPOST"
                    )
                    
        except Exception as e:
            logger.error("Failed to consolidate Aeropost packages", error=str(e))
            raise
    
    async def calculate_import_costs(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate import costs with Colombian taxes and duties
        
        Args:
            package_data: Package information
            
        Returns:
            Import cost breakdown
        """
        try:
            # Use SOAP service for accurate calculation
            transport = Transport(operation_timeout=10)
            soap_client = SOAPClient(self.soap_url, transport=transport)
            
            result = soap_client.service.CalculateImportCosts(
                APIKey=self.credentials.get("API_KEY"),
                PackageValue=package_data["value"],
                WeightPounds=package_data["weight_lb"],
                Category=package_data.get("category", "GENERAL"),
                ContainsElectronics=package_data.get("has_electronics", False)
            )
            
            if result.Success:
                return {
                    "product_value": float(result.ProductValueCOP),
                    "shipping_cost": float(result.ShippingCostCOP),
                    "customs_duty": float(result.CustomsDutyCOP),
                    "vat": float(result.VATCOP),
                    "handling_fee": float(result.HandlingFeeCOP),
                    "insurance": float(result.InsuranceCOP) if result.InsuranceCOP else 0,
                    "total_cost": float(result.TotalCostCOP),
                    "currency": "COP",
                    "exchange_rate": float(result.ExchangeRate),
                    "breakdown": {
                        "duty_rate": float(result.DutyRate),
                        "vat_rate": 0.19,  # Colombian VAT
                        "category": package_data.get("category", "GENERAL"),
                        "weight_charge_per_lb": float(result.WeightChargePerLb)
                    },
                    "delivery_time": result.EstimatedDeliveryDays
                }
            else:
                # Fallback to REST API
                return await self._calculate_costs_rest(package_data)
                
        except Exception as e:
            logger.error("Failed to calculate import costs via SOAP", error=str(e))
            return await self._calculate_costs_rest(package_data)
    
    async def _calculate_costs_rest(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate costs using REST API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/calculator/import",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    },
                    json={
                        "value_usd": package_data["value"],
                        "weight_lb": package_data["weight_lb"],
                        "category": package_data.get("category", "GENERAL"),
                        "destination": "CO"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    costs = response.json()
                    return costs
                else:
                    # Manual fallback calculation
                    return self._calculate_costs_manual(package_data)
                    
        except Exception:
            return self._calculate_costs_manual(package_data)
    
    def _calculate_costs_manual(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manual cost calculation as last resort"""
        value_usd = float(package_data["value"])
        weight_lb = float(package_data["weight_lb"])
        category = package_data.get("category", "GENERAL")
        
        # Aeropost standard rates (approximate)
        weight_rates = {
            "GENERAL": 7.50,
            "TECHNOLOGY": 8.50,
            "CLOTHING": 6.50
        }
        
        rate_per_lb = weight_rates.get(category, 7.50)
        exchange_rate = 4200  # Approximate COP/USD
        
        # Calculate costs
        shipping_cost_usd = weight_lb * rate_per_lb
        
        # Colombian import taxes
        duty_rates = {
            "GENERAL": 0.15,
            "TECHNOLOGY": 0.05,
            "CLOTHING": 0.15
        }
        
        duty_rate = duty_rates.get(category, 0.15)
        vat_rate = 0.19
        
        # If value + shipping > $200 USD, apply taxes
        if (value_usd + shipping_cost_usd) > 200:
            customs_duty = (value_usd + shipping_cost_usd) * duty_rate
            vat_base = value_usd + shipping_cost_usd + customs_duty
            vat = vat_base * vat_rate
        else:
            customs_duty = 0
            vat = 0
        
        handling_fee = 35000  # COP
        insurance = value_usd * 0.02 * exchange_rate if value_usd > 100 else 0
        
        total_usd = value_usd + shipping_cost_usd + customs_duty + vat
        total_cop = (total_usd * exchange_rate) + handling_fee + insurance
        
        return {
            "product_value": value_usd * exchange_rate,
            "shipping_cost": shipping_cost_usd * exchange_rate,
            "customs_duty": customs_duty * exchange_rate,
            "vat": vat * exchange_rate,
            "handling_fee": handling_fee,
            "insurance": insurance,
            "total_cost": total_cop,
            "currency": "COP",
            "exchange_rate": exchange_rate,
            "breakdown": {
                "duty_rate": duty_rate,
                "vat_rate": vat_rate,
                "category": category,
                "weight_charge_per_lb": rate_per_lb
            },
            "delivery_time": "5-8 business days"
        }
    
    async def declare_content(self, package_id: str, declaration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Declare package content for customs
        
        Args:
            package_id: Package identifier
            declaration: Content declaration
            
        Returns:
            Declaration confirmation
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/packages/{package_id}/declaration",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    },
                    json={
                        "items": [
                            {
                                "description": item["description"],
                                "quantity": item["quantity"],
                                "unit_value": item["unit_value"],
                                "hs_code": item.get("hs_code", ""),
                                "origin_country": item.get("origin", "USA")
                            }
                            for item in declaration["items"]
                        ],
                        "invoice": {
                            "number": declaration.get("invoice_number"),
                            "date": declaration.get("purchase_date"),
                            "merchant": declaration.get("merchant"),
                            "total": declaration["total_value"]
                        }
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "declaration_id": result["declaration_id"],
                        "package_id": package_id,
                        "status": "declared",
                        "customs_form_id": result.get("customs_form_id"),
                        "declared_value": declaration["total_value"],
                        "declared_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to declare content: {response.status_code}",
                        carrier="AEROPOST"
                    )
                    
        except Exception as e:
            logger.error("Failed to declare Aeropost package content", error=str(e))
            raise
    
    async def track_package(self, tracking_number: str) -> TrackingResponse:
        """
        Track package through Aeropost network
        
        Args:
            tracking_number: Aeropost tracking number
            
        Returns:
            Tracking information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tracking/{tracking_number}",
                    headers={"Authorization": self._get_auth_header()},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    tracking_data = response.json()
                    
                    events = []
                    for event in tracking_data.get("tracking_events", []):
                        events.append(TrackingEvent(
                            date=datetime.fromisoformat(event["date"]),
                            status=self._map_status(event["status"]),
                            description=event["description"],
                            location=event.get("location"),
                            details=event
                        ))
                    
                    # Calculate estimated delivery
                    estimated_delivery = None
                    if tracking_data.get("estimated_delivery"):
                        estimated_delivery = datetime.fromisoformat(tracking_data["estimated_delivery"])
                    
                    return TrackingResponse(
                        tracking_number=tracking_number,
                        carrier="AEROPOST",
                        status=self._map_status(tracking_data["status"]),
                        events=events,
                        current_location=tracking_data.get("current_location"),
                        estimated_delivery=estimated_delivery,
                        delivered_date=datetime.fromisoformat(tracking_data["delivered_date"]) if tracking_data.get("delivered_date") else None,
                        weight_lb=tracking_data.get("weight_pounds"),
                        customs_status=tracking_data.get("customs_status")
                    )
                else:
                    return TrackingResponse(
                        tracking_number=tracking_number,
                        carrier="AEROPOST",
                        status="NOT_FOUND",
                        events=[],
                        error="Package not found"
                    )
                    
        except Exception as e:
            logger.error("Failed to track Aeropost package", error=str(e))
            return TrackingResponse(
                tracking_number=tracking_number,
                carrier="AEROPOST",
                status="ERROR",
                events=[],
                error=str(e)
            )
    
    def _map_status(self, aeropost_status: str) -> str:
        """Map Aeropost status to standard status"""
        status_map = {
            "RECEIVED_MIAMI": "IN_TRANSIT",
            "CUSTOMS_CLEARANCE": "IN_TRANSIT",
            "IN_COLOMBIA": "IN_TRANSIT",
            "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
            "DELIVERED": "DELIVERED",
            "EXCEPTION": "EXCEPTION",
            "RETURNED": "RETURNED"
        }
        return status_map.get(aeropost_status.upper(), aeropost_status)
    
    async def request_photos(self, package_id: str) -> Dict[str, Any]:
        """
        Request photos of package content
        
        Args:
            package_id: Package identifier
            
        Returns:
            Photo request confirmation
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/packages/{package_id}/services/photos",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    },
                    json={
                        "photo_type": "CONTENT",
                        "quantity": 3
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "service_id": result["service_id"],
                        "package_id": package_id,
                        "service_type": "PHOTOS",
                        "status": result["status"],
                        "fee": result["fee"],
                        "currency": "USD",
                        "estimated_completion": result.get("estimated_completion"),
                        "requested_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to request photos: {response.status_code}",
                        carrier="AEROPOST"
                    )
                    
        except Exception as e:
            logger.error("Failed to request Aeropost photos", error=str(e))
            raise
    
    async def create_shipping_order(self, customer_id: str, packages: List[str], 
                                   destination: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create shipping order from Miami to Colombia
        
        Args:
            customer_id: Customer identifier
            packages: List of package IDs to ship
            destination: Destination address in Colombia
            
        Returns:
            Shipping order details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/shipping/create",
                    headers={
                        "Authorization": self._get_auth_header(),
                        "Content-Type": "application/json"
                    },
                    json={
                        "customer_id": customer_id,
                        "packages": packages,
                        "destination": {
                            "name": destination["name"],
                            "address": destination["address"],
                            "city": destination["city"],
                            "department": destination.get("department", ""),
                            "postal_code": destination.get("postal_code", ""),
                            "phone": destination["phone"],
                            "email": destination.get("email", "")
                        },
                        "service_type": "STANDARD",
                        "insurance": destination.get("insurance", False)
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    order = response.json()
                    
                    return {
                        "order_id": order["order_id"],
                        "tracking_number": order["tracking_number"],
                        "status": order["status"],
                        "total_weight": order["total_weight"],
                        "total_cost": order["total_cost"],
                        "currency": "COP",
                        "estimated_delivery": order["estimated_delivery"],
                        "created_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to create shipping order: {response.status_code}",
                        carrier="AEROPOST"
                    )
                    
        except Exception as e:
            logger.error("Failed to create Aeropost shipping order", error=str(e))
            raise
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Check Aeropost API health status"""
        try:
            async with httpx.AsyncClient() as client:
                start = datetime.now()
                response = await client.get(
                    f"{self.base_url}/health",
                    headers={"Authorization": self._get_auth_header()},
                    timeout=5.0
                )
                latency = (datetime.now() - start).total_seconds() * 1000
                
                return {
                    "carrier": "AEROPOST",
                    "status": "operational" if response.status_code == 200 else "degraded",
                    "latency_ms": latency,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "carrier": "AEROPOST", 
                "status": "down",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }