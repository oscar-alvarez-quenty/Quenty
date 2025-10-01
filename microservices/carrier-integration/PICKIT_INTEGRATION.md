# Pickit Integration Documentation

## Overview

Pickit is a last-mile delivery and pickup point network service that provides flexible delivery options for e-commerce businesses. This integration enables Quenty to leverage Pickit's extensive network of pickup points, lockers, and delivery services.

## Features

### Core Capabilities
- **Pickup Point Network**: Access to thousands of pickup locations including lockers, stores, and kiosks
- **Last-Mile Delivery**: Efficient urban and suburban delivery services
- **Real-Time Tracking**: Live shipment tracking with detailed event updates
- **Proof of Delivery**: Digital signatures, photos, and pickup codes
- **Flexible Delivery Options**: Customer choice between home delivery and pickup points

### Integration Features
- OAuth 2.0 authentication with automatic token refresh
- Webhook support for real-time status updates
- Signature validation for secure webhook processing
- Circuit breaker pattern for fault tolerance
- Comprehensive error handling and logging

## API Endpoints

### 1. Pickup Points

#### Find Nearby Pickup Points
```http
GET /api/v1/pickit/pickup-points
```

**Query Parameters:**
- `latitude` (required): Latitude coordinate
- `longitude` (required): Longitude coordinate  
- `radius_km` (optional, default: 5): Search radius in kilometers
- `limit` (optional, default: 20): Maximum results to return

**Response:**
```json
{
  "status": "success",
  "count": 3,
  "pickup_points": [
    {
      "id": "PP-12345",
      "name": "Downtown Locker Station",
      "code": "DLS-001",
      "type": "LOCKER",
      "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US"
      },
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "distance_km": 0.5,
      "opening_hours": {
        "monday": "06:00-22:00",
        "tuesday": "06:00-22:00",
        "wednesday": "06:00-22:00",
        "thursday": "06:00-22:00",
        "friday": "06:00-24:00",
        "saturday": "08:00-22:00",
        "sunday": "08:00-20:00"
      },
      "services": ["PACKAGE_PICKUP", "PACKAGE_DROP", "RETURNS"],
      "capacity": {
        "small": 15,
        "medium": 8,
        "large": 4
      }
    }
  ]
}
```

#### Get Pickup Point Details
```http
GET /api/v1/pickit/pickup-points/{point_id}
```

Returns detailed information about a specific pickup point including photos, accessibility information, and current availability.

### 2. Shipping Operations

#### Generate Quote with Pickup Option
```http
POST /api/v1/quotes
```

Include pickup point ID in metadata:
```json
{
  "carrier": "Pickit",
  "origin": {...},
  "destination": {...},
  "packages": [...],
  "service_type": "pickup_point",
  "metadata": {
    "pickup_point_id": "PP-12345"
  }
}
```

#### Create Shipment with Pickup Point Delivery
```http
POST /api/v1/labels
```

```json
{
  "carrier": "Pickit",
  "order_id": "ORDER-001",
  "origin": {...},
  "destination": {...},
  "packages": [...],
  "metadata": {
    "pickup_point_id": "PP-12345",
    "customer_reference": "CUST-REF-001"
  }
}
```

**Response includes:**
- Tracking number
- Pickup code (for customer collection)
- QR code for easy scanning
- Label PDF (base64 encoded)

### 3. Tracking and Proof

#### Track Shipment
```http
POST /api/v1/tracking
```

```json
{
  "carrier": "Pickit",
  "tracking_number": "PKT-1234567890"
}
```

**Tracking Statuses:**
- `created`: Shipment created
- `picked_up`: Package collected from sender
- `in_transit`: En route to destination
- `at_pickup_point`: Available for customer collection
- `out_for_delivery`: Out for home delivery
- `delivered`: Successfully delivered
- `failed`: Delivery failed
- `returned`: Returned to sender

#### Get Proof of Delivery
```http
POST /api/v1/pickit/shipments/{tracking_number}/proof-of-delivery
```

**Response:**
```json
{
  "tracking_number": "PKT-1234567890",
  "delivered_at": "2024-01-15T14:30:00Z",
  "signed_by": "John Doe",
  "signature_image": "base64...",
  "delivery_photo": "base64...",
  "location": "Front door",
  "pickup_code_used": "PICKUP-123456"
}
```

### 4. Service Management

#### Check Service Coverage
```http
GET /api/v1/pickit/service-coverage
```

**Query Parameters:**
- `postal_code`: Postal code to check
- `city`: City name
- `country`: Country code (default: US)

#### Cancel Shipment
```http
POST /api/v1/pickit/shipments/{tracking_number}/cancel
```

```json
{
  "reason": "Customer request"
}
```

## Webhooks

### Event Types

Pickit sends webhooks for the following events:
- `shipment.created`: New shipment created
- `shipment.picked_up`: Package collected
- `shipment.in_transit`: Package in transit
- `shipment.at_pickup_point`: Arrived at pickup point
- `shipment.delivered`: Successfully delivered
- `shipment.failed`: Delivery failed
- `pickup.scheduled`: Pickup scheduled
- `pickup.completed`: Pickup completed

