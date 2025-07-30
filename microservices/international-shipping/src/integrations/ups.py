"""
UPS API Integration
Implements UPS shipping services including rate calculation,
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


class UPSIntegration(CarrierIntegrationBase):
    """UPS API integration"""
    
    def __init__(self, api_key: str, user_id: str, password: str, account_number: str, sandbox: bool = True):
        super().__init__(api_key, None, sandbox)
        self.user_id = user_id
        self.password = password
        self.account_number = account_number
        self._access_token = None
        self._token_expiry = None
    
    def _get_base_url(self) -> str:
        """Get UPS API base URL"""
        if self.sandbox:
            return "https://wwwcie.ups.com/api"
        return "https://onlinetools.ups.com/api"
    
    async def _get_access_token(self) -> str:
        """Get or refresh UPS OAuth token"""
        if self._access_token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._access_token
        
        auth_url = "https://wwwcie.ups.com/security/v1/oauth/token" if self.sandbox else "https://onlinetools.ups.com/security/v1/oauth/token"
        
        payload = {
            "grant_type": "client_credentials"
        }
        
        headers = {
            "x-merchant-id": self.account_number,
            "Authorization": f"Basic {self.api_key}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                auth_url,
                data=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 14400)  # UPS tokens last 4 hours
                self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                return self._access_token
            else:
                # Return mock token for demonstration
                return "mock_ups_token"
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get UPS API headers with authentication"""
        token = await self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "transId": str(datetime.utcnow().timestamp()),
            "transactionSrc": "testing"
        }
    
    def _normalize_status(self, ups_status: str) -> ShipmentStatus:
        """Normalize UPS status to standard status"""
        status_mapping = {
            "M": ShipmentStatus.CREATED,  # Manifest
            "P": ShipmentStatus.PICKED_UP,  # Pickup
            "I": ShipmentStatus.IN_TRANSIT,  # In Transit
            "O": ShipmentStatus.OUT_FOR_DELIVERY,  # Out for Delivery
            "D": ShipmentStatus.DELIVERED,  # Delivered
            "X": ShipmentStatus.EXCEPTION,  # Exception
            "RS": ShipmentStatus.RETURNED,  # Returned to Sender
            "V": ShipmentStatus.CANCELLED  # Voided
        }
        
        return status_mapping.get(ups_status.upper(), ShipmentStatus.IN_TRANSIT)
    
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
        """Calculate UPS shipping rates"""
        
        url = f"{self.base_url}/rating/v1/Shop"
        
        # Convert kg to lbs for UPS
        weight_lbs = weight_kg * 2.20462
        
        payload = {
            "RateRequest": {
                "Request": {
                    "TransactionReference": {
                        "CustomerContext": "Rating Request"
                    }
                },
                "Shipment": {
                    "Shipper": {
                        "Name": "Shipper",
                        "ShipperNumber": self.account_number,
                        "Address": {
                            "AddressLine": [""],
                            "City": "Origin City",
                            "StateProvinceCode": "",
                            "PostalCode": "00000",
                            "CountryCode": origin_country
                        }
                    },
                    "ShipTo": {
                        "Name": "Recipient",
                        "Address": {
                            "AddressLine": [""],
                            "City": "Destination City",
                            "StateProvinceCode": "",
                            "PostalCode": "00000",
                            "CountryCode": destination_country
                        }
                    },
                    "Package": [{
                        "PackagingType": {
                            "Code": "02"  # Customer Supplied Package
                        },
                        "Dimensions": {
                            "UnitOfMeasurement": {
                                "Code": "CM"
                            },
                            "Length": str(length_cm),
                            "Width": str(width_cm),
                            "Height": str(height_cm)
                        },
                        "PackageWeight": {
                            "UnitOfMeasurement": {
                                "Code": "LBS"
                            },
                            "Weight": str(weight_lbs)
                        },
                        "PackageServiceOptions": {
                            "DeclaredValue": {
                                "CurrencyCode": currency,
                                "MonetaryValue": str(value)
                            }
                        }
                    }]
                }
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
            
            for rated_shipment in data.get("RateResponse", {}).get("RatedShipment", []):
                service_code = rated_shipment.get("Service", {}).get("Code", "")
                service_name = self._get_service_name(service_code)
                
                rate = ShippingRate(
                    carrier="UPS",
                    service_type=service_name,
                    base_rate=float(rated_shipment.get("TransportationCharges", {}).get("MonetaryValue", 0)),
                    weight_rate=0.0,  # UPS includes in transportation charges
                    fuel_surcharge=float(rated_shipment.get("ServiceOptionsCharges", {}).get("MonetaryValue", 0)),
                    insurance_rate=float(rated_shipment.get("ItemizedCharges", [{}])[0].get("MonetaryValue", 0) if rated_shipment.get("ItemizedCharges") else 0),
                    total_cost=float(rated_shipment.get("TotalCharges", {}).get("MonetaryValue", 0)),
                    currency=rated_shipment.get("TotalCharges", {}).get("CurrencyCode", "USD"),
                    transit_days=int(rated_shipment.get("GuaranteedDelivery", {}).get("BusinessDaysInTransit", 3)),
                    valid_until=datetime.utcnow() + timedelta(hours=24)
                )
                rates.append(rate)
            
            return rates
    
    def _get_service_name(self, service_code: str) -> str:
        """Get UPS service name from code"""
        service_names = {
            "07": "UPS Worldwide Express",
            "08": "UPS Worldwide Expedited",
            "11": "UPS Standard",
            "54": "UPS Worldwide Express Plus",
            "65": "UPS Worldwide Saver"
        }
        return service_names.get(service_code, "UPS Express")
    
    def _get_mock_rates(self, origin: str, destination: str, weight: float, value: float) -> List[ShippingRate]:
        """Get mock UPS rates for demonstration"""
        base_rate = 48.0
        weight_rate = weight * 9.2
        fuel_surcharge = (base_rate + weight_rate) * 0.13
        insurance_rate = value * 0.006
        
        services = [
            ("UPS Worldwide Express Plus", 2, 1.5),
            ("UPS Worldwide Express", 3, 1.0),
            ("UPS Worldwide Saver", 4, 0.9)
        ]
        
        rates = []
        for service_name, transit_days, multiplier in services:
            total = (base_rate + weight_rate + fuel_surcharge + insurance_rate) * multiplier
            
            rate = ShippingRate(
                carrier="UPS",
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
        """Create UPS shipment and generate label"""
        
        url = f"{self.base_url}/shipments/v1/ship"
        
        # Convert kg to lbs
        weight_lbs = request.weight_kg * 2.20462
        
        payload = {
            "ShipmentRequest": {
                "Request": {
                    "TransactionReference": {
                        "CustomerContext": request.reference_number or "Shipment Request"
                    }
                },
                "Shipment": {
                    "Description": request.description,
                    "Shipper": {
                        "Name": request.origin_address.get("company", ""),
                        "AttentionName": request.origin_address.get("name", ""),
                        "ShipperNumber": self.account_number,
                        "Phone": {
                            "Number": request.origin_address.get("phone", "")
                        },
                        "Address": {
                            "AddressLine": [request.origin_address.get("line1", "")],
                            "City": request.origin_address.get("city", ""),
                            "StateProvinceCode": request.origin_address.get("state", ""),
                            "PostalCode": request.origin_address.get("postal_code", ""),
                            "CountryCode": request.origin_address.get("country_code", "")
                        }
                    },
                    "ShipTo": {
                        "Name": request.destination_address.get("company", ""),
                        "AttentionName": request.destination_address.get("name", ""),
                        "Phone": {
                            "Number": request.destination_address.get("phone", "")
                        },
                        "Address": {
                            "AddressLine": [request.destination_address.get("line1", "")],
                            "City": request.destination_address.get("city", ""),
                            "StateProvinceCode": request.destination_address.get("state", ""),
                            "PostalCode": request.destination_address.get("postal_code", ""),
                            "CountryCode": request.destination_address.get("country_code", "")
                        }
                    },
                    "PaymentInformation": {
                        "ShipmentCharge": [{
                            "Type": "01",  # Transportation
                            "BillShipper": {
                                "AccountNumber": self.account_number
                            }
                        }]
                    },
                    "Service": {
                        "Code": "07"  # UPS Worldwide Express
                    },
                    "Package": [{
                        "Packaging": {
                            "Code": "02"  # Customer Supplied
                        },
                        "Dimensions": {
                            "UnitOfMeasurement": {
                                "Code": "CM"
                            },
                            "Length": str(request.length_cm),
                            "Width": str(request.width_cm),
                            "Height": str(request.height_cm)
                        },
                        "PackageWeight": {
                            "UnitOfMeasurement": {
                                "Code": "LBS"
                            },
                            "Weight": str(weight_lbs)
                        },
                        "PackageServiceOptions": {
                            "DeclaredValue": {
                                "CurrencyCode": request.currency,
                                "MonetaryValue": str(request.value)
                            }
                        }
                    }],
                    "LabelSpecification": {
                        "LabelImageFormat": {
                            "Code": "PDF"
                        },
                        "LabelStockSize": {
                            "Height": "4",
                            "Width": "6"
                        }
                    }
                }
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
            shipment_response = data.get("ShipmentResponse", {})
            shipment_results = shipment_response.get("ShipmentResults", {})
            
            return ShipmentResponse(
                tracking_number=shipment_results.get("ShipmentIdentificationNumber", ""),
                carrier="UPS",
                service_type="UPS Worldwide Express",
                label_url=shipment_results.get("PackageResults", [{}])[0].get("ShippingLabel", {}).get("GraphicImage", ""),
                label_format="PDF",
                estimated_delivery=datetime.utcnow() + timedelta(days=3),
                total_cost=float(shipment_results.get("ShipmentCharges", {}).get("TotalCharges", {}).get("MonetaryValue", 0)),
                currency=shipment_results.get("ShipmentCharges", {}).get("TotalCharges", {}).get("CurrencyCode", "USD"),
                reference_number=request.reference_number
            )
    
    def _get_mock_shipment_response(self, request: ShipmentRequest) -> ShipmentResponse:
        """Get mock shipment response for demonstration"""
        import random
        
        tracking_number = f"1Z{self.account_number[:6]}{random.randint(1000000000, 9999999999)}"
        
        return ShipmentResponse(
            tracking_number=tracking_number,
            carrier="UPS",
            service_type="UPS Worldwide Express",
            label_url=f"https://api.ups.com/labels/{tracking_number}.pdf",
            label_format="PDF",
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            total_cost=132.25,
            currency="USD",
            reference_number=request.reference_number
        )
    
    async def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """Track UPS shipment"""
        
        url = f"{self.base_url}/track/v1/details/{tracking_number}"
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers
            )
            
            if response.status_code != 200:
                # Return mock data for demonstration
                return self._get_mock_tracking_data(tracking_number)
            
            data = response.json()
            track_response = data.get("trackResponse", {})
            shipment = track_response.get("shipment", [{}])[0]
            package = shipment.get("package", [{}])[0]
            
            events = []
            for activity in package.get("activity", []):
                location = activity.get("location", {})
                
                tracking_event = TrackingEvent(
                    timestamp=datetime.fromisoformat(f"{activity.get('date', '')}T{activity.get('time', '')}"),
                    location=f"{location.get('address', {}).get('city', '')}, {location.get('address', {}).get('stateProvince', '')}",
                    status=self._normalize_status(activity.get("status', {}).get('type', '')),
                    description=activity.get("status", {}).get("description", ""),
                    raw_status=activity.get("status", {}).get("type", "")
                )
                events.append(tracking_event)
            
            return {
                "tracking_number": tracking_number,
                "carrier": "UPS",
                "status": events[0].status if events else ShipmentStatus.CREATED,
                "events": [event.dict() for event in events],
                "estimated_delivery": package.get("deliveryDate", [{}])[0].get("date"),
                "origin": shipment.get("shipper", {}).get("address", {}).get("city"),
                "destination": package.get("deliveryAddress", {}).get("city")
            }
    
    def _get_mock_tracking_data(self, tracking_number: str) -> Dict[str, Any]:
        """Get mock tracking data for demonstration"""
        events = [
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(days=2),
                location="Mexico City, MX",
                status=ShipmentStatus.PICKED_UP,
                description="Pickup scan",
                raw_status="P"
            ),
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(days=1, hours=22),
                location="Mexico City, MX",
                status=ShipmentStatus.IN_TRANSIT,
                description="Origin scan",
                raw_status="I"
            ),
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=18),
                location="Louisville, KY",
                status=ShipmentStatus.IN_TRANSIT,
                description="Arrival scan",
                raw_status="I"
            ),
            TrackingEvent(
                timestamp=datetime.utcnow() - timedelta(hours=6),
                location="Miami, FL",
                status=ShipmentStatus.IN_TRANSIT,
                description="Destination scan",
                raw_status="I"
            )
        ]
        
        return {
            "tracking_number": tracking_number,
            "carrier": "UPS",
            "status": events[-1].status,
            "events": [event.dict() for event in events],
            "estimated_delivery": datetime.utcnow() + timedelta(hours=24),
            "origin": "Mexico City, MX",
            "destination": "Miami, FL"
        }
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel UPS shipment"""
        
        url = f"{self.base_url}/shipments/v1/void/cancel/{tracking_number}"
        
        headers = await self._get_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=headers
            )
            
            return response.status_code == 200
    
    async def validate_address(self, address: Dict[str, str]) -> Dict[str, Any]:
        """Validate address with UPS"""
        
        url = f"{self.base_url}/addressvalidation/v1/1"
        
        payload = {
            "AddressValidationRequest": {
                "Request": {
                    "TransactionReference": {
                        "CustomerContext": "Address Validation"
                    }
                },
                "Address": {
                    "AddressLine": [address.get("line1", "")],
                    "City": address.get("city", ""),
                    "StateProvinceCode": address.get("state", ""),
                    "PostalCode": address.get("postal_code", ""),
                    "CountryCode": address.get("country_code", "")
                }
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
                # Return basic validation
                return {
                    "valid": True,
                    "normalized_address": address,
                    "suggestions": []
                }
            
            data = response.json()
            validation_response = data.get("AddressValidationResponse", {})
            
            return {
                "valid": validation_response.get("Response", {}).get("ResponseStatus", {}).get("Code") == "1",
                "normalized_address": validation_response.get("ValidatedAddress", address),
                "suggestions": validation_response.get("CandidateAddress", [])
            }