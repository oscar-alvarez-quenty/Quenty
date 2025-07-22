from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
import httpx
import structlog
from typing import Any, Dict
import consul
import asyncio
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

class Settings(BaseSettings):
    service_name: str = "api-gateway"
    customer_service_url: str = "http://customer-service:8001"
    order_service_url: str = "http://order-service:8002"
    pickup_service_url: str = "http://pickup-service:8003"
    intl_shipping_service_url: str = "http://international-shipping-service:8004"
    microcredit_service_url: str = "http://microcredit-service:8005"
    analytics_service_url: str = "http://analytics-service:8006"
    reverse_logistics_service_url: str = "http://reverse-logistics-service:8007"
    franchise_service_url: str = "http://franchise-service:8008"
    consul_host: str = "consul"
    consul_port: int = 8500
    
settings = Settings()

app = FastAPI(
    title="Quenty API Gateway",
    description="API Gateway for Quenty Microservices",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service registry
service_registry = {
    "customer": settings.customer_service_url,
    "order": settings.order_service_url,
    "pickup": settings.pickup_service_url,
    "international-shipping": settings.intl_shipping_service_url,
    "microcredit": settings.microcredit_service_url,
    "analytics": settings.analytics_service_url,
    "reverse-logistics": settings.reverse_logistics_service_url,
    "franchise": settings.franchise_service_url,
}

# Circuit breaker decorator
@circuit(failure_threshold=5, recovery_timeout=30)
async def make_service_request(service_url: str, path: str, method: str = "GET", **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(method, f"{service_url}{path}", **kwargs)
        response.raise_for_status()
        return response.json()

# Retry decorator for resilience
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def resilient_request(service_name: str, path: str, method: str = "GET", **kwargs):
    service_url = service_registry.get(service_name)
    if not service_url:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    try:
        return await make_service_request(service_url, path, method, **kwargs)
    except Exception as e:
        logger.error(f"Error calling {service_name}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.get("/services/health")
async def check_all_services():
    health_status = {}
    for service_name, service_url in service_registry.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                health_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            health_status[service_name] = "unreachable"
    return health_status

# Customer endpoints
@app.get("/api/v1/customers/{customer_id}")
async def get_customer(customer_id: str):
    return await resilient_request("customer", f"/api/v1/customers/{customer_id}")

@app.post("/api/v1/customers")
async def create_customer(request: Request):
    body = await request.json()
    return await resilient_request("customer", "/api/v1/customers", method="POST", json=body)

# Order endpoints
@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str):
    return await resilient_request("order", f"/api/v1/orders/{order_id}")

@app.post("/api/v1/orders")
async def create_order(request: Request):
    body = await request.json()
    return await resilient_request("order", "/api/v1/orders", method="POST", json=body)

@app.post("/api/v1/orders/{order_id}/quote")
async def quote_order(order_id: str):
    return await resilient_request("order", f"/api/v1/orders/{order_id}/quote", method="POST")

# Pickup endpoints
@app.post("/api/v1/pickups")
async def schedule_pickup(request: Request):
    body = await request.json()
    return await resilient_request("pickup", "/api/v1/pickups", method="POST", json=body)

@app.get("/api/v1/pickups/{pickup_id}")
async def get_pickup(pickup_id: str):
    return await resilient_request("pickup", f"/api/v1/pickups/{pickup_id}")

# International Shipping endpoints
@app.post("/api/v1/international-shipping/kyc")
async def validate_kyc(request: Request):
    body = await request.json()
    return await resilient_request("international-shipping", "/api/v1/kyc", method="POST", json=body)

# Microcredit endpoints
@app.post("/api/v1/microcredit/apply")
async def apply_microcredit(request: Request):
    body = await request.json()
    return await resilient_request("microcredit", "/api/v1/apply", method="POST", json=body)

@app.get("/api/v1/microcredit/{customer_id}/status")
async def get_credit_status(customer_id: str):
    return await resilient_request("microcredit", f"/api/v1/{customer_id}/status")

# Analytics endpoints
@app.get("/api/v1/analytics/dashboard/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    return await resilient_request("analytics", f"/api/v1/dashboard/{dashboard_id}")

@app.get("/api/v1/analytics/kpis")
async def get_kpis(request: Request):
    params = dict(request.query_params)
    return await resilient_request("analytics", "/api/v1/kpis", params=params)

# Reverse Logistics endpoints
@app.post("/api/v1/returns")
async def create_return(request: Request):
    body = await request.json()
    return await resilient_request("reverse-logistics", "/api/v1/returns", method="POST", json=body)

@app.get("/api/v1/returns/{return_id}")
async def get_return(return_id: str):
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}")

# Franchise endpoints
@app.get("/api/v1/franchises/{franchise_id}")
async def get_franchise(franchise_id: str):
    return await resilient_request("franchise", f"/api/v1/franchises/{franchise_id}")

@app.post("/api/v1/franchises")
async def create_franchise(request: Request):
    body = await request.json()
    return await resilient_request("franchise", "/api/v1/franchises", method="POST", json=body)

# Service Discovery Registration
async def register_with_consul():
    c = consul.Consul(host=settings.consul_host, port=settings.consul_port)
    try:
        c.agent.service.register(
            name=settings.service_name,
            service_id=f"{settings.service_name}-1",
            address="api-gateway",
            port=8000,
            check=consul.Check.http(
                url="http://api-gateway:8000/health",
                interval="10s",
                timeout="5s"
            )
        )
        logger.info(f"Registered {settings.service_name} with Consul")
    except Exception as e:
        logger.error(f"Failed to register with Consul: {str(e)}")

@app.on_event("startup")
async def startup_event():
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)