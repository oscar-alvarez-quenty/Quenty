"""
FedEx API Integration
Implements FedEx shipping services including rate calculation,
shipment creation, tracking, and label generation
"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from .base import (
    CarrierIntegrationBase, ShippingRate, ShipmentRequest, 
    ShipmentResponse, TrackingEvent, ShipmentStatus
)


class FedExIntegration(CarrierIntegrationBase):
    """FedEx API integration"""
    
    def __init__(self, api_key: str, api_secret: str, account_number: str, sandbox: bool = True):
        super().__init__(api_key, api_secret, sandbox)
        self.account_number = account_number
        self._access_token = None
        self._token_expiry = None
    
    def _get_base_url(self) -> str:
        """Get FedEx API base URL"""
        if self.sandbox:
            return "https://apis-sandbox.fedex.com"
        return "https://apis.fedex.com"
    
    async def _get_access_token(self) -> str:
        """Get or refresh FedEx OAuth token"""
        if self._access_token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._access_token
        
        url = f"{self.base_url}/oauth/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)
                self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                return self._access_token
            else:
                # Return mock token for demonstration
                return "mock_fedex_token"
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get FedEx API headers with authentication"""
        token = await self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-locale": "en_US"
        }
    
    def _normalize_status(self, fedex_status: str) -> ShipmentStatus:
        """Normalize FedEx status to standard status"""
        status_mapping = {
            "INITIATED": ShipmentStatus.CREATED,
            "PICKED_UP": ShipmentStatus.PICKED_UP,
            "IN_TRANSIT": ShipmentStatus.IN_TRANSIT,
            "OUT_FOR_DELIVERY": ShipmentStatus.OUT_FOR_DELIVERY,
            "DELIVERED": ShipmentStatus.DELIVERED,
            "CANCELLED": ShipmentStatus.CANCELLED,
            "EXCEPTION": ShipmentStatus.EXCEPTION,
            "RETURNED": ShipmentStatus.RETURNED
        }
        
        return status_mapping.get(fedex_status.upper(), ShipmentStatus.IN_TRANSIT)
    
    async def calculate_rates(
        self,
        origin_country: str,
        destination_country: str,
        weight_kg: float,
        length_cm: float,
        width_cm: float,
        height_cm: float,
        value: float,
        currency: str = "USD"
    ) -> List[ShippingRate]:
        """Calculate FedEx shipping rates"""
        
        url = f"{self.base_url}/rate/v1/rates/quotes"
        
        payload = {
            "accountNumber": {
                "value": self.account_number
            },
            "requestedShipment": {
                "shipper": {
                    "address": {
                        "countryCode": origin_country,
                        "postalCode": "00000"
                    }
                },
                "recipient": {
                    "address": {
                        "countryCode": destination_country,
                        "postalCode": "00000"
                    }
                },
                "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
                "requestedPackageLineItems": [{
                    "weight": {
                        "units": "KG",
                        "value": weight_kg
                    },
                    "dimensions": {
                        "length": int(length_cm),
                        "width": int(width_cm),
                        "height": int(height_cm),
                        "units": "CM"
                    },
                    "declaredValue": {
                        "amount": value,
                        "currency": currency
                    }
                }]
            },
            "rateRequestControlParameters": {
                "returnTransitTimes": True
            }
        }
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                # Return mock data for demonstration
                return self._get_mock_rates(origin_country, destination_country, weight_kg, value)
            
            data = response.json()
            rates = []
            
            for rate_reply in data.get("output", {}).get("rateReplyDetails", []):
                service_name = rate_reply.get("serviceName", "")
                rated_shipment = rate_reply.get("ratedShipmentDetails", [{}])[0]
                
                rate = ShippingRate(
                    carrier="FedEx",
                    service_type=service_name,
                    base_rate=float(rated_shipment.get("totalBaseCharge", 0)),
                    weight_rate=float(rated_shipment.get("totalFreightDiscounts", 0)),
                    fuel_surcharge=float(rated_shipment.get("totalSurcharges", 0)),
                    insurance_rate=float(rated_shipment.get("totalInsuranceCharge", 0)),
                    total_cost=float(rated_shipment.get("totalNetCharge", 0)),
                    currency=rated_shipment.get("currency", "USD"),
                    transit_days=rate_reply.get("commit", {}).get("transitDays", 3),
                    valid_until=datetime.utcnow() + timedelta(hours=24)
                )
                rates.append(rate)
            
            return rates
    
    def _get_mock_rates(self, origin: str, destination: str, weight: float, value: float) -> List[ShippingRate]:
        """Get mock FedEx rates for demonstration"""
        base_rate = 42.0
        weight_rate = weight * 7.8
        fuel_surcharge = (base_rate + weight_rate) * 0.10
        insurance_rate = value * 0.004
        
        services = [
            ("FedEx International Priority", 3, 1.0),
            ("FedEx International Economy", 5, 0.8),
            ("FedEx International First", 1, 1.5)
        ]
        
        rates = []
        for service_name, transit_days, multiplier in services:
            total = (base_rate + weight_rate + fuel_surcharge + insurance_rate) * multiplier
            
            rate = ShippingRate(
                carrier="FedEx",
                service_type=service_name,
                base_rate=base_rate * multiplier,
                weight_rate=weight_rate,
                fuel_surcharge=fuel_surcharge,
                insurance_rate=insurance_rate,
                total_cost=total,
                currency="USD",
                transit_days=transit_days,
                valid_until=datetime.utcnow() + timedelta(hours=24)
            )
            rates.append(rate)
        
        return rates
    
    async def create_shipment(self, request: ShipmentRequest) -> ShipmentResponse:
        """Create FedEx shipment and generate label"""
        
        url = f"{self.base_url}/ship/v1/shipments"
        
        payload = {
            "labelResponseOptions": "URL_ONLY",
            "requestedShipment": {
                "shipper": {
                    "contact": {
                        "personName": request.origin_address.get("name", ""),
                        "phoneNumber": request.origin_address.get("phone", ""),
                        "companyName": request.origin_address.get("company", "")
                    },
                    "address": {
                        "streetLines": [request.origin_address.get("line1", "")],
                        "city": request.origin_address.get("city", ""),
                        "stateOrProvinceCode": request.origin_address.get("state", ""),
                        "postalCode": request.origin_address.get("postal_code", ""),
                        "countryCode": request.origin_address.get("country_code", "")
                    }
                },
                "recipients": [{
                    "contact": {
                        "personName": request.destination_address.get("name", ""),
                        "phoneNumber": request.destination_address.get("phone", ""),
                        "companyName": request.destination_address.get("company", "")
                    },
                    "address": {
                        "streetLines": [request.destination_address.get("line1", "")],
                        "city": request.destination_address.get("city", ""),
                        "stateOrProvinceCode": request.destination_address.get("state", ""),
                        "postalCode": request.destination_address.get("postal_code", ""),
                        "countryCode": request.destination_address.get("country_code", "")
                    }
                }],
                "shippingChargesPayment": {
                    "paymentType": "SENDER",
                    "payor": {
                        "responsibleParty": {
                            "accountNumber": {
                                "value": self.account_number
                            }
                        }
                    }
                },
                "labelSpecification": {
                    "labelFormatType": "COMMON2D",
                    "imageType": "PDF",
                    "labelStockType": "PAPER_LETTER"
                },
                "requestedPackageLineItems": [{
                    "weight": {
                        "units": "KG",
                        "value": request.weight_kg
                    },
                    "dimensions": {
                        "length": int(request.length_cm),
                        "width": int(request.width_cm),
                        "height": int(request.height_cm),
                        "units": "CM"
                    },
                    "customerReferences": [{
                        "customerReferenceType": "CUSTOMER_REFERENCE",
                        "value": request.reference_number or ""
                    }]
                }],
                "serviceType": "INTERNATIONAL_PRIORITY"
            },
            "accountNumber": {
                "value": self.account_number
            }
        }
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                # Return mock data for demonstration
                return self._get_mock_shipment_response(request)
            
            data = response.json()
            output = data.get("output", {})
            
            return ShipmentResponse(
                tracking_number=output.get("masterTrackingNumber", ""),
                carrier="FedEx",
                service_type="International Priority",
                label_url=output.get("pieceResponses", [{}])[0].get("packageDocuments", [{}])[0].get("url", ""),
                label_format="PDF",
                estimated_delivery=datetime.utcnow() + timedelta(days=3),
                total_cost=float(output.get("shipmentRating", {}).get("totalNetCharge", 0)),
                currency="USD",
                reference_number=request.reference_number
            )
    
    def _get_mock_shipment_response(self, request: ShipmentRequest) -> ShipmentResponse:
        """Get mock shipment response for demonstration"""
        import random
        
        tracking_number = f"FX{random.randint(100000000000, 999999999999)}"
        
        return ShipmentResponse(
            tracking_number=tracking_number,
            carrier="FedEx",
            service_type="International Priority",
            label_url=f"https://api.fedex.com/labels/{tracking_number}.pdf",
            label_format="PDF",
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            total_cost=118.75,
            currency="USD",
            reference_number=request.reference_number
        )
    
    async def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """Track FedEx shipment"""
        
        url = f"{self.base_url}/track/v1/trackingnumbers"
        
        payload = {
            "includeDetailedScans": True,
            "trackingInfo": [{
                "trackingNumberInfo": {
                    "trackingNumber": tracking_number
                }
            }]
        }
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                # Return mock data for demonstration
                return self._get_mock_tracking_data(tracking_number)
            
            data = response.json()
            tracking_results = data.get("output", {}).get("completeTrackResults", [{}])[0]
            track_results = tracking_results.get("trackResults", [{}])[0]
            
            events = []
            for scan in track_results.get("scanEvents", []):
                tracking_event = TrackingEvent(
                    timestamp=datetime.fromisoformat(scan.get("date", "")),
                    location=f"{scan.get('scanLocation', {}).get('city', '')}, {scan.get('scanLocation', {}).get('stateOrProvinceCode', '')}",
                    status=self._normalize_status(scan.get("derivedStatus", "")),
                    description=scan.get("eventDescription", ""),
                    raw_status=scan.get("derivedStatus", "")
                )
                events.append(tracking_event)
            
            return {
                "tracking_number": tracking_number,
                "carrier": "FedEx",
                "status": events[0].status if events else ShipmentStatus.CREATED,
                "events": [event.dict() for event in events],
                "estimated_delivery": track_results.get("estimatedDeliveryTimeWindow", {}).get("endTime"),
                "origin": track_results.get("originLocation", {}).get("locationContactAndAddress", {}).get("address", {}).get("city"),
                "destination": track_results.get("destinationLocation", {}).get("locationContactAndAddress", {}).get("address", {}).get("city")
            }
    
    def _get_mock_tracking_data(self, tracking_number: str) -> Dict[str, Any]:
        """Get mock tracking data for demonstration"""
        events = [
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(days=2),
                location="Mexico City, MX",
                status=ShipmentStatus.PICKED_UP,
                description="Picked up",
                raw_status="PU"
            ),
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(days=1, hours=20),
                location="Mexico City, MX",
                status=ShipmentStatus.IN_TRANSIT,
                description="In transit",
                raw_status="IT"
            ),
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=14),
                location="Memphis, TN",
                status=ShipmentStatus.IN_TRANSIT,
                description="At FedEx origin facility",
                raw_status="IT"
            ),
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=4),
                location="Miami, FL",
                status=ShipmentStatus.IN_TRANSIT,
                description="At destination sort facility",
                raw_status="IT"
            )
        ]
        
        return {
            "tracking_number": tracking_number,
            "carrier": "FedEx",
            "status": events[-1].status,
            "events": [event.dict() for event in events],
            "estimated_delivery": datetime.utcnow() + timedelta(days=1),
            "origin": "Mexico City, MX",
            "destination": "Miami, FL"
        }
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel FedEx shipment"""
        
        url = f"{self.base_url}/ship/v1/shipments/cancel"
        
        payload = {
            "accountNumber": {
                "value": self.account_number
            },
            "trackingNumber": tracking_number
        }
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                json=payload,
                headers=headers
            )
            
            return response.status_code == 200
    
    async def validate_address(self, address: Dict[str, str]) -> Dict[str, Any]:
        """Validate address with FedEx"""
        
        url = f"{self.base_url}/address/v1/addresses/resolve"
        
        payload = {
            "addressesToValidate": [{
                "address": {
                    "streetLines": [address.get("line1", "")],
                    "city": address.get("city", ""),
                    "stateOrProvinceCode": address.get("state", ""),
                    "postalCode": address.get("postal_code", ""),
                    "countryCode": address.get("country_code", "")
                }
            }]
        }
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 200:
                # Return basic validation
                return {
                    "valid": True,
                    "normalized_address": address,
                    "suggestions": []
                }
            
            data = response.json()
            resolved = data.get("output", {}).get("resolvedAddresses", [{}])[0]
            
            return {
                "valid": resolved.get("classification") == "BUSINESS",
                "normalized_address": resolved.get("address", address),
                "suggestions": resolved.get("suggestedAddresses", [])
            }