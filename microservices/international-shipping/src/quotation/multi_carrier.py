"""
Multi-Carrier Quotation System
Implements comprehensive rate comparison across DHL, FedEx, and UPS
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QuotationRequest:
    """Multi-carrier quotation request parameters"""
    origin_country: str
    destination_country: str
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    origin_postal_code: Optional[str] = None
    destination_postal_code: Optional[str] = None
    weight_kg: float = 0.0
    length_cm: float = 0.0
    width_cm: float = 0.0
    height_cm: float = 0.0
    value: float = 0.0
    currency: str = "USD"
    insurance_required: bool = False
    signature_required: bool = False
    carrier_codes: Optional[List[str]] = None  # Specific carriers to quote
    service_types: Optional[List[str]] = None  # Specific services to include


class CarrierQuote(BaseModel):
    """Individual carrier quote response"""
    carrier_code: str = Field(..., description="Carrier identifier (DHL, FEDEX, UPS)")
    carrier_name: str = Field(..., description="Display name of the carrier")
    service_type: str = Field(..., description="Service type name")
    service_code: Optional[str] = Field(None, description="Internal service code")
    
    # Cost breakdown
    base_rate: float = Field(..., description="Base shipping rate")
    weight_rate: float = Field(0.0, description="Weight-based additional cost")
    fuel_surcharge: float = Field(0.0, description="Fuel surcharge")
    insurance_rate: float = Field(0.0, description="Insurance cost")
    additional_fees: Dict[str, float] = Field(default_factory=dict, description="Other fees")
    total_cost: float = Field(..., description="Total shipping cost")
    currency: str = Field("USD", description="Currency code")
    
    # Service details
    transit_days: int = Field(..., description="Estimated delivery days")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date/time")
    cutoff_time: Optional[str] = Field(None, description="Daily cutoff time for this service")
    
    # Availability and reliability
    available: bool = Field(True, description="Whether this service is available")
    confidence_score: float = Field(1.0, description="Reliability score (0-1)")
    error_message: Optional[str] = Field(None, description="Error details if unavailable")
    
    # Metadata
    quoted_at: datetime = Field(default_factory=datetime.utcnow, description="Quote timestamp")
    valid_until: datetime = Field(..., description="Quote expiration time")


class QuotationResponse(BaseModel):
    """Multi-carrier quotation response"""
    request_id: str = Field(..., description="Unique request identifier")
    quotes: List[CarrierQuote] = Field(..., description="All carrier quotes")
    
    # Request summary
    origin: str = Field(..., description="Origin description")
    destination: str = Field(..., description="Destination description")
    package_details: Dict[str, Any] = Field(..., description="Package information")
    
    # Comparative analysis
    cheapest_quote: Optional[CarrierQuote] = Field(None, description="Lowest cost option")
    fastest_quote: Optional[CarrierQuote] = Field(None, description="Fastest delivery option")
    recommended_quote: Optional[CarrierQuote] = Field(None, description="Best overall value")
    
    # Metadata
    total_quotes: int = Field(..., description="Number of quotes returned")
    successful_carriers: int = Field(..., description="Number of carriers that provided quotes")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Any carrier errors")
    processing_time_ms: int = Field(..., description="Time taken to generate quotes")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class MultiCarrierQuotationService:
    """Service for multi-carrier rate quotations"""
    
    def __init__(self):
        self.carrier_factory = None  # Will be set via dependency injection
        self.carrier_configs = {}  # Carrier configurations
        self.default_carriers = ["DHL", "FEDEX", "UPS"]
        self.quotation_timeout = 30.0  # seconds
        
    def set_carrier_factory(self, factory):
        """Set carrier factory for dependency injection"""
        self.carrier_factory = factory
    
    def set_carrier_config(self, carrier_code: str, config: Dict[str, str]):
        """Set configuration for a carrier"""
        self.carrier_configs[carrier_code] = config
    
    async def get_quotations(self, request: QuotationRequest) -> QuotationResponse:
        """
        Get quotations from multiple carriers
        
        Args:
            request: Quotation request parameters
            
        Returns:
            QuotationResponse with quotes from all available carriers
        """
        start_time = datetime.utcnow()
        request_id = f"quote_{int(start_time.timestamp())}_{hash(str(request))}"
        
        # Determine which carriers to quote
        carriers_to_quote = request.carrier_codes or self.default_carriers
        
        # Get quotes from all carriers concurrently
        quote_tasks = []
        for carrier_code in carriers_to_quote:
            if carrier_code in self.carrier_configs:
                task = self._get_carrier_quote(carrier_code, request)
                quote_tasks.append(task)
        
        # Execute all quotes concurrently with timeout
        try:
            quotes_results = await asyncio.wait_for(
                asyncio.gather(*quote_tasks, return_exceptions=True),
                timeout=self.quotation_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Quotation timeout for request {request_id}")
            quotes_results = [Exception("Quotation timeout")] * len(quote_tasks)
        
        # Process results
        quotes = []
        errors = []
        
        for i, result in enumerate(quotes_results):
            carrier_code = carriers_to_quote[i]
            
            if isinstance(result, Exception):
                error_msg = str(result)
                logger.error(f"Error getting quote from {carrier_code}: {error_msg}")
                errors.append({
                    "carrier": carrier_code,
                    "error": error_msg
                })
            elif isinstance(result, list):
                # Multiple quotes from carrier (different service types)
                quotes.extend(result)
            elif result:
                # Single quote from carrier
                quotes.append(result)
        
        # Filter by service types if specified
        if request.service_types:
            quotes = [q for q in quotes if q.service_type in request.service_types]
        
        # Sort quotes by total cost
        quotes.sort(key=lambda x: x.total_cost)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Find best options
        cheapest_quote = quotes[0] if quotes else None
        fastest_quote = min(quotes, key=lambda x: x.transit_days) if quotes else None
        recommended_quote = self._calculate_recommended_quote(quotes)
        
        return QuotationResponse(
            request_id=request_id,
            quotes=quotes,
            origin=f"{request.origin_city or ''}, {request.origin_country}".strip(", "),
            destination=f"{request.destination_city or ''}, {request.destination_country}".strip(", "),
            package_details={
                "weight_kg": request.weight_kg,
                "dimensions_cm": {
                    "length": request.length_cm,
                    "width": request.width_cm,
                    "height": request.height_cm
                },
                "value": request.value,
                "currency": request.currency,
                "insurance_required": request.insurance_required
            },
            cheapest_quote=cheapest_quote,
            fastest_quote=fastest_quote,
            recommended_quote=recommended_quote,
            total_quotes=len(quotes),
            successful_carriers=len([r for r in quotes_results if not isinstance(r, Exception)]),
            errors=errors,
            processing_time_ms=int(processing_time)
        )
    
    async def _get_carrier_quote(self, carrier_code: str, request: QuotationRequest) -> List[CarrierQuote]:
        """
        Get quotes from a specific carrier
        
        Args:
            carrier_code: Carrier identifier
            request: Quotation request
            
        Returns:
            List of CarrierQuote objects for different service types
        """
        try:
            # Get carrier configuration
            config = self.carrier_configs.get(carrier_code, {})
            
            # Create carrier integration instance
            if not self.carrier_factory:
                raise Exception("Carrier factory not configured")
            
            integration = self.carrier_factory.create_integration(
                carrier_code, config, sandbox=True
            )
            
            if not integration:
                raise Exception(f"Carrier {carrier_code} not supported")
            
            # Get rates from carrier API
            rates = await integration.calculate_rates(
                origin_country=request.origin_country,
                destination_country=request.destination_country,
                weight_kg=request.weight_kg,
                length_cm=request.length_cm,
                width_cm=request.width_cm,
                height_cm=request.height_cm,
                value=request.value,
                currency=request.currency
            )
            
            # Convert to CarrierQuote objects
            quotes = []
            for rate in rates:
                # Calculate estimated delivery date
                estimated_delivery = datetime.utcnow() + timedelta(days=rate.transit_days)
                
                # Determine cutoff time based on carrier
                cutoff_time = self._get_carrier_cutoff_time(carrier_code)
                
                # Calculate confidence score based on carrier reliability
                confidence_score = self._calculate_confidence_score(carrier_code, rate.service_type)
                
                quote = CarrierQuote(
                    carrier_code=carrier_code,
                    carrier_name=rate.carrier,
                    service_type=rate.service_type,
                    base_rate=rate.base_rate,
                    weight_rate=rate.weight_rate,
                    fuel_surcharge=rate.fuel_surcharge,
                    insurance_rate=rate.insurance_rate,
                    additional_fees=rate.additional_fees or {},
                    total_cost=rate.total_cost,
                    currency=rate.currency,
                    transit_days=rate.transit_days,
                    estimated_delivery=estimated_delivery,
                    cutoff_time=cutoff_time,
                    available=True,
                    confidence_score=confidence_score,
                    valid_until=rate.valid_until
                )
                
                quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting quote from {carrier_code}: {str(e)}")
            
            # Return error quote
            error_quote = CarrierQuote(
                carrier_code=carrier_code,
                carrier_name=self._get_carrier_display_name(carrier_code),
                service_type="Service Unavailable",
                base_rate=0.0,
                total_cost=0.0,
                transit_days=0,
                available=False,
                confidence_score=0.0,
                error_message=str(e),
                valid_until=datetime.utcnow() + timedelta(hours=1)
            )
            
            return [error_quote]
    
    def _calculate_recommended_quote(self, quotes: List[CarrierQuote]) -> Optional[CarrierQuote]:
        """
        Calculate recommended quote based on cost, speed, and reliability
        
        Args:
            quotes: List of available quotes
            
        Returns:
            Best overall value quote
        """
        if not quotes:
            return None
        
        available_quotes = [q for q in quotes if q.available]
        if not available_quotes:
            return None
        
        # Calculate score for each quote (lower is better)
        scored_quotes = []
        for quote in available_quotes:
            # Normalize cost (0-1 scale)
            min_cost = min(q.total_cost for q in available_quotes)
            max_cost = max(q.total_cost for q in available_quotes)
            cost_score = (quote.total_cost - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
            
            # Normalize transit days (0-1 scale)
            min_days = min(q.transit_days for q in available_quotes)
            max_days = max(q.transit_days for q in available_quotes)
            speed_score = (quote.transit_days - min_days) / (max_days - min_days) if max_days > min_days else 0
            
            # Reliability score (higher confidence is better, so invert)
            reliability_score = 1.0 - quote.confidence_score
            
            # Weighted total score (cost=50%, speed=30%, reliability=20%)
            total_score = (cost_score * 0.5) + (speed_score * 0.3) + (reliability_score * 0.2)
            
            scored_quotes.append((quote, total_score))
        
        # Return quote with lowest score (best value)
        best_quote = min(scored_quotes, key=lambda x: x[1])
        return best_quote[0]
    
    def _get_carrier_display_name(self, carrier_code: str) -> str:
        """Get display name for carrier"""
        display_names = {
            "DHL": "DHL Express",
            "FEDEX": "FedEx",
            "UPS": "UPS"
        }
        return display_names.get(carrier_code, carrier_code)
    
    def _get_carrier_cutoff_time(self, carrier_code: str) -> str:
        """Get daily cutoff time for carrier"""
        cutoff_times = {
            "DHL": "18:00",
            "FEDEX": "19:00", 
            "UPS": "17:30"
        }
        return cutoff_times.get(carrier_code, "17:00")
    
    def _calculate_confidence_score(self, carrier_code: str, service_type: str) -> float:
        """
        Calculate confidence score based on carrier and service reliability
        
        Args:
            carrier_code: Carrier identifier
            service_type: Service type
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base reliability scores by carrier
        base_scores = {
            "DHL": 0.95,
            "FEDEX": 0.93,
            "UPS": 0.92
        }
        
        # Service type modifiers
        service_modifiers = {
            "Express": 0.05,
            "Priority": 0.03,
            "Standard": 0.0,
            "Economy": -0.02,
            "Saver": -0.01
        }
        
        base_score = base_scores.get(carrier_code, 0.85)
        
        # Apply service modifier
        modifier = 0.0
        for service_key, mod_value in service_modifiers.items():
            if service_key.lower() in service_type.lower():
                modifier = mod_value
                break
        
        final_score = min(1.0, max(0.0, base_score + modifier))
        return final_score
    
    async def get_carrier_quote_comparison(self, request: QuotationRequest) -> Dict[str, Any]:
        """
        Get detailed comparison analysis of carrier quotes
        
        Args:
            request: Quotation request
            
        Returns:
            Detailed comparison analysis
        """
        response = await self.get_quotations(request)
        
        if not response.quotes:
            return {
                "comparison": "No quotes available",
                "analysis": {},
                "recommendations": []
            }
        
        available_quotes = [q for q in response.quotes if q.available]
        
        # Cost analysis
        costs = [q.total_cost for q in available_quotes]
        cost_analysis = {
            "min_cost": min(costs) if costs else 0,
            "max_cost": max(costs) if costs else 0,
            "avg_cost": sum(costs) / len(costs) if costs else 0,
            "cost_spread": max(costs) - min(costs) if costs else 0
        }
        
        # Transit time analysis
        transit_times = [q.transit_days for q in available_quotes]
        time_analysis = {
            "fastest_delivery": min(transit_times) if transit_times else 0,
            "slowest_delivery": max(transit_times) if transit_times else 0,
            "avg_delivery": sum(transit_times) / len(transit_times) if transit_times else 0
        }
        
        # Carrier breakdown
        carrier_breakdown = {}
        for quote in available_quotes:
            if quote.carrier_code not in carrier_breakdown:
                carrier_breakdown[quote.carrier_code] = {
                    "services": [],
                    "cost_range": {"min": float('inf'), "max": 0},
                    "transit_range": {"min": float('inf'), "max": 0}
                }
            
            carrier_info = carrier_breakdown[quote.carrier_code]
            carrier_info["services"].append({
                "service": quote.service_type,
                "cost": quote.total_cost,
                "transit_days": quote.transit_days,
                "confidence": quote.confidence_score
            })
            
            # Update ranges
            if quote.total_cost < carrier_info["cost_range"]["min"]:
                carrier_info["cost_range"]["min"] = quote.total_cost
            if quote.total_cost > carrier_info["cost_range"]["max"]:
                carrier_info["cost_range"]["max"] = quote.total_cost
            
            if quote.transit_days < carrier_info["transit_range"]["min"]:
                carrier_info["transit_range"]["min"] = quote.transit_days
            if quote.transit_days > carrier_info["transit_range"]["max"]:
                carrier_info["transit_range"]["max"] = quote.transit_days
        
        # Generate recommendations
        recommendations = []
        
        if response.cheapest_quote:
            recommendations.append({
                "type": "cost_savings",
                "message": f"Save money with {response.cheapest_quote.carrier_name} {response.cheapest_quote.service_type}",
                "details": f"${response.cheapest_quote.total_cost:.2f} - {response.cheapest_quote.transit_days} days"
            })
        
        if response.fastest_quote and response.fastest_quote != response.cheapest_quote:
            recommendations.append({
                "type": "fast_delivery",
                "message": f"Fastest delivery with {response.fastest_quote.carrier_name} {response.fastest_quote.service_type}",
                "details": f"${response.fastest_quote.total_cost:.2f} - {response.fastest_quote.transit_days} days"
            })
        
        if response.recommended_quote:
            recommendations.append({
                "type": "best_value",
                "message": f"Best overall value: {response.recommended_quote.carrier_name} {response.recommended_quote.service_type}",
                "details": f"${response.recommended_quote.total_cost:.2f} - {response.recommended_quote.transit_days} days"
            })
        
        return {
            "quotation_summary": {
                "total_quotes": response.total_quotes,
                "successful_carriers": response.successful_carriers,
                "processing_time_ms": response.processing_time_ms
            },
            "cost_analysis": cost_analysis,
            "time_analysis": time_analysis,
            "carrier_breakdown": carrier_breakdown,
            "recommendations": recommendations,
            "quotes": [quote.dict() for quote in available_quotes]
        }