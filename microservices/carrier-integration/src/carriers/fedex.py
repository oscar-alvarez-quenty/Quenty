import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from ..schemas import (
    QuoteRequest, QuoteResponse,
    LabelRequest, LabelResponse,
    TrackingResponse, TrackingEvent,
    PickupRequest, PickupResponse
)

logger = structlog.get_logger()

class FedExClient:
    """FedEx Web Services API Client"""
    
    def __init__(self, credentials: Dict[str, Any], environment: str = "production"):
        self.credentials = credentials
        self.environment = environment
        self.base_url = self._get_base_url()
        self.access_token = None
        self.token_expires = None
        
    def _get_base_url(self) -> str:
        """Get FedEx API base URL based on environment"""
        if self.environment == "sandbox":
            return "https://apis-sandbox.fedex.com"
        return "https://apis.fedex.com"
    
    async def _get_access_token(self) -> str:
        """Get or refresh OAuth 2.0 access token"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.credentials['client_id'],
                    "client_secret": self.credentials['client_secret']
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=data['expires_in'] - 60)
            
            return self.access_token
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_quote(self, request: QuoteRequest) -> QuoteResponse:
        """Get shipping quote from FedEx"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "accountNumber": {"value": self.credentials['account_number']},
                    "requestedShipment": {
                        "shipper": self._format_address(request.origin),
                        "recipient": self._format_address(request.destination),
                        "shipDateStamp": (request.pickup_date or datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                        "serviceType": self._get_service_type(request.service_type),
                        "packagingType": "YOUR_PACKAGING",
                        "pickupType": "REGULAR_PICKUP",
                        "rateRequestType": ["ACCOUNT", "LIST"],
                        "requestedPackageLineItems": [
                            {
                                "weight": {
                                    "units": "KG",
                                    "value": pkg.weight_kg
                                },
                                "dimensions": {
                                    "length": pkg.length_cm,
                                    "width": pkg.width_cm,
                                    "height": pkg.height_cm,
                                    "units": "CM"
                                }
                            } for pkg in request.packages
                        ]
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/rate/v1/rates/quotes",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "X-locale": "en_US"
                    },
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                rate_reply = data['output']['rateReplyDetails'][0]
                
                return QuoteResponse(
                    quote_id=f"FEDEX-{datetime.now().timestamp()}",
                    carrier="FedEx",
                    service_type=rate_reply['serviceName'],
                    amount=rate_reply['ratedShipmentDetails'][0]['totalNetCharge'],
                    currency=rate_reply['ratedShipmentDetails'][0]['currency'],
                    estimated_days=rate_reply.get('commit', {}).get('transitDays', 5),
                    valid_until=datetime.now() + timedelta(hours=24)
                )
                
        except httpx.HTTPError as e:
            logger.error("FedEx quote request failed", error=str(e))
            raise Exception(f"FedEx API error: {str(e)}")
    
    async def generate_label(self, request: LabelRequest) -> LabelResponse:
        """Generate shipping label with FedEx"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "labelResponseOptions": "LABEL",
                    "requestedShipment": {
                        "shipper": self._format_address(request.origin),
                        "recipients": [self._format_address(request.destination)],
                        "shipDatestamp": datetime.now().strftime("%Y-%m-%d"),
                        "serviceType": self._get_service_type(request.service_type),
                        "packagingType": "YOUR_PACKAGING",
                        "pickupType": "REGULAR_PICKUP",
                        "shippingChargesPayment": {
                            "paymentType": "SENDER",
                            "payor": {
                                "responsibleParty": {
                                    "accountNumber": {"value": self.credentials['account_number']}
                                }
                            }
                        },
                        "labelSpecification": {
                            "imageType": "PDF",
                            "labelStockType": "PAPER_4X6"
                        },
                        "requestedPackageLineItems": [
                            {
                                "weight": {
                                    "units": "KG",
                                    "value": pkg.weight_kg
                                },
                                "dimensions": {
                                    "length": pkg.length_cm,
                                    "width": pkg.width_cm,
                                    "height": pkg.height_cm,
                                    "units": "CM"
                                },
                                "customerReferences": [
                                    {
                                        "customerReferenceType": "CUSTOMER_REFERENCE",
                                        "value": request.order_id
                                    }
                                ]
                            } for pkg in request.packages
                        ]
                    },
                    "accountNumber": {"value": self.credentials['account_number']}
                }
                
                response = await client.post(
                    f"{self.base_url}/ship/v1/shipments",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "X-locale": "en_US"
                    },
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                data = response.json()
                output = data['output']
                
                return LabelResponse(
                    tracking_number=output['transactionShipments'][0]['masterTrackingNumber'],
                    carrier="FedEx",
                    label_data=output['transactionShipments'][0]['pieceResponses'][0]['packageDocuments'][0]['encodedLabel'],
                    estimated_delivery=datetime.now() + timedelta(days=3),
                    cost=0,  # Parse from response if available
                    currency="USD"
                )
                
        except httpx.HTTPError as e:
            logger.error("FedEx label generation failed", error=str(e))
            raise Exception(f"FedEx API error: {str(e)}")
    
    async def track_shipment(self, tracking_number: str) -> TrackingResponse:
        """Track FedEx shipment"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/track/v1/trackingnumbers",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "X-locale": "en_US"
                    },
                    json={
                        "includeDetailedScans": True,
                        "trackingInfo": [
                            {
                                "trackingNumberInfo": {
                                    "trackingNumber": tracking_number
                                }
                            }
                        ]
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                track_result = data['output']['completeTrackResults'][0]['trackResults'][0]
                
                events = []
                for scan in track_result.get('scanEvents', []):
                    events.append(TrackingEvent(
                        date=datetime.fromisoformat(scan['date']),
                        status=scan['eventType'],
                        description=scan['eventDescription'],
                        location=scan.get('scanLocation', {}).get('city')
                    ))
                
                return TrackingResponse(
                    tracking_number=tracking_number,
                    carrier="FedEx",
                    status=track_result['latestStatusDetail']['statusByLocale'],
                    current_location=track_result.get('latestStatusDetail', {}).get('scanLocation', {}).get('city'),
                    estimated_delivery=datetime.fromisoformat(track_result['estimatedDeliveryTimeWindow']['window']['ends']) if 'estimatedDeliveryTimeWindow' in track_result else None,
                    delivered_date=datetime.fromisoformat(track_result['actualDeliveryTime']) if track_result.get('isDelivered') else None,
                    events=events
                )
                
        except httpx.HTTPError as e:
            logger.error("FedEx tracking failed", error=str(e))
            raise Exception(f"FedEx API error: {str(e)}")
    
    async def schedule_pickup(self, request: PickupRequest) -> PickupResponse:
        """Schedule pickup with FedEx"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "associatedAccountNumber": {"value": self.credentials['account_number']},
                    "originDetail": {
                        "pickupLocation": self._format_address(request.address),
                        "readyDateTimestamp": request.pickup_date.strftime("%Y-%m-%dT%H:%M:%S"),
                        "companyCloseTime": request.pickup_window_end,
                        "packageLocation": "FRONT"
                    },
                    "packageCount": request.packages_count,
                    "totalWeight": {
                        "units": "KG",
                        "value": request.total_weight_kg
                    },
                    "carrierCode": "FDXE",
                    "remarks": request.special_instructions
                }
                
                response = await client.post(
                    f"{self.base_url}/pickup/v1/pickups",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "X-locale": "en_US"
                    },
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                return PickupResponse(
                    confirmation_number=data['output']['pickupConfirmationNumber'],
                    carrier="FedEx",
                    pickup_date=request.pickup_date,
                    pickup_window=f"{request.pickup_window_start}-{request.pickup_window_end}",
                    status="scheduled"
                )
                
        except httpx.HTTPError as e:
            logger.error("FedEx pickup scheduling failed", error=str(e))
            raise Exception(f"FedEx API error: {str(e)}")
    
    def _get_service_type(self, service_type: Optional[str]) -> str:
        """Map service type to FedEx service code"""
        mapping = {
            "express": "INTERNATIONAL_PRIORITY",
            "overnight": "PRIORITY_OVERNIGHT",
            "same_day": "SAME_DAY",
            "economy": "INTERNATIONAL_ECONOMY",
            "standard": "FEDEX_GROUND"
        }
        return mapping.get(service_type, "INTERNATIONAL_PRIORITY")
    
    def _format_address(self, address) -> Dict:
        """Format address for FedEx API"""
        return {
            "contact": {
                "personName": address.contact_name,
                "phoneNumber": address.contact_phone,
                "companyName": address.company
            },
            "address": {
                "streetLines": [address.street],
                "city": address.city,
                "stateOrProvinceCode": address.state,
                "postalCode": address.postal_code,
                "countryCode": address.country
            }
        }