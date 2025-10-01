"""
Pickit Integration Client
Last-mile delivery and pickup point network service
"""

import httpx
import structlog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import hmac
import json
from decimal import Decimal
import base64

from ..schemas import (
    QuoteRequest, QuoteResponse,
    TrackingRequest, TrackingResponse, TrackingEvent,
    LabelRequest, LabelResponse,
    PickupRequest, PickupResponse
)
from ..credentials_manager import get_credential_manager
from ..error_handlers import CarrierException

logger = structlog.get_logger()


class PickitClient:
    """Client for Pickit pickup point network and last-mile delivery services"""
    
    def __init__(self):
        self.base_url = "https://api.pickit.net/v2"
        self.credentials = self._load_credentials()
        self.session = None
        self.access_token = None
        self.token_expiry = None
        
    def _load_credentials(self) -> Dict[str, str]:
        """Load Pickit credentials from manager"""
        manager = get_credential_manager()
        return manager.get_all_credentials("PICKIT")
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token"""
        if self.access_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return
            
        await self._authenticate()
    
    async def _authenticate(self) -> None:
        """Authenticate with Pickit API and get access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/token",
                    json={
                        "client_id": self.credentials.get("CLIENT_ID"),
                        "client_secret": self.credentials.get("CLIENT_SECRET"),
                        "grant_type": "client_credentials",
                        "scope": "shipments tracking labels pickup_points"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    auth_data = response.json()
                    self.access_token = auth_data["access_token"]
                    expires_in = auth_data.get("expires_in", 3600)
                    self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    
                    logger.info(
                        "pickit_authentication_successful",
                        expires_in=expires_in
                    )
                else:
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="AUTH_FAILED",
                        message=f"Authentication failed: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(
                "pickit_authentication_error",
                error=str(e)
            )
            raise CarrierException(
                carrier="Pickit",
                error_code="AUTH_ERROR",
                message=f"Failed to authenticate with Pickit: {str(e)}"
            )
    
    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Generate HMAC signature for webhook validation"""
        secret = self.credentials.get("WEBHOOK_SECRET", "")
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def get_pickup_points(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get available pickup points near a location
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            
        Returns:
            List of pickup point locations
        """
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/pickup-points",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    },
                    params={
                        "lat": latitude,
                        "lng": longitude,
                        "radius": radius_km,
                        "limit": limit,
                        "status": "active"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    pickup_points = response.json()["data"]
                    
                    return [
                        {
                            "id": point["id"],
                            "name": point["name"],
                            "code": point["code"],
                            "type": point["type"],  # LOCKER, STORE, KIOSK
                            "address": {
                                "street": point["address"]["street"],
                                "city": point["address"]["city"],
                                "state": point["address"]["state"],
                                "postal_code": point["address"]["postal_code"],
                                "country": point["address"]["country"]
                            },
                            "location": {
                                "latitude": point["location"]["lat"],
                                "longitude": point["location"]["lng"]
                            },
                            "distance_km": point["distance"],
                            "opening_hours": point.get("opening_hours", {}),
                            "services": point.get("services", []),
                            "capacity": {
                                "small": point["capacity"]["small"],
                                "medium": point["capacity"]["medium"],
                                "large": point["capacity"]["large"]
                            }
                        }
                        for point in pickup_points
                    ]
                else:
                    logger.error(
                        "pickit_pickup_points_error",
                        status_code=response.status_code,
                        response=response.text
                    )
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="PICKUP_POINTS_ERROR",
                        message=f"Failed to get pickup points: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(
                "pickit_request_error",
                error=str(e)
            )
            raise CarrierException(
                carrier="Pickit",
                error_code="REQUEST_ERROR",
                message=f"Request to Pickit failed: {str(e)}"
            )
    
    async def get_quote(self, request: QuoteRequest) -> QuoteResponse:
        """
        Get shipping quote from Pickit
        
        Args:
            request: Quote request with shipment details
            
        Returns:
            Quote response with pricing and transit time
        """
        await self._ensure_authenticated()
        
        try:
            # Calculate volumetric weight
            total_weight = sum(pkg.weight_kg for pkg in request.packages)
            total_volume = sum(
                (pkg.length_cm * pkg.width_cm * pkg.height_cm) / 5000
                for pkg in request.packages
            )
            chargeable_weight = max(total_weight, total_volume)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/shipments/quote",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "origin": {
                            "postal_code": request.origin.postal_code,
                            "city": request.origin.city,
                            "country": request.origin.country
                        },
                        "destination": {
                            "postal_code": request.destination.postal_code,
                            "city": request.destination.city,
                            "country": request.destination.country
                        },
                        "packages": [
                            {
                                "weight": pkg.weight_kg,
                                "length": pkg.length_cm,
                                "width": pkg.width_cm,
                                "height": pkg.height_cm,
                                "value": float(pkg.declared_value) if pkg.declared_value else 0
                            }
                            for pkg in request.packages
                        ],
                        "service_type": self._map_service_type(request.service_type),
                        "pickup_point": request.metadata.get("pickup_point_id") if request.metadata else None
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    quote_data = response.json()
                    
                    # Calculate transit time
                    transit_days = quote_data.get("estimated_transit_days", 2)
                    estimated_delivery = datetime.utcnow() + timedelta(days=transit_days)
                    
                    return QuoteResponse(
                        carrier="Pickit",
                        service_type=request.service_type,
                        total_price=Decimal(str(quote_data["total_price"])),
                        currency=quote_data.get("currency", "USD"),
                        transit_days=transit_days,
                        estimated_delivery=estimated_delivery,
                        breakdown={
                            "base_rate": quote_data.get("base_rate", 0),
                            "fuel_surcharge": quote_data.get("fuel_surcharge", 0),
                            "insurance": quote_data.get("insurance", 0),
                            "handling_fee": quote_data.get("handling_fee", 0),
                            "pickup_point_fee": quote_data.get("pickup_point_fee", 0)
                        },
                        metadata={
                            "quote_id": quote_data.get("quote_id"),
                            "service_level": quote_data.get("service_level"),
                            "pickup_point_available": quote_data.get("pickup_point_available", False)
                        }
                    )
                else:
                    logger.error(
                        "pickit_quote_error",
                        status_code=response.status_code,
                        response=response.text
                    )
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="QUOTE_ERROR",
                        message=f"Failed to get quote: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(
                "pickit_request_error",
                error=str(e)
            )
            raise CarrierException(
                carrier="Pickit",
                error_code="REQUEST_ERROR",
                message=f"Request to Pickit failed: {str(e)}"
            )
    
    async def generate_label(self, request: LabelRequest) -> LabelResponse:
        """
        Generate shipping label with Pickit
        
        Args:
            request: Label request with shipment details
            
        Returns:
            Label response with tracking number and label data
        """
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/shipments/create",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "order_id": request.order_id,
                        "shipper": {
                            "name": request.origin.contact_name,
                            "company": request.origin.company,
                            "address": {
                                "street": request.origin.street,
                                "city": request.origin.city,
                                "state": request.origin.state,
                                "postal_code": request.origin.postal_code,
                                "country": request.origin.country
                            },
                            "phone": request.origin.contact_phone,
                            "email": request.origin.contact_email
                        },
                        "recipient": {
                            "name": request.destination.contact_name,
                            "company": request.destination.company,
                            "address": {
                                "street": request.destination.street,
                                "city": request.destination.city,
                                "state": request.destination.state,
                                "postal_code": request.destination.postal_code,
                                "country": request.destination.country
                            },
                            "phone": request.destination.contact_phone,
                            "email": request.destination.contact_email
                        },
                        "pickup_point_id": request.metadata.get("pickup_point_id") if request.metadata else None,
                        "packages": [
                            {
                                "weight": pkg.weight_kg,
                                "length": pkg.length_cm,
                                "width": pkg.width_cm,
                                "height": pkg.height_cm,
                                "value": float(pkg.declared_value) if pkg.declared_value else 0,
                                "description": pkg.description
                            }
                            for pkg in request.packages
                        ],
                        "service_type": self._map_service_type(request.service_type),
                        "label_format": request.label_format or "PDF",
                        "label_size": request.label_size or "4x6",
                        "metadata": {
                            "order_id": request.order_id,
                            "customer_reference": request.metadata.get("customer_reference") if request.metadata else None
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    label_data = response.json()
                    
                    return LabelResponse(
                        carrier="Pickit",
                        tracking_number=label_data["tracking_number"],
                        label_url=label_data.get("label_url"),
                        label_data=label_data.get("label_data"),  # Base64 encoded
                        label_format=label_data.get("label_format", "PDF"),
                        shipment_id=label_data["shipment_id"],
                        metadata={
                            "barcode": label_data.get("barcode"),
                            "qr_code": label_data.get("qr_code"),
                            "pickup_code": label_data.get("pickup_code"),
                            "estimated_delivery": label_data.get("estimated_delivery"),
                            "pickup_point": label_data.get("pickup_point")
                        }
                    )
                else:
                    logger.error(
                        "pickit_label_error",
                        status_code=response.status_code,
                        response=response.text
                    )
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="LABEL_ERROR",
                        message=f"Failed to generate label: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(
                "pickit_request_error",
                error=str(e)
            )
            raise CarrierException(
                carrier="Pickit",
                error_code="REQUEST_ERROR",
                message=f"Request to Pickit failed: {str(e)}"
            )
    
    async def track_shipment(self, request: TrackingRequest) -> TrackingResponse:
        """
        Track shipment with Pickit
        
        Args:
            request: Tracking request with tracking number
            
        Returns:
            Tracking response with current status and events
        """
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/shipments/{request.tracking_number}/tracking",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    tracking_data = response.json()
                    
                    # Map Pickit status to standard status
                    status_map = {
                        "created": "pending",
                        "picked_up": "in_transit",
                        "in_transit": "in_transit",
                        "at_pickup_point": "out_for_delivery",
                        "out_for_delivery": "out_for_delivery",
                        "delivered": "delivered",
                        "failed": "exception",
                        "returned": "returned"
                    }
                    
                    events = []
                    for event in tracking_data.get("events", []):
                        events.append(
                            TrackingEvent(
                                timestamp=datetime.fromisoformat(event["timestamp"]),
                                status=event["status"],
                                description=event["description"],
                                location=event.get("location"),
                                details=event.get("details", {})
                            )
                        )
                    
                    return TrackingResponse(
                        carrier="Pickit",
                        tracking_number=request.tracking_number,
                        status=status_map.get(tracking_data["status"], "unknown"),
                        events=events,
                        estimated_delivery=datetime.fromisoformat(tracking_data["estimated_delivery"]) 
                            if tracking_data.get("estimated_delivery") else None,
                        current_location=tracking_data.get("current_location"),
                        metadata={
                            "pickup_point": tracking_data.get("pickup_point"),
                            "pickup_code": tracking_data.get("pickup_code"),
                            "delivery_attempts": tracking_data.get("delivery_attempts", 0),
                            "proof_of_delivery": tracking_data.get("proof_of_delivery")
                        }
                    )
                else:
                    logger.error(
                        "pickit_tracking_error",
                        status_code=response.status_code,
                        response=response.text
                    )
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="TRACKING_ERROR",
                        message=f"Failed to track shipment: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(
                "pickit_request_error",
                error=str(e)
            )
            raise CarrierException(
                carrier="Pickit",
                error_code="REQUEST_ERROR",
                message=f"Request to Pickit failed: {str(e)}"
            )
    
    async def schedule_pickup(self, request: PickupRequest) -> PickupResponse:
        """
        Schedule a pickup with Pickit
        
        Args:
            request: Pickup request with details
            
        Returns:
            Pickup response with confirmation
        """
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/pickups/schedule",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "pickup_date": request.pickup_date.isoformat(),
                        "pickup_window": {
                            "start": request.pickup_window_start,
                            "end": request.pickup_window_end
                        },
                        "address": {
                            "street": request.address.street,
                            "city": request.address.city,
                            "state": request.address.state,
                            "postal_code": request.address.postal_code,
                            "country": request.address.country
                        },
                        "contact": {
                            "name": request.contact_name,
                            "phone": request.contact_phone,
                            "email": request.contact_email
                        },
                        "packages_count": request.packages_count,
                        "total_weight": request.total_weight_kg,
                        "instructions": request.special_instructions,
                        "shipment_ids": request.shipment_ids if hasattr(request, 'shipment_ids') else []
                    },
                    timeout=15.0
                )
                
                if response.status_code in [200, 201]:
                    pickup_data = response.json()
                    
                    return PickupResponse(
                        carrier="Pickit",
                        pickup_id=pickup_data["pickup_id"],
                        confirmation_number=pickup_data["confirmation_number"],
                        scheduled_date=datetime.fromisoformat(pickup_data["scheduled_date"]),
                        pickup_window_start=pickup_data["pickup_window"]["start"],
                        pickup_window_end=pickup_data["pickup_window"]["end"],
                        status="scheduled",
                        metadata={
                            "driver_name": pickup_data.get("driver_name"),
                            "driver_phone": pickup_data.get("driver_phone"),
                            "estimated_arrival": pickup_data.get("estimated_arrival"),
                            "tracking_url": pickup_data.get("tracking_url")
                        }
                    )
                else:
                    logger.error(
                        "pickit_pickup_error",
                        status_code=response.status_code,
                        response=response.text
                    )
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="PICKUP_ERROR",
                        message=f"Failed to schedule pickup: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(
                "pickit_request_error",
                error=str(e)
            )
            raise CarrierException(
                carrier="Pickit",
                error_code="REQUEST_ERROR",
                message=f"Request to Pickit failed: {str(e)}"
            )
    
    async def cancel_shipment(self, tracking_number: str, reason: str = "") -> Dict[str, Any]:
        """
        Cancel a shipment
        
        Args:
            tracking_number: Tracking number to cancel
            reason: Cancellation reason
            
        Returns:
            Cancellation confirmation
        """
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/shipments/{tracking_number}/cancel",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "reason": reason,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="CANCEL_ERROR",
                        message=f"Failed to cancel shipment: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            raise CarrierException(
                carrier="Pickit",
                error_code="REQUEST_ERROR",
                message=f"Request to Pickit failed: {str(e)}"
            )
    
    async def get_proof_of_delivery(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get proof of delivery for a shipment
        
        Args:
            tracking_number: Tracking number
            
        Returns:
            Proof of delivery information
        """
        await self._ensure_authenticated()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/shipments/{tracking_number}/proof-of-delivery",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    pod_data = response.json()
                    
                    return {
                        "tracking_number": tracking_number,
                        "delivered_at": pod_data["delivered_at"],
                        "signed_by": pod_data.get("signed_by"),
                        "signature_image": pod_data.get("signature_image"),  # Base64
                        "delivery_photo": pod_data.get("delivery_photo"),  # Base64
                        "location": pod_data.get("location"),
                        "notes": pod_data.get("notes"),
                        "pickup_code_used": pod_data.get("pickup_code_used")
                    }
                else:
                    raise CarrierException(
                        carrier="Pickit",
                        error_code="POD_ERROR",
                        message=f"Failed to get proof of delivery: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            raise CarrierException(
                carrier="Pickit",
                error_code="REQUEST_ERROR",
                message=f"Request to Pickit failed: {str(e)}"
            )
    
    def _map_service_type(self, service_type: str) -> str:
        """Map generic service type to Pickit service type"""
        service_map = {
            "express": "NEXT_DAY",
            "standard": "STANDARD",
            "economy": "ECONOMY",
            "same_day": "SAME_DAY",
            "pickup_point": "PICKUP_POINT"
        }
        return service_map.get(service_type.lower(), "STANDARD")
    
    async def validate_webhook(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Validate webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
            timestamp: Timestamp from webhook header
            
        Returns:
            True if signature is valid
        """
        expected_signature = self._generate_signature(payload, timestamp)
        return hmac.compare_digest(signature, expected_signature)
    
    async def process_webhook(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook event from Pickit
        
        Args:
            event_type: Type of webhook event
            data: Event data
            
        Returns:
            Processed event data
        """
        logger.info(
            "pickit_webhook_received",
            event_type=event_type,
            tracking_number=data.get("tracking_number")
        )
        
        event_handlers = {
            "shipment.created": self._handle_shipment_created,
            "shipment.picked_up": self._handle_shipment_picked_up,
            "shipment.in_transit": self._handle_shipment_in_transit,
            "shipment.at_pickup_point": self._handle_shipment_at_pickup_point,
            "shipment.delivered": self._handle_shipment_delivered,
            "shipment.failed": self._handle_shipment_failed,
            "pickup.scheduled": self._handle_pickup_scheduled,
            "pickup.completed": self._handle_pickup_completed
        }
        
        handler = event_handlers.get(event_type)
        if handler:
            return await handler(data)
        else:
            logger.warning(
                "pickit_unknown_webhook_event",
                event_type=event_type
            )
            return {"status": "unknown_event"}
    
    async def _handle_shipment_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipment created event"""
        return {
            "event": "shipment_created",
            "tracking_number": data["tracking_number"],
            "shipment_id": data["shipment_id"],
            "status": "created",
            "timestamp": data["timestamp"]
        }
    
    async def _handle_shipment_picked_up(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipment picked up event"""
        return {
            "event": "shipment_picked_up",
            "tracking_number": data["tracking_number"],
            "status": "in_transit",
            "pickup_time": data["pickup_time"],
            "driver": data.get("driver")
        }
    
    async def _handle_shipment_in_transit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipment in transit event"""
        return {
            "event": "shipment_in_transit",
            "tracking_number": data["tracking_number"],
            "status": "in_transit",
            "current_location": data.get("current_location"),
            "estimated_delivery": data.get("estimated_delivery")
        }
    
    async def _handle_shipment_at_pickup_point(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipment arrived at pickup point event"""
        return {
            "event": "shipment_at_pickup_point",
            "tracking_number": data["tracking_number"],
            "status": "at_pickup_point",
            "pickup_point": data["pickup_point"],
            "pickup_code": data.get("pickup_code"),
            "hold_until": data.get("hold_until")
        }
    
    async def _handle_shipment_delivered(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipment delivered event"""
        return {
            "event": "shipment_delivered",
            "tracking_number": data["tracking_number"],
            "status": "delivered",
            "delivered_at": data["delivered_at"],
            "signed_by": data.get("signed_by"),
            "delivery_location": data.get("delivery_location")
        }
    
    async def _handle_shipment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shipment failed event"""
        return {
            "event": "shipment_failed",
            "tracking_number": data["tracking_number"],
            "status": "failed",
            "failure_reason": data["reason"],
            "failure_time": data["timestamp"],
            "next_action": data.get("next_action")
        }
    
    async def _handle_pickup_scheduled(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pickup scheduled event"""
        return {
            "event": "pickup_scheduled",
            "pickup_id": data["pickup_id"],
            "confirmation_number": data["confirmation_number"],
            "scheduled_date": data["scheduled_date"],
            "status": "scheduled"
        }
    
    async def _handle_pickup_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pickup completed event"""
        return {
            "event": "pickup_completed",
            "pickup_id": data["pickup_id"],
            "completed_at": data["completed_at"],
            "packages_collected": data["packages_collected"],
            "status": "completed"
        }


# Export the client
__all__ = ["PickitClient"]