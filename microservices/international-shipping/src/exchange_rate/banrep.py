"""
Banco de la República (Colombia Central Bank) API Integration
Implements daily TRM (Tasa Representativa del Mercado) exchange rate fetching
"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging
import asyncio

logger = logging.getLogger(__name__)


class ExchangeRate(BaseModel):
    """Exchange rate model"""
    currency_from: str
    currency_to: str
    rate: float
    date: date
    source: str
    created_at: datetime


class TRMResponse(BaseModel):
    """TRM API response model"""
    valor: float
    fecha: str
    unidad: str


class BanrepAPIClient:
    """Banco de la República API client for TRM data"""
    
    def __init__(self):
        self.base_url = "https://www.banrep.gov.co/TasaCambio/TRM.jsp"
        self.api_url = "https://www.banrep.gov.co/TasaCambio/TRMQueryEngine.jsp"
        self.timeout = 30.0
    
    async def get_current_trm(self) -> Optional[ExchangeRate]:
        """
        Get current TRM (USD to COP) from Banco de la República
        
        Returns:
            ExchangeRate object with current TRM or None if failed
        """
        try:
            today = date.today()
            return await self.get_trm_for_date(today)
        except Exception as e:
            logger.error(f"Error fetching current TRM: {e}")
            return None
    
    async def get_trm_for_date(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Get TRM for specific date
        
        Args:
            target_date: Date to fetch TRM for
            
        Returns:
            ExchangeRate object or None if failed
        """
        try:
            # Format date for Banrep API (YYYY-MM-DD)
            date_str = target_date.strftime("%Y-%m-%d")
            
            # Banrep API parameters
            params = {
                "StartDate": date_str,
                "EndDate": date_str,  
                "Consultar": "Consultar",
                "format": "json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.api_url,
                    params=params,
                    headers={
                        "User-Agent": "Quenty-International-Shipping/1.0",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    logger.warning(f"Banrep API returned status {response.status_code}")
                    return await self._get_fallback_trm(target_date)
                
                # Parse JSON response
                data = response.json()
                
                if not data or len(data) == 0:
                    logger.warning(f"No TRM data found for date {date_str}")
                    return await self._get_fallback_trm(target_date)
                
                # Extract TRM value from response
                trm_data = data[0] if isinstance(data, list) else data
                trm_value = float(trm_data.get("valor", 0))
                
                if trm_value <= 0:
                    logger.warning(f"Invalid TRM value: {trm_value}")
                    return await self._get_fallback_trm(target_date)
                
                return ExchangeRate(
                    currency_from="USD",
                    currency_to="COP",
                    rate=trm_value,
                    date=target_date,
                    source="Banco de la República",
                    created_at=datetime.utcnow()
                )
                
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching TRM for {target_date}")
            return await self._get_fallback_trm(target_date)
        except Exception as e:
            logger.error(f"Error fetching TRM for {target_date}: {e}")
            return await self._get_fallback_trm(target_date)
    
    async def _get_fallback_trm(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Fallback method using alternative Banrep endpoint
        
        Args:
            target_date: Date to fetch TRM for
            
        Returns:
            ExchangeRate object or None if all methods fail
        """
        try:
            # Alternative endpoint with XML response
            xml_url = "https://www.banrep.gov.co/TRM/TRMQuery.jsp"
            date_str = target_date.strftime("%d/%m/%Y")
            
            params = {
                "fecha": date_str,
                "format": "xml"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(xml_url, params=params)
                
                if response.status_code == 200:
                    content = response.text
                    # Simple XML parsing for TRM value
                    import re
                    trm_match = re.search(r'<valor>([0-9,\.]+)</valor>', content)
                    if trm_match:
                        trm_str = trm_match.group(1).replace(',', '')
                        trm_value = float(trm_str)
                        
                        return ExchangeRate(
                            currency_from="USD",
                            currency_to="COP",
                            rate=trm_value,
                            date=target_date,
                            source="Banco de la República (fallback)",
                            created_at=datetime.utcnow()
                        )
                        
        except Exception as e:
            logger.error(f"Fallback TRM fetch failed: {e}")
        
        # If all methods fail, return None
        return None
    
    async def get_trm_history(self, start_date: date, end_date: date) -> List[ExchangeRate]:
        """
        Get TRM history for date range
        
        Args:
            start_date: Start date for history
            end_date: End date for history
            
        Returns:
            List of ExchangeRate objects
        """
        exchange_rates = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                # Skip weekends (Banrep doesn't publish TRM on weekends)
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    rate = await self.get_trm_for_date(current_date)
                    if rate:
                        exchange_rates.append(rate)
                    
                    # Add small delay between requests to be respectful
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error fetching TRM for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        return exchange_rates
    
    async def validate_connection(self) -> bool:
        """
        Validate connection to Banrep API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            yesterday = date.today() - timedelta(days=1)
            rate = await self.get_trm_for_date(yesterday)
            return rate is not None
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False


class ExchangeRateService:
    """Service class for exchange rate operations"""
    
    def __init__(self):
        self.banrep_client = BanrepAPIClient()
        self._cache = {}
        self._cache_ttl = timedelta(hours=1)  # Cache for 1 hour
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str, target_date: Optional[date] = None) -> Optional[ExchangeRate]:
        """
        Get exchange rate between two currencies
        
        Args:
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'COP')
            target_date: Date for exchange rate, defaults to today
            
        Returns:
            ExchangeRate object or None if not available
        """
        if target_date is None:
            target_date = date.today()
        
        # Check cache first
        cache_key = f"{from_currency}_{to_currency}_{target_date}"
        if cache_key in self._cache:
            cached_rate, cached_time = self._cache[cache_key]
            if datetime.utcnow() - cached_time < self._cache_ttl:
                return cached_rate
        
        # Handle USD to COP (TRM)
        if from_currency == "USD" and to_currency == "COP":
            rate = await self.banrep_client.get_trm_for_date(target_date)
            if rate:
                self._cache[cache_key] = (rate, datetime.utcnow())
            return rate
        
        # Handle COP to USD (inverse TRM)
        elif from_currency == "COP" and to_currency == "USD":
            trm_rate = await self.banrep_client.get_trm_for_date(target_date)
            if trm_rate:
                inverse_rate = ExchangeRate(
                    currency_from="COP",
                    currency_to="USD", 
                    rate=1.0 / trm_rate.rate,
                    date=target_date,
                    source=f"{trm_rate.source} (inverse)",
                    created_at=datetime.utcnow()
                )
                self._cache[cache_key] = (inverse_rate, datetime.utcnow())
                return inverse_rate
        
        # For other currency pairs, would need additional APIs
        # This could be extended with other exchange rate providers
        logger.warning(f"Exchange rate not available for {from_currency} to {to_currency}")
        return None
    
    async def convert_amount(self, amount: float, from_currency: str, to_currency: str, target_date: Optional[date] = None) -> Optional[float]:
        """
        Convert amount between currencies
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            target_date: Date for exchange rate
            
        Returns:
            Converted amount or None if conversion not possible
        """
        if from_currency == to_currency:
            return amount
        
        rate = await self.get_exchange_rate(from_currency, to_currency, target_date)
        if rate:
            return amount * rate.rate
        
        return None
    
    async def get_current_usd_cop_rate(self) -> Optional[float]:
        """
        Get current USD to COP exchange rate (TRM)
        
        Returns:
            Current TRM rate or None if not available
        """
        rate = await self.banrep_client.get_current_trm()
        return rate.rate if rate else None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for exchange rate service
        
        Returns:
            Dictionary with service health information
        """
        try:
            connection_ok = await self.banrep_client.validate_connection()
            current_rate = None
            
            if connection_ok:
                current_rate = await self.get_current_usd_cop_rate()
            
            return {
                "service": "exchange_rate",
                "status": "healthy" if connection_ok else "degraded",
                "banrep_connection": connection_ok,
                "current_usd_cop_rate": current_rate,
                "cache_size": len(self._cache),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "service": "exchange_rate", 
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }