from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from ..models import ExchangeRate
from ..exchange_rate.banco_republica import BancoRepublicaClient
from ..database import SessionLocal

logger = structlog.get_logger()

class ExchangeRateService:
    """Service to manage exchange rates and currency conversions"""
    
    def __init__(self):
        self.banco_republica_client = BancoRepublicaClient()
        self.scheduler = AsyncIOScheduler()
        self.current_trm = None
        self.spread = 0.03  # 3% default spread
        
    async def start_scheduler(self):
        """Start scheduled tasks for TRM updates"""
        try:
            # Schedule TRM update every day at 6:00 AM
            self.scheduler.add_job(
                self.update_trm,
                'cron',
                hour=6,
                minute=0,
                id='daily_trm_update'
            )
            
            # Schedule TRM variation check every day at 7:00 AM
            self.scheduler.add_job(
                self.check_trm_variation,
                'cron',
                hour=7,
                minute=0,
                id='daily_trm_variation_check'
            )
            
            self.scheduler.start()
            logger.info("Exchange rate scheduler started")
            
            # Get initial TRM
            await self.update_trm()
            
        except Exception as e:
            logger.error("Failed to start exchange rate scheduler", error=str(e))
    
    async def stop_scheduler(self):
        """Stop scheduled tasks"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Exchange rate scheduler stopped")
    
    async def update_trm(self):
        """Update TRM from Banco de la República"""
        try:
            logger.info("Updating TRM from Banco de la República")
            
            # Get current TRM
            trm_data = await self.banco_republica_client.get_current_trm()
            
            # Save to database
            db = SessionLocal()
            try:
                exchange_rate = ExchangeRate(
                    from_currency="COP",
                    to_currency="USD",
                    rate=trm_data["rate"],
                    source="banco_republica",
                    valid_date=trm_data["valid_date"],
                    spread=self.spread
                )
                
                db.add(exchange_rate)
                db.commit()
                
                self.current_trm = trm_data
                
                logger.info("TRM updated successfully", rate=trm_data["rate"])
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error("Failed to update TRM", error=str(e))
    
    async def check_trm_variation(self):
        """Check TRM variation and send alerts if needed"""
        try:
            variation = await self.banco_republica_client.check_trm_variation(threshold_percentage=5.0)
            
            if variation and variation.get("alert"):
                logger.warning("High TRM variation detected", **variation)
                # TODO: Send notification to administrators
                await self._send_trm_alert(variation)
                
        except Exception as e:
            logger.error("Failed to check TRM variation", error=str(e))
    
    async def get_current_trm(self) -> Dict[str, Any]:
        """Get current TRM with spread applied"""
        try:
            if not self.current_trm:
                await self.update_trm()
            
            if self.current_trm:
                effective_rate = self.current_trm["rate"] * (1 + self.spread)
                
                return {
                    "rate": self.current_trm["rate"],
                    "from_currency": "COP",
                    "to_currency": "USD",
                    "valid_date": self.current_trm["valid_date"],
                    "source": self.current_trm["source"],
                    "spread": self.spread,
                    "effective_rate": effective_rate
                }
            
            # Fallback
            return {
                "rate": 4000.0,
                "from_currency": "COP",
                "to_currency": "USD",
                "valid_date": datetime.now(),
                "source": "fallback",
                "spread": self.spread,
                "effective_rate": 4000.0 * (1 + self.spread)
            }
            
        except Exception as e:
            logger.error("Failed to get current TRM", error=str(e))
            raise
    
    async def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies"""
        try:
            if from_currency == to_currency:
                return amount
            
            # Get exchange rate
            rate = await self.get_rate(from_currency, to_currency)
            
            # Apply conversion
            converted = amount * rate
            
            logger.info("Currency converted", 
                       amount=amount, 
                       from_currency=from_currency,
                       to_currency=to_currency,
                       rate=rate,
                       converted=converted)
            
            return converted
            
        except Exception as e:
            logger.error("Currency conversion failed", error=str(e))
            raise
    
    async def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies"""
        try:
            # Currently only supporting COP <-> USD
            if from_currency == "COP" and to_currency == "USD":
                trm = await self.get_current_trm()
                return 1 / trm["effective_rate"]
            elif from_currency == "USD" and to_currency == "COP":
                trm = await self.get_current_trm()
                return trm["effective_rate"]
            else:
                raise ValueError(f"Unsupported currency pair: {from_currency}/{to_currency}")
                
        except Exception as e:
            logger.error("Failed to get exchange rate", error=str(e))
            raise
    
    async def _send_trm_alert(self, variation: Dict[str, Any]):
        """Send TRM variation alert to administrators"""
        # TODO: Implement email/SMS notification
        logger.info("TRM alert would be sent", variation=variation)