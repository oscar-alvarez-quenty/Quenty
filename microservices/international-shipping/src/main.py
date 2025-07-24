from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import structlog
from typing import Optional, List, Dict, Any
import consul
import httpx
import os
import logging
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

from .models import Manifest, ManifestItem, ShippingRate, Country, ShippingCarrier, Base, ManifestStatus, ShippingZone
from .database import get_db, create_tables, engine

# Import logging configuration
try:
    from .logging_config import LOGGING_MESSAGES, ERROR_MESSAGES, INFO_MESSAGES, DEBUG_MESSAGES, WARNING_MESSAGES
except ImportError:
    # Fallback if logging_config is not available
    LOGGING_MESSAGES = ERROR_MESSAGES = INFO_MESSAGES = DEBUG_MESSAGES = WARNING_MESSAGES = {}

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Set log level from environment
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = structlog.get_logger("international-shipping-service")

class Settings(BaseSettings):
    service_name: str = "international-shipping-service"
    database_url: str = "postgresql+asyncpg://intlship:intlship_pass@intl-shipping-db:5432/intl_shipping_db"
    redis_url: str = "redis://redis:6379/4"
    consul_host: str = "consul"
    consul_port: int = 8500
    auth_service_url: str = "http://auth-service:8003"

    class Config:
        env_file = ".env"

settings = Settings()

# HTTP Bearer for token extraction
security = HTTPBearer()

app = FastAPI(
    title="International Shipping Service",
    description="Microservice for international shipping and manifest management",
    version="2.0.0"
)

# Auth dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token with auth service and return user info"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/profile",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(user_info = Depends(verify_token)):
    """Get current authenticated user"""
    return user_info

def require_permissions(permissions: list[str]):
    """Require specific permissions"""
    def permission_checker(current_user = Depends(get_current_user)):
        user_permissions = set(current_user.get('permissions', []))
        required_permissions = set(permissions)
        
        # Superusers have all permissions
        if current_user.get('is_superuser'):
            return current_user
        
        # Check if user has required permissions
        if not required_permissions.issubset(user_permissions):
            missing_perms = required_permissions - user_permissions
            raise HTTPException(
                status_code=403,
                detail=f"Missing permissions: {', '.join(missing_perms)}"
            )
        
        return current_user
    
    return permission_checker

# Pydantic models for API
class ManifestCreate(BaseModel):
    origin_country: str
    destination_country: str
    total_weight: float
    total_volume: Optional[float] = None
    total_value: float
    currency: Optional[str] = "USD"
    company_id: str
    created_by: str

class ManifestUpdate(BaseModel):
    status: Optional[str] = None
    total_weight: Optional[float] = None
    total_volume: Optional[float] = None
    total_value: Optional[float] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class ManifestResponse(BaseModel):
    id: int
    unique_id: str
    status: str
    total_weight: float
    total_volume: Optional[float]
    total_value: float
    currency: str
    origin_country: str
    destination_country: str
    shipping_zone: Optional[str]
    estimated_delivery: Optional[datetime]
    tracking_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    company_id: str
    created_by: str

class ManifestItemCreate(BaseModel):
    manifest_id: int
    description: str
    quantity: int
    weight: float
    volume: Optional[float] = None
    value: float
    hs_code: Optional[str] = None
    country_of_origin: Optional[str] = None
    product_id: Optional[int] = None

class ShippingRateCreate(BaseModel):
    manifest_id: int
    carrier_name: str
    service_type: str
    base_rate: float
    weight_rate: Optional[float] = 0.0
    volume_rate: Optional[float] = 0.0
    fuel_surcharge: Optional[float] = 0.0
    insurance_rate: Optional[float] = 0.0
    total_cost: float
    currency: Optional[str] = "USD"
    transit_days: Optional[int] = None

class CountryCreate(BaseModel):
    name: str
    iso_code: str
    zone: Optional[str] = None

