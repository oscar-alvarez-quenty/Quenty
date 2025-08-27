# Carrier Integration Service

Comprehensive carrier integration microservice for Quenty logistics platform, providing unified API for multiple shipping carriers and exchange rate services.

## Features

### 🚚 Supported Carriers
- **DHL Express** - International express shipping
- **FedEx** - International and domestic shipping
- **UPS** - Worldwide shipping services
- **Servientrega** - Colombian national coverage
- **Interrapidisimo** - Colombian regional logistics
- **Pickit** - Last-mile delivery and pickup point network

### 📦 International Mailbox Services
- **Pasarex** - Virtual mailbox with Miami and Madrid locations
  - Package consolidation and pre-alerts
  - Repackaging and protection services
  - Multi-location support (USA/Europe)
- **Aeropost** - Miami PO Box service
  - IATA weight calculations
  - Photo verification services
  - Express consolidation options

### 💱 Exchange Rate Services
- **Banco de la República** - Official Colombian TRM (Tasa Representativa del Mercado)
- Automatic daily updates at 6:00 AM
- Variation monitoring and alerts
- Configurable spread for customer rates

### 🔧 Key Features
- **Unified API** - Single interface for all carriers
- **Automatic Fallback** - Smart carrier switching on failures
- **Rate Limiting** - Prevent API abuse and respect carrier limits
- **Circuit Breaker** - Fault tolerance and resilience
- **Webhook Support** - Real-time tracking updates
- **Credential Encryption** - AES-256 encryption for secure storage
- **Health Monitoring** - Real-time carrier status tracking
- **Comprehensive Logging** - Structured logging with contextual data

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Local Development

1. Clone the repository
```bash
git clone https://github.com/your-org/quenty.git
cd quenty/microservices/carrier-integration
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set environment variables
```bash
export DATABASE_URL="postgresql://carrier:carrier_pass@localhost:5441/carrier_integration_db"
export REDIS_URL="redis://localhost:6379/1"
export ENCRYPTION_KEY="your-encryption-key-here"
export LOG_LEVEL="DEBUG"
```

5. Run database migrations
```bash
alembic upgrade head
```

6. Start the service
```bash
uvicorn src.main:app --reload --port 8009
```

### Docker Deployment

```bash
# Build and run with docker-compose
docker-compose -f docker-compose.microservices.yml up carrier-integration-service
```

## Configuration

### Carrier Credentials

Each carrier requires specific credentials. Save them via the API:

#### DHL
```json
POST /api/v1/carriers/DHL/credentials
{
  "environment": "production",
  "credentials": {
    "username": "your-dhl-username",
    "password": "your-dhl-password",
    "account_number": "your-account-number",
    "message_reference": "your-reference"
  }
}
```

#### FedEx
```json
POST /api/v1/carriers/FedEx/credentials
{
  "environment": "production",
  "credentials": {
    "client_id": "your-fedex-client-id",
    "client_secret": "your-fedex-secret",
    "account_number": "your-account-number"
  }
}
```

#### UPS
```json
POST /api/v1/carriers/UPS/credentials
{
  "environment": "production",
  "credentials": {
    "client_id": "your-ups-client-id",
    "client_secret": "your-ups-secret",
    "shipper_number": "your-shipper-number",
    "merchant_id": "your-merchant-id"
  }
}
```

#### Servientrega
```json
POST /api/v1/carriers/Servientrega/credentials
{
  "environment": "production",
  "credentials": {
    "username": "your-servientrega-user",
    "password": "your-servientrega-password",
    "agreement_code": "your-agreement-code"
  }
}
```

#### Interrapidisimo
```json
POST /api/v1/carriers/Interrapidisimo/credentials
{
  "environment": "production",
  "credentials": {
    "api_key": "your-api-key",
    "client_id": "your-client-id",
    "customer_code": "your-customer-code"
  }
}
```

#### Pickit
```json
POST /api/v1/carriers/Pickit/credentials
{
  "environment": "production",
  "credentials": {
    "client_id": "your-pickit-client-id",
    "client_secret": "your-pickit-client-secret",
    "webhook_secret": "your-webhook-secret"
  }
}
```

## API Documentation

### Core Endpoints

#### Get Shipping Quote
```http
POST /api/v1/quotes
Content-Type: application/json

{
  "carrier": "DHL",  // Optional - omit for best quote
  "origin": {
    "street": "Calle 100 #15-20",
    "city": "Bogota",
    "postal_code": "110111",
    "country": "CO",
    "contact_name": "Sender Name",
    "contact_phone": "+573001234567"
  },
  "destination": {
    "street": "123 Main St",
    "city": "New York",
    "postal_code": "10001",
    "country": "US",
    "contact_name": "Receiver Name",
    "contact_phone": "+12125551234"
  },
  "packages": [{
    "weight_kg": 5.0,
    "length_cm": 30,
    "width_cm": 20,
    "height_cm": 15,
    "declared_value": 100,
    "currency": "USD"
  }],
  "service_type": "express"
}
```

#### Generate Shipping Label
```http
POST /api/v1/labels
Content-Type: application/json

