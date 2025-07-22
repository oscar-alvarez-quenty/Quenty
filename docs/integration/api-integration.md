# API Integration Guide

## Overview

This guide provides comprehensive information for integrating with the Quenty microservices platform, including authentication, API usage patterns, SDKs, webhooks, and best practices.

## API Architecture

### Base URLs

```
Production:  https://api.quenty.com
Staging:     https://staging-api.quenty.com  
Development: http://localhost:8000
```

### Service Endpoints

| Service | Port | Base Path | Description |
|---------|------|-----------|-------------|
| API Gateway | 8000 | `/api/v1` | Main entry point |
| Customer Service | 8001 | `/api/v1/users`, `/api/v1/companies` | User & company management |
| Order Service | 8002 | `/api/v1/products`, `/api/v1/orders` | Order & inventory management |  
| Shipping Service | 8004 | `/api/v1/manifests`, `/api/v1/shipping` | International shipping |

## Authentication

### JWT Token Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### API Key Authentication

For server-to-server integrations:

```http
GET /api/v1/orders
Authorization: Bearer YOUR_API_KEY
X-Company-ID: COMP-001
```

### Token Refresh

```http  
POST /api/v1/auth/refresh
Content-Type: application/json
Authorization: Bearer REFRESH_TOKEN

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## API Usage Patterns

### Standard CRUD Operations

#### Create Resource
```http
POST /api/v1/users
Content-Type: application/json
Authorization: Bearer ACCESS_TOKEN

{
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Read Resources
```http
# List resources
GET /api/v1/users?limit=20&offset=0&active=true

# Get specific resource  
GET /api/v1/users/123
```

#### Update Resource
```http
PUT /api/v1/users/123
Content-Type: application/json
Authorization: Bearer ACCESS_TOKEN

{
  "first_name": "John Updated",
  "phone": "+1234567890"
}
```

#### Delete Resource
```http
DELETE /api/v1/users/123
Authorization: Bearer ACCESS_TOKEN
```

### Pagination

All list endpoints support pagination:

```http
GET /api/v1/orders?limit=50&offset=100
```

**Response:**
```json
{
  "orders": [...],
  "total": 1250,
  "limit": 50,
  "offset": 100,
  "has_next": true,
  "has_previous": true
}
```

### Filtering and Search

```http
# Filter by status
GET /api/v1/orders?status=pending&status=processing

# Search by name
GET /api/v1/products?search=electronics

# Date range filtering
GET /api/v1/orders?created_from=2025-01-01&created_to=2025-01-31

# Complex filtering
GET /api/v1/manifests?company_id=COMP-001&status=submitted&destination_country=US
```

### Sorting

```http
# Sort by single field
GET /api/v1/orders?sort=created_at

# Sort descending
GET /api/v1/orders?sort=-created_at

# Multiple sort fields
GET /api/v1/products?sort=category,name
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": {
      "user_id": "123",
      "timestamp": "2025-07-22T10:30:00Z",
      "request_id": "req_abc123"
    }
  }
}
```

### Validation Errors

```json
{
  "error": {
    "code": "VALIDATION_ERROR", 
    "message": "Request validation failed",
    "details": {
      "field_errors": {
        "email": ["Invalid email format"],
        "password": ["Password must be at least 8 characters"]
      }
    }
  }
}
```

## Rate Limiting

### Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642781123
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642781123
Retry-After: 60

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds."
  }
}
```

## Webhooks

### Webhook Configuration

Register webhook endpoints:

```http
POST /api/v1/webhooks
Content-Type: application/json
Authorization: Bearer ACCESS_TOKEN

{
  "url": "https://your-app.com/webhooks/quenty",
  "events": ["order.created", "order.shipped", "manifest.submitted"],
  "secret": "your_webhook_secret",
  "active": true
}
```

### Webhook Events

#### Order Events
- `order.created` - New order created
- `order.updated` - Order status changed
- `order.shipped` - Order shipped
- `order.delivered` - Order delivered
- `order.cancelled` - Order cancelled

#### Shipping Events
- `manifest.created` - New manifest created
- `manifest.submitted` - Manifest submitted for processing
- `manifest.approved` - Manifest approved by carrier
- `manifest.shipped` - Manifest dispatched
- `shipment.tracking_update` - Tracking status updated

#### User Events
- `user.created` - New user registered
- `user.updated` - User profile updated
- `company.created` - New company registered

### Webhook Payload

```json
{
  "event": "order.created",
  "timestamp": "2025-07-22T10:30:00Z",
  "data": {
    "order_id": "ORD-123",
    "customer_id": "CUST-456",
    "status": "pending",
    "total_amount": 299.99,
    "items": [...]
  },
  "webhook_id": "wh_abc123",
  "delivery_attempt": 1
}
```

### Webhook Verification

Verify webhook authenticity using HMAC signature:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

## SDK Examples

### Python SDK

```python
from quenty_sdk import QuentyClient

# Initialize client
client = QuentyClient(
    base_url="https://api.quenty.com",
    api_key="your_api_key",
    company_id="COMP-001"
)

# Create user
user = client.users.create({
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
})

# List orders
orders = client.orders.list(
    status="pending",
    limit=50,
    offset=0
)

# Create manifest
manifest = client.manifests.create({
    "origin_country": "MX",
    "destination_country": "US",
    "items": [
        {
            "description": "Electronics",
            "quantity": 1,
            "weight": 2.5,
            "value": 500.0
        }
    ]
})

# Get shipping rates
rates = client.shipping.get_rates(
    manifest_id=manifest.id,
    carriers=["DHL", "FedEx"]
)
```

### JavaScript SDK

```javascript
import QuentyClient from '@quenty/sdk';

// Initialize client
const client = new QuentyClient({
  baseUrl: 'https://api.quenty.com',
  apiKey: 'your_api_key',
  companyId: 'COMP-001'
});

// Create product
const product = await client.products.create({
  name: 'Sample Product',
  sku: 'SKU-001',
  price: 99.99,
  category: 'Electronics'
});

// List inventory
const inventory = await client.inventory.list({
  location: 'Warehouse A',
  lowStock: true
});

// Create order
const order = await client.orders.create({
  customerId: 'CUST-123',
  items: [
    {
      productId: product.id,
      quantity: 2
    }
  ]
});
```

### cURL Examples

#### Create Company
```bash
curl -X POST "https://api.quenty.com/api/v1/companies" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "business_name": "Acme Corporation LLC",
    "document_type": "NIT",
    "document_number": "123456789"
  }'
```

#### Get Orders
```bash
curl -X GET "https://api.quenty.com/api/v1/orders?status=pending&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Company-ID: COMP-001"
```

#### Create Manifest
```bash
curl -X POST "https://api.quenty.com/api/v1/manifests" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: COMP-001" \
  -d '{
    "origin_country": "MX",
    "destination_country": "US", 
    "total_weight": 5.5,
    "total_value": 1000.0,
    "items": [
      {
        "description": "Electronics",
        "quantity": 2,
        "weight": 2.75,
        "value": 500.0
      }
    ]
  }'
```

## Integration Patterns

### Synchronous Integration

For real-time operations:

```python
# Order creation with immediate inventory check
try:
    # Check inventory
    inventory = client.inventory.get(product_id=123)
    if inventory.available_quantity >= requested_quantity:
        # Create order
        order = client.orders.create(order_data)
        return {"success": True, "order_id": order.id}
    else:
        return {"success": False, "error": "Insufficient inventory"}
except Exception as e:
    return {"success": False, "error": str(e)}
```

### Asynchronous Integration

For heavy operations:

```python
# Create manifest and get rates asynchronously
manifest = client.manifests.create(manifest_data)

# Poll for rate updates
import time
max_attempts = 10
attempt = 0

while attempt < max_attempts:
    rates = client.shipping.get_rates(manifest.id)
    if rates:
        break
    time.sleep(2)
    attempt += 1
```

### Batch Operations

```python
# Bulk product creation
products_data = [
    {"name": "Product 1", "sku": "SKU-001", "price": 99.99},
    {"name": "Product 2", "sku": "SKU-002", "price": 149.99},
    # ... more products
]

# Process in batches
batch_size = 100
for i in range(0, len(products_data), batch_size):
    batch = products_data[i:i + batch_size]
    result = client.products.bulk_create(batch)
    print(f"Created {len(result.created)} products")
```

## Best Practices

### 1. Authentication Management

```python
class QuentyClientWrapper:
    def __init__(self, api_key, company_id):
        self.client = QuentyClient(api_key=api_key, company_id=company_id)
        self.token_expires_at = None
        
    def _ensure_valid_token(self):
        if not self.token_expires_at or time.time() > self.token_expires_at:
            self._refresh_token()
            
    def _refresh_token(self):
        response = self.client.auth.refresh()
        self.token_expires_at = time.time() + response.expires_in
```

### 2. Error Handling

```python
from quenty_sdk.exceptions import QuentyAPIError, RateLimitError

def safe_api_call(api_function, *args, **kwargs):
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            return api_function(*args, **kwargs)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                time.sleep(e.retry_after)
                continue
            raise
        except QuentyAPIError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            raise
```

### 3. Pagination Handling

```python
def get_all_orders(client, **filters):
    orders = []
    offset = 0
    limit = 100
    
    while True:
        response = client.orders.list(
            limit=limit,
            offset=offset,
            **filters
        )
        orders.extend(response.orders)
        
        if not response.has_next:
            break
            
        offset += limit
        
    return orders
```

### 4. Caching Strategy

```python
from functools import lru_cache
import time

class CachedQuentyClient:
    def __init__(self, client):
        self.client = client
        self._cache = {}
        
    @lru_cache(maxsize=1000)
    def get_product(self, product_id, ttl=300):
        cache_key = f"product_{product_id}"
        now = time.time()
        
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if now - timestamp < ttl:
                return data
                
        product = self.client.products.get(product_id)
        self._cache[cache_key] = (product, now)
        return product
```

## Testing Integration

### Unit Tests

```python
import unittest
from unittest.mock import patch, MagicMock
from your_app import QuentyIntegration

class TestQuentyIntegration(unittest.TestCase):
    
    def setUp(self):
        self.integration = QuentyIntegration(
            api_key="test_key",
            company_id="TEST-COMP"
        )
    
    @patch('quenty_sdk.QuentyClient')
    def test_create_order(self, mock_client):
        # Setup mock
        mock_client.orders.create.return_value = MagicMock(id="ORD-123")
        
        # Test
        result = self.integration.create_order({
            "customer_id": "CUST-123",
            "items": [{"product_id": 1, "quantity": 2}]
        })
        
        # Assert
        self.assertEqual(result.id, "ORD-123")
        mock_client.orders.create.assert_called_once()
```

### Integration Tests

```python
import pytest
from quenty_sdk import QuentyClient

@pytest.fixture
def client():
    return QuentyClient(
        base_url="http://localhost:8000",
        api_key="test_api_key",
        company_id="TEST-COMP"
    )

def test_full_order_workflow(client):
    # Create customer
    customer = client.users.create({
        "username": "test_user",
        "email": "test@example.com"
    })
    
    # Create product
    product = client.products.create({
        "name": "Test Product",
        "sku": "TEST-001",
        "price": 99.99
    })
    
    # Create order
    order = client.orders.create({
        "customer_id": customer.unique_id,
        "items": [{"product_id": product.id, "quantity": 1}]
    })
    
    # Verify order
    assert order.status == "pending"
    assert len(order.items) == 1
    
    # Cleanup
    client.orders.delete(order.id)
    client.products.delete(product.id)
    client.users.delete(customer.id)
```

## Monitoring and Debugging

### Request Logging

```python
import logging
from quenty_sdk.middleware import RequestLoggingMiddleware

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('quenty.api')

client = QuentyClient(
    api_key="your_key",
    middlewares=[RequestLoggingMiddleware(logger)]
)
```

### Performance Monitoring

```python
import time
from functools import wraps

def monitor_api_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            print(f"API call {func.__name__}: {duration:.2f}s, success: {success}")
    return wrapper
```

## Security Considerations

### 1. API Key Management
- Store API keys securely (environment variables, key management systems)
- Rotate API keys regularly
- Use different keys for different environments

### 2. Input Validation
```python
def validate_order_data(data):
    required_fields = ['customer_id', 'items']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
            
    if not isinstance(data['items'], list) or len(data['items']) == 0:
        raise ValueError("Order must have at least one item")
```

### 3. Rate Limiting Compliance
- Implement client-side rate limiting
- Use exponential backoff for retries
- Monitor rate limit headers

### 4. Data Privacy
- Only request necessary data
- Implement data retention policies
- Use HTTPS for all API calls