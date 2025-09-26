import httpx
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import base64
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from ..schemas import (
    QuoteRequest, QuoteResponse,
    LabelRequest, LabelResponse,
    TrackingResponse, TrackingEvent,
    PickupRequest, PickupResponse
)
from ..utils.encryption import decrypt_credentials

logger = structlog.get_logger()

class DHLClient:
    """DHL Express API Client"""

    def __init__(self, credentials: Dict[str, Any] = None, environment: str = None):
        # Load from environment variables if credentials not provided
        if credentials is None:
            credentials = self._load_from_env()

        self.credentials = credentials
        self.environment = environment or os.getenv('DHL_ENVIRONMENT', 'sandbox')
        self.base_url = self._get_base_url()
        self.headers = self._get_headers()

    def _load_from_env(self) -> Dict[str, Any]:
        """Load DHL credentials from environment variables"""
        return {
            'username': os.getenv('DHL_USERNAME'),
            'password': os.getenv('DHL_PASSWORD'),
            'account_number': os.getenv('DHL_ACCOUNT_NUMBER')
        }
        
    def _get_base_url(self) -> str:
        """Get DHL API base URL based on environment"""
        if self.environment == "sandbox":
            return "https://express.api.dhl.com/mydhlapi/test"
        return "https://express.api.dhl.com/mydhlapi"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        # DHL now uses HTTP Basic Auth with username and password
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_quote(self, request: QuoteRequest) -> QuoteResponse:
        """Get shipping quote from DHL"""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare request payload
                payload = {
                    "customerDetails": {
                        "shipperDetails": {
                            "postalCode": request.origin.postal_code,
                            "cityName": request.origin.city,
                            "countryCode": request.origin.country
                        },
                        "receiverDetails": {
                            "postalCode": request.destination.postal_code,
                            "cityName": request.destination.city,
                            "countryCode": request.destination.country
                        }
                    },
                    "accounts": [
                        {
                            "typeCode": "shipper",
                            "number": self.credentials['account_number']
                        }
                    ],
                    "plannedShippingDateAndTime": "2025-09-15T13:00:00GMT+01:00",  # Use working date for now
                    "unitOfMeasurement": "metric",
                    "isCustomsDeclarable": request.customs_value is not None,
                    "packages": [
                        {
                            "weight": pkg.weight_kg,
                            "dimensions": {
                                "length": pkg.length_cm,
                                "width": pkg.width_cm,
                                "height": pkg.height_cm
                            }
                        } for pkg in request.packages
                    ]
                }
                
                if request.customs_value:
                    payload["monetaryAmount"] = [
                        {
                            "typeCode": "declaredValue",
                            "value": request.customs_value,
                            "currency": request.packages[0].currency
                        }
                    ]
                
                # Make API call with Basic Auth
                # httpx supports auth parameter directly with tuples
                username = self.credentials.get('username')
                password = self.credentials.get('password')
                logger.info(f"DHL auth - username: {username[:5] if username else None}..., password len: {len(password) if password else 0}")

                response = await client.post(
                    f"{self.base_url}/rates",
                    headers=self.headers,
                    auth=(username, password) if username and password else None,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 404:
                    # Try without product code - let DHL select best product
                    logger.info("Retrying without product code")
                    payload.pop('productCode', None)
                    response = await client.post(
                        f"{self.base_url}/rates",
                        headers=self.headers,
                        auth=(username, password) if username and password else None,
                        json=payload,
                        timeout=30.0
                    )

                if response.status_code != 200:
                    logger.error("DHL API error response", status=response.status_code, body=response.text)
                response.raise_for_status()

                data = response.json()

                # Parse response - handle different response structures
                if 'products' not in data or not data['products']:
                    logger.error("No products in DHL response", response=data)
                    raise Exception("No shipping products available for this route")

                # Find first product with a price (skip free/zero-price options)
                product = None
                for p in data['products']:
                    has_price = False
                    if 'totalPrice' in p and p['totalPrice']:
                        for price_item in p['totalPrice']:
                            if price_item.get('price', 0) > 0:
                                has_price = True
                                break
                    if has_price:
                        product = p
                        break

                # Fallback to first product if all are free
                if not product:
                    product = data['products'][0]

                # Get price information - handle DHL's multiple currency format
                price = 0
                currency = 'USD'
                if 'totalPrice' in product and product['totalPrice']:
                    # DHL returns array with different currency types (BILLC, PULCL, BASEC)
                    # Look for the one with priceCurrency (usually the second one)
                    for price_item in product['totalPrice']:
                        if 'priceCurrency' in price_item:
                            price = price_item.get('price', 0)
                            currency = price_item.get('priceCurrency', 'USD')
                            break
                    # Fallback to first non-zero price
                    if price == 0:
                        for price_item in product['totalPrice']:
                            if price_item.get('price', 0) > 0:
                                price = price_item.get('price', 0)
                                # Default to USD if no currency specified
                                currency = price_item.get('priceCurrency', 'USD')
                                break

                return QuoteResponse(
                    quote_id=f"DHL-{datetime.now().timestamp()}",
                    carrier="DHL",
                    service_type=product.get('productName', 'EXPRESS'),
                    amount=price,
                    currency=currency,
                    estimated_days=self._parse_transit_time(product.get('deliveryCapabilities')),
                    valid_until=datetime.now() + timedelta(hours=24),
                    breakdown={
                        'base_charge': price,
                        'fuel_surcharge': 0  # Simplified for now
                    }
                )
                
        except httpx.HTTPError as e:
            logger.error("DHL quote request failed", error=str(e))
            raise Exception(f"DHL API error: {str(e)}")
    
    async def generate_label(self, request: LabelRequest) -> LabelResponse:
        """Generate shipping label with DHL"""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare shipment request
                payload = {
                    "plannedShippingDateAndTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S GMT+00:00"),
                    "pickup": {
                        "isRequested": False
                    },
                    "accounts": [
                        {
                            "typeCode": "shipper",
                            "number": self.credentials['account_number']
                        }
                    ],
                    "outputImageProperties": {
                        "encodingFormat": "pdf",
                        "imageOptions": [
                            {
                                "typeCode": "label",
                                "templateName": "ECOM26_84_001"
                            }
                        ]
                    },
                    "customerDetails": {
                        "shipperDetails": self._format_address_details(request.origin),
                        "receiverDetails": self._format_address_details(request.destination)
                    },
                    "content": {
                        "packages": [
                            {
                                "weight": pkg.weight_kg,
                                "dimensions": {
                                    "length": pkg.length_cm,
                                    "width": pkg.width_cm,
                                    "height": pkg.height_cm
                                },
                                "customerReferences": [
                                    {
                                        "value": request.order_id,
                                        "typeCode": "CU"
                                    }
                                ]
                            } for pkg in request.packages
                        ],
                        "isCustomsDeclarable": request.customs_documents is not None,
                        "description": "Shipment",
                        "incoterm": "DAP",
                        "unitOfMeasurement": "metric"
                    }
                }
                
                # Add customs information if applicable
                if request.customs_documents:
                    payload["content"]["exportDeclaration"] = {
                        "lineItems": [
                            {
                                "number": idx + 1,
                                "description": pkg.description or "Merchandise",
                                "price": pkg.declared_value or 0,
                                "quantity": {
                                    "value": 1,
                                    "unitOfMeasurement": "PCS"
                                },
                                "weight": {
                                    "netValue": pkg.weight_kg,
                                    "grossValue": pkg.weight_kg
                                }
                            } for idx, pkg in enumerate(request.packages)
                        ],
                        "invoice": {
                            "number": request.reference_number or request.order_id,
                            "date": datetime.now().strftime("%Y-%m-%d")
                        }
                    }
                
                # Make API call
                # Make API call with Basic Auth
                response = await client.post(
                    f"{self.base_url}/shipments",
                    headers=self.headers,
                    auth=(self.credentials['username'], self.credentials['password']),
                    json=payload,
                    timeout=60.0
                )
                if response.status_code != 200:
                    logger.error("DHL API error response", status=response.status_code, body=response.text)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract label information
                shipment = data['shipmentTrackingNumber']
                documents = data.get('documents', [])
                label_doc = next((doc for doc in documents if doc['typeCode'] == 'label'), None)
                
                return LabelResponse(
                    tracking_number=shipment,
                    carrier="DHL",
                    label_data=label_doc.get('content') if label_doc else None,
                    awb_number=data.get('shipmentIdentificationNumber'),
                    estimated_delivery=datetime.now() + timedelta(days=3),  # Parse from response
                    cost=data.get('totalPrice', [{}])[0].get('price', 0),
                    currency=data.get('totalPrice', [{}])[0].get('currency', 'USD')
                )
                
        except httpx.HTTPError as e:
            logger.error("DHL label generation failed", error=str(e))
            raise Exception(f"DHL API error: {str(e)}")
    
    async def track_shipment(self, tracking_number: str) -> TrackingResponse:
        """Track DHL shipment"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/shipments/{tracking_number}/tracking",
                    headers=self.headers,
                    auth=(self.credentials['username'], self.credentials['password']),
                    params={"trackingView": "all-checkpoints"},
                    timeout=30.0
                )
                if response.status_code != 200:
                    logger.error("DHL API error response", status=response.status_code, body=response.text)
                response.raise_for_status()
                
                data = response.json()
                shipment = data['shipments'][0]
                
                # Parse tracking events
                events = []
                for event in shipment.get('events', []):
                    events.append(TrackingEvent(
                        date=datetime.fromisoformat(event['date']),
                        status=event['typeCode'],
                        description=event['description'],
                        location=event.get('location', {}).get('address', {}).get('addressLocality')
                    ))
                
                # Determine current status
                status = shipment['status']['statusCode']
                delivered = status == 'delivered'
                
                return TrackingResponse(
                    tracking_number=tracking_number,
                    carrier="DHL",
                    status=status,
                    current_location=shipment.get('status', {}).get('location', {}).get('address', {}).get('addressLocality'),
                    estimated_delivery=datetime.fromisoformat(shipment['estimatedTimeOfDelivery']) if 'estimatedTimeOfDelivery' in shipment else None,
                    delivered_date=datetime.fromisoformat(shipment['actualTimeOfDelivery']) if delivered and 'actualTimeOfDelivery' in shipment else None,
                    events=events,
                    proof_of_delivery={
                        'signature': shipment.get('proofOfDelivery', {}).get('signatureImage'),
                        'signed_by': shipment.get('proofOfDelivery', {}).get('signedBy')
                    } if delivered else None
                )
                
        except httpx.HTTPError as e:
            logger.error("DHL tracking failed", error=str(e))
            raise Exception(f"DHL API error: {str(e)}")
    
    async def schedule_pickup(self, request: PickupRequest) -> PickupResponse:
        """Schedule pickup with DHL"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "plannedPickupDateAndTime": request.pickup_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "accounts": [
                        {
                            "typeCode": "shipper",
                            "number": self.credentials['account_number']
                        }
                    ],
                    "customerDetails": {
                        "shipperDetails": self._format_address_details(request.address)
                    },
                    "shipmentDetails": [
                        {
                            "productCode": "P",  # Express Worldwide
                            "accounts": [
                                {
                                    "typeCode": "shipper",
                                    "number": self.credentials['account_number']
                                }
                            ],
                            "packages": [
                                {
                                    "typeCode": "3BX",
                                    "weight": request.total_weight_kg / request.packages_count
                                } for _ in range(request.packages_count)
                            ]
                        }
                    ],
                    "pickupDetails": {
                        "readyByTime": request.pickup_window_start,
                        "latestReadyTime": request.pickup_window_end
                    },
                    "remarks": request.special_instructions
                }
                
                response = await client.post(
                    f"{self.base_url}/pickups",
                    headers=self.headers,
                    auth=(self.credentials['username'], self.credentials['password']),
                    json=payload,
                    timeout=30.0
                )
                if response.status_code != 200:
                    logger.error("DHL API error response", status=response.status_code, body=response.text)
                response.raise_for_status()
                
                data = response.json()
                
                return PickupResponse(
                    confirmation_number=data['confirmationNumber'],
                    carrier="DHL",
                    pickup_date=request.pickup_date,
                    pickup_window=f"{request.pickup_window_start}-{request.pickup_window_end}",
                    status="scheduled"
                )
                
        except httpx.HTTPError as e:
            logger.error("DHL pickup scheduling failed", error=str(e))
            raise Exception(f"DHL API error: {str(e)}")
    
    def _get_product_code(self, service_type: Optional[str]) -> str:
        """Map service type to DHL product code"""
        mapping = {
            "express": "P",  # Express Worldwide
            "overnight": "N",  # Express 9:00
            "same_day": "I",  # Express 12:00
            "economy": "U",  # Express Worldwide Economy
            "standard": "P"  # Default to Express Worldwide
        }
        return mapping.get(service_type, "P")
    
    def _format_address_details(self, address) -> Dict:
        """Format address for DHL API"""
        return {
            "postalAddress": {
                "cityName": address.city,
                "countryCode": address.country,
                "postalCode": address.postal_code,
                "addressLine1": address.street,
                "addressLine2": address.state
            },
            "contactInformation": {
                "companyName": address.company or address.contact_name,
                "fullName": address.contact_name,
                "phone": address.contact_phone,
                "email": address.contact_email
            }
        }
    
    def _parse_transit_time(self, capabilities: Optional[Dict]) -> int:
        """Parse transit time from DHL response"""
        if not capabilities:
            return 5  # Default
        
        # Extract estimated days from delivery capabilities
        total_transit = capabilities.get('totalTransitDays')
        if total_transit:
            return int(total_transit)
        
        return 5  # Default