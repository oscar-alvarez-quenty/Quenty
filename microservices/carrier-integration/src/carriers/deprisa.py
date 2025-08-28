"""
Deprisa Carrier Integration
Colombian logistics provider for domestic and express shipping
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from decimal import Decimal
import base64

from ..error_handlers import CarrierError, ValidationError, AuthenticationError

logger = logging.getLogger(__name__)


class DeprisaCarrier:
    """
    Deprisa carrier implementation for Colombian shipping
    """
    
    # API Configuration
    BASE_URL = "https://api.deprisa.com/v2"
    SANDBOX_URL = "https://sandbox-api.deprisa.com/v2"
    
    # Service types mapping
    SERVICE_TYPES = {
        'express': 'DEP-EXP',
        'standard': 'DEP-STD',
        'economy': 'DEP-ECO',
        'same_day': 'DEP-SD',
        'next_day': 'DEP-ND',
        'documents': 'DEP-DOC',
        'merchandise': 'DEP-MER'
    }
    
    # Status mapping
    STATUS_MAP = {
        'CREATED': 'pending',
        'COLLECTED': 'picked_up',
        'IN_TRANSIT': 'in_transit',
        'OUT_FOR_DELIVERY': 'out_for_delivery',
        'DELIVERED': 'delivered',
        'EXCEPTION': 'exception',
        'RETURNED': 'returned',
        'CANCELLED': 'cancelled'
    }
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Deprisa carrier
        
        Args:
            credentials: Dictionary containing:
                - client_id: API client ID
                - client_secret: API client secret
                - account_number: Deprisa account number
                - sandbox: Use sandbox environment (default: False)
        """
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.account_number = credentials.get('account_number')
        self.sandbox = credentials.get('sandbox', False)
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Deprisa requires client_id and client_secret")
        
        self.base_url = self.SANDBOX_URL if self.sandbox else self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'CarrierIntegration/1.0'
        })
        
        self.access_token = None
        self.token_expires_at = None
        
        # Authenticate on initialization
        self.authenticate()
    
    def authenticate(self) -> bool:
        """
        Authenticate with Deprisa API
        
        Returns:
            True if authentication successful
        
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            endpoint = f"{self.base_url}/auth/token"
            
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            if self.account_number:
                auth_data['account_number'] = self.account_number
            
            response = self.session.post(endpoint, json=auth_data, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                expires_in = data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Update session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                logger.info("Successfully authenticated with Deprisa")
                return True
            else:
                raise AuthenticationError(f"Deprisa authentication failed: {response.text}")
                
        except requests.RequestException as e:
            raise AuthenticationError(f"Deprisa authentication error: {str(e)}")
    
    def ensure_authenticated(self):
        """Ensure valid authentication token"""
        if not self.access_token or not self.token_expires_at:
            self.authenticate()
        elif datetime.now() >= self.token_expires_at:
            logger.info("Token expired, re-authenticating...")
            self.authenticate()
    
    def calculate_quote(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate shipping quote
        
        Args:
            shipment_data: Shipment details including origin, destination, packages
        
        Returns:
            Quote information with rates and transit times
        """
        self.ensure_authenticated()
        
        try:
            # Build quote request
            quote_request = {
                'origin': self._format_address(shipment_data['origin']),
                'destination': self._format_address(shipment_data['destination']),
                'packages': self._format_packages(shipment_data.get('packages', [])),
                'service_type': shipment_data.get('service_type', 'standard'),
                'insurance': shipment_data.get('insurance', False),
                'declared_value': shipment_data.get('declared_value', 0),
                'collection_date': shipment_data.get('collection_date')
            }
            
            response = self.session.post(
                f"{self.base_url}/shipping/quote",
                json=quote_request,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Quote calculation failed: {response.text}")
            
            quote_data = response.json()
            
            # Format response
            return {
                'carrier': 'deprisa',
                'quote_id': quote_data.get('quote_id'),
                'valid_until': quote_data.get('valid_until'),
                'services': self._format_services(quote_data.get('services', [])),
                'total_weight': sum(p.get('weight', 0) for p in shipment_data.get('packages', [])),
                'currency': 'COP'
            }
            
        except Exception as e:
            logger.error(f"Quote calculation error: {e}")
            raise CarrierError(f"Failed to calculate quote: {str(e)}")
    
    def create_shipment(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a shipment
        
        Args:
            shipment_data: Complete shipment information
        
        Returns:
            Shipment details with tracking number
        """
        self.ensure_authenticated()
        
        try:
            # Prepare shipment request
            if 'quote_id' in shipment_data:
                # Create from existing quote
                request_data = {
                    'quote_id': shipment_data['quote_id'],
                    'reference': shipment_data.get('reference'),
                    'collection_date': shipment_data.get('collection_date'),
                    'special_instructions': shipment_data.get('special_instructions')
                }
            else:
                # Direct creation
                request_data = {
                    'origin': self._format_address(shipment_data['origin']),
                    'destination': self._format_address(shipment_data['destination']),
                    'packages': self._format_packages(shipment_data.get('packages', [])),
                    'service_type': self.SERVICE_TYPES.get(
                        shipment_data.get('service_type', 'standard'),
                        'DEP-STD'
                    ),
                    'reference': shipment_data.get('reference'),
                    'collection_date': shipment_data.get('collection_date'),
                    'special_instructions': shipment_data.get('special_instructions'),
                    'options': {
                        'email_notifications': True,
                        'sms_notifications': shipment_data['destination'].get('phone') is not None,
                        'proof_of_delivery': True,
                        'signature_required': shipment_data.get('signature_required', True)
                    }
                }
            
            response = self.session.post(
                f"{self.base_url}/shipping/create",
                json=request_data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Shipment creation failed: {response.text}")
            
            result = response.json()
            
            return {
                'carrier': 'deprisa',
                'tracking_number': result['tracking_number'],
                'shipment_id': result['shipment_id'],
                'label_url': result.get('label_url'),
                'status': 'created',
                'service_type': result['service']['name'],
                'estimated_delivery': result.get('estimated_delivery'),
                'cost': {
                    'amount': result['pricing']['total'],
                    'currency': result['pricing']['currency']
                }
            }
            
        except Exception as e:
            logger.error(f"Shipment creation error: {e}")
            raise CarrierError(f"Failed to create shipment: {str(e)}")
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """
        Track a shipment
        
        Args:
            tracking_number: Tracking number
        
        Returns:
            Tracking information
        """
        self.ensure_authenticated()
        
        try:
            response = self.session.get(
                f"{self.base_url}/tracking/{tracking_number}",
                timeout=30
            )
            
            if response.status_code == 404:
                raise CarrierError(f"Shipment not found: {tracking_number}")
            elif response.status_code != 200:
                raise CarrierError(f"Tracking failed: {response.text}")
            
            tracking_data = response.json()
            
            return {
                'carrier': 'deprisa',
                'tracking_number': tracking_number,
                'status': self.STATUS_MAP.get(
                    tracking_data['status'],
                    tracking_data['status'].lower()
                ),
                'status_description': tracking_data.get('status_description'),
                'last_update': tracking_data.get('last_update'),
                'current_location': {
                    'city': tracking_data.get('current_city'),
                    'state': tracking_data.get('current_state'),
                    'country': 'CO'
                },
                'estimated_delivery': tracking_data.get('estimated_delivery'),
                'actual_delivery': tracking_data.get('delivered_at'),
                'events': self._format_tracking_events(tracking_data.get('events', [])),
                'proof_of_delivery': tracking_data.get('proof_of_delivery')
            }
            
        except Exception as e:
            logger.error(f"Tracking error: {e}")
            raise CarrierError(f"Failed to track shipment: {str(e)}")
    
    def cancel_shipment(self, tracking_number: str, reason: str = None) -> Dict[str, Any]:
        """
        Cancel a shipment
        
        Args:
            tracking_number: Tracking number
            reason: Cancellation reason
        
        Returns:
            Cancellation confirmation
        """
        self.ensure_authenticated()
        
        try:
            cancel_data = {
                'reason': reason or 'Customer request',
                'requested_by': 'API Client'
            }
            
            response = self.session.post(
                f"{self.base_url}/shipping/shipments/{tracking_number}/cancel",
                json=cancel_data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Cancellation failed: {response.text}")
            
            result = response.json()
            
            return {
                'carrier': 'deprisa',
                'tracking_number': tracking_number,
                'status': 'cancelled',
                'cancelled_at': result.get('cancelled_at'),
                'refund': result.get('refund')
            }
            
        except Exception as e:
            logger.error(f"Cancellation error: {e}")
            raise CarrierError(f"Failed to cancel shipment: {str(e)}")
    
    def generate_label(self, tracking_number: str, format: str = 'PDF') -> bytes:
        """
        Generate shipping label
        
        Args:
            tracking_number: Tracking number
            format: Label format (PDF, ZPL, PNG)
        
        Returns:
            Label data as bytes
        """
        self.ensure_authenticated()
        
        try:
            response = self.session.get(
                f"{self.base_url}/labels/{tracking_number}",
                params={'format': format},
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Label generation failed: {response.text}")
            
            return response.content
            
        except Exception as e:
            logger.error(f"Label generation error: {e}")
            raise CarrierError(f"Failed to generate label: {str(e)}")
    
    def schedule_pickup(self, pickup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a pickup
        
        Args:
            pickup_data: Pickup details
        
        Returns:
            Pickup confirmation
        """
        self.ensure_authenticated()
        
        try:
            request_data = {
                'tracking_numbers': pickup_data.get('tracking_numbers', []),
                'pickup_date': pickup_data['pickup_date'],
                'time_window': pickup_data.get('time_window', 'AM'),
                'address': self._format_address(pickup_data.get('address', {})),
                'contact': {
                    'name': pickup_data.get('contact_name'),
                    'phone': pickup_data.get('contact_phone'),
                    'email': pickup_data.get('contact_email')
                },
                'special_instructions': pickup_data.get('instructions', '')
            }
            
            response = self.session.post(
                f"{self.base_url}/pickup/schedule",
                json=request_data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Pickup scheduling failed: {response.text}")
            
            result = response.json()
            
            return {
                'carrier': 'deprisa',
                'pickup_id': result['pickup_id'],
                'confirmation_number': result.get('confirmation_number'),
                'status': 'scheduled',
                'pickup_date': result['pickup_date'],
                'time_window': result['time_window']
            }
            
        except Exception as e:
            logger.error(f"Pickup scheduling error: {e}")
            raise CarrierError(f"Failed to schedule pickup: {str(e)}")
    
    def get_service_points(self, location_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get service points near a location
        
        Args:
            location_data: Location information (city, postal_code, coordinates)
        
        Returns:
            List of nearby service points
        """
        self.ensure_authenticated()
        
        try:
            params = {
                'city': location_data.get('city'),
                'postal_code': location_data.get('postal_code'),
                'radius_km': location_data.get('radius', 10)
            }
            
            if location_data.get('latitude') and location_data.get('longitude'):
                params['latitude'] = location_data['latitude']
                params['longitude'] = location_data['longitude']
            
            response = self.session.get(
                f"{self.base_url}/service-points",
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Service points query failed: {response.text}")
            
            points = response.json().get('service_points', [])
            
            return [
                {
                    'carrier': 'deprisa',
                    'point_id': point['point_id'],
                    'name': point['name'],
                    'type': point.get('type'),
                    'address': {
                        'street': point.get('street'),
                        'city': point.get('city'),
                        'state': point.get('state'),
                        'postal_code': point.get('postal_code'),
                        'country': 'CO'
                    },
                    'coordinates': {
                        'latitude': point.get('latitude'),
                        'longitude': point.get('longitude')
                    },
                    'hours': point.get('hours'),
                    'services': point.get('services', [])
                }
                for point in points
            ]
            
        except Exception as e:
            logger.error(f"Service points error: {e}")
            raise CarrierError(f"Failed to get service points: {str(e)}")
    
    def validate_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an address
        
        Args:
            address: Address to validate
        
        Returns:
            Validation result with standardized address
        """
        self.ensure_authenticated()
        
        try:
            response = self.session.post(
                f"{self.base_url}/address/validate",
                json=self._format_address(address),
                timeout=30
            )
            
            if response.status_code != 200:
                raise ValidationError(f"Address validation failed: {response.text}")
            
            result = response.json()
            
            return {
                'valid': result.get('valid', False),
                'standardized': result.get('standardized_address'),
                'suggestions': result.get('suggestions', []),
                'warnings': result.get('warnings', [])
            }
            
        except Exception as e:
            logger.error(f"Address validation error: {e}")
            raise ValidationError(f"Failed to validate address: {str(e)}")
    
    def get_transit_times(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Get transit times between cities
        
        Args:
            origin: Origin city
            destination: Destination city
        
        Returns:
            Transit time information by service
        """
        self.ensure_authenticated()
        
        try:
            params = {
                'origin': origin,
                'destination': destination
            }
            
            response = self.session.get(
                f"{self.base_url}/transit-times",
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Transit times query failed: {response.text}")
            
            data = response.json()
            
            return {
                'origin': origin,
                'destination': destination,
                'services': data.get('services', []),
                'zone': data.get('zone'),
                'distance_km': data.get('distance_km')
            }
            
        except Exception as e:
            logger.error(f"Transit times error: {e}")
            raise CarrierError(f"Failed to get transit times: {str(e)}")
    
    def _format_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """Format address for Deprisa API"""
        return {
            'name': address.get('name', ''),
            'company': address.get('company', ''),
            'street': address.get('street', ''),
            'number': address.get('number', ''),
            'apartment': address.get('apartment', ''),
            'neighborhood': address.get('neighborhood', ''),
            'city': address.get('city', ''),
            'state': address.get('state', ''),
            'postal_code': address.get('postal_code', ''),
            'country_code': address.get('country_code', 'CO'),
            'phone': address.get('phone', ''),
            'email': address.get('email', ''),
            'reference': address.get('reference', '')
        }
    
    def _format_packages(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format packages for Deprisa API"""
        formatted = []
        for pkg in packages:
            formatted.append({
                'weight': float(pkg.get('weight', 0)),  # kg
                'length': float(pkg.get('length', 0)),  # cm
                'width': float(pkg.get('width', 0)),    # cm
                'height': float(pkg.get('height', 0)),  # cm
                'value': float(pkg.get('value', 0)),    # COP
                'quantity': int(pkg.get('quantity', 1)),
                'description': pkg.get('description', ''),
                'type': pkg.get('type', 'BOX'),
                'reference': pkg.get('reference', '')
            })
        return formatted
    
    def _format_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format service options from quote"""
        formatted = []
        for service in services:
            formatted.append({
                'code': service['code'],
                'name': service['name'],
                'transit_days': service['transit_days'],
                'estimated_delivery': service.get('estimated_delivery'),
                'cost': {
                    'amount': service['pricing']['total'],
                    'currency': service['pricing']['currency'],
                    'breakdown': {
                        'base_rate': service['pricing'].get('base_rate'),
                        'fuel_surcharge': service['pricing'].get('fuel_surcharge'),
                        'insurance': service['pricing'].get('insurance'),
                        'tax': service['pricing'].get('tax')
                    }
                },
                'cutoff_time': service.get('cutoff_time'),
                'available': service.get('available', True)
            })
        return formatted
    
    def _format_tracking_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tracking events"""
        formatted = []
        for event in events:
            formatted.append({
                'timestamp': event['timestamp'],
                'status': self.STATUS_MAP.get(event['status'], event['status'].lower()),
                'description': event['description'],
                'location': {
                    'city': event.get('city'),
                    'state': event.get('state'),
                    'country': 'CO'
                }
            })
        return formatted