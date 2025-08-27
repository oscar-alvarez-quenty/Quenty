# Shopify Integration Service

Comprehensive Shopify integration service with support for all major Shopify modules and features.

## Features

### Core Modules Implemented

#### 1. **Products Module** (`src/modules/products.py`)
- Complete CRUD operations for products
- Variant management
- Image handling
- Metafields support
- Bulk operations
- CSV import/export
- Product recommendations
- Search functionality

#### 2. **Orders Module** (`src/modules/orders.py`)
- Order creation and management
- Fulfillment processing
- Refunds and returns
- Transaction handling
- Risk analysis
- Order events tracking
- Bulk fulfillment
- Analytics and metrics

#### 3. **Customers Module** (`src/modules/customers.py`)
- Customer management
- Address handling
- Customer groups
- Saved searches
- Tags management
- Customer lifetime value calculation
- Segmentation
- Marketing preferences

#### 4. **Inventory Module** (`src/modules/inventory.py`)
- Multi-location inventory
- Stock level management
- Inventory adjustments
- Transfer between locations
- Low stock alerts
- Inventory value tracking
- External system sync
- Reservation system

#### 5. **Webhooks Module** (`src/modules/webhooks.py`)
- Webhook registration/management
- Event processing
- Webhook verification
- Bulk operations
- Event handlers
- Monitoring and metrics

### Additional Features

- **Authentication**: OAuth 2.0 and private app support
- **Rate Limiting**: Built-in rate limiter with bucket algorithm
- **GraphQL Support**: GraphQL queries and mutations
- **Bulk Operations**: Efficient handling of large datasets
- **Database Caching**: Local caching of Shopify data
- **Async Processing**: Celery for background tasks
- **Multi-store Support**: Handle multiple Shopify stores
- **Webhook Processing**: Real-time event handling
- **Error Handling**: Comprehensive error management
- **Monitoring**: Health checks and metrics endpoints

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (optional)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd microservices/shopify-integration
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec shopify-integration alembic upgrade head
```

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/shopify_db
export REDIS_URL=redis://localhost:6379/0
```

3. Initialize database:
```bash
alembic upgrade head
```

4. Start the service:
```bash
python src/main.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://shopify_user:shopify_pass@localhost:5432/shopify_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `HOST` | Service host | `0.0.0.0` |
| `PORT` | Service port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `SQL_ECHO` | Enable SQL query logging | `false` |

### Shopify Store Configuration

Store credentials are managed through the API and stored encrypted in the database.

## API Documentation

### Authentication

#### OAuth Flow

1. **Initiate OAuth**:
```http
GET /api/v1/auth/oauth/authorize?shop=myshop.myshopify.com
```

2. **OAuth Callback**:
```http
GET /api/v1/auth/oauth/callback?code=xxx&shop=myshop.myshopify.com
```

### Core Endpoints

#### Stores
- `GET /api/v1/stores` - List all stores
- `POST /api/v1/stores` - Add new store
- `GET /api/v1/stores/{store_id}` - Get store details
- `PUT /api/v1/stores/{store_id}` - Update store
- `DELETE /api/v1/stores/{store_id}` - Remove store

#### Products
- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product
- `GET /api/v1/products/{product_id}` - Get product
- `PUT /api/v1/products/{product_id}` - Update product
- `DELETE /api/v1/products/{product_id}` - Delete product
- `POST /api/v1/products/import` - Import from CSV
- `GET /api/v1/products/export` - Export to CSV

#### Orders
- `GET /api/v1/orders` - List orders
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{order_id}` - Get order
- `PUT /api/v1/orders/{order_id}` - Update order
- `POST /api/v1/orders/{order_id}/fulfill` - Fulfill order
- `POST /api/v1/orders/{order_id}/cancel` - Cancel order
- `POST /api/v1/orders/{order_id}/refund` - Refund order

#### Customers
- `GET /api/v1/customers` - List customers
- `POST /api/v1/customers` - Create customer
- `GET /api/v1/customers/{customer_id}` - Get customer
- `PUT /api/v1/customers/{customer_id}` - Update customer
- `DELETE /api/v1/customers/{customer_id}` - Delete customer
- `GET /api/v1/customers/search` - Search customers

#### Inventory
- `GET /api/v1/inventory/levels` - Get inventory levels
- `POST /api/v1/inventory/adjust` - Adjust inventory
- `POST /api/v1/inventory/set` - Set inventory level
- `POST /api/v1/inventory/transfer` - Transfer inventory
- `GET /api/v1/inventory/locations` - List locations

#### Webhooks
- `GET /api/v1/webhooks` - List webhooks
- `POST /api/v1/webhooks` - Register webhook
- `DELETE /api/v1/webhooks/{webhook_id}` - Remove webhook
- `POST /api/v1/webhooks/register-all` - Register all webhooks
- `POST /api/v1/webhooks/process` - Process webhook event

