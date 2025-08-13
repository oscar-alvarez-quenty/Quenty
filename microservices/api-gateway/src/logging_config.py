"""
API Gateway Logging Configuration
Comprehensive logging dictionaries for all log levels
"""

# Error Messages Dictionary
ERROR_MESSAGES = {
    "AGW_E001": {
        "code": "AGW_E001",
        "message": "Failed to authenticate request",
        "level": "ERROR",
        "description": "Authentication failure when validating request credentials"
    },
    "AGW_E002": {
        "code": "AGW_E002", 
        "message": "Service unavailable: {service_name}",
        "level": "ERROR",
        "description": "Target microservice is unavailable or not responding"
    },
    "AGW_E003": {
        "code": "AGW_E003",
        "message": "Request timeout to service: {service_name}",
        "level": "ERROR", 
        "description": "Request to downstream service exceeded timeout threshold"
    },
    "AGW_E004": {
        "code": "AGW_E004",
        "message": "Rate limit exceeded for client: {client_id}",
        "level": "ERROR",
        "description": "Client has exceeded allowed request rate limits"
    },
    "AGW_E005": {
        "code": "AGW_E005",
        "message": "Invalid request format: {validation_error}",
        "level": "ERROR",
        "description": "Request does not conform to expected schema or format"
    },
    "AGW_E006": {
        "code": "AGW_E006",
        "message": "Circuit breaker open for service: {service_name}",
        "level": "ERROR",
        "description": "Circuit breaker pattern activated due to service failures"
    },
    "AGW_E007": {
        "code": "AGW_E007",
        "message": "Load balancer failure: {error_details}",
        "level": "ERROR",
        "description": "Load balancing algorithm encountered an error"
    }
}

# Info Messages Dictionary
INFO_MESSAGES = {
    "AGW_I001": {
        "code": "AGW_I001",
        "message": "API Gateway started successfully on port {port}",
        "level": "INFO",
        "description": "Gateway service initialization completed successfully"
    },
    "AGW_I002": {
        "code": "AGW_I002",
        "message": "Request routed to {service_name}: {method} {path}",
        "level": "INFO", 
        "description": "Successful request routing to downstream service"
    },
    "AGW_I003": {
        "code": "AGW_I003",
        "message": "Health check passed for service: {service_name}",
        "level": "INFO",
        "description": "Downstream service health check successful"
    },
    "AGW_I004": {
        "code": "AGW_I004",
        "message": "Circuit breaker closed for service: {service_name}",
        "level": "INFO",
        "description": "Circuit breaker pattern deactivated, service recovered"
    },
    "AGW_I005": {
        "code": "AGW_I005",
        "message": "Client authenticated successfully: {client_id}",
        "level": "INFO",
        "description": "Client request authentication completed successfully"
    },
    "AGW_I006": {
        "code": "AGW_I006",
        "message": "Rate limit reset for client: {client_id}",
        "level": "INFO",
        "description": "Client rate limit window has been reset"
    },
    "AGW_I007": {
        "code": "AGW_I007",
        "message": "Service discovery updated: {service_count} services available",
        "level": "INFO",
        "description": "Service registry has been updated with new service instances"
    }
}

# Debug Messages Dictionary
DEBUG_MESSAGES = {
    "AGW_D001": {
        "code": "AGW_D001",
        "message": "Processing request: {request_id} from {client_ip}",
        "level": "DEBUG",
        "description": "Detailed request processing information"
    },
    "AGW_D002": {
        "code": "AGW_D002",
        "message": "Header validation: {headers}",
        "level": "DEBUG",
        "description": "Request header validation details"
    },
    "AGW_D003": {
        "code": "AGW_D003",
        "message": "Request body size: {body_size} bytes",
        "level": "DEBUG",
        "description": "Request payload size information"
    },
    "AGW_D004": {
        "code": "AGW_D004",
        "message": "Service selection algorithm: {algorithm} selected {service_instance}",
        "level": "DEBUG",
        "description": "Load balancing service selection details"
    },
    "AGW_D005": {
        "code": "AGW_D005",
        "message": "Request transformation: {transformation_details}",
        "level": "DEBUG",
        "description": "Request modification or transformation details"
    },
    "AGW_D006": {
        "code": "AGW_D006",
        "message": "Response received from {service_name}: {status_code} in {response_time}ms",
        "level": "DEBUG",
        "description": "Downstream service response details"
    },
    "AGW_D007": {
        "code": "AGW_D007",
        "message": "Cache operation: {operation} for key {cache_key}",
        "level": "DEBUG",
        "description": "Cache read/write operation details"
    }
}

# Warning Messages Dictionary
WARNING_MESSAGES = {
    "AGW_W001": {
        "code": "AGW_W001",
        "message": "High response time from {service_name}: {response_time}ms",
        "level": "WARNING",
        "description": "Service response time exceeds normal thresholds"
    },
    "AGW_W002": {
        "code": "AGW_W002",
        "message": "Service health check failed: {service_name}",
        "level": "WARNING",
        "description": "Downstream service health check returned failure"
    },
    "AGW_W003": {
        "code": "AGW_W003",
        "message": "High request rate from client: {client_id} ({rate} req/min)",
        "level": "WARNING", 
        "description": "Client approaching rate limit threshold"
    },
    "AGW_W004": {
        "code": "AGW_W004",
        "message": "Circuit breaker half-open for service: {service_name}",
        "level": "WARNING",
        "description": "Circuit breaker testing service availability"
    },
    "AGW_W005": {
        "code": "AGW_W005",
        "message": "Service instance unavailable: {service_instance}",
        "level": "WARNING",
        "description": "Specific service instance removed from load balancer pool"
    },
    "AGW_W006": {
        "code": "AGW_W006",
        "message": "Deprecated API endpoint accessed: {endpoint}",
        "level": "WARNING",
        "description": "Client using deprecated API version or endpoint"
    },
    "AGW_W007": {
        "code": "AGW_W007",
        "message": "Memory usage high: {memory_percentage}%",
        "level": "WARNING",
        "description": "Gateway memory usage approaching critical levels"
    }
}

# Combined logging messages for easy access
LOGGING_MESSAGES = {
    **ERROR_MESSAGES,
    **INFO_MESSAGES, 
    **DEBUG_MESSAGES,
    **WARNING_MESSAGES
}