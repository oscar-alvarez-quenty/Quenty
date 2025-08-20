from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
import time
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import structlog
import redis.asyncio as redis
import json

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent API abuse"""
    
    def __init__(
        self,
        app,
        redis_url: str = "redis://redis:6379/1",
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.redis_client = None
    
    async def dispatch(self, request: Request, call_next):
        # Initialize Redis client if not already done
        if not self.redis_client:
            self.redis_client = await redis.from_url(self.redis_url)
        
        # Get client identifier (IP or API key)
        client_id = self._get_client_id(request)
        
        # Check rate limits
        try:
            allowed = await self._check_rate_limit(client_id)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e))
            # Allow request if rate limit check fails
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = int(time.time())
        
        # Check per-minute limit
        minute_key = f"rate_limit:minute:{client_id}:{now // 60}"
        minute_count = await self.redis_client.incr(minute_key)
        await self.redis_client.expire(minute_key, 60)
        
        if minute_count > self.requests_per_minute:
            logger.warning("Rate limit exceeded (per minute)", 
                          client_id=client_id,
                          count=minute_count,
                          limit=self.requests_per_minute)
            return False
        
        # Check per-hour limit
        hour_key = f"rate_limit:hour:{client_id}:{now // 3600}"
        hour_count = await self.redis_client.incr(hour_key)
        await self.redis_client.expire(hour_key, 3600)
        
        if hour_count > self.requests_per_hour:
            logger.warning("Rate limit exceeded (per hour)",
                          client_id=client_id,
                          count=hour_count,
                          limit=self.requests_per_hour)
            return False
        
        return True
    
    async def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = int(time.time())
        minute_key = f"rate_limit:minute:{client_id}:{now // 60}"
        
        count = await self.redis_client.get(minute_key)
        if count:
            return max(0, self.requests_per_minute - int(count))
        return self.requests_per_minute


class CarrierThrottlingMiddleware(BaseHTTPMiddleware):
    """Throttling middleware for carrier-specific rate limits"""
    
    def __init__(self, app):
        super().__init__(app)
        self.carrier_limits = {
            "DHL": {"requests_per_second": 10, "requests_per_minute": 300},
            "FedEx": {"requests_per_second": 15, "requests_per_minute": 500},
            "UPS": {"requests_per_second": 10, "requests_per_minute": 400},
            "Servientrega": {"requests_per_second": 5, "requests_per_minute": 200},
            "Interrapidisimo": {"requests_per_second": 8, "requests_per_minute": 300}
        }
        self.request_times = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is a carrier-specific request
        carrier = self._extract_carrier(request)
        if not carrier:
            return await call_next(request)
        
        # Check carrier-specific rate limits
        if not self._check_carrier_limit(carrier):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Carrier rate limit exceeded",
                    "message": f"Too many requests to {carrier}. Please try again later.",
                    "carrier": carrier,
                    "retry_after": 1
                },
                headers={"Retry-After": "1"}
            )
        
        # Add slight delay to prevent overwhelming carrier APIs
        await self._apply_throttling(carrier)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _extract_carrier(self, request: Request) -> Optional[str]:
        """Extract carrier from request"""
        path = request.url.path
        
        # Check if request body contains carrier
        if request.method == "POST" and hasattr(request, '_body'):
            try:
                body = json.loads(request._body)
                return body.get('carrier')
            except:
                pass
        
        # Check if carrier is in path
        for carrier in self.carrier_limits.keys():
            if carrier.lower() in path.lower():
                return carrier
        
        return None
    
    def _check_carrier_limit(self, carrier: str) -> bool:
        """Check carrier-specific rate limit"""
        now = time.time()
        limits = self.carrier_limits.get(carrier, {})
        
        # Clean old timestamps
        self.request_times[carrier] = [
            t for t in self.request_times[carrier]
            if now - t < 60
        ]
        
        # Check per-second limit
        recent_second = [
            t for t in self.request_times[carrier]
            if now - t < 1
        ]
        if len(recent_second) >= limits.get("requests_per_second", 10):
            return False
        
        # Check per-minute limit
        if len(self.request_times[carrier]) >= limits.get("requests_per_minute", 300):
            return False
        
        # Record this request
        self.request_times[carrier].append(now)
        
        return True
    
    async def _apply_throttling(self, carrier: str):
        """Apply throttling delay based on carrier"""
        # Add small delay to prevent overwhelming carrier APIs
        delays = {
            "DHL": 0.1,
            "FedEx": 0.067,
            "UPS": 0.1,
            "Servientrega": 0.2,
            "Interrapidisimo": 0.125
        }
        
        delay = delays.get(carrier, 0.1)
        await asyncio.sleep(delay)


class WebhookAuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for webhook endpoints"""
    
    def __init__(self, app):
        super().__init__(app)
        self.webhook_secrets = {
            "DHL": "dhl_webhook_secret",
            "FedEx": "fedex_webhook_secret",
            "UPS": "ups_webhook_secret",
            "Servientrega": "servientrega_webhook_secret",
            "Interrapidisimo": "interrapidisimo_webhook_secret"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is a webhook endpoint
        if not request.url.path.startswith("/webhooks/"):
            return await call_next(request)
        
        # Extract carrier from path
        path_parts = request.url.path.split("/")
        if len(path_parts) < 3:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid webhook path"}
            )
        
        carrier = path_parts[2].upper()
        
        # Verify webhook signature
        if not self._verify_webhook_signature(request, carrier):
            logger.warning("Invalid webhook signature", carrier=carrier)
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid webhook signature"}
            )
        
        # Process webhook
        response = await call_next(request)
        
        return response
    
    def _verify_webhook_signature(self, request: Request, carrier: str) -> bool:
        """Verify webhook signature based on carrier"""
        secret = self.webhook_secrets.get(carrier)
        if not secret:
            return False
        
        # Get signature from headers (carrier-specific)
        signature_headers = {
            "DHL": "X-DHL-Signature",
            "FedEx": "X-FedEx-Signature",
            "UPS": "X-UPS-Signature",
            "Servientrega": "X-Servientrega-Token",
            "Interrapidisimo": "X-Inter-Signature"
        }
        
        header_name = signature_headers.get(carrier)
        if not header_name:
            return False
        
        provided_signature = request.headers.get(header_name)
        if not provided_signature:
            return False
        
        # TODO: Implement actual signature verification based on carrier requirements
        # This is a placeholder implementation
        return provided_signature == secret