# MercadoLibre Integration Service

## Overview

Complete integration service for MercadoLibre marketplace, the largest e-commerce platform in Latin America. This microservice handles product listings, order management, customer questions, messaging, and shipping through MercadoEnvíos.

## Features

### 🔐 Authentication & Authorization
- OAuth2 integration with MercadoLibre
- Automatic token refresh
- Multi-account support
- Secure credential storage

### 📦 Product Management
- Create, update, and delete listings
- Bulk product synchronization
- Inventory management
- Product variations support
- Image and video management
- Category prediction
- Listing health monitoring

### 🛍️ Order Processing
- Real-time order synchronization
- Order status tracking
- Payment processing integration
- Buyer communication
- Order notes and tags

### 💬 Customer Communication
- Question management and auto-response
- Direct messaging with buyers
- Message templates
- Attachment support

### 🚚 Shipping Integration (MercadoEnvíos)
- Shipping label generation
- Tracking information
- Multiple shipping methods
- Cost calculation
- Delivery management

### 🔄 Real-time Updates
- Webhook support for instant notifications
- Event-driven architecture
- Automatic data synchronization
- Background task processing

### 📊 Analytics & Monitoring
- Sales metrics
- Performance dashboards
- Prometheus metrics
- Health monitoring

## Supported Countries

The service supports all MercadoLibre sites:

| Site ID | Country | Currency | Language |
|---------|---------|----------|----------|
| MLA | Argentina | ARS | Spanish |
| MLB | Brazil | BRL | Portuguese |
| MCO | Colombia | COP | Spanish |
| MLM | Mexico | MXN | Spanish |
| MLU | Uruguay | UYU | Spanish |
| MLC | Chile | CLP | Spanish |
| MLV | Venezuela | VES | Spanish |
| MPE | Peru | PEN | Spanish |
| MEC | Ecuador | USD | Spanish |

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- MercadoLibre Developer Account
- Application credentials from MercadoLibre

### 2. Get MercadoLibre Credentials

