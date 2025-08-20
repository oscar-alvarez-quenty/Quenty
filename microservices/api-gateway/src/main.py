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
import os
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
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
logger = structlog.get_logger("api-gateway")

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
    auth_service_url: str = "http://auth-service:8009"
    carrier_integration_service_url: str = "http://carrier-integration-service:8009"
    consul_host: str = "consul"
    consul_port: int = 8500
    
settings = Settings()

app = FastAPI(
    title="Quenty API Gateway",
    description="API Gateway for Quenty Microservices",
    version="2.0.0"
)

# Prometheus metrics
api_gateway_operations_total = Counter(
    'api_gateway_operations_total',
    'Total number of api-gateway operations',
    ['operation', 'status']
)
api_gateway_request_duration = Histogram(
    'api_gateway_request_duration_seconds',
    'Duration of api-gateway requests in seconds',
    ['method', 'endpoint']
)
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['service', 'method', 'endpoint', 'status']
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
    "carrier-integration": settings.carrier_integration_service_url,
    "auth": settings.auth_service_url,
}

# Circuit breaker decorator
@circuit(failure_threshold=5, recovery_timeout=30)
async def make_service_request(service_url: str, path: str, method: str = "GET", **kwargs):
    start_time = asyncio.get_event_loop().time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug(
                DEBUG_MESSAGES["AGW_D001"]["message"].format(request_id=f"{method}_{path}", client_ip=service_url),
                **DEBUG_MESSAGES["AGW_D001"]
            )
            response = await client.request(method, f"{service_url}{path}", **kwargs)
            response_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            logger.debug(
                DEBUG_MESSAGES["AGW_D006"]["message"].format(
                    service_name=service_url.split("//")[1].split(":")[0], 
                    status_code=response.status_code, 
                    response_time=response_time
                ),
                **DEBUG_MESSAGES["AGW_D006"]
            )
            
            if response_time > 2000:  # Log warning for slow responses
                logger.warning(
                    WARNING_MESSAGES["AGW_W001"]["message"].format(
                        service_name=service_url.split("//")[1].split(":")[0], 
                        response_time=response_time
                    ),
                    **WARNING_MESSAGES["AGW_W001"]
                )
            
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as e:
        logger.error(
            ERROR_MESSAGES["AGW_E003"]["message"].format(service_name=service_url.split("//")[1].split(":")[0]),
            **ERROR_MESSAGES["AGW_E003"]
        )
        raise
    except Exception as e:
        logger.error(
            ERROR_MESSAGES["AGW_E002"]["message"].format(service_name=service_url.split("//")[1].split(":")[0]),
            **ERROR_MESSAGES["AGW_E002"]
        )
        raise

# Retry decorator for resilience
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def resilient_request(service_name: str, path: str, method: str = "GET", **kwargs):
    service_url = service_registry.get(service_name)
    if not service_url:
        logger.error(
            ERROR_MESSAGES["AGW_E002"]["message"].format(service_name=service_name),
            **ERROR_MESSAGES["AGW_E002"]
        )
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    try:
        logger.info(
            INFO_MESSAGES["AGW_I002"]["message"].format(service_name=service_name, method=method, path=path),
            **INFO_MESSAGES["AGW_I002"]
        )
        result = await make_service_request(service_url, path, method, **kwargs)
        return result
    except Exception as e:
        logger.error(
            ERROR_MESSAGES["AGW_E002"]["message"].format(service_name=service_name),
            **ERROR_MESSAGES["AGW_E002"],
            error_details=str(e)
        )
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.service_name}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/services/health")
async def check_all_services():
    health_status = {}
    for service_name, service_url in service_registry.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                if response.status_code == 200:
                    health_status[service_name] = "healthy"
                    logger.info(
                        INFO_MESSAGES["AGW_I003"]["message"].format(service_name=service_name),
                        **INFO_MESSAGES["AGW_I003"]
                    )
                else:
                    health_status[service_name] = "unhealthy"
                    logger.warning(
                        WARNING_MESSAGES["AGW_W002"]["message"].format(service_name=service_name),
                        **WARNING_MESSAGES["AGW_W002"]
                    )
        except Exception as e:
            health_status[service_name] = "unreachable"
            logger.warning(
                WARNING_MESSAGES["AGW_W002"]["message"].format(service_name=service_name),
                **WARNING_MESSAGES["AGW_W002"],
                error_details=str(e)
            )
    return health_status

