from typing import Dict, Any, Optional, List
import structlog
from sqlalchemy.orm import Session
from ..models import FallbackConfiguration, FallbackEvent, CarrierType
from ..schemas import QuoteRequest, QuoteResponse
from ..database import SessionLocal

logger = structlog.get_logger()

class FallbackService:
    """Service to manage carrier fallback logic"""
    
    def __init__(self):
        self.fallback_configs = {}
        self.load_configurations()
        
    def load_configurations(self):
        """Load fallback configurations from database"""
        try:
            db = SessionLocal()
            try:
                configs = db.query(FallbackConfiguration).filter(
                    FallbackConfiguration.is_active == True
                ).all()
                
                for config in configs:
                    self.fallback_configs[config.route] = config.priority_order
                    
                logger.info("Fallback configurations loaded", count=len(configs))
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error("Failed to load fallback configurations", error=str(e))
    
    async def configure_priority(self, route: str, carriers: List[str]):
        """Configure fallback priority for a route"""
        try:
            db = SessionLocal()
            try:
                # Check if configuration exists
                config = db.query(FallbackConfiguration).filter(
                    FallbackConfiguration.route == route
                ).first()
                
                if config:
                    # Update existing
                    config.priority_order = carriers
                    config.is_active = True
                else:
                    # Create new
                    config = FallbackConfiguration(
                        route=route,
                        priority_order=carriers,
                        is_active=True
                    )
                    db.add(config)
                
                db.commit()
                
                # Update in-memory cache
                self.fallback_configs[route] = carriers
                
                logger.info("Fallback configuration updated", route=route, carriers=carriers)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error("Failed to configure fallback", error=str(e))
            raise
    
    async def get_fallback_quote(self, request: QuoteRequest, exclude: List[str] = None) -> Optional[QuoteResponse]:
        """Get quote from fallback carrier"""
        try:
            # Determine route
            route = f"{request.origin.country}-{request.destination.country}"
            
            # Get priority order
            carriers = self.fallback_configs.get(route, self._get_default_carriers())
            
            # Filter out excluded carriers
            if exclude:
                carriers = [c for c in carriers if c not in exclude]
            
            if not carriers:
                logger.warning("No fallback carriers available", route=route)
                return None
            
            # Try carriers in order
            from .carrier_service import CarrierService
            carrier_service = CarrierService()
            
            for carrier in carriers:
                try:
                    logger.info("Trying fallback carrier", carrier=carrier)
                    quote = await carrier_service.get_quote(carrier, request)
                    
                    # Record fallback event
                    await self._record_fallback(
                        order_id=request.order_id if hasattr(request, 'order_id') else "QUOTE",
                        from_carrier=exclude[0] if exclude else "PRIMARY",
                        to_carrier=carrier,
                        reason="Primary carrier unavailable"
                    )
                    
                    return quote
                    
                except Exception as e:
                    logger.warning("Fallback carrier failed", carrier=carrier, error=str(e))
                    continue
            
            return None
            
        except Exception as e:
            logger.error("Fallback quote failed", error=str(e))
            return None
    
    async def select_primary_carrier(self, route: str) -> Optional[str]:
        """Select primary carrier for a route"""
        carriers = self.fallback_configs.get(route, self._get_default_carriers())
        return carriers[0] if carriers else None
    
    async def select_fallback_carrier(self, route: str, exclude: List[str]) -> Optional[str]:
        """Select next available fallback carrier"""
        carriers = self.fallback_configs.get(route, self._get_default_carriers())
        
        for carrier in carriers:
            if carrier not in exclude:
                return carrier
        
        return None
    
    async def _record_fallback(self, order_id: str, from_carrier: str, to_carrier: str, reason: str):
        """Record fallback event in database"""
        try:
            db = SessionLocal()
            try:
                event = FallbackEvent(
                    order_id=order_id,
                    from_carrier=CarrierType[from_carrier] if from_carrier != "PRIMARY" else CarrierType.DHL,
                    to_carrier=CarrierType[to_carrier],
                    reason=reason
                )
                
                db.add(event)
                db.commit()
                
                logger.info("Fallback event recorded", 
                           order_id=order_id,
                           from_carrier=from_carrier,
                           to_carrier=to_carrier)
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error("Failed to record fallback event", error=str(e))
    
    def _get_default_carriers(self) -> List[str]:
        """Get default carrier priority"""
        return ["DHL", "FedEx", "UPS", "Servientrega", "Interrapidisimo"]