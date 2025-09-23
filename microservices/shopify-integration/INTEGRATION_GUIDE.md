# Shopify Integration Guide

## Table of Contents
1. [Initial Setup](#initial-setup)
2. [Store Configuration](#store-configuration)
3. [OAuth Integration](#oauth-integration)
4. [Private App Setup](#private-app-setup)
5. [Webhook Configuration](#webhook-configuration)
6. [Data Synchronization](#data-synchronization)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Initial Setup

### Prerequisites

1. **Shopify Store**: Active Shopify store or development store
2. **App Credentials**: Either OAuth app or Private app credentials
3. **Server Requirements**: Public URL for webhooks (use ngrok for development)

### Installation Steps

1. **Start the service**:
```bash
docker-compose up -d shopify-integration shopify-worker shopify-beat
```

2. **Run database migrations**:
```bash
docker-compose exec shopify-integration alembic upgrade head
```

3. **Verify installation**:
```bash
curl http://localhost:8010/health
```

## Store Configuration

### Method 1: OAuth App

#### Step 1: Create Shopify App

1. Go to [Shopify Partners](https://partners.shopify.com/)
2. Create new app
3. Set OAuth redirect URL:
   ```
   https://your-domain.com/api/v1/auth/oauth/callback
   ```

4. Configure required scopes:
   ```
   read_products, write_products,
   read_orders, write_orders,
   read_customers, write_customers,
   read_inventory, write_inventory,
   read_fulfillments, write_fulfillments
   ```

#### Step 2: Implement OAuth Flow

1. **Initiate OAuth**:
```python
import requests

# Start OAuth flow
params = {
    "shop": "myshop.myshopify.com"
}
response = requests.get(
    "http://localhost:8010/api/v1/auth/oauth/authorize",
    params=params
)
auth_url = response.json()["auth_url"]
# Redirect user to auth_url
```

2. **Handle OAuth Callback**:
```python
# After user approves, Shopify redirects to callback
# Your callback endpoint should call:
callback_data = {
    "shop": "myshop.myshopify.com",
    "code": "authorization_code_from_shopify",
    "state": "optional_state_parameter"
}
response = requests.post(
    "http://localhost:8010/api/v1/auth/oauth/callback",
    json=callback_data
)
store = response.json()
print(f"Store registered with ID: {store['id']}")
```

### Method 2: Private App

#### Step 1: Create Private App in Shopify

1. Go to your Shopify Admin
2. Navigate to Settings → Apps and sales channels
3. Click "Develop apps"
4. Create private app
5. Configure Admin API scopes
6. Generate API credentials

#### Step 2: Register Private App

```python
import requests

store_data = {
    "store_domain": "myshop.myshopify.com",
    "access_token": "shppa_xxx",  # Private app password
    "api_key": "xxx",
    "api_secret": "xxx",
    "private_app": true
}

response = requests.post(
    "http://localhost:8010/api/v1/stores",
    json=store_data
)
store = response.json()
print(f"Store registered with ID: {store['id']}")
```

## Webhook Configuration

### Register Webhooks

```python
import requests

# Register all standard webhooks
webhook_config = {
    "store_id": 1,
    "base_url": "https://your-domain.com",
    "topics": [
        "orders/create",
        "orders/updated",
        "orders/cancelled",
        "orders/fulfilled",
        "products/create",
        "products/update",
        "products/delete",
        "customers/create",
        "customers/update",
        "inventory_levels/update"
    ]
}

response = requests.post(
    "http://localhost:8010/api/v1/webhooks/register-all",
    json=webhook_config
)
result = response.json()
print(f"Registered {result['total_registered']} webhooks")
```

### Handle Incoming Webhooks

```python
from fastapi import Request, HTTPException
import hmac
import hashlib
import base64

@app.post("/webhooks/orders-create")
async def handle_order_created(request: Request):
    # Get headers
    topic = request.headers.get("X-Shopify-Topic")
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain")
    
    # Get raw body
    body = await request.body()
    
    # Verify webhook
    secret = "your_webhook_secret"
    calculated_hmac = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
    ).decode()
    
    if not hmac.compare_digest(calculated_hmac, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid webhook")
    
    # Process webhook
    order = await request.json()
    
    # Forward to integration service
    response = requests.post(
        "http://localhost:8010/api/v1/webhooks/process",
        json=order,
        headers={
            "X-Shopify-Topic": topic,
            "X-Shopify-Shop-Domain": shop_domain
        }
    )
    
    return {"status": "success"}
```

## Data Synchronization

### Initial Full Sync

```python
import requests
from datetime import datetime, timedelta

store_id = 1

# Sync products
print("Syncing products...")
response = requests.post(
    "http://localhost:8010/api/v1/sync/products",
    json={
        "store_id": store_id,
        "full_sync": True
    }
)
print(f"Products sync: {response.json()}")

# Sync orders (last 30 days)
print("Syncing orders...")
since_date = (datetime.now() - timedelta(days=30)).isoformat()
response = requests.post(
    "http://localhost:8010/api/v1/sync/orders",
    json={
        "store_id": store_id,
        "full_sync": False,
        "since_date": since_date
    }
)
print(f"Orders sync: {response.json()}")

# Sync customers
print("Syncing customers...")
response = requests.post(
    "http://localhost:8010/api/v1/sync/customers",
    json={
        "store_id": store_id,
        "full_sync": True
    }
)
print(f"Customers sync: {response.json()}")

# Sync inventory
print("Syncing inventory...")
response = requests.post(
    "http://localhost:8010/api/v1/sync/inventory",
    json={
        "store_id": store_id,
        "full_sync": True
    }
)
print(f"Inventory sync: {response.json()}")
```

### Schedule Periodic Sync

The service includes Celery Beat for scheduled synchronization. Configure in environment:

```env
SYNC_INTERVAL_MINUTES=30
SYNC_BATCH_SIZE=250
```

Or programmatically:

```python
from celery.schedules import crontab

# Configure periodic tasks
CELERYBEAT_SCHEDULE = {
    'sync-products': {
        'task': 'src.tasks.sync_tasks.sync_products',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'sync-orders': {
        'task': 'src.tasks.sync_tasks.sync_orders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'sync-inventory': {
        'task': 'src.tasks.sync_tasks.sync_inventory',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}
```

## Best Practices

### 1. Rate Limiting

The service handles rate limiting automatically, but follow these practices:

```python
# Good: Use bulk operations
products = [
    {"title": "Product 1", "price": 10.00},
    {"title": "Product 2", "price": 20.00},
    # ... more products
]
response = requests.post(
    "http://localhost:8010/api/v1/products/bulk",
    json={"store_id": 1, "products": products}
)

# Bad: Individual requests in loop
for product in products:
    requests.post("/api/v1/products", json=product)  # Don't do this!
```

### 2. Error Handling

```python
import time
from typing import Optional

def api_call_with_retry(
    method: str,
    url: str,
    max_retries: int = 3,
    **kwargs
) -> Optional[dict]:
    """Make API call with exponential backoff retry"""
    
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 2))
                time.sleep(retry_after)
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None
```

### 3. Webhook Processing

```python
from enum import Enum
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

class WebhookPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class WebhookProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.priority_queues = {
            WebhookPriority.HIGH: asyncio.Queue(),
            WebhookPriority.MEDIUM: asyncio.Queue(),
            WebhookPriority.LOW: asyncio.Queue()
        }
    
    async def process_webhook(
        self,
        topic: str,
        data: Dict[str, Any],
        priority: WebhookPriority = WebhookPriority.MEDIUM
    ):
        """Process webhook with priority"""
        await self.priority_queues[priority].put({
            'topic': topic,
            'data': data,
            'timestamp': datetime.now()
        })
    
    async def worker(self):
        """Process webhooks in priority order"""
        while True:
            # Check high priority first
            for priority in WebhookPriority:
                queue = self.priority_queues[priority]
                if not queue.empty():
                    webhook = await queue.get()
                    await self._process(webhook)
                    break
            await asyncio.sleep(0.1)
    
    async def _process(self, webhook: Dict[str, Any]):
        """Actually process the webhook"""
        topic = webhook['topic']
        data = webhook['data']
        
        # Process based on topic
        if topic == 'orders/create':
            await self.process_order_created(data)
        elif topic == 'inventory_levels/update':
            await self.process_inventory_update(data)
        # ... more handlers
```

### 4. Data Caching

```python
import redis
import json
from typing import Optional

class ShopifyCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.ttl = 300  # 5 minutes
    
    def get_product(self, product_id: str) -> Optional[dict]:
        """Get product from cache"""
        key = f"product:{product_id}"
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set_product(self, product_id: str, product: dict):
        """Cache product data"""
        key = f"product:{product_id}"
        self.redis_client.setex(
            key,
            self.ttl,
            json.dumps(product)
        )
    
    def invalidate_product(self, product_id: str):
        """Remove product from cache"""
        key = f"product:{product_id}"
        self.redis_client.delete(key)
```

### 5. Monitoring

```python
import logging
from prometheus_client import Counter, Histogram, Gauge

# Metrics
webhook_counter = Counter(
    'shopify_webhooks_total',
    'Total webhooks received',
    ['topic', 'store']
)
sync_duration = Histogram(
    'shopify_sync_duration_seconds',
    'Sync duration in seconds',
    ['sync_type']
)
active_stores = Gauge(
    'shopify_active_stores',
    'Number of active stores'
)

# Structured logging
logger = logging.getLogger(__name__)

class ShopifyMonitor:
    @staticmethod
    def log_webhook(topic: str, store: str, success: bool):
        """Log webhook processing"""
        webhook_counter.labels(topic=topic, store=store).inc()
        
        if success:
            logger.info(
                "Webhook processed",
                extra={
                    'topic': topic,
                    'store': store,
                    'status': 'success'
                }
            )
        else:
            logger.error(
                "Webhook failed",
                extra={
                    'topic': topic,
                    'store': store,
                    'status': 'failed'
                }
            )
```

## Troubleshooting

### Common Issues

#### 1. OAuth Redirect Not Working

**Problem**: OAuth callback fails or redirects to wrong URL

**Solution**:
```python
# Check callback URL configuration
print(f"Callback URL: {os.getenv('OAUTH_CALLBACK_URL')}")

# Ensure it matches Shopify app settings exactly
# Including protocol (https) and trailing slashes
```

#### 2. Webhook Verification Failures

**Problem**: Webhooks fail HMAC verification

**Solution**:
```python
# Debug webhook verification
def debug_webhook_verification(body: bytes, hmac_header: str, secret: str):
    # Ensure body is raw bytes
    print(f"Body type: {type(body)}")
    print(f"Body (first 100 chars): {body[:100]}")
    
    # Calculate HMAC
    calculated = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    
    print(f"Received HMAC: {hmac_header}")
    print(f"Calculated HMAC: {calculated}")
    print(f"Match: {hmac.compare_digest(calculated, hmac_header)}")
```

#### 3. Rate Limiting Issues

**Problem**: Getting 429 errors frequently

**Solution**:
```python
# Check current rate limit status
response = requests.get(
    "http://localhost:8010/api/v1/products",
    params={"store_id": 1, "limit": 1}
)
print(f"Rate limit remaining: {response.headers.get('X-RateLimit-Remaining')}")
print(f"Rate limit reset: {response.headers.get('X-RateLimit-Reset')}")

# Use bulk operations for large datasets
# Enable caching to reduce API calls
# Implement queue-based processing
```

#### 4. Sync Failures

**Problem**: Data sync incomplete or failing

**Solution**:
```python
# Check sync logs
response = requests.get(
    "http://localhost:8010/api/v1/sync/logs",
    params={"store_id": 1}
)
logs = response.json()

for log in logs['logs']:
    if log['status'] == 'failed':
        print(f"Failed sync: {log['sync_type']}")
        print(f"Error: {log['error_message']}")
        print(f"Details: {log['error_details']}")

# Retry failed sync with smaller batch
response = requests.post(
    "http://localhost:8010/api/v1/sync/products",
    json={
        "store_id": 1,
        "batch_size": 50,  # Smaller batch
        "retry_failed": True
    }
)
```

#### 5. Database Connection Issues

**Problem**: Can't connect to database

**Solution**:
```bash
# Check database connectivity
docker-compose exec shopify-integration python -c "
from database import get_db_session
with get_db_session() as session:
    result = session.execute('SELECT 1')
    print('Database connected:', result.scalar() == 1)
"

# Check migrations
docker-compose exec shopify-integration alembic current

# Reset database if needed
docker-compose exec shopify-integration alembic downgrade base
docker-compose exec shopify-integration alembic upgrade head
```

### Debug Mode

Enable debug mode for detailed logging:

```env
LOG_LEVEL=DEBUG
SQL_ECHO=true
```

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable request debugging
import http.client
http.client.HTTPConnection.debuglevel = 1
```

### Performance Tuning

1. **Database Indexes**: Ensure indexes are created
```sql
-- Check existing indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename LIKE 'shopify_%';
```

2. **Connection Pooling**: Optimize pool size
```python
# In database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

3. **Caching Strategy**: Implement multi-level cache
```python
# L1: In-memory cache
# L2: Redis cache
# L3: Database cache
```

## Support

For additional help:
1. Check logs: `docker-compose logs shopify-integration`
2. Review API documentation: http://localhost:8010/docs
3. Monitor Celery tasks: http://localhost:5556 (Flower UI)
4. Check metrics: http://localhost:8010/metrics