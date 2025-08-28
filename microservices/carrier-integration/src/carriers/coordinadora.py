"""
Coordinadora Carrier Integration
Colombian logistics provider with nationwide coverage
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from decimal import Decimal
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring

from ..error_handlers import CarrierError, ValidationError, AuthenticationError

logger = logging.getLogger(__name__)


class CoordinadoraCarrier:
    """
    Coordinadora carrier implementation for Colombian shipping
    """
    
    # API Configuration
    BASE_URL = "https://api.coordinadora.com/cm-api-rest"
    SANDBOX_URL = "https://sandbox.coordinadora.com/cm-api-rest"
    
    # Service types mapping
    SERVICE_TYPES = {
        'standard': 'NOR',  # Normal
        'express': 'EXP',   # Express
        'documents': 'DOC', # Documents
        'heavy': 'CAR',     # Heavy cargo
        'reverse': 'REV'    # Reverse logistics
    }
    
    # Status mapping
    STATUS_MAP = {
        '1': 'pending',
        '2': 'picked_up',
        '3': 'in_transit',
        '4': 'out_for_delivery',
        '5': 'delivered',
        '6': 'exception',
        '7': 'returned',
        '8': 'cancelled'
    }
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize Coordinadora carrier
        
        Args:
            credentials: Dictionary containing:
                - api_key: API key
                - api_password: API password
                - nit: Company NIT
                - client_code: Client code
                - sandbox: Use sandbox environment (default: False)
        """
        self.api_key = credentials.get('api_key')
        self.api_password = credentials.get('api_password')
        self.nit = credentials.get('nit')
        self.client_code = credentials.get('client_code')
        self.sandbox = credentials.get('sandbox', False)
        
        if not all([self.api_key, self.api_password, self.nit]):
            raise ValueError("Coordinadora requires api_key, api_password, and nit")
        
        self.base_url = self.SANDBOX_URL if self.sandbox else self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Set authentication headers
        self._setup_authentication()
    
    def _setup_authentication(self):
        """Setup authentication headers"""
        auth_string = f"{self.api_key}:{self.api_password}"
        auth_hash = hashlib.sha256(auth_string.encode()).hexdigest()
        
        self.session.headers.update({
            'Authorization': f'Bearer {auth_hash}',
            'X-API-Key': self.api_key,
            'X-NIT': self.nit
        })
        
        if self.client_code:
            self.session.headers['X-Client-Code'] = self.client_code
    
    def calculate_quote(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate shipping quote
        
        Args:
            shipment_data: Shipment details including origin, destination, packages
        
        Returns:
            Quote information with rates and transit times
        """
        try:
            # Build quote request for Coordinadora
            quote_request = {
                'origen': {
                    'ciudad': self._get_city_code(shipment_data['origin'].get('city')),
                    'direccion': shipment_data['origin'].get('street', ''),
                    'telefono': shipment_data['origin'].get('phone', '')
                },
                'destino': {
                    'ciudad': self._get_city_code(shipment_data['destination'].get('city')),
                    'direccion': shipment_data['destination'].get('street', ''),
                    'telefono': shipment_data['destination'].get('phone', '')
                },
                'unidades': self._format_packages_for_quote(shipment_data.get('packages', [])),
                'tipo_servicio': self.SERVICE_TYPES.get(
                    shipment_data.get('service_type', 'standard'),
                    'NOR'
                ),
                'valor_declarado': shipment_data.get('declared_value', 0),
                'tipo_pago': shipment_data.get('payment_type', 'CONTADO')
            }
            
            response = self.session.post(
                f"{self.base_url}/cotizador/cotizar",
                json=quote_request,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Quote calculation failed: {response.text}")
            
            quote_data = response.json()
            
            # Format response
            services = []
            for service in quote_data.get('servicios', []):
                services.append({
                    'code': service['codigo'],
                    'name': service['nombre'],
                    'transit_days': service.get('dias_entrega', 1),
                    'estimated_delivery': self._calculate_delivery_date(service.get('dias_entrega', 1)),
                    'cost': {
                        'amount': float(service['valor_total']),
                        'currency': 'COP',
                        'breakdown': {
                            'base_rate': float(service.get('valor_flete', 0)),
                            'handling': float(service.get('valor_manejo', 0)),
                            'insurance': float(service.get('valor_seguro', 0)),
                            'tax': float(service.get('valor_iva', 0))
                        }
                    },
                    'available': True
                })
            
            return {
                'carrier': 'coordinadora',
                'quote_id': quote_data.get('numero_cotizacion'),
                'valid_until': (datetime.now() + timedelta(days=7)).isoformat(),
                'services': services,
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
        try:
            # Build shipment request
            request_data = {
                'remitente': self._format_sender(shipment_data['origin']),
                'destinatario': self._format_recipient(shipment_data['destination']),
                'unidades': self._format_packages_for_shipment(shipment_data.get('packages', [])),
                'tipo_servicio': self.SERVICE_TYPES.get(
                    shipment_data.get('service_type', 'standard'),
                    'NOR'
                ),
                'valor_declarado': shipment_data.get('declared_value', 0),
                'observaciones': shipment_data.get('special_instructions', ''),
                'referencia': shipment_data.get('reference', ''),
                'contenido': shipment_data.get('content_description', 'Merchandise'),
                'cuenta_pago': self.client_code or self.nit,
                'tipo_pago': shipment_data.get('payment_type', 'CONTADO')
            }
            
            # Add collection date if provided
            if shipment_data.get('collection_date'):
                request_data['fecha_recogida'] = shipment_data['collection_date']
            
            response = self.session.post(
                f"{self.base_url}/envios/generar",
                json=request_data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Shipment creation failed: {response.text}")
            
            result = response.json()
            
            # Get label URL
            label_url = f"{self.base_url}/envios/etiqueta/{result['numero_guia']}"
            
            return {
                'carrier': 'coordinadora',
                'tracking_number': result['numero_guia'],
                'shipment_id': result.get('id_envio'),
                'label_url': label_url,
                'status': 'created',
                'service_type': shipment_data.get('service_type', 'standard'),
                'estimated_delivery': result.get('fecha_estimada_entrega'),
                'cost': {
                    'amount': float(result.get('valor_total', 0)),
                    'currency': 'COP'
                }
            }
            
        except Exception as e:
            logger.error(f"Shipment creation error: {e}")
            raise CarrierError(f"Failed to create shipment: {str(e)}")
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """
        Track a shipment
        
        Args:
            tracking_number: Tracking number (guía)
        
        Returns:
            Tracking information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/seguimiento/consultar/{tracking_number}",
                timeout=30
            )
            
            if response.status_code == 404:
                raise CarrierError(f"Shipment not found: {tracking_number}")
            elif response.status_code != 200:
                raise CarrierError(f"Tracking failed: {response.text}")
            
            tracking_data = response.json()
            
            # Map status
            current_status = self.STATUS_MAP.get(
                tracking_data.get('estado_codigo', '1'),
                'pending'
            )
            
            # Format tracking events
            events = []
            for event in tracking_data.get('movimientos', []):
                events.append({
                    'timestamp': event['fecha_hora'],
                    'status': self.STATUS_MAP.get(event.get('estado_codigo', ''), 'in_transit'),
                    'description': event['descripcion'],
                    'location': {
                        'city': event.get('ciudad'),
                        'state': event.get('departamento'),
                        'country': 'CO'
                    }
                })
            
            return {
                'carrier': 'coordinadora',
                'tracking_number': tracking_number,
                'status': current_status,
                'status_description': tracking_data.get('estado_descripcion'),
                'last_update': tracking_data.get('fecha_actualizacion'),
                'current_location': {
                    'city': tracking_data.get('ciudad_actual'),
                    'state': tracking_data.get('departamento_actual'),
                    'country': 'CO'
                },
                'origin': {
                    'city': tracking_data.get('ciudad_origen'),
                    'state': tracking_data.get('departamento_origen')
                },
                'destination': {
                    'city': tracking_data.get('ciudad_destino'),
                    'state': tracking_data.get('departamento_destino')
                },
                'estimated_delivery': tracking_data.get('fecha_estimada_entrega'),
                'actual_delivery': tracking_data.get('fecha_entrega'),
                'events': events,
                'proof_of_delivery': {
                    'signature': tracking_data.get('firma_recibido'),
                    'name': tracking_data.get('nombre_recibe'),
                    'identification': tracking_data.get('identificacion_recibe'),
                    'relationship': tracking_data.get('parentesco')
                } if tracking_data.get('fecha_entrega') else None
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
        try:
            cancel_data = {
                'numero_guia': tracking_number,
                'motivo': reason or 'Solicitud del cliente',
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            response = self.session.post(
                f"{self.base_url}/envios/anular",
                json=cancel_data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Cancellation failed: {response.text}")
            
            result = response.json()
            
            return {
                'carrier': 'coordinadora',
                'tracking_number': tracking_number,
                'status': 'cancelled',
                'cancelled_at': result.get('fecha_anulacion'),
                'confirmation': result.get('confirmacion')
            }
            
        except Exception as e:
            logger.error(f"Cancellation error: {e}")
            raise CarrierError(f"Failed to cancel shipment: {str(e)}")
    
    def generate_label(self, tracking_number: str, format: str = 'PDF') -> bytes:
        """
        Generate shipping label
        
        Args:
            tracking_number: Tracking number
            format: Label format (PDF, ZPL)
        
        Returns:
            Label data as bytes
        """
        try:
            params = {
                'formato': format.upper(),
                'tipo': 'etiqueta'
            }
            
            response = self.session.get(
                f"{self.base_url}/envios/etiqueta/{tracking_number}",
                params=params,
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
        try:
            # Format pickup request for Coordinadora
            request_data = {
                'fecha_recogida': pickup_data['pickup_date'],
                'hora_inicio': pickup_data.get('time_start', '08:00'),
                'hora_fin': pickup_data.get('time_end', '18:00'),
                'direccion': self._format_address(pickup_data.get('address', {})),
                'contacto': {
                    'nombre': pickup_data.get('contact_name'),
                    'telefono': pickup_data.get('contact_phone'),
                    'email': pickup_data.get('contact_email')
                },
                'guias': pickup_data.get('tracking_numbers', []),
                'observaciones': pickup_data.get('instructions', '')
            }
            
            response = self.session.post(
                f"{self.base_url}/recogidas/programar",
                json=request_data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Pickup scheduling failed: {response.text}")
            
            result = response.json()
            
            return {
                'carrier': 'coordinadora',
                'pickup_id': result['numero_recogida'],
                'confirmation_number': result.get('confirmacion'),
                'status': 'scheduled',
                'pickup_date': result['fecha_recogida'],
                'time_window': f"{result.get('hora_inicio')} - {result.get('hora_fin')}"
            }
            
        except Exception as e:
            logger.error(f"Pickup scheduling error: {e}")
            raise CarrierError(f"Failed to schedule pickup: {str(e)}")
    
    def get_coverage(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check service coverage for a location
        
        Args:
            location_data: Location information (city, postal_code)
        
        Returns:
            Coverage information
        """
        try:
            params = {
                'ciudad': self._get_city_code(location_data.get('city')),
                'tipo_servicio': location_data.get('service_type', 'NOR')
            }
            
            response = self.session.get(
                f"{self.base_url}/cobertura/consultar",
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Coverage check failed: {response.text}")
            
            coverage = response.json()
            
            return {
                'carrier': 'coordinadora',
                'covered': coverage.get('cobertura', False),
                'city': location_data.get('city'),
                'services_available': coverage.get('servicios_disponibles', []),
                'transit_days': coverage.get('dias_entrega'),
                'restrictions': coverage.get('restricciones', [])
            }
            
        except Exception as e:
            logger.error(f"Coverage check error: {e}")
            raise CarrierError(f"Failed to check coverage: {str(e)}")
    
    def validate_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an address
        
        Args:
            address: Address to validate
        
        Returns:
            Validation result
        """
        try:
            # Coordinadora address validation
            validation_request = {
                'ciudad': self._get_city_code(address.get('city')),
                'direccion': address.get('street', ''),
                'barrio': address.get('neighborhood', ''),
                'telefono': address.get('phone', '')
            }
            
            response = self.session.post(
                f"{self.base_url}/direcciones/validar",
                json=validation_request,
                timeout=30
            )
            
            if response.status_code != 200:
                raise ValidationError(f"Address validation failed: {response.text}")
            
            result = response.json()
            
            return {
                'valid': result.get('valida', False),
                'normalized_address': result.get('direccion_normalizada'),
                'city_code': result.get('codigo_ciudad'),
                'zone': result.get('zona'),
                'warnings': result.get('advertencias', [])
            }
            
        except Exception as e:
            logger.error(f"Address validation error: {e}")
            raise ValidationError(f"Failed to validate address: {str(e)}")
    
    def get_cities(self) -> List[Dict[str, Any]]:
        """
        Get list of cities served by Coordinadora
        
        Returns:
            List of cities with codes
        """
        try:
            response = self.session.get(
                f"{self.base_url}/ciudades/listar",
                timeout=30
            )
            
            if response.status_code != 200:
                raise CarrierError(f"Cities retrieval failed: {response.text}")
            
            cities = response.json()
            
            return [
                {
                    'code': city['codigo'],
                    'name': city['nombre'],
                    'state': city['departamento'],
                    'zone': city.get('zona')
                }
                for city in cities
            ]
            
        except Exception as e:
            logger.error(f"Cities retrieval error: {e}")
            raise CarrierError(f"Failed to get cities: {str(e)}")
    
    def _get_city_code(self, city_name: str) -> str:
        """
        Get city code from city name
        
        Args:
            city_name: City name
        
        Returns:
            City code
        """
        # This would typically use a cached mapping
        # For now, return a default or lookup
        city_codes = {
            'Bogotá': '11001',
            'Medellín': '05001',
            'Cali': '76001',
            'Barranquilla': '08001',
            'Cartagena': '13001',
            'Bucaramanga': '68001',
            'Pereira': '66001',
            'Manizales': '17001',
            'Cúcuta': '54001',
            'Ibagué': '73001'
        }
        return city_codes.get(city_name, '11001')  # Default to Bogotá
    
    def _format_sender(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """Format sender information for Coordinadora"""
        return {
            'nombre': address.get('name', ''),
            'nit': address.get('nit', self.nit),
            'direccion': address.get('street', ''),
            'telefono': address.get('phone', ''),
            'ciudad': self._get_city_code(address.get('city', '')),
            'email': address.get('email', '')
        }
    
    def _format_recipient(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """Format recipient information for Coordinadora"""
        return {
            'nombre': address.get('name', ''),
            'identificacion': address.get('identification', ''),
            'direccion': f"{address.get('street', '')} {address.get('number', '')}",
            'telefono': address.get('phone', ''),
            'ciudad': self._get_city_code(address.get('city', '')),
            'email': address.get('email', ''),
            'barrio': address.get('neighborhood', '')
        }
    
    def _format_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """Format address for Coordinadora API"""
        return {
            'direccion': f"{address.get('street', '')} {address.get('number', '')}",
            'ciudad': self._get_city_code(address.get('city', '')),
            'barrio': address.get('neighborhood', ''),
            'referencias': address.get('reference', '')
        }
    
    def _format_packages_for_quote(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format packages for quote calculation"""
        formatted = []
        for pkg in packages:
            formatted.append({
                'peso': float(pkg.get('weight', 0)),
                'largo': float(pkg.get('length', 0)),
                'ancho': float(pkg.get('width', 0)),
                'alto': float(pkg.get('height', 0)),
                'cantidad': int(pkg.get('quantity', 1)),
                'valor_declarado': float(pkg.get('value', 0))
            })
        return formatted
    
    def _format_packages_for_shipment(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format packages for shipment creation"""
        formatted = []
        for i, pkg in enumerate(packages):
            formatted.append({
                'numero': i + 1,
                'peso': float(pkg.get('weight', 0)),
                'largo': float(pkg.get('length', 0)),
                'ancho': float(pkg.get('width', 0)),
                'alto': float(pkg.get('height', 0)),
                'cantidad': int(pkg.get('quantity', 1)),
                'valor_declarado': float(pkg.get('value', 0)),
                'contenido': pkg.get('description', 'Merchandise'),
                'referencia': pkg.get('reference', f"PKG-{i+1}")
            })
        return formatted
    
    def _calculate_delivery_date(self, transit_days: int) -> str:
        """Calculate estimated delivery date"""
        # Skip weekends
        delivery_date = datetime.now()
        days_added = 0
        while days_added < transit_days:
            delivery_date += timedelta(days=1)
            if delivery_date.weekday() < 5:  # Monday = 0, Friday = 4
                days_added += 1
        return delivery_date.isoformat()