### Webhook Security

All webhooks include:
- `X-Pickit-Signature`: HMAC-SHA256 signature
- `X-Pickit-Timestamp`: Request timestamp

Validate webhooks using:
```python
signature = hmac.new(
    webhook_secret.encode(),
    f"{timestamp}.{body}".encode(),
    hashlib.sha256
).hexdigest()
```

### Webhook Payload Example

```json
{
  "event_type": "shipment.at_pickup_point",
  "data": {
    "tracking_number": "PKT-1234567890",
    "timestamp": "2024-01-15T10:00:00Z",
    "pickup_point": {
      "id": "PP-12345",
      "name": "Downtown Locker Station",
      "address": "123 Main St, New York, NY 10001"
    },
    "pickup_code": "PICKUP-123456",
    "hold_until": "2024-01-22T23:59:59Z",
    "notification_sent": true
  }
}
```

## Configuration

### Environment Variables

```bash
# Required
PICKIT_CLIENT_ID=your-client-id
PICKIT_CLIENT_SECRET=your-client-secret

# Optional
PICKIT_WEBHOOK_SECRET=your-webhook-secret
PICKIT_API_URL=https://api.pickit.net/v2  # Default
PICKIT_TIMEOUT=30  # Request timeout in seconds
```

### Authentication Flow

1. Client credentials are exchanged for an access token
2. Token is cached and reused until expiry
3. Automatic refresh 60 seconds before expiration
4. All API calls include `Authorization: Bearer {token}` header

## Testing

### Test Endpoints

```bash
# Test authentication
curl -X POST http://localhost:8009/api/v1/carriers/Pickit/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "sandbox",
    "credentials": {
      "client_id": "test-client",
      "client_secret": "test-secret"
    }
  }'

# Find pickup points
curl "http://localhost:8009/api/v1/pickit/pickup-points?lat=40.7128&lng=-74.0060&radius=5"

# Get quote with Pickit
curl -X POST http://localhost:8009/api/v1/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "carrier": "Pickit",
    "origin": {
      "postal_code": "10001",
      "city": "New York",
      "country": "US"
    },
    "destination": {
      "postal_code": "10002",
      "city": "New York",
      "country": "US"
    },
    "packages": [{
      "weight_kg": 2,
      "length_cm": 30,
      "width_cm": 20,
      "height_cm": 15
    }]
  }'
```

### Mock Webhook Testing

```bash
# Simulate shipment at pickup point event
curl -X POST http://localhost:8009/webhooks/pickit/events \
  -H "Content-Type: application/json" \
  -H "X-Pickit-Signature: mock-signature" \
  -H "X-Pickit-Timestamp: 2024-01-15T10:00:00Z" \
  -d '{
    "event_type": "shipment.at_pickup_point",
    "data": {
      "tracking_number": "PKT-TEST-001",
      "timestamp": "2024-01-15T10:00:00Z",
      "pickup_point": {
        "id": "PP-12345",
        "name": "Test Pickup Point"
      },
      "pickup_code": "TEST-123456"
    }
  }'
```

## Error Handling

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `AUTH_FAILED` | Authentication failed | Check credentials |
| `PICKUP_POINTS_ERROR` | Failed to fetch pickup points | Verify location parameters |
| `QUOTE_ERROR` | Quote generation failed | Check address validity |
| `LABEL_ERROR` | Label creation failed | Verify shipment details |
| `TRACKING_ERROR` | Tracking lookup failed | Verify tracking number |
| `CANCEL_ERROR` | Cancellation failed | Check if shipment is eligible |
| `POD_ERROR` | POD retrieval failed | Verify delivery status |

### Rate Limiting

- **API Limits**: 20 requests/second, 600 requests/minute
- **Webhook Processing**: Async with retry logic
- **Circuit Breaker**: Opens after 5 failures, recovers after 60 seconds

## Best Practices

### 1. Pickup Point Selection
- Cache pickup point data for 24 hours
- Display opening hours prominently
- Show capacity availability in real-time
- Provide clear pickup instructions

### 2. Customer Communication
- Send pickup codes via SMS and email
- Include QR codes for easy scanning
- Notify about approaching hold deadlines
- Provide pickup point photos/maps

### 3. Performance Optimization
- Batch tracking requests when possible
- Use webhook events instead of polling
- Implement exponential backoff for retries
- Cache frequently accessed data

### 4. Security
- Rotate webhook secrets regularly
- Validate all webhook signatures
- Use environment variables for secrets
- Log security events for audit

## Support

For technical support or API access:
- Documentation: https://developers.pickit.net
- Support Email: api-support@pickit.net
- Status Page: https://status.pickit.net

## Changelog

### Version 1.0.0 (2024-01-15)
- Initial Pickit integration
- Support for pickup points and last-mile delivery
- Webhook integration with signature validation
- Proof of delivery functionality
- Service coverage checking