#### Synchronization
- `POST /api/v1/sync/products` - Sync products
- `POST /api/v1/sync/orders` - Sync orders
- `POST /api/v1/sync/customers` - Sync customers
- `POST /api/v1/sync/inventory` - Sync inventory
- `GET /api/v1/sync/status` - Get sync status

### Health & Monitoring

- `GET /health` - Health check
- `GET /metrics` - Service metrics

## Usage Examples

### Python Client

```python
import requests

# Base URL
base_url = "http://localhost:8010/api/v1"

# Add a store
store_data = {
    "store_domain": "myshop.myshopify.com",
    "access_token": "your-access-token",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret"
}
response = requests.post(f"{base_url}/stores", json=store_data)
store = response.json()

# Create a product
product_data = {
    "store_id": store["id"],
    "title": "Sample Product",
    "body_html": "<p>Product description</p>",
    "vendor": "Sample Vendor",
    "product_type": "Sample Type",
    "variants": [
        {
            "price": "29.99",
            "sku": "SAMPLE-001",
            "inventory_quantity": 100
        }
    ]
}
response = requests.post(f"{base_url}/products", json=product_data)
product = response.json()

# Get orders
response = requests.get(f"{base_url}/orders", params={"store_id": store["id"]})
orders = response.json()
```

### cURL Examples

```bash
# Health check
curl http://localhost:8010/health

# List products
curl http://localhost:8010/api/v1/products?store_id=1

# Create customer
curl -X POST http://localhost:8010/api/v1/customers \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": 1,
    "email": "customer@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

## Webhook Processing

### Setting Up Webhooks

1. **Register webhooks**:
```python
import requests

webhook_data = {
    "store_id": 1,
    "topics": [
        "orders/create",
        "orders/updated",
        "products/create",
        "products/update",
        "customers/create"
    ],
    "base_url": "https://your-domain.com"
}
response = requests.post(f"{base_url}/webhooks/register-all", json=webhook_data)
```

2. **Process incoming webhooks**:
```python
@app.post("/webhook/orders-create")
async def handle_order_created(request: Request):
    # Verify webhook
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    data = await request.body()
    
    if not verify_webhook(data, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid webhook")
    
    # Process order
    order = await request.json()
    # ... process order data
```

## Background Tasks

The service uses Celery for background tasks:

- **Periodic sync**: Automatically sync data at intervals
- **Bulk operations**: Process large imports/exports
- **Webhook processing**: Async webhook event processing
- **Inventory updates**: Batch inventory adjustments

### Celery Commands

```bash
# Start worker
celery -A src.tasks.celery_app worker --loglevel=info

# Start beat scheduler
celery -A src.tasks.celery_app beat --loglevel=info

# Monitor with Flower
celery -A src.tasks.celery_app flower
```

## Database Schema

The service uses PostgreSQL with the following main tables:

- `shopify_stores` - Store configurations
- `shopify_products` - Product cache
- `shopify_variants` - Product variants
- `shopify_orders` - Order cache
- `shopify_customers` - Customer cache
- `inventory_locations` - Inventory locations
- `inventory_levels` - Stock levels
- `shopify_webhooks` - Webhook registrations
- `webhook_events` - Webhook event log
- `sync_logs` - Synchronization history

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific module
pytest tests/test_products.py
```

### Test Categories

- Unit tests for each module
- Integration tests for API endpoints
- Webhook verification tests
- Rate limiting tests
- Database operation tests

## Monitoring

### Metrics Available

- Total stores connected
- Products/Orders/Customers count
- Sync status and history
- Webhook processing stats
- API call metrics
- Error rates

### Logging

Structured logging with levels:
- `DEBUG`: Detailed information
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical issues

## Security

- **Encryption**: All sensitive data encrypted at rest
- **Authentication**: OAuth 2.0 and API key support
- **Webhook Verification**: HMAC validation
- **Rate Limiting**: Built-in rate limiting
- **Input Validation**: Pydantic models for validation
- **CORS**: Configurable CORS settings

## Troubleshooting

### Common Issues

1. **Rate Limiting**:
   - Solution: Adjust rate limiter settings or use bulk operations

2. **Webhook Verification Failures**:
   - Check webhook secret configuration
   - Ensure raw body is used for verification

3. **Sync Failures**:
   - Check API credentials
   - Review sync logs in database
   - Verify network connectivity

4. **Database Connection Issues**:
   - Verify DATABASE_URL
   - Check PostgreSQL is running
   - Review connection pool settings

## Performance Optimization

- **Caching**: Local database caching reduces API calls
- **Bulk Operations**: Process multiple items in single requests
- **Async Processing**: Background tasks for heavy operations
- **Connection Pooling**: Efficient database connections
- **Rate Limiting**: Smart rate limiting with bucket algorithm

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request

## License

[License information]

## Support

For issues or questions:
- Open an issue on GitHub
- Contact support team
- Check documentation

## Roadmap

- [ ] GraphQL API support
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-currency support
- [ ] B2B features
- [ ] Mobile app integration
- [ ] Advanced reporting
- [ ] AI-powered insights