class CarrierCreate(BaseModel):
    name: str
    code: str
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    supported_services: Optional[List[str]] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

# Manifest endpoints
@app.get("/api/v1/manifests", response_model=Dict[str, Any])
async def get_manifests(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_manifests = [
            {
                "id": 1,
                "unique_id": "MAN-20250122001",
                "date": datetime.utcnow() - timedelta(days=1),
                "guides_created": 15,
                "total_items": 45,
                "manifest_status": "open",
                "company_id": "COMP-001"
            },
            {
                "id": 2,
                "unique_id": "MAN-20250121001",
                "date": datetime.utcnow() - timedelta(days=2),
                "guides_created": 32,
                "total_items": 87,
                "manifest_status": "closed",
                "company_id": "COMP-002"
            }
        ]
        
        if status:
            mock_manifests = [m for m in mock_manifests if m["manifest_status"] == status]
            
        return {"manifests": mock_manifests, "total": len(mock_manifests), "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error fetching manifests: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/manifests/{manifest_id}", response_model=Dict[str, Any])
async def get_manifest(
    manifest_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "id": manifest_id,
            "unique_id": f"MAN-{8:08d}".format(manifest_id),
            "date": datetime.utcnow() - timedelta(days=1),
            "guides_created": 15,
            "total_items": 45,
            "manifest_type": 2,
            "company_id": "COMP-001",
            "warehouse_id": 1,
            "manifest_status": "open",
            "created_at": datetime.utcnow() - timedelta(days=1),
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error fetching manifest {manifest_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/manifests", response_model=Dict[str, Any])
async def create_manifest(
    manifest: ManifestCreate,
    current_user = Depends(require_permissions(["shipping:create"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        unique_id = f"MAN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "id": 16,  # Mock ID
            "unique_id": unique_id,
            "status": ManifestStatus.DRAFT.value,
            "total_weight": manifest.total_weight,
            "total_volume": manifest.total_volume,
            "total_value": manifest.total_value,
            "currency": manifest.currency,
            "origin_country": manifest.origin_country,
            "destination_country": manifest.destination_country,
            "shipping_zone": None,
            "estimated_delivery": None,
            "tracking_number": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "company_id": manifest.company_id,
            "created_by": manifest.created_by
        }
    except Exception as e:
        logger.error(f"Error creating manifest: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/manifests/{manifest_id}", response_model=Dict[str, Any])
async def update_manifest(
    manifest_id: int,
    manifest_update: ManifestUpdate,
    current_user = Depends(require_permissions(["shipping:update"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        current_manifest = await get_manifest(manifest_id, db)
        
        update_data = manifest_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in current_manifest:
                current_manifest[field] = value
        
        current_manifest["updated_at"] = datetime.utcnow()
        return current_manifest
    except Exception as e:
        logger.error(f"Error updating manifest {manifest_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/v1/manifests/{manifest_id}")
async def delete_manifest(
    manifest_id: int,
    current_user = Depends(require_permissions(["shipping:delete"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {"message": f"Manifest {manifest_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting manifest {manifest_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Manifest Items endpoints
@app.get("/api/v1/manifests/{manifest_id}/items", response_model=List[Dict[str, Any]])
async def get_manifest_items(
    manifest_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_items = [
            {
                "id": 1,
                "manifest_id": manifest_id,
                "description": "Electronics - Smartphones",
                "quantity": 10,
                "weight": 5.5,
                "volume": 0.02,
                "value": 5000.0,
                "hs_code": "8517.12",
                "country_of_origin": "CN",
                "product_id": 1,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "manifest_id": manifest_id,
                "description": "Clothing - T-shirts",
                "quantity": 50,
                "weight": 2.0,
                "volume": 0.05,
                "value": 500.0,
                "hs_code": "6109.10",
                "country_of_origin": "BD",
                "product_id": 2,
                "created_at": datetime.utcnow()
            }
        ]
        return mock_items
    except Exception as e:
        logger.error(f"Error fetching manifest items for {manifest_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/manifests/{manifest_id}/items", response_model=Dict[str, Any])
async def create_manifest_item(
    manifest_id: int,
    item: ManifestItemCreate,
    current_user = Depends(require_permissions(["shipping:create"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "id": 16,  # Mock ID
            "manifest_id": manifest_id,
            "description": item.description,
            "quantity": item.quantity,
            "weight": item.weight,
            "volume": item.volume,
            "value": item.value,
            "hs_code": item.hs_code,
            "country_of_origin": item.country_of_origin,
            "product_id": item.product_id,
            "created_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error creating manifest item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Shipping rates endpoints
@app.get("/api/v1/shipping/rates", response_model=List[Dict[str, Any]])
async def get_shipping_rates(
    origin: str = Query(...),
    destination: str = Query(...),
    weight: float = Query(...),
    value: float = Query(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_rates = [
            {
                "carrier_name": "DHL Express",
                "service_type": "Express Worldwide",
                "base_rate": 45.0,
                "weight_rate": 8.5,
                "volume_rate": 0.0,
                "fuel_surcharge": 5.5,
                "insurance_rate": value * 0.005,
                "total_cost": 45.0 + (weight * 8.5) + 5.5 + (value * 0.005),
                "currency": "USD",
                "transit_days": 3,
                "valid_until": datetime.utcnow() + timedelta(hours=24)
            },
            {
                "carrier_name": "FedEx International",
                "service_type": "International Priority",
                "base_rate": 42.0,
                "weight_rate": 7.8,
                "volume_rate": 0.0,
                "fuel_surcharge": 4.8,
                "insurance_rate": value * 0.004,
                "total_cost": 42.0 + (weight * 7.8) + 4.8 + (value * 0.004),
                "currency": "USD",
                "transit_days": 4,
                "valid_until": datetime.utcnow() + timedelta(hours=24)
            },
            {
                "carrier_name": "UPS Worldwide",
                "service_type": "Express Plus",
                "base_rate": 48.0,
                "weight_rate": 9.2,
                "volume_rate": 0.0,
                "fuel_surcharge": 6.0,
                "insurance_rate": value * 0.006,
                "total_cost": 48.0 + (weight * 9.2) + 6.0 + (value * 0.006),
                "currency": "USD",
                "transit_days": 2,
                "valid_until": datetime.utcnow() + timedelta(hours=24)
            }
        ]
        return mock_rates
    except Exception as e:
        logger.error(f"Error fetching shipping rates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/shipping/validate", response_model=Dict[str, Any])
async def validate_shipping(
    origin: str,
    destination: str,
    weight: float,
    value: float,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Shipping validation logic
        validation_results = {
            "valid": True,
            "origin_country": origin,
            "destination_country": destination,
            "weight_kg": weight,
            "value_usd": value,
            "shipping_zone": "Zone_2",
            "restricted_items": [],
            "required_documents": ["Commercial Invoice", "Packing List"],
            "estimated_transit_days": 3,
            "customs_value_limit": 2500.0,
            "weight_limit_kg": 70.0,
            "warnings": []
        }
        
        # Add warnings based on validation
        if value > 2000:
            validation_results["warnings"].append("High value shipment - additional insurance recommended")
        if weight > 30:
            validation_results["warnings"].append("Heavy shipment - additional handling charges may apply")
        
        return validation_results
    except Exception as e:
        logger.error(f"Error validating shipping: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Countries endpoints
@app.get("/api/v1/countries", response_model=List[Dict[str, Any]])
async def get_countries(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_countries = [
            {
                "id": 1,
                "name": "United States",
                "iso_code": "US",
                "zone": "Zone_1",
                "active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "name": "Mexico",
                "iso_code": "MX",
                "zone": "Zone_1",
                "active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": 3,
                "name": "Colombia",
                "iso_code": "CO",
                "zone": "Zone_2",
                "active": True,
                "created_at": datetime.utcnow()
            },
            {
                "id": 4,
                "name": "China",
                "iso_code": "CN",
                "zone": "Zone_3",
                "active": True,
                "created_at": datetime.utcnow()
            }
        ]
        return mock_countries
    except Exception as e:
        logger.error(f"Error fetching countries: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/countries", response_model=Dict[str, Any])
async def create_country(
    country: CountryCreate,
    current_user = Depends(require_permissions(["admin:create"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "id": 16,  # Mock ID
            "name": country.name,
            "iso_code": country.iso_code,
            "zone": country.zone,
            "active": True,
            "created_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error creating country: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Carriers endpoints
@app.get("/api/v1/carriers", response_model=List[Dict[str, Any]])
async def get_carriers(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        mock_carriers = [
            {
                "id": 1,
                "name": "DHL Express",
                "code": "DHL",
                "api_endpoint": "https://api.dhl.com/v1",
                "active": True,
                "supported_services": ["Express Worldwide", "Express 12:00", "Express 9:00"],
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "name": "FedEx International",
                "code": "FEDEX",
                "api_endpoint": "https://api.fedex.com/v1",
                "active": True,
                "supported_services": ["International Priority", "International Economy", "International First"],
                "created_at": datetime.utcnow()
            },
            {
                "id": 3,
                "name": "UPS Worldwide",
                "code": "UPS",
                "api_endpoint": "https://api.ups.com/v1",
                "active": True,
                "supported_services": ["Express Plus", "Express", "Express Saver"],
                "created_at": datetime.utcnow()
            }
        ]
        return mock_carriers
    except Exception as e:
        logger.error(f"Error fetching carriers: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/carriers", response_model=Dict[str, Any])
async def create_carrier(
    carrier: CarrierCreate,
    current_user = Depends(require_permissions(["admin:create"])),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "id": 16,  # Mock ID
            "name": carrier.name,
            "code": carrier.code,
            "api_endpoint": carrier.api_endpoint,
            "active": True,
            "supported_services": carrier.supported_services or [],
            "created_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error creating carrier: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Tracking endpoints
@app.get("/api/v1/tracking/{tracking_number}", response_model=Dict[str, Any])
async def track_shipment(
    tracking_number: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        return {
            "tracking_number": tracking_number,
            "status": "in_transit",
            "origin": "Mexico City, MX",
            "destination": "Miami, FL, US",
            "estimated_delivery": datetime.utcnow() + timedelta(days=2),
            "carrier": "DHL Express",
            "service_type": "Express Worldwide",
            "events": [
                {
                    "timestamp": datetime.utcnow() - timedelta(days=1),
                    "location": "Mexico City, MX",
                    "status": "picked_up",
                    "description": "Package picked up from origin"
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=12),
                    "location": "Mexico City Airport, MX",
                    "status": "in_transit",
                    "description": "Departed from origin facility"
                },
                {
                    "timestamp": datetime.utcnow() - timedelta(hours=8),
                    "location": "Miami Airport, FL, US",
                    "status": "in_transit",
                    "description": "Arrived at destination facility"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error tracking shipment {tracking_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="international-shipping-service",
            port=8004,
            check=consul.Check.http(
                url="http://international-shipping-service:8004/health",
                interval="10s",
                timeout="5s"
            )
        )
        logger.info(f"Registered {settings.service_name} with Consul")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {str(e)}")

@app.on_event("startup")
async def startup_event():
    await create_tables()
    await register_with_consul()
    logger.info(f"{settings.service_name} started")

@app.on_event("shutdown")
async def shutdown_event():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.deregister(f"{settings.service_name}-1")
        logger.info(f"Deregistered {settings.service_name} from Consul")
    except Exception as e:
        logger.error(f"Failed to deregister from Consul: {str(e)}")