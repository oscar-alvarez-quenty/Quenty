import httpx
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from zeep import Client as SOAPClient
from zeep.transports import Transport
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
import hashlib
from ..schemas import (
    QuoteRequest, QuoteResponse,
    LabelRequest, LabelResponse,
    TrackingResponse, TrackingEvent,
    PickupRequest, PickupResponse
)

logger = structlog.get_logger()

class ServientregaClient:
    """Servientrega SOAP Web Service Client for Colombian logistics"""

    def __init__(self, credentials: Dict[str, Any] = None, environment: str = None):
        # Load from environment variables if credentials not provided
        if credentials is None:
            credentials = self._load_from_env()

        self.credentials = credentials
        self.environment = environment or os.getenv('SERVIENTREGA_ENVIRONMENT', 'test')
        self.wsdl_url = self._get_wsdl_url()
        self.soap_client = None
        self._initialize_soap_client()

    def _load_from_env(self) -> Dict[str, Any]:
        """Load Servientrega credentials from environment variables"""
        return {
            'username': os.getenv('SERVIENTREGA_USER'),
            'password': os.getenv('SERVIENTREGA_PASSWORD'),
            'billing_code': os.getenv('SERVIENTREGA_BILLING_CODE'),
            'id_client': os.getenv('SERVIENTREGA_ID_CLIENT'),
            'name_pack': os.getenv('SERVIENTREGA_NAME_PACK')
        }
        
    def _get_wsdl_url(self) -> str:
        """Get Servientrega WSDL URL based on environment"""
        if self.environment == "sandbox":
            return "http://web.servientrega.com:8081/GenerarGuia.asmx?wsdl"
        return "https://guias.servientrega.com/GenerarGuia.asmx?wsdl"
    
    def _initialize_soap_client(self):
        """Initialize SOAP client with authentication"""
        try:
            transport = Transport(timeout=30)
            self.soap_client = SOAPClient(wsdl=self.wsdl_url, transport=transport)
        except Exception as e:
            logger.error("Failed to initialize Servientrega SOAP client", error=str(e))
            raise
    
    def _generate_auth_hash(self) -> str:
        """Generate authentication hash for Servientrega"""
        # Servientrega uses MD5 hash of user:password:date
        date_str = datetime.now().strftime("%Y%m%d")
        auth_string = f"{self.credentials['username']}:{self.credentials['password']}:{date_str}"
        return hashlib.md5(auth_string.encode()).hexdigest()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_quote(self, request: QuoteRequest) -> QuoteResponse:
        """Get shipping quote from Servientrega"""
        try:
            # Servientrega typically requires origin and destination codes
            origin_code = await self._get_city_code(request.origin.city, request.origin.postal_code)
            dest_code = await self._get_city_code(request.destination.city, request.destination.postal_code)
            
            # Calculate total weight and volume
            total_weight = sum(pkg.weight_kg for pkg in request.packages)
            total_volume = sum(
                (pkg.length_cm * pkg.width_cm * pkg.height_cm) / 1000000
                for pkg in request.packages
            )
            
            # Call SOAP service for quote
            response = self.soap_client.service.ConsultarLiquidacion(
                usuario=self.credentials['username'],
                clave=self.credentials['password'],
                codigoConvenio=self.credentials['agreement_code'],
                origen=origin_code,
                destino=dest_code,
                peso=total_weight,
                volumen=total_volume,
                valorDeclarado=request.customs_value or 0,
                tipoServicio=self._get_service_type(request.service_type)
            )
            
            if response and response.Exitoso:
                return QuoteResponse(
                    quote_id=f"SERVIENTREGA-{datetime.now().timestamp()}",
                    carrier="Servientrega",
                    service_type=self._map_service_name(response.TipoServicio),
                    amount=float(response.ValorFlete),
                    currency="COP",
                    estimated_days=int(response.DiasEntrega) if hasattr(response, 'DiasEntrega') else 3,
                    valid_until=datetime.now() + timedelta(hours=24),
                    breakdown={
                        'base_freight': float(response.ValorFlete),
                        'fuel_surcharge': float(response.ValorSobreflete) if hasattr(response, 'ValorSobreflete') else 0,
                        'management_fee': float(response.ValorCostomanejo) if hasattr(response, 'ValorCostomanejo') else 0
                    },
                    notes=[response.Mensaje] if hasattr(response, 'Mensaje') else []
                )
            else:
                error_msg = response.Mensaje if hasattr(response, 'Mensaje') else "Quote request failed"
                raise Exception(f"Servientrega quote error: {error_msg}")
                
        except Exception as e:
            logger.error("Servientrega quote request failed", error=str(e))
            raise Exception(f"Servientrega API error: {str(e)}")
    
    async def generate_label(self, request: LabelRequest) -> LabelResponse:
        """Generate shipping label (guía) with Servientrega"""
        try:
            # Get city codes
            origin_code = await self._get_city_code(request.origin.city, request.origin.postal_code)
            dest_code = await self._get_city_code(request.destination.city, request.destination.postal_code)
            
            # Prepare shipment data
            shipment_data = {
                'usuario': self.credentials['username'],
                'clave': self.credentials['password'],
                'codigoConvenio': self.credentials['agreement_code'],
                'remitente': {
                    'nombres': request.origin.contact_name,
                    'direccion': request.origin.street,
                    'ciudad': origin_code,
                    'telefono': request.origin.contact_phone,
                    'email': request.origin.contact_email
                },
                'destinatario': {
                    'nombres': request.destination.contact_name,
                    'direccion': request.destination.street,
                    'ciudad': dest_code,
                    'telefono': request.destination.contact_phone,
                    'email': request.destination.contact_email
                },
                'piezas': []
            }
            
            # Add packages
            for idx, pkg in enumerate(request.packages):
                shipment_data['piezas'].append({
                    'peso': pkg.weight_kg,
                    'largo': pkg.length_cm,
                    'ancho': pkg.width_cm,
                    'alto': pkg.height_cm,
                    'valorDeclarado': pkg.declared_value or 0,
                    'descripcion': pkg.description or f"Paquete {idx + 1}",
                    'referencia': request.order_id
                })
            
            # Generate guide number
            response = self.soap_client.service.GenerarGuiaSticker(
                **shipment_data,
                tipoServicio=self._get_service_type(request.service_type),
                adicionales=request.reference_number,
                observaciones=f"Orden: {request.order_id}"
            )
            
            if response and response.Exitoso:
                return LabelResponse(
                    tracking_number=response.NumeroGuia,
                    carrier="Servientrega",
                    label_data=response.StickerPDF if hasattr(response, 'StickerPDF') else None,
                    label_url=response.URLSticker if hasattr(response, 'URLSticker') else None,
                    barcode=response.CodigoBarras if hasattr(response, 'CodigoBarras') else response.NumeroGuia,
                    estimated_delivery=datetime.now() + timedelta(days=3),
                    cost=float(response.ValorTotal) if hasattr(response, 'ValorTotal') else 0,
                    currency="COP"
                )
            else:
                error_msg = response.Mensaje if hasattr(response, 'Mensaje') else "Label generation failed"
                raise Exception(f"Servientrega label error: {error_msg}")
                
        except Exception as e:
            logger.error("Servientrega label generation failed", error=str(e))
            raise Exception(f"Servientrega API error: {str(e)}")
    
    async def track_shipment(self, tracking_number: str) -> TrackingResponse:
        """Track Servientrega shipment"""
        try:
            # Call tracking web service
            response = self.soap_client.service.ConsultarGuia(
                usuario=self.credentials['username'],
                clave=self.credentials['password'],
                numeroGuia=tracking_number
            )
            
            if response and response.Exitoso:
                # Parse tracking events
                events = []
                if hasattr(response, 'Trazabilidad') and response.Trazabilidad:
                    for evento in response.Trazabilidad:
                        events.append(TrackingEvent(
                            date=datetime.strptime(evento.Fecha, "%Y-%m-%d %H:%M:%S"),
                            status=evento.Estado,
                            description=evento.Descripcion,
                            location=evento.Ciudad if hasattr(evento, 'Ciudad') else None,
                            details={
                                'office': evento.Oficina if hasattr(evento, 'Oficina') else None,
                                'responsible': evento.Responsable if hasattr(evento, 'Responsable') else None
                            }
                        ))
                
                # Determine current status
                current_status = response.EstadoActual if hasattr(response, 'EstadoActual') else "En tránsito"
                delivered = current_status.lower() in ['entregado', 'entregada']
                
                return TrackingResponse(
                    tracking_number=tracking_number,
                    carrier="Servientrega",
                    status=current_status,
                    current_location=response.CiudadActual if hasattr(response, 'CiudadActual') else None,
                    estimated_delivery=datetime.strptime(
                        response.FechaEstimadaEntrega, "%Y-%m-%d"
                    ) if hasattr(response, 'FechaEstimadaEntrega') else None,
                    delivered_date=datetime.strptime(
                        response.FechaEntrega, "%Y-%m-%d %H:%M:%S"
                    ) if delivered and hasattr(response, 'FechaEntrega') else None,
                    events=events,
                    proof_of_delivery={
                        'recipient': response.PersonaRecibe if hasattr(response, 'PersonaRecibe') else None,
                        'id_number': response.CedulaRecibe if hasattr(response, 'CedulaRecibe') else None,
                        'relationship': response.Parentesco if hasattr(response, 'Parentesco') else None
                    } if delivered else None
                )
            else:
                error_msg = response.Mensaje if hasattr(response, 'Mensaje') else "Tracking failed"
                raise Exception(f"Servientrega tracking error: {error_msg}")
                
        except Exception as e:
            logger.error("Servientrega tracking failed", error=str(e))
            raise Exception(f"Servientrega API error: {str(e)}")
    
    async def schedule_pickup(self, request: PickupRequest) -> PickupResponse:
        """Schedule pickup with Servientrega"""
        try:
            # Get city code
            city_code = await self._get_city_code(request.address.city, request.address.postal_code)
            
            # Schedule pickup via SOAP service
            response = self.soap_client.service.SolicitarRecoleccion(
                usuario=self.credentials['username'],
                clave=self.credentials['password'],
                codigoConvenio=self.credentials['agreement_code'],
                fecha=request.pickup_date.strftime("%Y-%m-%d"),
                horaInicio=request.pickup_window_start,
                horaFin=request.pickup_window_end,
                direccion=request.address.street,
                ciudad=city_code,
                telefono=request.address.contact_phone,
                contacto=request.address.contact_name,
                empresa=request.address.company or request.address.contact_name,
                cantidadPiezas=request.packages_count,
                pesoTotal=request.total_weight_kg,
                observaciones=request.special_instructions,
                guias=",".join(request.tracking_numbers) if request.tracking_numbers else ""
            )
            
            if response and response.Exitoso:
                return PickupResponse(
                    confirmation_number=response.NumeroRecoleccion,
                    carrier="Servientrega",
                    pickup_date=request.pickup_date,
                    pickup_window=f"{request.pickup_window_start}-{request.pickup_window_end}",
                    status="scheduled",
                    cost=float(response.Valor) if hasattr(response, 'Valor') else 0,
                    currency="COP"
                )
            else:
                error_msg = response.Mensaje if hasattr(response, 'Mensaje') else "Pickup scheduling failed"
                raise Exception(f"Servientrega pickup error: {error_msg}")
                
        except Exception as e:
            logger.error("Servientrega pickup scheduling failed", error=str(e))
            raise Exception(f"Servientrega API error: {str(e)}")
    
    async def _get_city_code(self, city: str, postal_code: str) -> str:
        """Get Servientrega city code from city name or postal code"""
        try:
            response = self.soap_client.service.ConsultarCiudad(
                usuario=self.credentials['username'],
                clave=self.credentials['password'],
                nombreCiudad=city,
                codigoPostal=postal_code
            )
            
            if response and response.Exitoso:
                return response.CodigoCiudad
            else:
                # Default to Bogotá if city not found
                logger.warning(f"City {city} not found, using default")
                return "11001"  # Bogotá code
                
        except Exception as e:
            logger.error("Failed to get city code", error=str(e))
            return "11001"  # Default to Bogotá
    
    async def check_coverage(self, city: str, postal_code: str) -> bool:
        """Check if Servientrega has coverage in a specific area"""
        try:
            response = self.soap_client.service.ConsultarCobertura(
                usuario=self.credentials['username'],
                clave=self.credentials['password'],
                ciudad=city,
                codigoPostal=postal_code
            )
            
            return response and response.TieneCobertura
            
        except Exception as e:
            logger.error("Failed to check coverage", error=str(e))
            return False
    
    def _get_service_type(self, service_type: Optional[str]) -> str:
        """Map service type to Servientrega service code"""
        mapping = {
            "express": "001",  # Mercancía Premier
            "standard": "002",  # Documento Unitario
            "economy": "003",  # Mercancía Industrial
            "same_day": "006",  # Hoy Mismo
            "overnight": "001"  # Default to Mercancía Premier
        }
        return mapping.get(service_type, "001")
    
    def _map_service_name(self, code: str) -> str:
        """Map Servientrega service code to name"""
        mapping = {
            "001": "Mercancía Premier",
            "002": "Documento Unitario",
            "003": "Mercancía Industrial",
            "006": "Hoy Mismo",
            "201": "Documento Masivo",
            "202": "Mercancía Masiva"
        }
        return mapping.get(code, "Servicio Servientrega")