from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import structlog
import time
from contextlib import asynccontextmanager
from typing import Optional

from .database import engine, Base, get_db
from .models import CarrierCredential, CarrierHealthStatus, ExchangeRate
from .carriers.dhl import DHLClient
from .carriers.fedex import FedExClient
from .carriers.ups import UPSClient
from .carriers.servientrega import ServientregaClient
from .carriers.interrapidisimo import InterrapidisimoClient
from .exchange_rate.banco_republica import BancoRepublicaClient
from .services.carrier_service import CarrierService
from .services.fallback_service import FallbackService
from .services.exchange_rate_service import ExchangeRateService
from .schemas import (
    QuoteRequest, QuoteResponse, 
    LabelRequest, LabelResponse,
    TrackingRequest, TrackingResponse,
    PickupRequest, PickupResponse,
    CarrierCredentialCreate, CarrierCredentialResponse,
    HealthCheckResponse, TRMResponse
)
from .logging_config import setup_logging

# Setup structured logging
logger = setup_logging()

# Prometheus metrics
request_count = Counter('carrier_integration_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('carrier_integration_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
carrier_api_calls = Counter('carrier_api_calls_total', 'Carrier API calls', ['carrier', 'operation', 'status'])
carrier_api_duration = Histogram('carrier_api_duration_seconds', 'Carrier API duration', ['carrier', 'operation'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Carrier Integration Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize services
    app.state.carrier_service = CarrierService()
    app.state.fallback_service = FallbackService()
    app.state.exchange_rate_service = ExchangeRateService()
    
    # Start scheduled tasks
    await app.state.exchange_rate_service.start_scheduler()
    
    logger.info("Carrier Integration Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Carrier Integration Service...")
    await app.state.exchange_rate_service.stop_scheduler()
    logger.info("Carrier Integration Service shut down")

app = FastAPI(
    title="Carrier Integration Service",
    description="Manages integrations with logistics carriers and exchange rates",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware
@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        service="carrier-integration",
        version="1.0.0"
    )

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Quote endpoints
@app.post("/api/v1/quotes", response_model=QuoteResponse)
async def get_quote(
    request: QuoteRequest,
    carrier_service: CarrierService = Depends(lambda: app.state.carrier_service),
    fallback_service: FallbackService = Depends(lambda: app.state.fallback_service)
):
    """Get shipping quote from specified carrier or best available"""
    try:
        logger.info("Processing quote request", carrier=request.carrier, destination=request.destination)
        
        if request.carrier:
            # Get quote from specific carrier
            quote = await carrier_service.get_quote(request.carrier, request)
        else:
            # Get best quote from available carriers
            quote = await carrier_service.get_best_quote(request)
        
        logger.info("Quote generated successfully", carrier=quote.carrier, amount=quote.amount)
        return quote
        
    except Exception as e:
        logger.error("Quote request failed", error=str(e))
        
        # Try fallback carrier
        if request.carrier:
            fallback_quote = await fallback_service.get_fallback_quote(request, exclude=[request.carrier])
            if fallback_quote:
                logger.info("Using fallback carrier", carrier=fallback_quote.carrier)
                return fallback_quote
        
        raise HTTPException(status_code=500, detail=str(e))

# Label generation endpoints
@app.post("/api/v1/labels", response_model=LabelResponse)
async def generate_label(
    request: LabelRequest,
    carrier_service: CarrierService = Depends(lambda: app.state.carrier_service)
):
    """Generate shipping label"""
    try:
        logger.info("Generating label", carrier=request.carrier, order_id=request.order_id)
        
        label = await carrier_service.generate_label(request.carrier, request)
        
        logger.info("Label generated successfully", tracking_number=label.tracking_number)
        return label
        
    except Exception as e:
        logger.error("Label generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Tracking endpoints
@app.post("/api/v1/tracking", response_model=TrackingResponse)
async def track_shipment(
    request: TrackingRequest,
    carrier_service: CarrierService = Depends(lambda: app.state.carrier_service)
):
    """Track shipment"""
    try:
        logger.info("Tracking shipment", carrier=request.carrier, tracking_number=request.tracking_number)
        
        tracking = await carrier_service.track_shipment(request.carrier, request.tracking_number)
        
        logger.info("Tracking retrieved successfully", status=tracking.status)
        return tracking
        
    except Exception as e:
        logger.error("Tracking failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Pickup scheduling endpoints
@app.post("/api/v1/pickups", response_model=PickupResponse)
async def schedule_pickup(
    request: PickupRequest,
    carrier_service: CarrierService = Depends(lambda: app.state.carrier_service)
):
    """Schedule pickup with carrier"""
    try:
        logger.info("Scheduling pickup", carrier=request.carrier, date=request.pickup_date)
        
        pickup = await carrier_service.schedule_pickup(request.carrier, request)
        
        logger.info("Pickup scheduled successfully", confirmation=pickup.confirmation_number)
        return pickup
        
    except Exception as e:
        logger.error("Pickup scheduling failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Carrier credential management
@app.post("/api/v1/carriers/{carrier}/credentials", response_model=CarrierCredentialResponse)
async def save_carrier_credentials(
    carrier: str,
    credentials: CarrierCredentialCreate,
    db = Depends(get_db)
):
    """Save or update carrier credentials"""
    try:
        logger.info("Saving carrier credentials", carrier=carrier)
        
        # Validate credentials
        carrier_service = app.state.carrier_service
        is_valid = await carrier_service.validate_credentials(carrier, credentials)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # Save encrypted credentials
        saved = await carrier_service.save_credentials(carrier, credentials, db)
        
        logger.info("Credentials saved successfully", carrier=carrier)
        return saved
        
    except Exception as e:
        logger.error("Failed to save credentials", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Carrier health status
@app.get("/api/v1/carriers/{carrier}/health")
async def get_carrier_health(
    carrier: str,
    carrier_service: CarrierService = Depends(lambda: app.state.carrier_service)
):
    """Get carrier integration health status"""
    try:
        health = await carrier_service.get_health_status(carrier)
        return health
    except Exception as e:
        logger.error("Failed to get carrier health", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Exchange rate endpoints
@app.get("/api/v1/exchange-rates/cop-usd", response_model=TRMResponse)
async def get_current_trm(
    exchange_service: ExchangeRateService = Depends(lambda: app.state.exchange_rate_service)
):
    """Get current TRM (COP to USD exchange rate)"""
    try:
        trm = await exchange_service.get_current_trm()
        return trm
    except Exception as e:
        logger.error("Failed to get TRM", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/exchange-rates/convert")
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    exchange_service: ExchangeRateService = Depends(lambda: app.state.exchange_rate_service)
):
    """Convert amount between currencies"""
    try:
        converted = await exchange_service.convert(amount, from_currency, to_currency)
        return {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": converted,
            "exchange_rate": await exchange_service.get_rate(from_currency, to_currency)
        }
    except Exception as e:
        logger.error("Currency conversion failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Fallback configuration
@app.post("/api/v1/fallback/configure")
async def configure_fallback(
    route: str,
    carriers: list[str],
    fallback_service: FallbackService = Depends(lambda: app.state.fallback_service)
):
    """Configure fallback priority for a route"""
    try:
        await fallback_service.configure_priority(route, carriers)
        return {"message": "Fallback configuration updated successfully"}
    except Exception as e:
        logger.error("Failed to configure fallback", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)