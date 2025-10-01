import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import structlog
from zeep import Client as SOAPClient
from zeep.transports import Transport
from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache

logger = structlog.get_logger()

class BancoRepublicaClient:
    """Client for Banco de la República Colombia TRM Web Service"""
    
    def __init__(self):
        self.wsdl_url = "https://www.superfinanciera.gov.co/SuperfinancieraWebServiceTRM/TCRMServicesWebService/TCRMServicesWebService?WSDL"
        self.cache = TTLCache(maxsize=100, ttl=86400)  # 24 hours cache
        self.last_trm = None
        self.last_update = None
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_current_trm(self) -> Dict[str, Any]:
        """Get current TRM (Tasa Representativa del Mercado) from Banco de la República"""
        try:
            # Check cache first
            cache_key = datetime.now().strftime("%Y-%m-%d")
            if cache_key in self.cache:
                logger.info("TRM retrieved from cache", date=cache_key)
                return self.cache[cache_key]
            
            # Create SOAP client
            transport = Transport(timeout=30)
            client = SOAPClient(wsdl=self.wsdl_url, transport=transport)
            
            # Call the web service
            response = client.service.queryTCRM(tcrmQueryAssociatedDate=datetime.now())
            
            if response:
                trm_data = {
                    "rate": float(response.value),
                    "valid_date": response.validityFrom,
                    "valid_until": response.validityTo,
                    "source": "banco_republica",
                    "unit": response.unit if hasattr(response, 'unit') else "COP/USD"
                }
                
                # Cache the result
                self.cache[cache_key] = trm_data
                self.last_trm = trm_data
                self.last_update = datetime.now()
                
                logger.info("TRM retrieved successfully", rate=trm_data["rate"], date=cache_key)
                
                return trm_data
            else:
                raise Exception("No TRM data received from Banco de la República")
                
        except Exception as e:
            logger.error("Failed to get TRM from Banco de la República", error=str(e))
            
            # Return last known TRM if available
            if self.last_trm:
                logger.warning("Using last known TRM as fallback", rate=self.last_trm["rate"])
                return self.last_trm
            
            # Default fallback TRM
            return {
                "rate": 4000.0,  # Conservative default
                "valid_date": datetime.now(),
                "valid_until": datetime.now() + timedelta(days=1),
                "source": "fallback",
                "unit": "COP/USD"
            }
    
    async def get_historical_trm(self, date: datetime) -> Dict[str, Any]:
        """Get historical TRM for a specific date"""
        try:
            # Check cache
            cache_key = date.strftime("%Y-%m-%d")
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Create SOAP client
            transport = Transport(timeout=30)
            client = SOAPClient(wsdl=self.wsdl_url, transport=transport)
            
            # Call the web service with specific date
            response = client.service.queryTCRM(tcrmQueryAssociatedDate=date)
            
            if response:
                trm_data = {
                    "rate": float(response.value),
                    "valid_date": response.validityFrom,
                    "valid_until": response.validityTo,
                    "source": "banco_republica",
                    "unit": "COP/USD"
                }
                
                # Cache the result
                self.cache[cache_key] = trm_data
                
                return trm_data
            else:
                raise Exception(f"No TRM data for date {date}")
                
        except Exception as e:
            logger.error("Failed to get historical TRM", date=date, error=str(e))
            raise
    
    async def check_trm_variation(self, threshold_percentage: float = 5.0) -> Optional[Dict[str, Any]]:
        """Check if TRM has varied more than threshold percentage from yesterday"""
        try:
            # Get today's TRM
            today_trm = await self.get_current_trm()
            
            # Get yesterday's TRM
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_trm = await self.get_historical_trm(yesterday)
            
            # Calculate variation
            variation = ((today_trm["rate"] - yesterday_trm["rate"]) / yesterday_trm["rate"]) * 100
            
            if abs(variation) > threshold_percentage:
                return {
                    "alert": True,
                    "variation_percentage": variation,
                    "today_rate": today_trm["rate"],
                    "yesterday_rate": yesterday_trm["rate"],
                    "threshold": threshold_percentage,
                    "message": f"TRM variation of {variation:.2f}% exceeds threshold of {threshold_percentage}%"
                }
            
            return None
            
        except Exception as e:
            logger.error("Failed to check TRM variation", error=str(e))
            return None