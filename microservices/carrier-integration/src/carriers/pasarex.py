"""
Pasarex Integration Client
International mailbox service for USA and Europe
"""

import httpx
import structlog
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import json
from decimal import Decimal

from ..schemas import (
    QuoteRequest, QuoteResponse,
    TrackingRequest, TrackingResponse, TrackingEvent,
    LabelRequest, LabelResponse
)
from ..credentials_manager import get_credential_manager
from ..error_handlers import CarrierException

logger = structlog.get_logger()


class PasarexClient:
    """Client for Pasarex international mailbox services"""

    def __init__(self, credentials: Dict[str, Any] = None, environment: str = None):
        # Load from environment variables if credentials not provided
        if credentials is None:
            credentials = self._load_from_env()

        self.credentials = credentials
        self.environment = environment or os.getenv('PASAREX_ENVIRONMENT', 'sandbox')
        self.base_url = self._get_base_url()
        self.access_token = None
        self.token_expires = None

    def _load_from_env(self) -> Dict[str, Any]:
        """Load Pasarex credentials from environment variables"""
        return {
            'api_key': os.getenv('PASAREX_API_KEY'),
            'api_secret': os.getenv('PASAREX_API_SECRET'),
            'account_number': os.getenv('PASAREX_ACCOUNT_NUMBER')
        }

    def _get_base_url(self) -> str:
        """Get Pasarex API base URL based on environment"""
        if self.environment == "sandbox":
            return "https://sandbox-api.pasarex.com/v2"
        return "https://api.pasarex.com/v2"
    
    async def _get_access_token(self) -> str:
        """Get OAuth 2.0 access token"""
        try:
            # Check if token is still valid
            if self.access_token and self.token_expires and datetime.now() < self.token_expires:
                return self.access_token
            
            # Request new token
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.credentials.get("CLIENT_ID"),
                        "client_secret": self.credentials.get("CLIENT_SECRET"),
                        "scope": "mailbox shipping tracking"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                    return self.access_token
                else:
                    raise CarrierException(
                        f"Failed to get Pasarex access token: {response.status_code}",
                        carrier="PASAREX"
                    )
                    
        except Exception as e:
            logger.error("Pasarex authentication failed", error=str(e))
            raise CarrierException(f"Pasarex authentication failed: {str(e)}", carrier="PASAREX")
    
    async def assign_mailbox(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign a virtual mailbox to a customer
        
        Args:
            customer_data: Customer information including ID and personal details
            
        Returns:
            Mailbox assignment details with USA and Spain addresses
        """
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mailbox/assign",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "customer_id": customer_data["customer_id"],
                        "email": customer_data["email"],
                        "full_name": customer_data["full_name"],
                        "phone": customer_data["phone"],
                        "document_type": customer_data.get("document_type", "CC"),
                        "document_number": customer_data["document_number"],
                        "locations": ["USA", "SPAIN"]
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    mailbox_data = response.json()
                    
                    return {
                        "mailbox_id": mailbox_data["mailbox_id"],
                        "customer_id": customer_data["customer_id"],
                        "usa_address": {
                            "name": mailbox_data["usa"]["recipient_name"],
                            "line1": mailbox_data["usa"]["address_line1"],
                            "line2": mailbox_data["usa"]["address_line2"],
                            "city": mailbox_data["usa"]["city"],
                            "state": mailbox_data["usa"]["state"],
                            "postal_code": mailbox_data["usa"]["postal_code"],
                            "country": "USA",
                            "phone": mailbox_data["usa"]["phone"]
                        },
                        "spain_address": {
                            "name": mailbox_data["spain"]["recipient_name"],
                            "line1": mailbox_data["spain"]["address_line1"],
                            "line2": mailbox_data["spain"]["address_line2"],
                            "city": mailbox_data["spain"]["city"],
                            "province": mailbox_data["spain"]["province"],
                            "postal_code": mailbox_data["spain"]["postal_code"],
                            "country": "SPAIN",
                            "phone": mailbox_data["spain"]["phone"]
                        },
                        "status": "active",
                        "created_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to assign mailbox: {response.status_code}",
                        carrier="PASAREX"
                    )
                    
        except Exception as e:
            logger.error("Failed to assign Pasarex mailbox", error=str(e))
            raise
    
    async def get_prealerts(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get pre-alert packages for a customer
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of pre-alerted packages
        """
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/prealerts/{customer_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    prealerts = response.json()["prealerts"]
                    
                    return [
                        {
                            "prealert_id": p["id"],
                            "tracking_number": p["tracking_number"],
                            "carrier": p["carrier"],
                            "origin": p["origin_location"],
                            "description": p["description"],
                            "value": p["declared_value"],
                            "weight_lb": p["weight_lb"],
                            "status": p["status"],
                            "expected_arrival": p["expected_arrival"],
                            "created_at": p["created_at"]
                        }
                        for p in prealerts
                    ]
                else:
                    return []
                    
        except Exception as e:
            logger.error("Failed to get Pasarex prealerts", error=str(e))
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
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/consolidation/create",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "customer_id": customer_id,
                        "package_ids": package_ids,
                        "service_options": {
                            "repack": True,
                            "remove_invoices": True,
                            "add_protection": True
                        }
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    consolidation = response.json()
                    
                    return {
                        "consolidation_id": consolidation["id"],
                        "status": consolidation["status"],
                        "packages_count": len(package_ids),
                        "estimated_weight": consolidation["estimated_weight_lb"],
                        "estimated_cost": consolidation["estimated_cost"],
                        "created_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to create consolidation: {response.status_code}",
                        carrier="PASAREX"
                    )
                    
        except Exception as e:
            logger.error("Failed to consolidate packages", error=str(e))
            raise
    
    async def calculate_import_costs(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate import costs including duties and taxes
        
        Args:
            package_data: Package information including value, weight, and category
            
        Returns:
            Breakdown of import costs
        """
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/calculator/import-costs",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "declared_value": package_data["value"],
                        "currency": package_data.get("currency", "USD"),
                        "weight_lb": package_data["weight_lb"],
                        "category": package_data.get("category", "GENERAL"),
                        "origin_country": package_data.get("origin", "USA"),
                        "contains_electronics": package_data.get("has_electronics", False)
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    costs = response.json()
                    
                    return {
                        "product_value": costs["product_value"],
                        "shipping_cost": costs["shipping_cost"],
                        "customs_duty": costs["customs_duty"],
                        "vat": costs["vat"],
                        "handling_fee": costs["handling_fee"],
                        "total_cost": costs["total_cost"],
                        "currency": "COP",
                        "exchange_rate": costs["exchange_rate"],
                        "breakdown": {
                            "duty_rate": costs["duty_percentage"],
                            "vat_rate": costs["vat_percentage"],
                            "category": package_data.get("category", "GENERAL")
                        }
                    }
                else:
                    # Fallback calculation
                    return self._calculate_import_costs_fallback(package_data)
                    
        except Exception as e:
            logger.error("Failed to calculate import costs", error=str(e))
            return self._calculate_import_costs_fallback(package_data)
    
    def _calculate_import_costs_fallback(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback import cost calculation"""
        value_usd = float(package_data["value"])
        weight_lb = float(package_data["weight_lb"])
        
        # Approximate rates
        shipping_rate_per_lb = 8.50  # USD per pound
        duty_rate = 0.15  # 15% average
        vat_rate = 0.19  # 19% Colombian VAT
        exchange_rate = 4200  # COP per USD (approximate)
        
        shipping_cost_usd = weight_lb * shipping_rate_per_lb
        total_before_taxes = value_usd + shipping_cost_usd
        
        customs_duty = total_before_taxes * duty_rate
        vat_base = total_before_taxes + customs_duty
        vat = vat_base * vat_rate
        
        total_usd = total_before_taxes + customs_duty + vat
        
        return {
            "product_value": value_usd * exchange_rate,
            "shipping_cost": shipping_cost_usd * exchange_rate,
            "customs_duty": customs_duty * exchange_rate,
            "vat": vat * exchange_rate,
            "handling_fee": 50000,  # Fixed handling fee in COP
            "total_cost": (total_usd * exchange_rate) + 50000,
            "currency": "COP",
            "exchange_rate": exchange_rate,
            "breakdown": {
                "duty_rate": duty_rate,
                "vat_rate": vat_rate,
                "category": package_data.get("category", "GENERAL")
            }
        }
    
    async def declare_content(self, package_id: str, declaration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Declare package content for customs
        
        Args:
            package_id: Package identifier
            declaration: Content declaration details
            
        Returns:
            Declaration confirmation
        """
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/packages/{package_id}/declare",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "items": declaration["items"],
                        "total_value": declaration["total_value"],
                        "currency": declaration.get("currency", "USD"),
                        "invoice_number": declaration.get("invoice_number"),
                        "purchase_date": declaration.get("purchase_date"),
                        "merchant": declaration.get("merchant")
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "declaration_id": result["declaration_id"],
                        "package_id": package_id,
                        "status": "declared",
                        "customs_code": result.get("customs_code"),
                        "declared_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to declare content: {response.status_code}",
                        carrier="PASAREX"
                    )
                    
        except Exception as e:
            logger.error("Failed to declare package content", error=str(e))
            raise
    
    async def track_package(self, tracking_number: str) -> TrackingResponse:
        """
        Track international package
        
        Args:
            tracking_number: Package tracking number
            
        Returns:
            Tracking information
        """
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tracking/{tracking_number}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    tracking_data = response.json()
                    
                    events = []
                    for event in tracking_data.get("events", []):
                        events.append(TrackingEvent(
                            date=datetime.fromisoformat(event["timestamp"]),
                            status=event["status"],
                            description=event["description"],
                            location=event.get("location"),
                            details=event
                        ))
                    
                    return TrackingResponse(
                        tracking_number=tracking_number,
                        carrier="PASAREX",
                        status=tracking_data["current_status"],
                        events=events,
                        current_location=tracking_data.get("current_location"),
                        estimated_delivery=datetime.fromisoformat(tracking_data["estimated_delivery"]) if tracking_data.get("estimated_delivery") else None,
                        delivered_date=datetime.fromisoformat(tracking_data["delivered_date"]) if tracking_data.get("delivered_date") else None
                    )
                else:
                    return TrackingResponse(
                        tracking_number=tracking_number,
                        carrier="PASAREX",
                        status="NOT_FOUND",
                        events=[],
                        error="Package not found"
                    )
                    
        except Exception as e:
            logger.error("Failed to track Pasarex package", error=str(e))
            return TrackingResponse(
                tracking_number=tracking_number,
                carrier="PASAREX",
                status="ERROR",
                events=[],
                error=str(e)
            )
    
    async def request_repack(self, package_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request package repackaging service
        
        Args:
            package_id: Package identifier
            options: Repack options (remove_boxes, add_bubble_wrap, etc.)
            
        Returns:
            Repack request confirmation
        """
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/packages/{package_id}/services/repack",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "remove_original_boxes": options.get("remove_boxes", True),
                        "add_bubble_wrap": options.get("add_protection", True),
                        "consolidate_items": options.get("consolidate", True),
                        "remove_invoices": options.get("remove_invoices", False),
                        "add_fragile_stickers": options.get("fragile", False)
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "service_id": result["service_request_id"],
                        "package_id": package_id,
                        "service_type": "REPACK",
                        "status": result["status"],
                        "fee": result["service_fee"],
                        "currency": "USD",
                        "requested_at": datetime.now().isoformat()
                    }
                else:
                    raise CarrierException(
                        f"Failed to request repack: {response.status_code}",
                        carrier="PASAREX"
                    )
                    
        except Exception as e:
            logger.error("Failed to request repack service", error=str(e))
            raise
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Check Pasarex API health status"""
        try:
            async with httpx.AsyncClient() as client:
                start = datetime.now()
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                latency = (datetime.now() - start).total_seconds() * 1000
                
                return {
                    "carrier": "PASAREX",
                    "status": "operational" if response.status_code == 200 else "degraded",
                    "latency_ms": latency,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "carrier": "PASAREX",
                "status": "down",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }