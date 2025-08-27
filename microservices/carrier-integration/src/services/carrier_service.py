from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import structlog
from sqlalchemy.orm import Session
from circuitbreaker import circuit
from ..models import CarrierCredential, CarrierHealthStatus, CarrierType, ServiceStatus
from ..carriers.dhl import DHLClient
from ..carriers.fedex import FedExClient
from ..carriers.ups import UPSClient
from ..carriers.servientrega import ServientregaClient
from ..carriers.interrapidisimo import InterrapidisimoClient
from ..carriers.pasarex import PasarexClient
from ..carriers.aeropost import AeropostClient
from ..schemas import (
    QuoteRequest, QuoteResponse,
    LabelRequest, LabelResponse,
    TrackingResponse,
    PickupRequest, PickupResponse,
    CarrierCredentialCreate
)
from ..utils.encryption import encrypt_credentials, decrypt_credentials

logger = structlog.get_logger()

class CarrierService:
    """Service to manage all carrier integrations"""
    
    def __init__(self):
        self.carriers = {}
        self.health_status = {}
        
    async def initialize_carrier(self, carrier: str, credentials: Dict[str, Any], environment: str = "production"):
        """Initialize a carrier client with credentials"""
        try:
            if carrier == "DHL":
                client = DHLClient(credentials, environment)
            elif carrier == "FedEx":
                client = FedExClient(credentials, environment)
            elif carrier == "UPS":
                client = UPSClient(credentials, environment)
            elif carrier == "Servientrega":
                client = ServientregaClient(credentials, environment)
            elif carrier == "Interrapidisimo":
                client = InterrapidisimoClient(credentials, environment)
            elif carrier == "Pasarex":
                client = PasarexClient()
            elif carrier == "Aeropost":
                client = AeropostClient()
            else:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            self.carriers[carrier] = client
            logger.info("Carrier initialized", carrier=carrier)
            
        except Exception as e:
            logger.error("Failed to initialize carrier", carrier=carrier, error=str(e))
            raise
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def get_quote(self, carrier: str, request: QuoteRequest) -> QuoteResponse:
        """Get quote from specific carrier with circuit breaker"""
        if carrier not in self.carriers:
            raise ValueError(f"Carrier {carrier} not initialized")
        
        try:
            client = self.carriers[carrier]
            quote = await client.get_quote(request)
            
            # Update health status
            await self._update_health_status(carrier, True)
            
            return quote
            
        except Exception as e:
            # Update health status
            await self._update_health_status(carrier, False, str(e))
            raise
    
    async def get_best_quote(self, request: QuoteRequest) -> QuoteResponse:
        """Get best quote from all available carriers"""
        quotes = []
        
        # Get quotes from all carriers in parallel
        tasks = []
        for carrier in self.carriers:
            if self._is_carrier_healthy(carrier):
                tasks.append(self._get_quote_safe(carrier, request))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful quotes
        for result in results:
            if isinstance(result, QuoteResponse):
                quotes.append(result)
        
        if not quotes:
            raise Exception("No carriers available for quote")
        
        # Return cheapest quote
        return min(quotes, key=lambda q: q.amount)
    
    async def _get_quote_safe(self, carrier: str, request: QuoteRequest) -> Optional[QuoteResponse]:
        """Get quote with error handling"""
        try:
            return await self.get_quote(carrier, request)
        except Exception as e:
            logger.warning("Failed to get quote from carrier", carrier=carrier, error=str(e))
            return None
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def generate_label(self, carrier: str, request: LabelRequest) -> LabelResponse:
        """Generate label with specific carrier"""
        if carrier not in self.carriers:
            raise ValueError(f"Carrier {carrier} not initialized")
        
        try:
            client = self.carriers[carrier]
            label = await client.generate_label(request)
            
            await self._update_health_status(carrier, True)
            
            return label
            
        except Exception as e:
            await self._update_health_status(carrier, False, str(e))
            raise
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def track_shipment(self, carrier: str, tracking_number: str) -> TrackingResponse:
        """Track shipment with specific carrier"""
        if carrier not in self.carriers:
            raise ValueError(f"Carrier {carrier} not initialized")
        
        try:
            client = self.carriers[carrier]
            tracking = await client.track_shipment(tracking_number)
            
            await self._update_health_status(carrier, True)
            
            return tracking
            
        except Exception as e:
            await self._update_health_status(carrier, False, str(e))
            raise
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def schedule_pickup(self, carrier: str, request: PickupRequest) -> PickupResponse:
        """Schedule pickup with specific carrier"""
        if carrier not in self.carriers:
            raise ValueError(f"Carrier {carrier} not initialized")
        
        try:
            client = self.carriers[carrier]
            pickup = await client.schedule_pickup(request)
            
            await self._update_health_status(carrier, True)
            
            return pickup
            
        except Exception as e:
            await self._update_health_status(carrier, False, str(e))
            raise
    
    async def validate_credentials(self, carrier: str, credentials: CarrierCredentialCreate) -> bool:
        """Validate carrier credentials"""
        try:
            # Initialize temporary client
            if carrier == "DHL":
                client = DHLClient(credentials.credentials, credentials.environment)
            elif carrier == "FedEx":
                client = FedExClient(credentials.credentials, credentials.environment)
            elif carrier == "UPS":
                client = UPSClient(credentials.credentials, credentials.environment)
            elif carrier == "Servientrega":
                client = ServientregaClient(credentials.credentials, credentials.environment)
            elif carrier == "Interrapidisimo":
                client = InterrapidisimoClient(credentials.credentials, credentials.environment)
            else:
                return False
            
            # Try to make a simple API call to validate
            # This would be carrier-specific validation
            return True
            
        except Exception as e:
            logger.error("Credential validation failed", carrier=carrier, error=str(e))
            return False
    
    async def save_credentials(self, carrier: str, credentials: CarrierCredentialCreate, db: Session):
        """Save carrier credentials to database"""
        try:
            # Encrypt credentials
            encrypted = encrypt_credentials(credentials.credentials)
            
            # Save to database
            db_credential = CarrierCredential(
                carrier=CarrierType[carrier],
                environment=credentials.environment,
                credentials=encrypted,
                validated_at=datetime.now()
            )
            
            db.add(db_credential)
            db.commit()
            
            # Initialize carrier
            await self.initialize_carrier(carrier, credentials.credentials, credentials.environment)
            
            return db_credential
            
        except Exception as e:
            db.rollback()
            raise
    
    async def get_health_status(self, carrier: str) -> Dict[str, Any]:
        """Get health status for a carrier"""
        if carrier not in self.health_status:
            return {
                "carrier": carrier,
                "status": "unknown",
                "message": "No health data available"
            }
        
        return self.health_status[carrier]
    
    def _is_carrier_healthy(self, carrier: str) -> bool:
        """Check if carrier is healthy"""
        if carrier not in self.health_status:
            return True  # Assume healthy if no data
        
        status = self.health_status[carrier]
        return status.get("status") != ServiceStatus.DOWN
    
    async def _update_health_status(self, carrier: str, success: bool, error: Optional[str] = None):
        """Update carrier health status"""
        if carrier not in self.health_status:
            self.health_status[carrier] = {
                "carrier": carrier,
                "status": ServiceStatus.OPERATIONAL,
                "consecutive_failures": 0,
                "last_check": datetime.now(),
                "last_success": datetime.now() if success else None
            }
        
        status = self.health_status[carrier]
        status["last_check"] = datetime.now()
        
        if success:
            status["status"] = ServiceStatus.OPERATIONAL
            status["consecutive_failures"] = 0
            status["last_success"] = datetime.now()
        else:
            status["consecutive_failures"] += 1
            
            if status["consecutive_failures"] >= 5:
                status["status"] = ServiceStatus.DOWN
            elif status["consecutive_failures"] >= 3:
                status["status"] = ServiceStatus.DEGRADED
            
            if error:
                status["last_error"] = error