1. Go to [MercadoLibre Developers](https://developers.mercadolibre.com/)
2. Create a new application
3. Get your `CLIENT_ID` and `CLIENT_SECRET`
4. Set redirect URI to `http://localhost:8012/auth/callback`

### 3. Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
MELI_CLIENT_ID=your_client_id
MELI_CLIENT_SECRET=your_client_secret
MELI_SITE_ID=MCO  # Your country site
```

### 4. Start the Service

```bash
# Using Docker Compose
docker-compose up -d mercadolibre-integration

# Initialize database
docker exec -it quenty-mercadolibre alembic upgrade head
```

### 5. Connect Your MercadoLibre Account

1. Open browser to: `http://localhost:8012/auth/connect`
2. Authorize the application
3. You'll be redirected back with success message

## API Documentation

### Authentication Endpoints

#### Connect MercadoLibre Account
```http
GET /auth/connect
```
Initiates OAuth2 flow

#### OAuth Callback
```http
GET /auth/callback?code={code}&state={state}
```
Handles OAuth2 callback

#### Refresh Token
```http
POST /auth/refresh/{account_id}
```
Refreshes access token

### Product Endpoints

#### List Products
```http
GET /products?account_id={id}&status={status}&offset={offset}&limit={limit}
```

#### Get Product
```http
GET /products/{item_id}
```

#### Create Product
```http
POST /products
Content-Type: application/json

{
  "account_id": 1,
  "title": "Product Title",
  "category_id": "MCO1234",
  "price": 99999,
  "available_quantity": 10,
  "condition": "new",
  "pictures": [
    {"source": "http://image.url"}
  ],
  "description": "Product description",
  "shipping": {
    "mode": "me2",
    "free_shipping": false
  }
}
```

#### Update Product
```http
PUT /products/{item_id}
Content-Type: application/json

{
  "price": 89999,
  "available_quantity": 5
}
```

#### Update Stock
```http
PATCH /products/{item_id}/stock
Content-Type: application/json

{
  "quantity": 20
}
```

#### Pause/Activate Product
```http
POST /products/{item_id}/pause
POST /products/{item_id}/activate
```

### Order Endpoints

#### List Orders
```http
GET /orders?account_id={id}&status={status}&from={date}&to={date}
```

#### Get Order Details
```http
GET /orders/{order_id}
```

#### Get Shipping Label
```http
GET /orders/{order_id}/shipping-label
```

#### Send Message to Buyer
```http
POST /orders/{order_id}/messages
Content-Type: application/json

{
  "message": "Your order has been shipped!",
  "attachments": []
}
```

### Question Endpoints

#### List Questions
```http
GET /questions?account_id={id}&status={status}&item_id={item_id}
```

#### Answer Question
```http
POST /questions/{question_id}/answer
Content-Type: application/json

{
  "text": "Answer text here"
}
```

### Webhook Endpoints

#### Register Webhook
```http
POST /webhooks/register
Content-Type: application/json

{
  "topic": "orders",
  "callback_url": "https://your-domain.com/webhook"
}
```

#### Process Webhook
```http
POST /webhooks/notification
Content-Type: application/json

{
  "resource": "/orders/123456789",
  "user_id": "123456789",
  "topic": "orders",
  "application_id": "987654321",
  "attempts": 1,
  "sent": "2024-01-01T10:00:00.000Z",
  "received": "2024-01-01T10:00:01.000Z"
}
```

### Inventory Endpoints

#### Sync Inventory
```http
POST /inventory/sync
Content-Type: application/json

{
  "account_id": 1
}
```

#### Bulk Update Stock
```http
POST /inventory/bulk-update
Content-Type: application/json

{
  "updates": [
    {"item_id": "MCO123", "quantity": 10},
    {"item_id": "MCO124", "quantity": 5}
  ]
}
```

## Database Schema

### Main Tables

- **meli_accounts**: Connected MercadoLibre accounts
- **meli_products**: Product listings
- **meli_inventory**: Stock management
- **meli_orders**: Order information
- **meli_shipments**: Shipping details
- **meli_questions**: Customer questions
- **meli_messages**: Conversation messages
- **meli_webhooks**: Webhook events
- **meli_sync_logs**: Synchronization history

## Background Tasks

The service uses Celery for background task processing:

### Periodic Tasks

- **Product Sync**: Every 30 minutes
- **Order Sync**: Every 10 minutes
- **Question Sync**: Every 15 minutes
- **Token Refresh**: Every 4 hours
- **Inventory Sync**: Every hour

### Manual Triggers

All sync tasks can be triggered manually via API endpoints.

## Webhook Topics

Subscribe to these topics for real-time updates:

- `orders`: Order status changes
- `items`: Product updates
- `questions`: New questions
- `messages`: New messages
- `shipments`: Shipping updates
- `claims`: Claim notifications
- `payments`: Payment status

## Error Handling

The service implements comprehensive error handling:

- Automatic retry with exponential backoff
- Dead letter queue for failed tasks
- Detailed error logging
- Graceful degradation

## Rate Limiting

MercadoLibre API rate limits:
- 10 requests per second per application
- Configurable burst limits
- Automatic throttling

## Security

- OAuth2 token encryption
- Secure credential storage
- Request signing for webhooks
- SQL injection prevention
- XSS protection

## Monitoring

### Health Check
```http
GET /health
```

### Metrics (Prometheus)
```http
GET /metrics
```

### Dashboard Statistics
```http
GET /dashboard-stats
```

Response:
```json
{
  "active_products": 150,
  "pending_orders": 23,
  "unanswered_questions": 5,
  "total_sales": 1250000.00
}
```

## Development

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
alembic upgrade head
```

3. Start the service:
```bash
uvicorn src.main:app --reload --port 8012
```

4. Start Celery worker:
```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

5. Start Celery beat:
```bash
celery -A src.tasks.celery_app beat --loglevel=info
```

### Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/

# Integration tests
pytest tests/integration/
```

## Docker Deployment

### Build Image
```bash
docker build -t mercadolibre-integration .
```

### Run Container
```bash
docker run -d \
  --name meli-integration \
  -p 8012:8012 \
  --env-file .env \
  mercadolibre-integration
```

### Docker Compose
```yaml
mercadolibre-integration:
  build: ./microservices/mercadolibre-integration
  ports:
    - "8012:8012"
  environment:
    - DATABASE_URL=postgresql://postgres:password@db:5432/meli_db
    - REDIS_URL=redis://redis:6379/4
  depends_on:
    - db
    - redis
    - rabbitmq
```

## Troubleshooting

### Common Issues

1. **Token Expired**
   - Solution: Use `/auth/refresh/{account_id}` endpoint

2. **Rate Limit Exceeded**
   - Solution: Adjust `RATE_LIMIT_CALLS_PER_SECOND` in config

3. **Webhook Not Receiving Events**
   - Check webhook URL is publicly accessible
   - Verify webhook secret matches

4. **Product Not Syncing**
   - Check category_id is valid
   - Verify required attributes are provided

5. **Order Messages Not Sending**
   - Ensure order status allows messaging
   - Check buyer hasn't blocked messages

## Best Practices

1. **Product Listings**
   - Use high-quality images (1200x1200px minimum)
   - Complete all recommended attributes
   - Set competitive pricing
   - Enable MercadoEnvíos for better visibility

2. **Customer Service**
   - Answer questions within 2 hours
   - Use message templates for common questions
   - Keep professional communication

3. **Order Management**
   - Process orders within 24 hours
   - Print shipping labels promptly
   - Update tracking information

4. **Inventory**
   - Sync inventory hourly
   - Set safety stock levels
   - Use bulk updates for efficiency

## API Limits

| Resource | Limit | Period |
|----------|-------|---------|
| API Calls | 10,000 | Per hour |
| Product Creation | 1,000 | Per day |
| Message Sending | 500 | Per hour |
| Bulk Operations | 100 items | Per request |

## Support

- [MercadoLibre Developer Portal](https://developers.mercadolibre.com/)
- [API Documentation](https://developers.mercadolibre.com.ar/es_ar/api-docs-es)
- [Developer Forum](https://developers.mercadolibre.com.ar/foro/)

## License

This integration is part of the Quenty platform and follows the same licensing terms.

## Changelog

### Version 1.0.0
- Initial release
- Full OAuth2 integration
- Product management
- Order processing
- Question handling
- Webhook support
- Multi-country support