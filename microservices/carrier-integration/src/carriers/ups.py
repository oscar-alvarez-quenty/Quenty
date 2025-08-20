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

class UPSClient:
    """UPS Developer Kit API Client"""
    
    def __init__(self, credentials: Dict[str, Any], environment: str = "production"):
        self.credentials = credentials
        self.environment = environment
        self.base_url = self._get_base_url()
        self.access_token = None
        self.token_expires = None
        
    def _get_base_url(self) -> str:
        """Get UPS API base URL based on environment"""
        if self.environment == "sandbox":
            return "https://wwwcie.ups.com/api"
        return "https://onlinetools.ups.com/api"
    
    async def _get_access_token(self) -> str:
        """Get or refresh OAuth 2.0 access token"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/security/v1/oauth/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "x-merchant-id": self.credentials.get('merchant_id', '')
                },
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.credentials['client_id'],
                    "client_secret": self.credentials['client_secret']
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=data['expires_in'] - 60)
            
            return self.access_token
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_quote(self, request: QuoteRequest) -> QuoteResponse:
        """Get shipping quote from UPS"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "RateRequest": {
                        "Request": {
                            "TransactionReference": {
                                "CustomerContext": f"Quote-{datetime.now().timestamp()}"
                            }
                        },
                        "Shipment": {
                            "Shipper": {
                                "Name": request.origin.contact_name,
                                "ShipperNumber": self.credentials['shipper_number'],
                                "Address": {
                                    "AddressLine": [request.origin.street],
                                    "City": request.origin.city,
                                    "StateProvinceCode": request.origin.state,
                                    "PostalCode": request.origin.postal_code,
                                    "CountryCode": request.origin.country
                                }
                            },
                            "ShipTo": {
                                "Name": request.destination.contact_name,
                                "Address": {
                                    "AddressLine": [request.destination.street],
                                    "City": request.destination.city,
                                    "StateProvinceCode": request.destination.state,
                                    "PostalCode": request.destination.postal_code,
                                    "CountryCode": request.destination.country
                                }
                            },
                            "ShipFrom": {
                                "Name": request.origin.contact_name,
                                "Address": {
                                    "AddressLine": [request.origin.street],
                                    "City": request.origin.city,
                                    "StateProvinceCode": request.origin.state,
                                    "PostalCode": request.origin.postal_code,
                                    "CountryCode": request.origin.country
                                }
                            },
                            "Service": {
                                "Code": self._get_service_code(request.service_type)
                            },
                            "Package": [
                                {
                                    "PackagingType": {
                                        "Code": "02"  # Customer Supplied Package
                                    },
                                    "Dimensions": {
                                        "UnitOfMeasurement": {
                                            "Code": "CM"
                                        },
                                        "Length": str(pkg.length_cm),
                                        "Width": str(pkg.width_cm),
                                        "Height": str(pkg.height_cm)
                                    },
                                    "PackageWeight": {
                                        "UnitOfMeasurement": {
                                            "Code": "KGS"
                                        },
                                        "Weight": str(pkg.weight_kg)
                                    }
                                } for pkg in request.packages
                            ]
                        }
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/rating/v2/Rate",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "transId": f"quote-{datetime.now().timestamp()}",
                        "transactionSrc": "Quenty"
                    },
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                rated_shipment = data['RateResponse']['RatedShipment'][0]
                
                return QuoteResponse(
                    quote_id=f"UPS-{datetime.now().timestamp()}",
                    carrier="UPS",
                    service_type=self._get_service_name(rated_shipment['Service']['Code']),
                    amount=float(rated_shipment['TotalCharges']['MonetaryValue']),
                    currency=rated_shipment['TotalCharges']['CurrencyCode'],
                    estimated_days=self._parse_transit_days(rated_shipment),
                    valid_until=datetime.now() + timedelta(hours=24),
                    breakdown={
                        'base_charge': float(rated_shipment['TransportationCharges']['MonetaryValue']),
                        'service_charge': float(rated_shipment.get('ServiceOptionsCharges', {}).get('MonetaryValue', 0))
                    }
                )
                
        except httpx.HTTPError as e:
            logger.error("UPS quote request failed", error=str(e))
            raise Exception(f"UPS API error: {str(e)}")
    
    async def generate_label(self, request: LabelRequest) -> LabelResponse:
        """Generate shipping label with UPS"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "ShipmentRequest": {
                        "Request": {
                            "TransactionReference": {
                                "CustomerContext": request.order_id
                            }
                        },
                        "Shipment": {
                            "Description": "Shipment",
                            "Shipper": {
                                "Name": request.origin.contact_name,
                                "AttentionName": request.origin.contact_name,
                                "CompanyDisplayableName": request.origin.company or request.origin.contact_name,
                                "ShipperNumber": self.credentials['shipper_number'],
                                "Phone": {
                                    "Number": request.origin.contact_phone
                                },
                                "Address": {
                                    "AddressLine": [request.origin.street],
                                    "City": request.origin.city,
                                    "StateProvinceCode": request.origin.state,
                                    "PostalCode": request.origin.postal_code,
                                    "CountryCode": request.origin.country
                                }
                            },
                            "ShipTo": {
                                "Name": request.destination.contact_name,
                                "AttentionName": request.destination.contact_name,
                                "Phone": {
                                    "Number": request.destination.contact_phone
                                },
                                "Address": {
                                    "AddressLine": [request.destination.street],
                                    "City": request.destination.city,
                                    "StateProvinceCode": request.destination.state,
                                    "PostalCode": request.destination.postal_code,
                                    "CountryCode": request.destination.country
                                }
                            },
                            "PaymentInformation": {
                                "ShipmentCharge": {
                                    "Type": "01",  # Transportation
                                    "BillShipper": {
                                        "AccountNumber": self.credentials['shipper_number']
                                    }
                                }
                            },
                            "Service": {
                                "Code": self._get_service_code(request.service_type)
                            },
                            "Package": [
                                {
                                    "Description": "Package",
                                    "Packaging": {
                                        "Code": "02"  # Customer Supplied Package
                                    },
                                    "Dimensions": {
                                        "UnitOfMeasurement": {
                                            "Code": "CM"
                                        },
                                        "Length": str(pkg.length_cm),
                                        "Width": str(pkg.width_cm),
                                        "Height": str(pkg.height_cm)
                                    },
                                    "PackageWeight": {
                                        "UnitOfMeasurement": {
                                            "Code": "KGS"
                                        },
                                        "Weight": str(pkg.weight_kg)
                                    },
                                    "ReferenceNumber": {
                                        "Code": "01",
                                        "Value": request.order_id
                                    }
                                } for pkg in request.packages
                            ]
                        },
                        "LabelSpecification": {
                            "LabelImageFormat": {
                                "Code": "PDF"
                            },
                            "LabelStockSize": {
                                "Height": "6",
                                "Width": "4"
                            }
                        }
                    }
                }
                
                # Add international forms if customs documents provided
                if request.customs_documents:
                    payload["ShipmentRequest"]["Shipment"]["InternationalForms"] = {
                        "FormType": ["01"],  # Invoice
                        "InvoiceNumber": request.reference_number or request.order_id,
                        "InvoiceDate": datetime.now().strftime("%Y%m%d"),
                        "Product": [
                            {
                                "Description": pkg.description or "Merchandise",
                                "Unit": {
                                    "Number": "1",
                                    "UnitOfMeasurement": {
                                        "Code": "PCS"
                                    },
                                    "Value": str(pkg.declared_value or 0)
                                },
                                "CommodityCode": "9999",
                                "OriginCountryCode": request.origin.country
                            } for pkg in request.packages
                        ]
                    }
                
                response = await client.post(
                    f"{self.base_url}/shipping/v1/shipments",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "transId": f"ship-{datetime.now().timestamp()}",
                        "transactionSrc": "Quenty"
                    },
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                data = response.json()
                shipment_response = data['ShipmentResponse']['ShipmentResults']
                
                # Extract tracking number and label
                tracking_number = shipment_response['PackageResults'][0]['TrackingNumber']
                label_image = shipment_response['PackageResults'][0]['ShippingLabel']['GraphicImage']
                
                return LabelResponse(
                    tracking_number=tracking_number,
                    carrier="UPS",
                    label_data=label_image,
                    barcode=tracking_number,
                    estimated_delivery=datetime.now() + timedelta(days=3),
                    cost=float(shipment_response['ShipmentCharges']['TotalCharges']['MonetaryValue']),
                    currency=shipment_response['ShipmentCharges']['TotalCharges']['CurrencyCode']
                )
                
        except httpx.HTTPError as e:
            logger.error("UPS label generation failed", error=str(e))
            raise Exception(f"UPS API error: {str(e)}")
    
    async def track_shipment(self, tracking_number: str) -> TrackingResponse:
        """Track UPS shipment"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/track/v1/details/{tracking_number}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "transId": f"track-{datetime.now().timestamp()}",
                        "transactionSrc": "Quenty"
                    },
                    params={
                        "locale": "en_US",
                        "returnSignature": "true"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                track_response = data['trackResponse']['shipment'][0]['package'][0]
                
                # Parse tracking events
                events = []
                for activity in track_response.get('activity', []):
                    events.append(TrackingEvent(
                        date=datetime.strptime(
                            f"{activity['date']} {activity.get('time', '000000')}",
                            "%Y%m%d %H%M%S"
                        ),
                        status=activity['status']['type'],
                        description=activity['status']['description'],
                        location=activity.get('location', {}).get('address', {}).get('city')
                    ))
                
                # Determine delivery status
                current_status = track_response['currentStatus']['description']
                delivered = track_response['currentStatus']['code'] == 'D'
                
                return TrackingResponse(
                    tracking_number=tracking_number,
                    carrier="UPS",
                    status=current_status,
                    current_location=track_response.get('currentStatus', {}).get('location', {}).get('address', {}).get('city'),
                    estimated_delivery=datetime.strptime(
                        track_response['deliveryDate'][0]['date'],
                        "%Y%m%d"
                    ) if 'deliveryDate' in track_response else None,
                    delivered_date=datetime.strptime(
                        track_response['deliveryDate'][0]['date'] + " " + track_response['deliveryTime']['endTime'],
                        "%Y%m%d %H%M%S"
                    ) if delivered else None,
                    events=events,
                    proof_of_delivery={
                        'signature': track_response.get('deliveryInformation', {}).get('signature'),
                        'signed_by': track_response.get('deliveryInformation', {}).get('receivedBy')
                    } if delivered else None
                )
                
        except httpx.HTTPError as e:
            logger.error("UPS tracking failed", error=str(e))
            raise Exception(f"UPS API error: {str(e)}")
    
    async def schedule_pickup(self, request: PickupRequest) -> PickupResponse:
        """Schedule pickup with UPS"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "PickupCreationRequest": {
                        "RatePickupIndicator": "N",
                        "Shipper": {
                            "Account": {
                                "AccountNumber": self.credentials['shipper_number'],
                                "AccountCountryCode": request.address.country
                            }
                        },
                        "PickupDateInfo": {
                            "CloseTime": request.pickup_window_end.replace(":", ""),
                            "ReadyTime": request.pickup_window_start.replace(":", ""),
                            "PickupDate": request.pickup_date.strftime("%Y%m%d")
                        },
                        "PickupAddress": {
                            "CompanyName": request.address.company or request.address.contact_name,
                            "ContactName": request.address.contact_name,
                            "AddressLine": request.address.street,
                            "City": request.address.city,
                            "StateProvince": request.address.state,
                            "PostalCode": request.address.postal_code,
                            "CountryCode": request.address.country,
                            "Phone": {
                                "Number": request.address.contact_phone
                            }
                        },
                        "AlternateAddressIndicator": "N",
                        "PickupPiece": [
                            {
                                "ServiceCode": "001",  # UPS Next Day Air
                                "Quantity": str(request.packages_count),
                                "DestinationCountryCode": "US",
                                "ContainerCode": "01"  # Package
                            }
                        ],
                        "TotalWeight": {
                            "Weight": str(request.total_weight_kg),
                            "UnitOfMeasurement": "KGS"
                        },
                        "PaymentMethod": "01",  # Shipper Account
                        "SpecialInstruction": request.special_instructions
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/pickup/v1/pickups",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "transId": f"pickup-{datetime.now().timestamp()}",
                        "transactionSrc": "Quenty"
                    },
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                pickup_response = data['PickupCreationResponse']
                
                return PickupResponse(
                    confirmation_number=pickup_response['PRN'],
                    carrier="UPS",
                    pickup_date=request.pickup_date,
                    pickup_window=f"{request.pickup_window_start}-{request.pickup_window_end}",
                    status="scheduled",
                    cost=float(pickup_response.get('RateResult', {}).get('GrandTotalOfAllCharge', 0)),
                    currency="USD"
                )
                
        except httpx.HTTPError as e:
            logger.error("UPS pickup scheduling failed", error=str(e))
            raise Exception(f"UPS API error: {str(e)}")
    
    async def validate_address(self, address) -> bool:
        """Validate address using UPS Address Validation API"""
        try:
            token = await self._get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/addressvalidation/v1/addressvalidation",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "XAVRequest": {
                            "AddressKeyFormat": {
                                "AddressLine": [address.street],
                                "PoliticalDivision2": address.city,
                                "PoliticalDivision1": address.state,
                                "PostcodePrimaryLow": address.postal_code,
                                "CountryCode": address.country
                            }
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                return data['XAVResponse']['ValidAddressIndicator'] == 'Y'
                
        except Exception as e:
            logger.error("UPS address validation failed", error=str(e))
            return False
    
    def _get_service_code(self, service_type: Optional[str]) -> str:
        """Map service type to UPS service code"""
        mapping = {
            "express": "07",  # UPS Worldwide Express
            "overnight": "01",  # UPS Next Day Air
            "standard": "03",  # UPS Ground
            "economy": "65",  # UPS Worldwide Saver
            "same_day": "13"  # UPS Next Day Air Saver
        }
        return mapping.get(service_type, "07")
    
    def _get_service_name(self, code: str) -> str:
        """Map UPS service code to name"""
        mapping = {
            "01": "UPS Next Day Air",
            "02": "UPS 2nd Day Air",
            "03": "UPS Ground",
            "07": "UPS Worldwide Express",
            "08": "UPS Worldwide Expedited",
            "11": "UPS Standard",
            "12": "UPS 3 Day Select",
            "13": "UPS Next Day Air Saver",
            "14": "UPS Express Early",
            "54": "UPS Worldwide Express Plus",
            "65": "UPS Worldwide Saver"
        }
        return mapping.get(code, "UPS Service")
    
    def _parse_transit_days(self, rated_shipment: Dict) -> int:
        """Parse transit days from UPS response"""
        if 'TimeInTransit' in rated_shipment:
            return int(rated_shipment['TimeInTransit']['ServiceSummary']['EstimatedArrival']['BusinessDaysInTransit'])
        return 5  # Default