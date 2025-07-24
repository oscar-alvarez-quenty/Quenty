"""
Common Prometheus metrics module for all microservices
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from functools import wraps

# Common metrics for all services
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['service', 'method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['service', 'method', 'endpoint']
)

# Service-specific metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    ['service']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Duration of database queries in seconds',
    ['service', 'operation']
)

business_operations_total = Counter(
    'business_operations_total',
    'Total number of business operations',
    ['service', 'operation', 'status']
)


def track_request_metrics(service_name: str):
    """Decorator to track request metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request info
            request = kwargs.get('request') or (args[0] if args else None)
            if hasattr(request, 'method') and hasattr(request, 'url'):
                method = request.method
                endpoint = str(request.url.path)
            else:
                method = 'UNKNOWN'
                endpoint = 'UNKNOWN'
            
            # Track in-progress requests
            http_requests_in_progress.labels(
                service=service_name,
                method=method,
                endpoint=endpoint
            ).inc()
            
            start_time = time.time()
            status = '500'  # Default to error
            
            try:
                response = await func(*args, **kwargs)
                # Extract status code
                if hasattr(response, 'status_code'):
                    status = str(response.status_code)
                else:
                    status = '200'
                return response
            except Exception as e:
                # Map exceptions to status codes
                if hasattr(e, 'status_code'):
                    status = str(e.status_code)
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time
                
                http_requests_total.labels(
                    service=service_name,
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                http_request_duration_seconds.labels(
                    service=service_name,
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                http_requests_in_progress.labels(
                    service=service_name,
                    method=method,
                    endpoint=endpoint
                ).dec()
        
        return wrapper
    return decorator


async def get_metrics():
    """Generate Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)