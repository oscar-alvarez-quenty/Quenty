# Pickit Integration - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [API Reference](#api-reference)
5. [Webhook Integration](#webhook-integration)
6. [Developer Guide](#developer-guide)
7. [Testing Guide](#testing-guide)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)
10. [Performance & Optimization](#performance--optimization)
11. [Security Best Practices](#security-best-practices)
12. [Migration Guide](#migration-guide)

---

## Overview

### What is Pickit?

Pickit is a comprehensive last-mile delivery and pickup point network service that provides flexible delivery solutions for e-commerce businesses. The service offers an extensive network of pickup locations including automated lockers, retail stores, and dedicated kiosks, enabling customers to choose their preferred delivery method.

### Key Benefits

- **Increased Delivery Success Rate**: Reduce failed deliveries by offering pickup points
- **Customer Convenience**: 24/7 availability at selected locations
- **Cost Efficiency**: Lower last-mile delivery costs through consolidation
- **Sustainability**: Reduced carbon footprint through optimized routes
- **Flexibility**: Multiple delivery options to suit customer preferences

### Integration Capabilities

The Pickit integration with Quenty provides:

- **Unified API**: Single interface for all Pickit services
- **Real-time Updates**: Webhook-based event notifications
- **Comprehensive Tracking**: End-to-end shipment visibility
- **Pickup Point Management**: Search and selection of optimal locations
- **Proof of Delivery**: Digital signatures and photographic evidence
- **Automated Authentication**: OAuth 2.0 with automatic token refresh

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Quenty Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  API Gateway     │───▶│ Carrier Service  │              │
│  └──────────────────┘    └──────────────────┘              │
│           │                        │                         │
│           ▼                        ▼                         │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Pickit Router   │    │  Pickit Client   │              │
│  └──────────────────┘    └──────────────────┘              │
│           │                        │                         │
│           ▼                        ▼                         │
│  ┌──────────────────────────────────────────┐              │
│  │         Pickit API (External)             │              │
│  └──────────────────────────────────────────┘              │
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Webhook Handler │◀───│  Event Processor │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                               │
│  ┌──────────────────────────────────────────┐              │
│  │            Database (PostgreSQL)          │              │
│  └──────────────────────────────────────────┘              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Request Flow**:
   - Client → API Gateway → Carrier Service → Pickit Client → Pickit API
   
2. **Response Flow**:
   - Pickit API → Pickit Client → Carrier Service → API Gateway → Client
   
3. **Webhook Flow**:
   - Pickit → Webhook Handler → Event Processor → Database → Notifications

### Key Classes and Modules

```python
# Core Components
PickitClient          # Main API client (src/carriers/pickit.py)
PickitRouter          # REST endpoints (src/routers/pickit.py)
CarrierService        # Service orchestration (src/services/carrier_service.py)
WebhookHandler        # Event processing (src/webhooks.py)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)
- Pickit API credentials

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/quenty.git
cd quenty/microservices/carrier-integration
```

#### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Configure Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required Pickit Configuration
PICKIT_CLIENT_ID=your-client-id
PICKIT_CLIENT_SECRET=your-client-secret
PICKIT_WEBHOOK_SECRET=your-webhook-secret

# Optional Configuration
PICKIT_API_URL=https://api.pickit.net/v2
PICKIT_TIMEOUT=30
PICKIT_MAX_RETRIES=3
PICKIT_RETRY_DELAY=1

# Database Configuration
DATABASE_URL=postgresql://carrier:password@localhost:5432/carrier_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/1

# Security
ENCRYPTION_KEY=your-32-byte-encryption-key-here
SECRET_KEY=your-secret-key-here
```

#### 4. Run Database Migrations

```bash
alembic upgrade head
```

#### 5. Start the Service

```bash
# Development mode
uvicorn src.main:app --reload --port 8009

# Production mode
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8009
```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.microservices.yml up carrier-integration-service

# Or build individually
docker build -t quenty/carrier-integration:latest .
docker run -p 8009:8009 --env-file .env quenty/carrier-integration:latest
```

### Quick Test

```bash
# Health check
curl http://localhost:8009/health

# Save credentials
curl -X POST http://localhost:8009/api/v1/carriers/Pickit/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "sandbox",
    "credentials": {
      "client_id": "test-client-id",
      "client_secret": "test-secret"
    }
  }'
```

---

## API Reference

### Authentication

All API requests require authentication. The Pickit client uses OAuth 2.0 client credentials flow.

```python
# Internal authentication flow
1. Client credentials sent to /auth/token
2. Access token received (valid for 3600 seconds)
3. Token cached and reused
4. Automatic refresh 60 seconds before expiry
```

### Base Endpoints

#### Find Pickup Points

**Endpoint**: `GET /api/v1/pickit/pickup-points`

**Description**: Search for available pickup points near a specified location.

**Query Parameters**:
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| latitude | float | Yes | Latitude coordinate | - |
| longitude | float | Yes | Longitude coordinate | - |
| radius_km | float | No | Search radius in kilometers | 5.0 |
| limit | int | No | Maximum results (max: 100) | 20 |

**Response**:
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

**Error Responses**:
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Invalid credentials
- `500 Internal Server Error`: Server error

**Example**:
```bash
curl "http://localhost:8009/api/v1/pickit/pickup-points?latitude=40.7128&longitude=-74.0060&radius_km=5"
```

---

#### Get Pickup Point Details

**Endpoint**: `GET /api/v1/pickit/pickup-points/{point_id}`

**Description**: Get detailed information about a specific pickup point.

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| point_id | string | Yes | Pickup point identifier |

**Response**:
```json
{
  "status": "success",
  "pickup_point": {
    "id": "PP-12345",
    "name": "Downtown Locker Station",
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
    },
    "accessibility": {
      "wheelchair": true,
      "parking": true,
      "public_transport": true
    },
    "images": [
      "https://cdn.pickit.net/images/pp-12345-front.jpg",
      "https://cdn.pickit.net/images/pp-12345-lockers.jpg"
    ],
    "instructions": "Enter through main entrance, lockers are on the left"
  }
}
```

---

#### Generate Shipping Quote

**Endpoint**: `POST /api/v1/quotes`

**Description**: Get a shipping quote from Pickit.

**Request Body**:
```json
{
  "carrier": "Pickit",
  "origin": {
    "street": "456 Warehouse Ave",
    "city": "Brooklyn",
    "state": "NY",
    "postal_code": "11201",
    "country": "US",
    "contact_name": "Warehouse Manager",
    "contact_phone": "+1234567890",
    "contact_email": "warehouse@company.com"
  },
  "destination": {
    "street": "789 Customer St",
    "city": "Manhattan",
    "state": "NY",
    "postal_code": "10001",
    "country": "US",
    "contact_name": "John Doe",
    "contact_phone": "+1987654321",
    "contact_email": "john.doe@email.com"
  },
  "packages": [
    {
      "weight_kg": 2.5,
      "length_cm": 30,
      "width_cm": 20,
      "height_cm": 15,
      "declared_value": 100,
      "currency": "USD",
      "description": "Electronic device"
    }
  ],
  "service_type": "standard",
  "metadata": {
    "pickup_point_id": "PP-12345"
  }
}
```

**Response**:
```json
{
  "carrier": "Pickit",
  "service_type": "standard",
  "total_price": 12.50,
  "currency": "USD",
  "transit_days": 2,
  "estimated_delivery": "2024-01-17T15:00:00Z",
  "breakdown": {
    "base_rate": 10.00,
    "fuel_surcharge": 1.50,
    "insurance": 0.50,
    "handling_fee": 0.50,
    "pickup_point_fee": 0.00
  },
  "metadata": {
    "quote_id": "QT-789456",
    "service_level": "STANDARD",
    "pickup_point_available": true
  }
}
```

---

#### Create Shipping Label

**Endpoint**: `POST /api/v1/labels`

**Description**: Generate a shipping label with Pickit.

**Request Body**:
```json
{
  "carrier": "Pickit",
  "order_id": "ORDER-001",
  "origin": {
    "company": "My Store",
    "contact_name": "Shipping Department",
    "street": "456 Warehouse Ave",
    "city": "Brooklyn",
    "state": "NY",
    "postal_code": "11201",
    "country": "US",
    "contact_phone": "+1234567890",
    "contact_email": "shipping@mystore.com"
  },
  "destination": {
    "contact_name": "Jane Smith",
    "street": "789 Customer St",
    "city": "Manhattan",
    "state": "NY",
    "postal_code": "10001",
    "country": "US",
    "contact_phone": "+1987654321",
    "contact_email": "jane.smith@email.com"
  },
  "packages": [
    {
      "weight_kg": 2.5,
      "length_cm": 30,
      "width_cm": 20,
      "height_cm": 15,
      "declared_value": 100,
      "description": "Order #001 - Electronics"
    }
  ],
  "service_type": "standard",
  "label_format": "PDF",
  "label_size": "4x6",
  "metadata": {
    "pickup_point_id": "PP-12345",
    "customer_reference": "CUST-REF-001"
  }
}
```

**Response**:
```json
{
  "carrier": "Pickit",
  "tracking_number": "PKT-1234567890",
  "label_url": "https://labels.pickit.net/PKT-1234567890.pdf",
  "label_data": "base64_encoded_pdf_content...",
  "label_format": "PDF",
  "shipment_id": "SHP-456789",
  "metadata": {
    "barcode": "123456789012345678",
    "qr_code": "data:image/png;base64,qr_code_image...",
    "pickup_code": "PICKUP-123456",
    "estimated_delivery": "2024-01-17T15:00:00Z",
    "pickup_point": {
      "id": "PP-12345",
      "name": "Downtown Locker Station",
      "address": "123 Main St, New York, NY 10001"
    }
  }
}
```

---

#### Track Shipment

**Endpoint**: `POST /api/v1/tracking`

**Description**: Track a shipment with Pickit.

**Request Body**:
```json
{
  "carrier": "Pickit",
  "tracking_number": "PKT-1234567890"
}
```

**Response**:
```json
{
  "carrier": "Pickit",
  "tracking_number": "PKT-1234567890",
  "status": "in_transit",
  "events": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "status": "created",
      "description": "Shipment created",
      "location": "Brooklyn, NY"
    },
    {
      "timestamp": "2024-01-15T14:00:00Z",
      "status": "picked_up",
      "description": "Package picked up",
      "location": "Brooklyn, NY"
    },
    {
      "timestamp": "2024-01-16T08:00:00Z",
      "status": "in_transit",
      "description": "Package in transit to destination",
      "location": "New York, NY",
      "details": {
        "vehicle": "VAN-123",
        "route": "NYC-001"
      }
    }
  ],
  "estimated_delivery": "2024-01-17T15:00:00Z",
  "current_location": "New York Distribution Center",
  "metadata": {
    "pickup_point": {
      "id": "PP-12345",
      "name": "Downtown Locker Station"
    },
    "pickup_code": "PICKUP-123456",
    "delivery_attempts": 0
  }
}
```

**Status Values**:
- `created`: Shipment created
- `picked_up`: Package collected from origin
- `in_transit`: Package in transit
- `at_pickup_point`: Available at pickup point
- `out_for_delivery`: Out for final delivery
- `delivered`: Successfully delivered
- `exception`: Delivery exception
- `returned`: Returned to sender

---

#### Get Proof of Delivery

**Endpoint**: `POST /api/v1/pickit/shipments/{tracking_number}/proof-of-delivery`

**Description**: Retrieve proof of delivery for a completed shipment.

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tracking_number | string | Yes | Shipment tracking number |

**Response**:
```json
{
  "status": "success",
  "proof_of_delivery": {
    "tracking_number": "PKT-1234567890",
    "delivered_at": "2024-01-17T14:32:00Z",
    "signed_by": "Jane Smith",
    "signature_image": "data:image/png;base64,signature_image...",
    "delivery_photo": "data:image/jpeg;base64,photo_image...",
    "location": "Front door",
    "pickup_code_used": null,
    "delivery_type": "HOME_DELIVERY",
    "coordinates": {
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "notes": "Left with receptionist"
  }
}
```

---

#### Cancel Shipment

**Endpoint**: `POST /api/v1/pickit/shipments/{tracking_number}/cancel`

**Description**: Cancel a shipment before delivery.

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tracking_number | string | Yes | Shipment tracking number |

**Request Body**:
```json
{
  "reason": "Customer request - order cancelled"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Shipment cancelled successfully",
  "cancellation": {
    "tracking_number": "PKT-1234567890",
    "cancelled_at": "2024-01-16T10:00:00Z",
    "reason": "Customer request - order cancelled",
    "refund_status": "pending",
    "refund_amount": 12.50
  }
}
```

---

#### Schedule Pickup

**Endpoint**: `POST /api/v1/pickups`

**Description**: Schedule a pickup for outbound shipments.

**Request Body**:
```json
{
  "carrier": "Pickit",
  "pickup_date": "2024-01-16T10:00:00Z",
  "pickup_window_start": "10:00",
  "pickup_window_end": "14:00",
  "address": {
    "company": "My Store",
    "street": "456 Warehouse Ave",
    "city": "Brooklyn",
    "state": "NY",
    "postal_code": "11201",
    "country": "US"
  },
  "contact_name": "Warehouse Manager",
  "contact_phone": "+1234567890",
  "contact_email": "warehouse@mystore.com",
  "packages_count": 5,
  "total_weight_kg": 25.5,
  "special_instructions": "Ring doorbell, packages ready at loading dock",
  "shipment_ids": ["PKT-1234567890", "PKT-1234567891"]
}
```

**Response**:
```json
{
  "carrier": "Pickit",
  "pickup_id": "PCK-789456",
  "confirmation_number": "CONF-123456",
  "scheduled_date": "2024-01-16T10:00:00Z",
  "pickup_window_start": "10:00",
  "pickup_window_end": "14:00",
  "status": "scheduled",
  "metadata": {
    "driver_name": "John Driver",
    "driver_phone": "+1555123456",
    "estimated_arrival": "2024-01-16T11:30:00Z",
    "tracking_url": "https://track.pickit.net/pickup/PCK-789456"
  }
}
```

---

#### Check Service Coverage

**Endpoint**: `GET /api/v1/pickit/service-coverage`

**Description**: Check if Pickit services are available in a specific area.

**Query Parameters**:
| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| postal_code | string | Yes | Postal code to check | - |
| city | string | Yes | City name | - |
| country | string | No | Country code (ISO 2) | US |

**Response**:
```json
{
  "status": "success",
  "coverage": {
    "postal_code": "10001",
    "city": "New York",
    "country": "US",
    "service_available": true,
    "service_types": ["STANDARD", "EXPRESS", "PICKUP_POINT"],
    "estimated_transit_days": {
      "STANDARD": 2,
      "EXPRESS": 1,
      "PICKUP_POINT": 2
    },
    "nearby_pickup_points": 15,
    "coverage_quality": "EXCELLENT",
    "restrictions": [],
    "surcharges": {
      "residential": false,
      "extended_area": false
    }
  }
}
```

---

## Webhook Integration

### Overview

Pickit sends real-time notifications about shipment events through webhooks. All webhooks are sent to the configured endpoint with HMAC-SHA256 signature for security.

### Webhook Endpoint

**URL**: `POST /webhooks/pickit/events`

### Security

All webhook requests include:
- `X-Pickit-Signature`: HMAC-SHA256 signature of the payload
- `X-Pickit-Timestamp`: ISO 8601 timestamp of the request
- `X-Pickit-Event`: Event type identifier

### Signature Validation

```python
import hmac
import hashlib

def validate_webhook(payload: str, signature: str, timestamp: str, secret: str) -> bool:
    message = f"{timestamp}.{payload}"
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### Event Types

#### Shipment Events

**shipment.created**
```json
{
  "event_type": "shipment.created",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "tracking_number": "PKT-1234567890",
    "shipment_id": "SHP-456789",
    "origin": {
      "city": "Brooklyn",
      "state": "NY",
      "country": "US"
    },
    "destination": {
      "city": "Manhattan",
      "state": "NY",
      "country": "US"
    },
    "service_type": "STANDARD",
    "estimated_delivery": "2024-01-17T15:00:00Z"
  }
}
```

**shipment.picked_up**
```json
{
  "event_type": "shipment.picked_up",
  "timestamp": "2024-01-15T14:00:00Z",
  "data": {
    "tracking_number": "PKT-1234567890",
    "pickup_time": "2024-01-15T14:00:00Z",
    "driver": {
      "name": "John Driver",
      "id": "DRV-123"
    },
    "vehicle": "VAN-456",
    "location": "Brooklyn, NY"
  }
}
```

**shipment.in_transit**
```json
{
  "event_type": "shipment.in_transit",
  "timestamp": "2024-01-16T08:00:00Z",
  "data": {
    "tracking_number": "PKT-1234567890",
    "current_location": "New York Distribution Center",
    "next_location": "Manhattan Hub",
    "estimated_arrival": "2024-01-16T14:00:00Z",
    "route": "NYC-001",
    "progress_percentage": 65
  }
}
```

**shipment.at_pickup_point**
```json
{
  "event_type": "shipment.at_pickup_point",
  "timestamp": "2024-01-17T10:00:00Z",
  "data": {
    "tracking_number": "PKT-1234567890",
    "pickup_point": {
      "id": "PP-12345",
      "name": "Downtown Locker Station",
      "address": "123 Main St, New York, NY 10001",
      "type": "LOCKER"
    },
    "pickup_code": "PICKUP-123456",
    "locker_number": "A-15",
    "hold_until": "2024-01-24T23:59:59Z",
    "customer_notified": true,
    "notification_channels": ["SMS", "EMAIL"]
  }
}
```

**shipment.delivered**
```json
{
  "event_type": "shipment.delivered",
  "timestamp": "2024-01-17T14:32:00Z",
  "data": {
    "tracking_number": "PKT-1234567890",
    "delivered_at": "2024-01-17T14:32:00Z",
    "delivery_type": "PICKUP_POINT",
    "pickup_point": {
      "id": "PP-12345",
      "name": "Downtown Locker Station"
    },
    "pickup_code_used": "PICKUP-123456",
    "collected_by": "Jane Smith",
    "proof_of_delivery": {
      "signature": true,
      "photo": true,
      "id_verified": true
    }
  }
}
```

**shipment.failed**
```json
{
  "event_type": "shipment.failed",
  "timestamp": "2024-01-17T15:00:00Z",
  "data": {
    "tracking_number": "PKT-1234567890",
    "failure_reason": "CUSTOMER_NOT_AVAILABLE",
    "failure_details": "No answer at door, no safe location",
    "attempts": 2,
    "next_action": "RETURN_TO_DEPOT",
    "rescheduled_for": "2024-01-18T10:00:00Z"
  }
}
```

#### Pickup Events

**pickup.scheduled**
```json
{
  "event_type": "pickup.scheduled",
  "timestamp": "2024-01-15T09:00:00Z",
  "data": {
    "pickup_id": "PCK-789456",
    "confirmation_number": "CONF-123456",
    "scheduled_date": "2024-01-16T10:00:00Z",
    "pickup_window": {
      "start": "10:00",
      "end": "14:00"
    },
    "address": {
      "street": "456 Warehouse Ave",
      "city": "Brooklyn",
      "state": "NY"
    },
    "driver_assigned": false
  }
}
```

**pickup.completed**
```json
{
  "event_type": "pickup.completed",
  "timestamp": "2024-01-16T11:30:00Z",
  "data": {
    "pickup_id": "PCK-789456",
    "completed_at": "2024-01-16T11:30:00Z",
    "packages_collected": 5,
    "total_weight_kg": 25.5,
    "driver": {
      "name": "John Driver",
      "id": "DRV-123"
    },
    "shipment_ids": [
      "PKT-1234567890",
      "PKT-1234567891",
      "PKT-1234567892"
    ],
    "notes": "All packages collected successfully"
  }
}
```

### Webhook Response

Your endpoint should return a 2xx status code to acknowledge receipt:

```json
{
  "status": "success",
  "message": "Event processed"
}
```

### Retry Policy

If your endpoint doesn't respond with 2xx:
- Retry 1: After 1 minute
- Retry 2: After 5 minutes
- Retry 3: After 15 minutes
- Retry 4: After 1 hour
- Retry 5: After 6 hours

After 5 failed attempts, the webhook is marked as failed and notifications stop.

---

## Developer Guide

### Code Structure

```
microservices/carrier-integration/
├── src/
│   ├── carriers/
│   │   ├── __init__.py
│   │   └── pickit.py          # Pickit API client
│   ├── routers/
│   │   ├── __init__.py
│   │   └── pickit.py          # Pickit-specific endpoints
│   ├── services/
│   │   └── carrier_service.py # Service orchestration
│   ├── models.py              # Database models
│   ├── schemas.py             # Pydantic models
│   ├── webhooks.py            # Webhook handlers
│   └── main.py                # FastAPI application
├── tests/
│   ├── test_pickit.py         # Unit tests
│   └── test_integration.py    # Integration tests
├── docs/
│   └── PICKIT_COMPLETE_DOCUMENTATION.md
└── requirements.txt
```

### Key Implementation Files

#### PickitClient (src/carriers/pickit.py)

Main responsibilities:
- OAuth 2.0 authentication
- API request/response handling
- Error handling and retries
- Webhook signature validation

Key methods:
```python
class PickitClient:
    async def _ensure_authenticated() -> None
    async def get_pickup_points() -> List[Dict]
    async def get_quote() -> QuoteResponse
    async def generate_label() -> LabelResponse
    async def track_shipment() -> TrackingResponse
    async def schedule_pickup() -> PickupResponse
    async def cancel_shipment() -> Dict
    async def get_proof_of_delivery() -> Dict
    async def validate_webhook() -> bool
    async def process_webhook() -> Dict
```

#### Router Implementation (src/routers/pickit.py)

Provides REST endpoints for Pickit-specific features:
```python
@router.get("/pickup-points")
@router.get("/pickup-points/{point_id}")
@router.post("/shipments/{tracking_number}/proof-of-delivery")
@router.post("/shipments/{tracking_number}/cancel")
@router.get("/service-coverage")
```

### Adding New Features

1. **Add to PickitClient**:
```python
# src/carriers/pickit.py
async def new_feature(self, params: Dict) -> Dict:
    await self._ensure_authenticated()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.base_url}/new-endpoint",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=params,
            timeout=15.0
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise CarrierException(
                carrier="Pickit",
                error_code="NEW_FEATURE_ERROR",
                message=f"Failed: {response.text}"
            )
```

2. **Add Router Endpoint**:
```python
# src/routers/pickit.py
@router.post("/new-feature")
async def new_feature_endpoint(
    request: NewFeatureRequest,
    client: PickitClient = Depends(get_pickit_client)
):
    try:
        result = await client.new_feature(request.dict())
        return {"status": "success", "data": result}
    except CarrierException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

3. **Add Schema**:
```python
# src/schemas.py
class NewFeatureRequest(BaseModel):
    field1: str
    field2: Optional[int] = None
    
class NewFeatureResponse(BaseModel):
    result: str
    metadata: Dict[str, Any]
```

### Error Handling

Custom exception hierarchy:
```python
CarrierException
├── AuthenticationError
├── RateLimitError
├── ValidationError
├── NetworkError
└── PickitSpecificError
```

Example error handling:
```python
try:
    result = await pickit_client.get_quote(request)
except AuthenticationError:
    # Refresh token and retry
    await pickit_client._authenticate()
    result = await pickit_client.get_quote(request)
except RateLimitError as e:
    # Wait and retry with exponential backoff
    await asyncio.sleep(e.retry_after)
    result = await pickit_client.get_quote(request)
except CarrierException as e:
    # Log and return error response
    logger.error(f"Pickit error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

### Logging

Structured logging with context:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "pickit_api_call",
    endpoint="/pickup-points",
    params={"lat": 40.7128, "lng": -74.0060},
    response_time=0.234,
    status_code=200
)
```

### Performance Considerations

1. **Connection Pooling**:
```python
# Reuse HTTP client
self.http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=10)
)
```

2. **Caching**:
```python
from functools import lru_cache
from aiocache import Cache

cache = Cache(Cache.REDIS)

@cache.cached(ttl=3600)
async def get_pickup_points_cached(lat, lng):
    return await pickit_client.get_pickup_points(lat, lng)
```

3. **Batch Operations**:
```python
async def batch_tracking(tracking_numbers: List[str]):
    tasks = [track_shipment(tn) for tn in tracking_numbers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

## Testing Guide

### Unit Tests

```python
# tests/test_pickit.py
import pytest
from unittest.mock import AsyncMock, patch
from src.carriers.pickit import PickitClient

@pytest.mark.asyncio
async def test_get_pickup_points():
    client = PickitClient()
    
    with patch.object(client, '_ensure_authenticated', new=AsyncMock()):
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "data": [{
                    "id": "PP-123",
                    "name": "Test Point",
                    "type": "LOCKER"
                }]
            }
            
            points = await client.get_pickup_points(40.7, -74.0)
            assert len(points) == 1
            assert points[0]["id"] == "PP-123"

@pytest.mark.asyncio
async def test_authentication():
    client = PickitClient()
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test-token",
            "expires_in": 3600
        }
        
        await client._authenticate()
        assert client.access_token == "test-token"
        assert client.token_expiry is not None

@pytest.mark.asyncio
async def test_webhook_validation():
    client = PickitClient()
    client.credentials = {"WEBHOOK_SECRET": "test-secret"}
    
    payload = '{"event": "test"}'
    timestamp = "2024-01-15T10:00:00Z"
    
    # Generate valid signature
    import hmac
    import hashlib
    message = f"{timestamp}.{payload}"
    signature = hmac.new(
        b"test-secret",
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    is_valid = await client.validate_webhook(payload, signature, timestamp)
    assert is_valid is True
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
import httpx
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_end_to_end_shipment():
    # 1. Save credentials
    response = client.post(
        "/api/v1/carriers/Pickit/credentials",
        json={
            "environment": "sandbox",
            "credentials": {
                "client_id": "test-client",
                "client_secret": "test-secret"
            }
        }
    )
    assert response.status_code == 200
    
    # 2. Find pickup points
    response = client.get(
        "/api/v1/pickit/pickup-points",
        params={"latitude": 40.7128, "longitude": -74.0060}
    )
    assert response.status_code == 200
    pickup_points = response.json()["pickup_points"]
    assert len(pickup_points) > 0
    
    # 3. Get quote
    response = client.post(
        "/api/v1/quotes",
        json={
            "carrier": "Pickit",
            "origin": {
                "postal_code": "11201",
                "city": "Brooklyn",
                "country": "US"
            },
            "destination": {
                "postal_code": "10001",
                "city": "Manhattan",
                "country": "US"
            },
            "packages": [{
                "weight_kg": 2,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15
            }],
            "metadata": {
                "pickup_point_id": pickup_points[0]["id"]
            }
        }
    )
    assert response.status_code == 200
    quote = response.json()
    assert quote["carrier"] == "Pickit"
    assert quote["total_price"] > 0
    
    # 4. Create label
    response = client.post(
        "/api/v1/labels",
        json={
            "carrier": "Pickit",
            "order_id": "TEST-001",
            "origin": {
                "street": "123 Test St",
                "city": "Brooklyn",
                "postal_code": "11201",
                "country": "US"
            },
            "destination": {
                "street": "456 Test Ave",
                "city": "Manhattan",
                "postal_code": "10001",
                "country": "US"
            },
            "packages": [{
                "weight_kg": 2,
                "length_cm": 30,
                "width_cm": 20,
                "height_cm": 15
            }]
        }
    )
    assert response.status_code == 200
    label = response.json()
    assert "tracking_number" in label
    
    # 5. Track shipment
    tracking_number = label["tracking_number"]
    response = client.post(
        "/api/v1/tracking",
        json={
            "carrier": "Pickit",
            "tracking_number": tracking_number
        }
    )
    assert response.status_code == 200
    tracking = response.json()
    assert tracking["tracking_number"] == tracking_number
```

### Load Testing

```python
# tests/load_test.py
import asyncio
import aiohttp
import time
from statistics import mean, stdev

async def make_request(session, url, data):
    start = time.time()
    async with session.post(url, json=data) as response:
        await response.json()
        return time.time() - start

async def load_test(concurrent_requests=10, total_requests=100):
    url = "http://localhost:8009/api/v1/pickit/pickup-points"
    params = {"latitude": 40.7128, "longitude": -74.0060}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(total_requests):
            task = make_request(session, url, params)
            tasks.append(task)
            
            if len(tasks) >= concurrent_requests:
                results = await asyncio.gather(*tasks)
                print(f"Batch complete: avg={mean(results):.3f}s")
                tasks = []
        
        if tasks:
            results = await asyncio.gather(*tasks)
            print(f"Final batch: avg={mean(results):.3f}s")

if __name__ == "__main__":
    asyncio.run(load_test())
```

### Mock Server for Development

```python
# tests/mock_pickit_server.py
from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import random
import string

mock_app = FastAPI()

@mock_app.post("/v2/auth/token")
async def mock_auth():
    return {
        "access_token": "mock-token-" + ''.join(random.choices(string.ascii_letters, k=10)),
        "expires_in": 3600,
        "token_type": "Bearer"
    }

@mock_app.get("/v2/pickup-points")
async def mock_pickup_points(lat: float, lng: float, radius: float = 5):
    return {
        "data": [
            {
                "id": f"PP-{random.randint(10000, 99999)}",
                "name": f"Mock Pickup Point {i}",
                "type": random.choice(["LOCKER", "STORE", "KIOSK"]),
                "address": {
                    "street": f"{random.randint(1, 999)} Mock St",
                    "city": "Mock City",
                    "state": "MC",
                    "postal_code": "12345",
                    "country": "US"
                },
                "location": {
                    "lat": lat + random.uniform(-0.05, 0.05),
                    "lng": lng + random.uniform(-0.05, 0.05)
                },
                "distance": random.uniform(0.1, radius),
                "capacity": {
                    "small": random.randint(5, 20),
                    "medium": random.randint(3, 10),
                    "large": random.randint(1, 5)
                }
            }
            for i in range(random.randint(3, 10))
        ]
    }

@mock_app.post("/v2/shipments/quote")
async def mock_quote(request: Request):
    data = await request.json()
    return {
        "quote_id": f"QT-{random.randint(100000, 999999)}",
        "total_price": round(random.uniform(5, 25), 2),
        "currency": "USD",
        "estimated_transit_days": random.randint(1, 3),
        "base_rate": round(random.uniform(4, 20), 2),
        "fuel_surcharge": round(random.uniform(0.5, 2), 2),
        "service_level": "STANDARD"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mock_app, host="0.0.0.0", port=8010)
```

---

## Production Deployment

### Environment Configuration

```bash
# Production .env file
# API Configuration
PICKIT_CLIENT_ID=${PICKIT_CLIENT_ID}
PICKIT_CLIENT_SECRET=${PICKIT_CLIENT_SECRET}
PICKIT_WEBHOOK_SECRET=${PICKIT_WEBHOOK_SECRET}
PICKIT_API_URL=https://api.pickit.net/v2
PICKIT_TIMEOUT=30
PICKIT_MAX_RETRIES=3

# Database
DATABASE_URL=postgresql://carrier:${DB_PASSWORD}@db-cluster.aws.com:5432/carrier_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis-cluster.aws.com:6379/1
REDIS_POOL_SIZE=10

# Security
ENCRYPTION_KEY=${ENCRYPTION_KEY}
SECRET_KEY=${SECRET_KEY}
ALLOWED_ORIGINS=https://app.quenty.com,https://api.quenty.com

# Monitoring
SENTRY_DSN=${SENTRY_DSN}
DATADOG_API_KEY=${DATADOG_API_KEY}
LOG_LEVEL=INFO

# Performance
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
WORKER_CONNECTIONS=1000
KEEPALIVE=5
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8009/health')"

# Start application
CMD ["gunicorn", "src.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8009", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: carrier-integration-service
  namespace: quenty
spec:
  replicas: 3
  selector:
    matchLabels:
      app: carrier-integration
  template:
    metadata:
      labels:
        app: carrier-integration
    spec:
      containers:
      - name: carrier-integration
        image: quenty/carrier-integration:v1.0.0
        ports:
        - containerPort: 8009
        env:
        - name: PICKIT_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: pickit-secrets
              key: client-id
        - name: PICKIT_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: pickit-secrets
              key: client-secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: connection-string
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8009
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8009
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: carrier-integration-service
  namespace: quenty
spec:
  selector:
    app: carrier-integration
  ports:
  - protocol: TCP
    port: 8009
    targetPort: 8009
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: carrier-integration-hpa
  namespace: quenty
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: carrier-integration-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Monitoring Setup

#### Prometheus Metrics

```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
pickit_requests = Counter(
    'pickit_api_requests_total',
    'Total Pickit API requests',
    ['endpoint', 'status']
)

pickit_request_duration = Histogram(
    'pickit_api_request_duration_seconds',
    'Pickit API request duration',
    ['endpoint']
)

# Business metrics
pickup_points_searched = Counter(
    'pickit_pickup_points_searched_total',
    'Total pickup point searches'
)

shipments_created = Counter(
    'pickit_shipments_created_total',
    'Total shipments created',
    ['service_type']
)

# Health metrics
token_expiry = Gauge(
    'pickit_token_expiry_seconds',
    'Seconds until token expiry'
)
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Pickit Integration Metrics",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [{
          "expr": "rate(pickit_api_requests_total[5m])"
        }]
      },
      {
        "title": "Request Duration P95",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(pickit_api_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(pickit_api_requests_total{status!=\"200\"}[5m])"
        }]
      },
      {
        "title": "Shipments Created",
        "targets": [{
          "expr": "sum(rate(pickit_shipments_created_total[1h])) by (service_type)"
        }]
      }
    ]
  }
}
```

### Database Migrations

```python
# alembic/versions/001_add_pickit_tables.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create Pickit-specific tables
    op.create_table(
        'pickit_shipments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tracking_number', sa.String(50), unique=True, nullable=False),
        sa.Column('shipment_id', sa.String(50), unique=True, nullable=False),
        sa.Column('order_id', sa.String(100), nullable=False),
        sa.Column('pickup_point_id', sa.String(50), nullable=True),
        sa.Column('pickup_code', sa.String(20), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True)
    )
    
    op.create_index('ix_pickit_shipments_tracking', 'pickit_shipments', ['tracking_number'])
    op.create_index('ix_pickit_shipments_order', 'pickit_shipments', ['order_id'])
    op.create_index('ix_pickit_shipments_status', 'pickit_shipments', ['status'])
    
    op.create_table(
        'pickit_pickup_points_cache',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('point_id', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('address', sa.JSON(), nullable=False),
        sa.Column('capacity', sa.JSON(), nullable=False),
        sa.Column('services', sa.JSON(), nullable=True),
        sa.Column('cached_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False)
    )
    
    op.create_index('ix_pickup_points_location', 'pickit_pickup_points_cache', 
                    ['latitude', 'longitude'])

def downgrade():
    op.drop_table('pickit_pickup_points_cache')
    op.drop_table('pickit_shipments')
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Problem**: Getting 401 Unauthorized errors

**Solutions**:
```python
# Check credentials
print(f"Client ID: {os.getenv('PICKIT_CLIENT_ID')}")
print(f"Has secret: {bool(os.getenv('PICKIT_CLIENT_SECRET'))}")

# Force re-authentication
client = PickitClient()
client.access_token = None
client.token_expiry = None
await client._authenticate()

# Verify token
import jwt
decoded = jwt.decode(client.access_token, options={"verify_signature": False})
print(f"Token expires: {decoded.get('exp')}")
```

#### 2. Webhook Signature Validation Failures

**Problem**: Webhooks being rejected with invalid signature

**Debug Steps**:
```python
# Log raw webhook data
@router.post("/webhooks/pickit/events")
async def debug_webhook(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    
    logger.info(
        "webhook_debug",
        body=body.decode(),
        signature=headers.get("x-pickit-signature"),
        timestamp=headers.get("x-pickit-timestamp")
    )
    
    # Verify signature manually
    import hmac
    import hashlib
    
    secret = os.getenv("PICKIT_WEBHOOK_SECRET")
    timestamp = headers.get("x-pickit-timestamp")
    signature = headers.get("x-pickit-signature")
    
    message = f"{timestamp}.{body.decode()}"
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Expected: {expected}")
    print(f"Received: {signature}")
    print(f"Match: {expected == signature}")
```

#### 3. Rate Limiting

**Problem**: Getting 429 Too Many Requests

**Solutions**:
```python
# Implement exponential backoff
import asyncio
from typing import Any, Callable

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Any:
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Rate limited, waiting {delay}s")
            await asyncio.sleep(delay)
    
    raise Exception("Max retries exceeded")

# Use rate limiting decorator
from aiolimiter import AsyncLimiter

rate_limiter = AsyncLimiter(20, 1)  # 20 requests per second

async def rate_limited_request():
    async with rate_limiter:
        return await pickit_client.get_quote(request)
```

#### 4. Connection Timeouts

**Problem**: Requests timing out

**Solutions**:
```python
# Increase timeout
client = httpx.AsyncClient(timeout=60.0)

# Implement circuit breaker
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def make_request():
    return await pickit_client.generate_label(request)

# Add retry logic
for attempt in range(3):
    try:
        result = await make_request()
        break
    except httpx.TimeoutException:
        if attempt == 2:
            raise
        await asyncio.sleep(1)
```

#### 5. Invalid Pickup Points

**Problem**: Selected pickup point not available

**Solutions**:
```python
# Validate pickup point before use
async def validate_pickup_point(point_id: str) -> bool:
    try:
        details = await pickit_client.get_pickup_point_details(point_id)
        return details.get("status") == "active"
    except Exception:
        return False

# Fallback to nearest available
async def get_alternative_pickup_point(lat: float, lng: float, excluded_id: str):
    points = await pickit_client.get_pickup_points(lat, lng, radius_km=10)
    return next(
        (p for p in points if p["id"] != excluded_id and p.get("status") == "active"),
        None
    )
```

### Debug Mode

Enable debug logging:

```python
# src/logging_config.py
import logging
import structlog

def setup_debug_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### Health Check Endpoints

```python
# Additional health checks
@router.get("/api/v1/pickit/health")
async def pickit_health_check(client: PickitClient = Depends(get_pickit_client)):
    checks = {
        "authentication": False,
        "api_connectivity": False,
        "webhook_endpoint": False,
        "database": False
    }
    
    # Check authentication
    try:
        await client._ensure_authenticated()
        checks["authentication"] = client.access_token is not None
    except Exception as e:
        logger.error(f"Auth check failed: {e}")
    
    # Check API connectivity
    try:
        response = await client.get_service_status()
        checks["api_connectivity"] = response.get("status") == "operational"
    except Exception as e:
        logger.error(f"API check failed: {e}")
    
    # Check database
    try:
        db.execute("SELECT 1")
        checks["database"] = True
    except Exception as e:
        logger.error(f"DB check failed: {e}")
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "healthy": all_healthy,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## Performance & Optimization

### Caching Strategy

```python
# Redis caching for pickup points
from aiocache import Cache
from aiocache.serializers import JsonSerializer

cache = Cache(Cache.REDIS, endpoint="localhost", port=6379, namespace="pickit")
cache.serializer = JsonSerializer()

@cache.cached(ttl=3600, key_builder=lambda f, lat, lng, radius: f"pp:{lat}:{lng}:{radius}")
async def get_cached_pickup_points(lat: float, lng: float, radius: float = 5.0):
    return await pickit_client.get_pickup_points(lat, lng, radius)

# Database query optimization
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

# Optimized query with eager loading
stmt = (
    select(PickitShipment)
    .options(selectinload(PickitShipment.events))
    .where(
        and_(
            PickitShipment.created_at >= start_date,
            PickitShipment.status.in_(["in_transit", "delivered"])
        )
    )
    .limit(100)
)
results = await session.execute(stmt)
```

### Connection Pooling

```python
# HTTP connection pooling
import httpx

class PickitClientOptimized:
    def __init__(self):
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30
            ),
            timeout=httpx.Timeout(30.0, connect=5.0),
            http2=True  # Enable HTTP/2
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

# Database connection pooling
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### Batch Processing

```python
# Batch shipment creation
async def create_batch_shipments(shipments: List[Dict]) -> List[LabelResponse]:
    batch_size = 10
    results = []
    
    for i in range(0, len(shipments), batch_size):
        batch = shipments[i:i + batch_size]
        tasks = [create_shipment(s) for s in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch shipment failed: {result}")
            else:
                results.append(result)
    
    return results

# Bulk tracking updates
async def bulk_track_shipments(tracking_numbers: List[str]) -> Dict[str, TrackingResponse]:
    semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
    
    async def track_with_semaphore(tn: str):
        async with semaphore:
            try:
                return tn, await pickit_client.track_shipment({"tracking_number": tn})
            except Exception as e:
                return tn, {"error": str(e)}
    
    tasks = [track_with_semaphore(tn) for tn in tracking_numbers]
    results = await asyncio.gather(*tasks)
    
    return dict(results)
```

### Response Compression

```python
# Enable response compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Compress large responses
import gzip
import base64

def compress_label_data(label_data: bytes) -> str:
    compressed = gzip.compress(label_data)
    return base64.b64encode(compressed).decode()

def decompress_label_data(compressed_data: str) -> bytes:
    decoded = base64.b64decode(compressed_data)
    return gzip.decompress(decoded)
```

---

## Security Best Practices

### API Key Management

```python
# Secure credential storage
from cryptography.fernet import Fernet
import os

class SecureCredentialManager:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY").encode()
        self.cipher = Fernet(key)
    
    def encrypt_credential(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_credential(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()

# Rotate API keys
async def rotate_api_keys():
    # Generate new credentials
    new_credentials = await pickit_client.rotate_credentials()
    
    # Update in database
    await update_credentials(new_credentials)
    
    # Update in memory
    pickit_client.credentials = new_credentials
    
    # Notify administrators
    await send_notification("API keys rotated successfully")
```

### Input Validation

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class SecurePickupPointRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(5.0, ge=0.1, le=50)
    limit: int = Field(20, ge=1, le=100)
    
    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Coordinates must be numeric")
        return float(v)

class SecureTrackingRequest(BaseModel):
    tracking_number: str = Field(..., min_length=5, max_length=50)
    
    @validator('tracking_number')
    def validate_tracking_number(cls, v):
        if not re.match(r'^PKT-[A-Z0-9]+$', v):
            raise ValueError("Invalid tracking number format")
        return v
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/pickit/sensitive-operation")
@limiter.limit("5 per minute")
async def sensitive_operation(request: Request):
    # Limited to 5 requests per minute per IP
    pass
```

### Audit Logging

```python
from datetime import datetime
import json

class AuditLogger:
    async def log_event(
        self,
        event_type: str,
        user_id: str,
        action: str,
        details: Dict[str, Any],
        ip_address: str
    ):
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "details": details,
            "ip_address": ip_address,
            "service": "pickit-integration"
        }
        
        # Store in database
        await db.audit_logs.insert_one(audit_entry)
        
        # Send to SIEM
        await send_to_siem(audit_entry)
        
        # Critical events alert
        if event_type in ["credential_change", "unauthorized_access"]:
            await send_security_alert(audit_entry)
```

---

## Migration Guide

### Migrating from Another Carrier

```python
# Migration script
import asyncio
from typing import List, Dict

class PickitMigrator:
    def __init__(self, old_carrier: str):
        self.old_carrier = old_carrier
        self.pickit_client = PickitClient()
        self.migration_log = []
    
    async def migrate_active_shipments(self) -> Dict[str, str]:
        """Map old tracking numbers to new Pickit tracking numbers"""
        mapping = {}
        
        # Get active shipments from old carrier
        active_shipments = await get_active_shipments(self.old_carrier)
        
        for shipment in active_shipments:
            try:
                # Create equivalent shipment in Pickit
                pickit_label = await self.pickit_client.generate_label({
                    "order_id": shipment["order_id"],
                    "origin": shipment["origin"],
                    "destination": shipment["destination"],
                    "packages": shipment["packages"]
                })
                
                mapping[shipment["tracking_number"]] = pickit_label.tracking_number
                
                self.migration_log.append({
                    "status": "success",
                    "old_tracking": shipment["tracking_number"],
                    "new_tracking": pickit_label.tracking_number
                })
                
            except Exception as e:
                self.migration_log.append({
                    "status": "failed",
                    "old_tracking": shipment["tracking_number"],
                    "error": str(e)
                })
        
        return mapping
    
    async def update_customer_notifications(self, mapping: Dict[str, str]):
        """Update customers with new tracking numbers"""
        for old_tracking, new_tracking in mapping.items():
            customer = await get_customer_by_tracking(old_tracking)
            if customer:
                await send_notification(
                    customer["email"],
                    f"Your tracking number has been updated to {new_tracking}"
                )
    
    async def export_migration_report(self) -> str:
        """Generate migration report"""
        success_count = len([l for l in self.migration_log if l["status"] == "success"])
        failed_count = len([l for l in self.migration_log if l["status"] == "failed"])
        
        report = f"""
        Migration Report
        ================
        Total Shipments: {len(self.migration_log)}
        Successful: {success_count}
        Failed: {failed_count}
        
        Details:
        {json.dumps(self.migration_log, indent=2)}
        """
        
        return report

# Run migration
async def run_migration():
    migrator = PickitMigrator("OldCarrier")
    
    print("Starting migration...")
    mapping = await migrator.migrate_active_shipments()
    
    print("Updating customers...")
    await migrator.update_customer_notifications(mapping)
    
    print("Generating report...")
    report = await migrator.export_migration_report()
    
    with open("migration_report.txt", "w") as f:
        f.write(report)
    
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(run_migration())
```

### Backward Compatibility

```python
# Support old API format
@app.post("/api/v1/legacy/create-shipment")
async def legacy_create_shipment(request: Dict[str, Any]):
    # Transform legacy format to Pickit format
    pickit_request = {
        "carrier": "Pickit",
        "order_id": request.get("reference_number"),
        "origin": {
            "street": request["from_address"]["line1"],
            "city": request["from_address"]["city"],
            "postal_code": request["from_address"]["zip"]
        },
        "destination": {
            "street": request["to_address"]["line1"],
            "city": request["to_address"]["city"],
            "postal_code": request["to_address"]["zip"]
        },
        "packages": [{
            "weight_kg": request["weight_lbs"] * 0.453592,
            "length_cm": request["dimensions"]["length"] * 2.54,
            "width_cm": request["dimensions"]["width"] * 2.54,
            "height_cm": request["dimensions"]["height"] * 2.54
        }]
    }
    
    # Create shipment with Pickit
    result = await create_label(pickit_request)
    
    # Transform response to legacy format
    return {
        "tracking_code": result["tracking_number"],
        "label_pdf": result["label_data"],
        "cost": result["metadata"]["cost"]
    }
```

---

## Appendix

### Glossary

- **Pickup Point**: Physical location where customers can collect packages
- **Locker**: Automated self-service pickup location
- **POD**: Proof of Delivery
- **Last-Mile**: Final leg of delivery from distribution center to customer
- **Pickup Code**: Unique code for collecting packages from pickup points
- **Circuit Breaker**: Pattern to prevent cascading failures
- **HMAC**: Hash-based Message Authentication Code
- **OAuth 2.0**: Authorization framework for API access

### Useful Links

- [Pickit API Documentation](https://developers.pickit.net)
- [Quenty Platform Documentation](https://docs.quenty.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io)

### Contact Information

- **Technical Support**: support@quenty.com
- **API Issues**: api-team@quenty.com
- **Security Concerns**: security@quenty.com

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial Pickit integration |
| 1.0.1 | 2024-01-20 | Added batch processing support |
| 1.0.2 | 2024-01-25 | Improved error handling |
| 1.1.0 | 2024-02-01 | Added pickup point caching |

---

*This documentation is maintained by the Quenty Engineering Team. Last updated: 2024-08-27*