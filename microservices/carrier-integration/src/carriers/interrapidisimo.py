import httpx
import json
import os
from typing import Dict, Any, Optional, List
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

class InterrapidisimoClient:
    """Interrapidisimo REST API Client for Colombian logistics"""

    def __init__(self, credentials: Dict[str, Any] = None, environment: str = None):
        # Load from environment variables if credentials not provided
        if credentials is None:
            credentials = self._load_from_env()

        self.credentials = credentials
        self.environment = environment or os.getenv('INTERRAPIDISIMO_ENVIRONMENT', 'sandbox')
        self.base_url = self._get_base_url()
        self.headers = self._get_headers()

    def _load_from_env(self) -> Dict[str, Any]:
        """Load Interrapidisimo credentials from environment variables"""
        return {
            'api_key': os.getenv('INTERRAPIDISIMO_API_KEY'),
            'client_id': os.getenv('INTERRAPIDISIMO_CLIENT_CODE'),
            'username': os.getenv('INTERRAPIDISIMO_USERNAME'),
            'password': os.getenv('INTERRAPIDISIMO_PASSWORD'),
            'contract_number': os.getenv('INTERRAPIDISIMO_CONTRACT_NUMBER')
        }
        
    def _get_base_url(self) -> str:
        """Get Interrapidisimo API base URL based on environment"""
        if self.environment == "sandbox":
            return "https://apitest.interrapidisimo.co/api/v1"
        return "https://api.interrapidisimo.co/api/v1"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.credentials['api_key'],
            "X-Client-Id": self.credentials['client_id']
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_quote(self, request: QuoteRequest) -> QuoteResponse:
        """Get shipping quote from Interrapidisimo"""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare quote request
                payload = {
                    "origen": {
                        "ciudad": request.origin.city,
                        "departamento": request.origin.state,
                        "codigoPostal": request.origin.postal_code
                    },
                    "destino": {
                        "ciudad": request.destination.city,
                        "departamento": request.destination.state,
                        "codigoPostal": request.destination.postal_code
                    },
                    "piezas": [
                        {
                            "peso": pkg.weight_kg,
                            "largo": pkg.length_cm,
                            "ancho": pkg.width_cm,
                            "alto": pkg.height_cm,
                            "valorDeclarado": pkg.declared_value or 0
                        } for pkg in request.packages
                    ],
                    "tipoServicio": self._get_service_type(request.service_type),
                    "codigoCliente": self.credentials['customer_code'],
                    "seguro": request.insurance_required
                }
                
                response = await client.post(
                    f"{self.base_url}/cotizacion",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("success"):
                    quote_data = data["data"]
                    return QuoteResponse(
                        quote_id=f"INTER-{quote_data.get('numeroCotizacion', datetime.now().timestamp())}",
                        carrier="Interrapidisimo",
                        service_type=self._map_service_name(quote_data['tipoServicio']),
                        amount=float(quote_data['valorTotal']),
                        currency="COP",
                        estimated_days=int(quote_data.get('diasEntrega', 3)),
                        valid_until=datetime.now() + timedelta(hours=24),
                        breakdown={
                            'freight': float(quote_data.get('valorFlete', 0)),
                            'management': float(quote_data.get('costoManejo', 0)),
                            'insurance': float(quote_data.get('valorSeguro', 0)),
                            'taxes': float(quote_data.get('iva', 0))
                        },
                        notes=quote_data.get('observaciones', [])
                    )
                else:
                    raise Exception(f"Quote failed: {data.get('message', 'Unknown error')}")
                    
        except httpx.HTTPError as e:
            logger.error("Interrapidisimo quote request failed", error=str(e))
            raise Exception(f"Interrapidisimo API error: {str(e)}")
    
    async def generate_label(self, request: LabelRequest) -> LabelResponse:
        """Generate shipping label (remesa) with Interrapidisimo"""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare shipment data
                payload = {
                    "remitente": {
                        "nombre": request.origin.contact_name,
                        "empresa": request.origin.company,
                        "direccion": request.origin.street,
                        "ciudad": request.origin.city,
                        "departamento": request.origin.state,
                        "codigoPostal": request.origin.postal_code,
                        "telefono": request.origin.contact_phone,
                        "email": request.origin.contact_email
                    },
                    "destinatario": {
                        "nombre": request.destination.contact_name,
                        "empresa": request.destination.company,
                        "direccion": request.destination.street,
                        "ciudad": request.destination.city,
                        "departamento": request.destination.state,
                        "codigoPostal": request.destination.postal_code,
                        "telefono": request.destination.contact_phone,
                        "email": request.destination.contact_email
                    },
                    "paquetes": [
                        {
                            "peso": pkg.weight_kg,
                            "largo": pkg.length_cm,
                            "ancho": pkg.width_cm,
                            "alto": pkg.height_cm,
                            "valorDeclarado": pkg.declared_value or 0,
                            "contenido": pkg.description or "Mercancía",
                            "referencia": request.order_id
                        } for pkg in request.packages
                    ],
                    "tipoServicio": self._get_service_type(request.service_type),
                    "codigoCliente": self.credentials['customer_code'],
                    "numeroFactura": request.reference_number or request.order_id,
                    "observaciones": f"Orden: {request.order_id}",
                    "generarRotulo": True,
                    "formatoRotulo": "PDF"
                }
                
                # Add customs info for international shipments
                if request.customs_documents:
                    payload["documentosAduaneros"] = request.customs_documents
                
                response = await client.post(
                    f"{self.base_url}/remesas",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("success"):
                    remesa = data["data"]
                    return LabelResponse(
                        tracking_number=remesa['numeroRemesa'],
                        carrier="Interrapidisimo",
                        label_url=remesa.get('urlRotulo'),
                        label_data=remesa.get('rotuloPDF'),  # Base64 encoded
                        barcode=remesa.get('codigoBarras', remesa['numeroRemesa']),
                        estimated_delivery=datetime.now() + timedelta(days=remesa.get('diasEntrega', 3)),
                        cost=float(remesa.get('valorTotal', 0)),
                        currency="COP"
                    )
                else:
                    raise Exception(f"Label generation failed: {data.get('message', 'Unknown error')}")
                    
        except httpx.HTTPError as e:
            logger.error("Interrapidisimo label generation failed", error=str(e))
            raise Exception(f"Interrapidisimo API error: {str(e)}")
    
    async def track_shipment(self, tracking_number: str) -> TrackingResponse:
        """Track Interrapidisimo shipment"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/rastreo/{tracking_number}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("success"):
                    tracking_data = data["data"]
                    
                    # Parse tracking events
                    events = []
                    for movimiento in tracking_data.get('movimientos', []):
                        events.append(TrackingEvent(
                            date=datetime.fromisoformat(movimiento['fecha']),
                            status=movimiento['estado'],
                            description=movimiento['descripcion'],
                            location=movimiento.get('ciudad'),
                            details={
                                'oficina': movimiento.get('oficina'),
                                'responsable': movimiento.get('responsable'),
                                'observaciones': movimiento.get('observaciones')
                            }
                        ))
                    
                    # Determine current status
                    current_status = tracking_data['estadoActual']
                    delivered = current_status.lower() in ['entregado', 'entregada']
                    
                    return TrackingResponse(
                        tracking_number=tracking_number,
                        carrier="Interrapidisimo",
                        status=current_status,
                        current_location=tracking_data.get('ubicacionActual'),
                        estimated_delivery=datetime.fromisoformat(
                            tracking_data['fechaEstimadaEntrega']
                        ) if tracking_data.get('fechaEstimadaEntrega') else None,
                        delivered_date=datetime.fromisoformat(
                            tracking_data['fechaEntrega']
                        ) if delivered and tracking_data.get('fechaEntrega') else None,
                        events=events,
                        proof_of_delivery={
                            'recipient': tracking_data.get('nombreRecibe'),
                            'id_number': tracking_data.get('cedulaRecibe'),
                            'signature_url': tracking_data.get('urlFirma'),
                            'photo_url': tracking_data.get('urlFoto')
                        } if delivered else None
                    )
                else:
                    raise Exception(f"Tracking failed: {data.get('message', 'Unknown error')}")
                    
        except httpx.HTTPError as e:
            logger.error("Interrapidisimo tracking failed", error=str(e))
            raise Exception(f"Interrapidisimo API error: {str(e)}")
    
    async def schedule_pickup(self, request: PickupRequest) -> PickupResponse:
        """Schedule pickup with Interrapidisimo"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "fecha": request.pickup_date.strftime("%Y-%m-%d"),
                    "horaInicio": request.pickup_window_start,
                    "horaFin": request.pickup_window_end,
                    "direccion": {
                        "direccion": request.address.street,
                        "ciudad": request.address.city,
                        "departamento": request.address.state,
                        "codigoPostal": request.address.postal_code
                    },
                    "contacto": {
                        "nombre": request.address.contact_name,
                        "empresa": request.address.company,
                        "telefono": request.address.contact_phone,
                        "email": request.address.contact_email
                    },
                    "cantidadPaquetes": request.packages_count,
                    "pesoTotal": request.total_weight_kg,
                    "codigoCliente": self.credentials['customer_code'],
                    "observaciones": request.special_instructions,
                    "remesas": request.tracking_numbers if request.tracking_numbers else []
                }
                
                response = await client.post(
                    f"{self.base_url}/recolecciones",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("success"):
                    pickup_data = data["data"]
                    return PickupResponse(
                        confirmation_number=pickup_data['numeroRecoleccion'],
                        carrier="Interrapidisimo",
                        pickup_date=request.pickup_date,
                        pickup_window=f"{request.pickup_window_start}-{request.pickup_window_end}",
                        status="scheduled",
                        cost=float(pickup_data.get('valor', 0)),
                        currency="COP"
                    )
                else:
                    raise Exception(f"Pickup scheduling failed: {data.get('message', 'Unknown error')}")
                    
        except httpx.HTTPError as e:
            logger.error("Interrapidisimo pickup scheduling failed", error=str(e))
            raise Exception(f"Interrapidisimo API error: {str(e)}")
    
    async def get_coverage(self, city: str, department: str = None) -> List[Dict]:
        """Get Interrapidisimo coverage for a city"""
        try:
            async with httpx.AsyncClient() as client:
                params = {"ciudad": city}
                if department:
                    params["departamento"] = department
                
                response = await client.get(
                    f"{self.base_url}/cobertura",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("success"):
                    return data["data"]["ciudades"]
                return []
                
        except Exception as e:
            logger.error("Failed to get coverage", error=str(e))
            return []
    
    async def validate_city(self, city: str, postal_code: str = None) -> bool:
        """Validate if city is covered by Interrapidisimo"""
        try:
            coverage = await self.get_coverage(city)
            if coverage:
                if postal_code:
                    return any(c.get('codigoPostal') == postal_code for c in coverage)
                return True
            return False
            
        except Exception as e:
            logger.error("City validation failed", error=str(e))
            return False
    
    async def get_tariffs(self, origin: str, destination: str) -> Dict:
        """Get tariff matrix between origin and destination"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tarifas",
                    headers=self.headers,
                    params={
                        "origen": origin,
                        "destino": destination,
                        "codigoCliente": self.credentials['customer_code']
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("success"):
                    return data["data"]
                return {}
                
        except Exception as e:
            logger.error("Failed to get tariffs", error=str(e))
            return {}
    
    def _get_service_type(self, service_type: Optional[str]) -> str:
        """Map service type to Interrapidisimo service code"""
        mapping = {
            "express": "HOY",      # Entrega Hoy
            "standard": "NORMAL",  # Servicio Normal
            "economy": "ECONOMICO", # Servicio Económico
            "same_day": "HOY",     # Entrega Hoy
            "overnight": "24HORAS", # Entrega 24 Horas
            "large": "GRANDES"     # Grandes Superficies
        }
        return mapping.get(service_type, "NORMAL")
    
    def _map_service_name(self, code: str) -> str:
        """Map Interrapidisimo service code to name"""
        mapping = {
            "HOY": "Entrega Hoy",
            "NORMAL": "Servicio Normal",
            "ECONOMICO": "Servicio Económico",
            "24HORAS": "Entrega 24 Horas",
            "GRANDES": "Grandes Superficies",
            "DOCUMENTOS": "Documentos",
            "PAQUETES": "Paquetes"
        }
        return mapping.get(code, "Servicio Interrapidisimo")
    
    async def generate_manifest(self, tracking_numbers: List[str]) -> Dict:
        """Generate dispatch manifest for multiple shipments"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/manifiestos",
                    headers=self.headers,
                    json={
                        "remesas": tracking_numbers,
                        "codigoCliente": self.credentials['customer_code'],
                        "formatoManifiesto": "PDF"
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("success"):
                    return {
                        "manifest_number": data["data"]["numeroManifiesto"],
                        "manifest_url": data["data"]["urlManifiesto"],
                        "manifest_pdf": data["data"].get("manifestoPDF")
                    }
                else:
                    raise Exception(f"Manifest generation failed: {data.get('message')}")
                    
        except Exception as e:
            logger.error("Manifest generation failed", error=str(e))
            raise