# Authentication endpoints
@app.post("/api/v1/auth/login")
async def login(request: Request):
    body = await request.json()
    return await resilient_request("auth", "/api/v1/auth/login", method="POST", json=body)

@app.post("/api/v1/auth/register")
async def register(request: Request):
    body = await request.json()
    return await resilient_request("auth", "/api/v1/users", method="POST", json=body)

@app.post("/api/v1/auth/refresh")
async def refresh_token(request: Request):
    body = await request.json()
    return await resilient_request("auth", "/api/v1/auth/refresh", method="POST", json=body)

@app.post("/api/v1/auth/logout")
async def logout(request: Request):
    headers = dict(request.headers)
    return await resilient_request("auth", "/api/v1/auth/logout", method="POST", headers=headers)

@app.post("/api/v1/auth/change-password")
async def change_password(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("auth", "/api/v1/auth/change-password", method="POST", json=body, headers=headers)

@app.get("/api/v1/profile")
async def get_profile(request: Request):
    headers = dict(request.headers)
    return await resilient_request("auth", "/api/v1/profile", headers=headers)

@app.put("/api/v1/profile")
async def update_profile(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("auth", "/api/v1/profile", method="PUT", json=body, headers=headers)

# OAuth endpoints
@app.get("/api/v1/auth/{provider}/login")
async def oauth_login(provider: str, redirect_uri: str = None):
    params = {"redirect_uri": redirect_uri} if redirect_uri else {}
    return await resilient_request("auth", f"/api/v1/auth/{provider}/login", params=params)

@app.get("/api/v1/auth/{provider}/callback")
async def oauth_callback(provider: str, request: Request):
    params = dict(request.query_params)
    return await resilient_request("auth", f"/api/v1/auth/{provider}/callback", params=params)

# User management endpoints
@app.post("/api/v1/users")
async def create_user(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("auth", "/api/v1/users", method="POST", json=body, headers=headers)

@app.get("/api/v1/users")
async def list_users(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("auth", "/api/v1/users", headers=headers, params=params)

@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("auth", f"/api/v1/users/{user_id}", headers=headers)

@app.put("/api/v1/users/{user_id}")
async def update_user(user_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("auth", f"/api/v1/users/{user_id}", method="PUT", json=body, headers=headers)

@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("auth", f"/api/v1/users/{user_id}", method="DELETE", headers=headers)

# Customer endpoints
@app.get("/api/v1/customers")
async def list_customers(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("customer", "/api/v1/customers", headers=headers, params=params)

@app.get("/api/v1/customers/{customer_id}")
async def get_customer(customer_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("customer", f"/api/v1/customers/{customer_id}", headers=headers)

@app.get("/api/v1/customers/by-user/{user_id}")
async def get_customer_by_user(user_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("customer", f"/api/v1/customers/by-user/{user_id}", headers=headers)

@app.post("/api/v1/customers")
async def create_customer(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("customer", "/api/v1/customers", method="POST", json=body, headers=headers)

@app.put("/api/v1/customers/{customer_id}")
async def update_customer(customer_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("customer", f"/api/v1/customers/{customer_id}", method="PUT", json=body, headers=headers)

@app.delete("/api/v1/customers/{customer_id}")
async def delete_customer(customer_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("customer", f"/api/v1/customers/{customer_id}", method="DELETE", headers=headers)

# Customer Support Tickets
@app.get("/api/v1/customers/{customer_id}/tickets")
async def get_customer_tickets(customer_id: str, request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("customer", f"/api/v1/customers/{customer_id}/tickets", headers=headers, params=params)

@app.post("/api/v1/customers/{customer_id}/tickets")
async def create_customer_ticket(customer_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("customer", f"/api/v1/customers/{customer_id}/tickets", method="POST", json=body, headers=headers)

@app.get("/api/v1/tickets/{ticket_id}/messages")
async def get_ticket_messages(ticket_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("customer", f"/api/v1/tickets/{ticket_id}/messages", headers=headers)

@app.post("/api/v1/tickets/{ticket_id}/messages")
async def add_ticket_message(ticket_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("customer", f"/api/v1/tickets/{ticket_id}/messages", method="POST", json=body, headers=headers)

# Customer Analytics
@app.get("/api/v1/customers/analytics")
async def get_customer_analytics(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("customer", "/api/v1/customers/analytics", headers=headers, params=params)

# Product endpoints
@app.get("/api/v1/products")
async def list_products(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("order", "/api/v1/products", headers=headers, params=params)

@app.get("/api/v1/products/{product_id}")
async def get_product(product_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("order", f"/api/v1/products/{product_id}", headers=headers)

@app.post("/api/v1/products")
async def create_product(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("order", "/api/v1/products", method="POST", json=body, headers=headers)

@app.put("/api/v1/products/{product_id}")
async def update_product(product_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("order", f"/api/v1/products/{product_id}", method="PUT", json=body, headers=headers)

@app.delete("/api/v1/products/{product_id}")
async def delete_product(product_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("order", f"/api/v1/products/{product_id}", method="DELETE", headers=headers)

# Order endpoints
@app.get("/api/v1/orders")
async def list_orders(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("order", "/api/v1/orders", headers=headers, params=params)

@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("order", f"/api/v1/orders/{order_id}", headers=headers)

@app.post("/api/v1/orders")
async def create_order(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("order", "/api/v1/orders", method="POST", json=body, headers=headers)

@app.put("/api/v1/orders/{order_id}/status")
async def update_order_status(order_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("order", f"/api/v1/orders/{order_id}/status", method="PUT", json=body, headers=headers)

@app.post("/api/v1/orders/{order_id}/quote")
async def quote_order(order_id: str):
    return await resilient_request("order", f"/api/v1/orders/{order_id}/quote", method="POST")

# Inventory endpoints
@app.get("/api/v1/inventory")
async def list_inventory(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("order", "/api/v1/inventory", headers=headers, params=params)

@app.get("/api/v1/products/low-stock")
async def get_low_stock_products(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("order", "/api/v1/products/low-stock", headers=headers, params=params)

@app.get("/api/v1/inventory/movements")
async def get_inventory_movements(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("order", "/api/v1/inventory/movements", headers=headers, params=params)

@app.post("/api/v1/inventory/movements")
async def create_inventory_movement(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("order", "/api/v1/inventory/movements", method="POST", json=body, headers=headers)

# Pickup endpoints
@app.get("/api/v1/pickups")
async def list_pickups(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("pickup", "/api/v1/pickups", headers=headers, params=params)

@app.post("/api/v1/pickups")
async def schedule_pickup(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("pickup", "/api/v1/pickups", method="POST", json=body, headers=headers)

@app.get("/api/v1/pickups/{pickup_id}")
async def get_pickup(pickup_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("pickup", f"/api/v1/pickups/{pickup_id}", headers=headers)

@app.put("/api/v1/pickups/{pickup_id}")
async def update_pickup(pickup_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("pickup", f"/api/v1/pickups/{pickup_id}", method="PUT", json=body, headers=headers)

@app.post("/api/v1/pickups/{pickup_id}/assign")
async def assign_pickup(pickup_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("pickup", f"/api/v1/pickups/{pickup_id}/assign", method="POST", json=body, headers=headers)

@app.post("/api/v1/pickups/{pickup_id}/complete")
async def complete_pickup(pickup_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("pickup", f"/api/v1/pickups/{pickup_id}/complete", method="POST", headers=headers)

@app.post("/api/v1/pickups/{pickup_id}/cancel")
async def cancel_pickup(pickup_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("pickup", f"/api/v1/pickups/{pickup_id}/cancel", method="POST", headers=headers)

@app.get("/api/v1/pickups/availability")
async def check_pickup_availability(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("pickup", "/api/v1/pickups/availability", headers=headers, params=params)

# Route Management endpoints
@app.post("/api/v1/routes")
async def create_route(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("pickup", "/api/v1/routes", method="POST", json=body, headers=headers)

@app.get("/api/v1/routes/{route_id}/pickups")
async def get_route_pickups(route_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("pickup", f"/api/v1/routes/{route_id}/pickups", headers=headers)

# International Shipping endpoints

# Manifest endpoints
@app.get("/api/v1/manifests")
async def list_manifests(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("international-shipping", "/api/v1/manifests", headers=headers, params=params)

@app.get("/api/v1/manifests/{manifest_id}")
async def get_manifest(manifest_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("international-shipping", f"/api/v1/manifests/{manifest_id}", headers=headers)

@app.post("/api/v1/manifests")
async def create_manifest(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("international-shipping", "/api/v1/manifests", method="POST", json=body, headers=headers)

@app.put("/api/v1/manifests/{manifest_id}")
async def update_manifest(manifest_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("international-shipping", f"/api/v1/manifests/{manifest_id}", method="PUT", json=body, headers=headers)

@app.delete("/api/v1/manifests/{manifest_id}")
async def delete_manifest(manifest_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("international-shipping", f"/api/v1/manifests/{manifest_id}", method="DELETE", headers=headers)

# Manifest Items endpoints
@app.get("/api/v1/manifests/{manifest_id}/items")
async def get_manifest_items(manifest_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("international-shipping", f"/api/v1/manifests/{manifest_id}/items", headers=headers)

@app.post("/api/v1/manifests/{manifest_id}/items")
async def create_manifest_item(manifest_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("international-shipping", f"/api/v1/manifests/{manifest_id}/items", method="POST", json=body, headers=headers)

# Shipping Rates endpoints
@app.get("/api/v1/shipping/rates")
async def get_shipping_rates(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("international-shipping", "/api/v1/shipping/rates", headers=headers, params=params)

@app.post("/api/v1/shipping/validate")
async def validate_shipping(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("international-shipping", "/api/v1/shipping/validate", method="POST", json=body, headers=headers)

# Countries endpoints
@app.get("/api/v1/countries")
async def list_countries(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("international-shipping", "/api/v1/countries", headers=headers, params=params)

@app.post("/api/v1/countries")
async def create_country(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("international-shipping", "/api/v1/countries", method="POST", json=body, headers=headers)

# Carriers endpoints
@app.get("/api/v1/carriers")
async def list_carriers(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("international-shipping", "/api/v1/carriers", headers=headers, params=params)

@app.post("/api/v1/carriers")
async def create_carrier(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("international-shipping", "/api/v1/carriers", method="POST", json=body, headers=headers)

# Tracking endpoints
@app.get("/api/v1/tracking/{tracking_number}")
async def track_shipment(tracking_number: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("international-shipping", f"/api/v1/tracking/{tracking_number}", headers=headers)

# Microcredit endpoints

# Credit Application endpoints
@app.get("/api/v1/microcredit/applications")
async def list_credit_applications(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("microcredit", "/api/v1/applications", headers=headers, params=params)

@app.post("/api/v1/microcredit/applications")
async def create_credit_application(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("microcredit", "/api/v1/applications", method="POST", json=body, headers=headers)

@app.get("/api/v1/microcredit/applications/{application_id}")
async def get_credit_application(application_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("microcredit", f"/api/v1/applications/{application_id}", headers=headers)

@app.post("/api/v1/microcredit/applications/{application_id}/decision")
async def make_credit_decision(application_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("microcredit", f"/api/v1/applications/{application_id}/decision", method="POST", json=body, headers=headers)

# Credit Account endpoints
@app.get("/api/v1/microcredit/accounts")
async def list_credit_accounts(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("microcredit", "/api/v1/accounts", headers=headers, params=params)

@app.post("/api/v1/microcredit/accounts/{account_id}/disburse")
async def disburse_credit(account_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("microcredit", f"/api/v1/accounts/{account_id}/disburse", method="POST", json=body, headers=headers)

# Payment endpoints
@app.get("/api/v1/microcredit/accounts/{account_id}/payments")
async def get_payment_history(account_id: str, request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("microcredit", f"/api/v1/accounts/{account_id}/payments", headers=headers, params=params)

@app.post("/api/v1/microcredit/accounts/{account_id}/payments")
async def make_payment(account_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("microcredit", f"/api/v1/accounts/{account_id}/payments", method="POST", json=body, headers=headers)

# Credit Score endpoints
@app.get("/api/v1/microcredit/credit-score/{customer_id}")
async def get_credit_score(customer_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("microcredit", f"/api/v1/credit-score/{customer_id}", headers=headers)

# Analytics endpoints
@app.get("/api/v1/analytics/dashboard")
async def get_analytics_dashboard(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("analytics", "/api/v1/analytics/dashboard", headers=headers, params=params)

@app.post("/api/v1/analytics/metrics")
async def ingest_metric(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("analytics", "/api/v1/analytics/metrics", method="POST", json=body, headers=headers)

@app.post("/api/v1/analytics/query")
async def query_analytics(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("analytics", "/api/v1/analytics/query", method="POST", json=body, headers=headers)

@app.post("/api/v1/analytics/reports")
async def generate_report(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("analytics", "/api/v1/analytics/reports", method="POST", json=body, headers=headers)

@app.get("/api/v1/analytics/reports/{report_id}")
async def get_report_status(report_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("analytics", f"/api/v1/analytics/reports/{report_id}", headers=headers)

@app.get("/api/v1/analytics/trends")
async def get_trends(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("analytics", "/api/v1/analytics/trends", headers=headers, params=params)

# Reverse Logistics endpoints
@app.get("/api/v1/returns")
async def list_returns(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("reverse-logistics", "/api/v1/returns", headers=headers, params=params)

@app.post("/api/v1/returns")
async def create_return(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", "/api/v1/returns", method="POST", json=body, headers=headers)

@app.get("/api/v1/returns/{return_id}")
async def get_return(return_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}", headers=headers)

@app.put("/api/v1/returns/{return_id}/approve")
async def approve_return(return_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}/approve", method="PUT", headers=headers)

@app.put("/api/v1/returns/{return_id}/reject")
async def reject_return(return_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}/reject", method="PUT", json=body, headers=headers)

@app.post("/api/v1/returns/{return_id}/schedule-pickup")
async def schedule_return_pickup(return_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}/schedule-pickup", method="POST", json=body, headers=headers)

@app.post("/api/v1/returns/{return_id}/inspection")
async def create_return_inspection(return_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}/inspection", method="POST", json=body, headers=headers)

@app.post("/api/v1/returns/{return_id}/process")
async def process_return(return_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}/process", method="POST", json=body, headers=headers)

@app.get("/api/v1/returns/{return_id}/tracking")
async def track_return(return_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("reverse-logistics", f"/api/v1/returns/{return_id}/tracking", headers=headers)

# Franchise endpoints
@app.get("/api/v1/franchises")
async def list_franchises(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("franchise", "/api/v1/franchises", headers=headers, params=params)

@app.post("/api/v1/franchises")
async def create_franchise(request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("franchise", "/api/v1/franchises", method="POST", json=body, headers=headers)

@app.get("/api/v1/franchises/{franchise_id}")
async def get_franchise(franchise_id: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("franchise", f"/api/v1/franchises/{franchise_id}", headers=headers)

@app.put("/api/v1/franchises/{franchise_id}")
async def update_franchise(franchise_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("franchise", f"/api/v1/franchises/{franchise_id}", method="PUT", json=body, headers=headers)

@app.put("/api/v1/franchises/{franchise_id}/status")
async def update_franchise_status(franchise_id: str, request: Request):
    body = await request.json()
    headers = dict(request.headers)
    return await resilient_request("franchise", f"/api/v1/franchises/{franchise_id}/status", method="PUT", json=body, headers=headers)

# Territory Management endpoints
@app.get("/api/v1/territories")
async def list_territories(request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("franchise", "/api/v1/territories", headers=headers, params=params)

@app.get("/api/v1/territories/{territory_code}")
async def get_territory(territory_code: str, request: Request):
    headers = dict(request.headers)
    return await resilient_request("franchise", f"/api/v1/territories/{territory_code}", headers=headers)

# Performance Tracking endpoints
@app.get("/api/v1/franchises/{franchise_id}/performance")
async def get_franchise_performance(franchise_id: str, request: Request):
    headers = dict(request.headers)
    params = dict(request.query_params)
    return await resilient_request("franchise", f"/api/v1/franchises/{franchise_id}/performance", headers=headers, params=params)

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
    logger.info(
        INFO_MESSAGES["AGW_I001"]["message"].format(port=8000),
        **INFO_MESSAGES["AGW_I001"]
    )

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