{
  "carrier": "FedEx",
  "order_id": "ORDER-001",
  "origin": {...},
  "destination": {...},
  "packages": [...],
  "service_type": "express"
}
```

#### Track Shipment
```http
POST /api/v1/tracking
Content-Type: application/json

{
  "carrier": "UPS",
  "tracking_number": "1Z999AA10123456784"
}
```

#### Schedule Pickup
```http
POST /api/v1/pickups
Content-Type: application/json

{
  "carrier": "Servientrega",
  "pickup_date": "2024-01-15T10:00:00",
  "pickup_window_start": "10:00",
  "pickup_window_end": "14:00",
  "address": {...},
  "packages_count": 5,
  "total_weight_kg": 25.5
}
```

#### Get Current TRM
```http
GET /api/v1/exchange-rates/cop-usd
```

#### Convert Currency
```http
POST /api/v1/exchange-rates/convert?amount=1000&from_currency=USD&to_currency=COP
```

### Pickit-Specific Endpoints

#### Get Pickup Points
```http
GET /api/v1/pickit/pickup-points?lat=40.7128&lng=-74.0060&radius=5
```

Returns available pickup points near the specified location with details about:
- Pickup point type (LOCKER, STORE, KIOSK)
- Opening hours and capacity
- Available services

#### Get Proof of Delivery
```http
POST /api/v1/pickit/shipments/{tracking_number}/proof-of-delivery
```

Returns proof of delivery including signature, photos, and pickup codes.

#### Cancel Shipment
```http
POST /api/v1/pickit/shipments/{tracking_number}/cancel
```

Cancel a Pickit shipment before delivery.

#### Check Service Coverage
```http
GET /api/v1/pickit/service-coverage?postal_code=10001&city=New+York&country=US
```

Check if Pickit services are available in a specific area.

### Webhook Endpoints

Carriers can send real-time updates to:
- `/webhooks/dhl/tracking` - DHL tracking updates
- `/webhooks/fedex/tracking` - FedEx tracking updates
- `/webhooks/ups/quantum-view` - UPS Quantum View events
- `/webhooks/servientrega/notifications` - Servientrega notifications
- `/webhooks/interrapidisimo/events` - Interrapidisimo events
- `/webhooks/pickit/events` - Pickit tracking and pickup point events

### Health & Monitoring

#### Health Check
```http
GET /health
```

#### Prometheus Metrics
```http
GET /metrics
```

#### Carrier Health Status
```http
GET /api/v1/carriers/{carrier}/health
```

## Testing

### Run Unit Tests
```bash
pytest tests/test_carriers.py -v
```

### Run Integration Tests
```bash
pytest tests/test_integration.py -v
```

### Run Exchange Rate Tests
```bash
pytest tests/test_exchange_rate.py -v
```

### Run All Tests
```bash
pytest tests/ -v --cov=src --cov-report=html
```

## Error Handling

The service implements comprehensive error handling:

- **Authentication Errors** - Invalid credentials
- **Rate Limiting** - Too many requests
- **Invalid Address** - Address validation failures
- **Coverage Issues** - No service to destination
- **Network Errors** - Connection timeouts
- **Service Unavailable** - Carrier API down

Each error includes:
- Error type
- Carrier-specific error code
- Human-readable message
- Retry information (if applicable)

## Rate Limiting

### Client Rate Limits
- 60 requests per minute
- 1000 requests per hour

### Carrier-Specific Limits
- **DHL**: 10 req/sec, 300 req/min
- **FedEx**: 15 req/sec, 500 req/min
- **UPS**: 10 req/sec, 400 req/min
- **Servientrega**: 5 req/sec, 200 req/min
- **Interrapidisimo**: 8 req/sec, 300 req/min
- **Pickit**: 20 req/sec, 600 req/min

## Monitoring

### Prometheus Metrics
- `carrier_integration_requests_total` - Total requests
- `carrier_integration_request_duration_seconds` - Request duration
- `carrier_api_calls_total` - Carrier API calls
- `carrier_api_duration_seconds` - Carrier API duration

### Logging
Structured JSON logs with:
- Request/response data
- Performance metrics
- Error details
- Carrier-specific context

## Security

- **Credential Encryption** - AES-256 encryption at rest
- **Webhook Authentication** - Signature verification
- **Rate Limiting** - DDoS protection
- **Input Validation** - Comprehensive request validation
- **CORS Configuration** - Configurable origins
- **SQL Injection Protection** - Parameterized queries

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

Proprietary - Quenty Logistics Platform

## Support

For issues or questions:
- Email: support@quenty.com
- Slack: #carrier-integration
- Documentation: https://docs.quenty.com/carrier-integration