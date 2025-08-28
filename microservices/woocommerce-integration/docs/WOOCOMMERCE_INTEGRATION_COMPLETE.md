# WooCommerce Integration Service - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [API Reference](#api-reference)
5. [Webhook Integration](#webhook-integration)
6. [Store Management](#store-management)
7. [Order Processing](#order-processing)
8. [Product & Inventory](#product--inventory)
9. [Shipping Integration](#shipping-integration)
10. [Synchronization](#synchronization)
11. [Security](#security)
12. [Testing](#testing)
13. [Deployment](#deployment)
14. [Monitoring & Observability](#monitoring--observability)
15. [Troubleshooting](#troubleshooting)
16. [Best Practices](#best-practices)

---

## Overview

The WooCommerce Integration Service is a comprehensive microservice that enables seamless integration between WooCommerce e-commerce stores and the Quenty logistics platform. This service provides real-time synchronization of orders, products, and customers while managing shipping operations through integrated carrier services.

### Key Features

- **Multi-Store Support**: Manage multiple WooCommerce stores from a single interface
- **Real-time Webhooks**: Instant updates for order and product changes
- **Automated Shipping**: Create shipping labels automatically when orders are placed
- **Inventory Sync**: Keep product stock levels synchronized
- **Order Management**: Complete order lifecycle management from creation to delivery
- **Customer Data Sync**: Maintain customer records across platforms
- **Secure API**: OAuth and encrypted credential storage
- **Scalable Architecture**: Microservice design with horizontal scaling support

### Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **HTTP Client**: httpx with async support
- **Authentication**: WooCommerce REST API v3 with OAuth 1.0a/Basic Auth
- **Container**: Docker
- **Orchestration**: Kubernetes-ready

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     WooCommerce Stores                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Store 1  │  │ Store 2  │  │ Store 3  │  │ Store N  │       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘       │
│        │             │             │             │               │
│        └─────────────┼─────────────┼─────────────┘               │
│                      │             │                             │
│               Webhooks│      REST API│                           │
└──────────────────────┼─────────────┼─────────────────────────────┘
                       ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│              WooCommerce Integration Service                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Gateway                            │   │
│  │  /api/v1/stores  /webhooks  /api/v1/orders  /api/v1/sync │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────┼─────────────────────────────────────┐   │
│  │                Service Layer                              │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │   │
│  │  │Order Service │ │Product Service│ │Webhook Handler│    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │   │
│  │  │Sync Service  │ │Notification  │ │Shipping Service│    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                          │
│  ┌────────────────────┼─────────────────────────────────────┐   │
│  │              Data Access Layer                            │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │   │
│  │  │  PostgreSQL  │ │    Redis     │ │  WC Clients  │     │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │   │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────┬───────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│               External Services                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Carrier Service  │  │ Email Service    │                     │
│  │ (DHL/FedEx/UPS) │  │ (SMTP/SendGrid)  │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Description

1. **API Gateway**: FastAPI-based REST API handling all incoming requests
2. **Service Layer**: Business logic separated by domain
3. **Data Access Layer**: Database operations and external API clients
4. **External Services**: Integration with carrier and notification services

### Data Flow

1. **Order Creation Flow**:
   ```
   WooCommerce → Webhook → Order Service → Database → Shipping Service → Carrier API
   ```

2. **Product Sync Flow**:
   ```
   Sync Service → WooCommerce API → Product Service → Database → Cache Update
   ```

3. **Tracking Update Flow**:
   ```
   Carrier Service → Shipping Service → Order Service → WooCommerce API
   ```

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)
- WooCommerce store with REST API enabled

### Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/quenty.git
cd quenty/microservices/woocommerce-integration
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/woocommerce_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600

# Security
SECRET_KEY=your-secret-key-generate-with-openssl
ENCRYPTION_KEY=your-32-byte-encryption-key

# Carrier Service
CARRIER_SERVICE_URL=http://localhost:8009
CARRIER_SERVICE_API_KEY=your-carrier-api-key

# Email Service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@quenty.com

# Service Configuration
SERVICE_NAME=woocommerce-integration
SERVICE_PORT=8010
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,https://app.quenty.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
```

#### 5. Initialize Database

```bash
# Create database
createdb woocommerce_db

# Run migrations
alembic upgrade head
```

#### 6. Start the Service

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --port 8010

# Production mode
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8010
```

### Docker Setup

```bash
# Build image
docker build -t woocommerce-integration:latest .

# Run with docker-compose
docker-compose up -d
```

### WooCommerce Store Setup

#### 1. Enable REST API

In WordPress Admin:
1. Go to WooCommerce → Settings → Advanced → REST API
2. Click "Add key"
3. Set Description: "Quenty Integration"
4. Set User: Your admin user
5. Set Permissions: Read/Write
6. Click "Generate API key"
7. Save the Consumer key and Consumer secret

#### 2. Configure Webhooks

In WordPress Admin:
1. Go to WooCommerce → Settings → Advanced → Webhooks
2. Click "Add webhook" for each event:

**Order Created Webhook**:
- Name: Order Created
- Status: Active
- Topic: Order created
- Delivery URL: `https://your-domain.com/webhooks/woocommerce/{store_id}`
- Secret: Generate a strong secret
- API Version: WP REST API Integration v3

**Order Updated Webhook**:
- Name: Order Updated
- Status: Active
- Topic: Order updated
- Delivery URL: `https://your-domain.com/webhooks/woocommerce/{store_id}`
- Secret: Same as above
- API Version: WP REST API Integration v3

Repeat for other events:
- Order deleted
- Product created
- Product updated
- Product deleted
- Customer created
- Customer updated

---

## API Reference

### Base URL

```
https://api.quenty.com/woocommerce
```

### Authentication

All API endpoints require authentication via Bearer token:

```http
Authorization: Bearer YOUR_API_TOKEN
```

### Endpoints

#### Store Management

##### Register Store

```http
POST /api/v1/stores
Content-Type: application/json

{
  "id": "store-123",
  "name": "My WooCommerce Store",
  "url": "https://mystore.com",
  "consumer_key": "ck_1234567890abcdef",
  "consumer_secret": "cs_abcdef1234567890",
  "webhook_secret": "webhook_secret_key",
  "version": "wc/v3"
}
```

**Response**:
```json
{
  "id": "store-123",
  "name": "My WooCommerce Store",
  "url": "https://mystore.com",
  "status": "registered",
  "store_info": {
    "woocommerce_version": "8.4.0",
    "wordpress_version": "6.4.2",
    "timezone": "America/New_York",
    "currency": "USD",
    "currency_symbol": "$"
  }
}
```

##### List Stores

```http
GET /api/v1/stores?active_only=true
```

**Response**:
```json
{
  "stores": [
    {
      "id": "store-123",
      "name": "My WooCommerce Store",
      "url": "https://mystore.com",
      "active": true,
      "currency": "USD",
      "last_sync": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

##### Get Store Details

```http
GET /api/v1/stores/{store_id}
```

##### Update Store

```http
PUT /api/v1/stores/{store_id}
Content-Type: application/json

{
  "name": "Updated Store Name",
  "webhook_secret": "new_webhook_secret"
}
```

##### Delete Store

```http
DELETE /api/v1/stores/{store_id}
```

#### Order Management

##### Get Orders

```http
GET /api/v1/stores/{store_id}/orders?status=processing&limit=20&offset=0
```

**Query Parameters**:
- `status`: Filter by order status (pending, processing, completed, etc.)
- `limit`: Number of results per page (default: 20, max: 100)
- `offset`: Pagination offset
- `start_date`: Orders created after this date (ISO 8601)
- `end_date`: Orders created before this date (ISO 8601)
- `customer_email`: Filter by customer email

**Response**:
```json
{
  "orders": [
    {
      "id": 1,
      "wc_order_id": 12345,
      "wc_order_number": "12345",
      "status": "processing",
      "customer_email": "customer@example.com",
      "customer_name": "John Doe",
      "total": 99.99,
      "currency": "USD",
      "tracking_number": "1Z999AA10123456784",
      "created_at": "2024-01-15T10:30:00Z",
      "items": [
        {
          "id": 1,
          "name": "Product Name",
          "sku": "PROD-001",
          "quantity": 2,
          "price": 49.99
        }
      ]
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

##### Get Order Details

```http
GET /api/v1/stores/{store_id}/orders/{order_id}
```

##### Create Shipping

```http
POST /api/v1/stores/{store_id}/orders/{order_id}/ship
Content-Type: application/json

{
  "carrier": "DHL",
  "service_type": "express"
}
```

**Response**:
```json
{
  "shipping_id": 123,
  "tracking_number": "1Z999AA10123456784",
  "carrier": "DHL",
  "label_url": "https://labels.carrier.com/label-123.pdf",
  "cost": 15.99,
  "estimated_delivery": "2024-01-17T18:00:00Z"
}
```

##### Update Order Status

```http
PUT /api/v1/stores/{store_id}/orders/{order_id}/status
Content-Type: application/json

{
  "status": "completed",
  "note": "Order has been delivered"
}
```

##### Cancel Order

```http
POST /api/v1/stores/{store_id}/orders/{order_id}/cancel
Content-Type: application/json

{
  "reason": "Customer request",
  "restock": true
}
```

#### Product Management

##### Get Products

```http
GET /api/v1/stores/{store_id}/products?search=shirt&in_stock=true&limit=20
```

**Query Parameters**:
- `search`: Search products by name or description
- `sku`: Filter by SKU
- `category`: Filter by category ID
- `in_stock`: Filter in-stock products only
- `limit`: Results per page
- `offset`: Pagination offset

**Response**:
```json
{
  "products": [
    {
      "id": 1,
      "wc_product_id": 100,
      "name": "Blue T-Shirt",
      "sku": "SHIRT-BLUE-M",
      "type": "simple",
      "price": 29.99,
      "regular_price": 39.99,
      "sale_price": 29.99,
      "stock_quantity": 50,
      "in_stock": true,
      "weight": 0.2,
      "dimensions": {
        "length": 30,
        "width": 20,
        "height": 2
      }
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

##### Update Product Stock

```http
PUT /api/v1/stores/{store_id}/products/{product_id}/stock
Content-Type: application/json

{
  "quantity": 100,
  "operation": "set"  // or "increase", "decrease"
}
```

##### Sync Product

```http
POST /api/v1/stores/{store_id}/products/{product_id}/sync
```

#### Synchronization

##### Sync Orders

```http
POST /api/v1/stores/{store_id}/sync/orders
Content-Type: application/json

{
  "since": "2024-01-01T00:00:00Z",
  "status": ["processing", "completed"]
}
```

**Response**:
```json
{
  "status": "started",
  "store_id": "store-123",
  "sync_type": "orders",
  "sync_id": "sync-456"
}
```

##### Sync Products

```http
POST /api/v1/stores/{store_id}/sync/products
Content-Type: application/json

{
  "full_sync": true,
  "include_variations": true
}
```

##### Get Sync Status

```http
GET /api/v1/stores/{store_id}/sync/status?sync_id=sync-456
```

**Response**:
```json
{
  "sync_id": "sync-456",
  "status": "completed",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:00Z",
  "items_processed": 500,
  "items_created": 50,
  "items_updated": 400,
  "items_failed": 0,
  "errors": []
}
```

#### Statistics

##### Get Store Statistics

```http
GET /api/v1/stores/{store_id}/stats?period=month
```

**Response**:
```json
{
  "store_id": "store-123",
  "period": "month",
  "statistics": {
    "orders": {
      "total": 1500,
      "by_status": {
        "pending": 10,
        "processing": 50,
        "completed": 1400,
        "cancelled": 30,
        "refunded": 10
      },
      "revenue": 150000.00
    },
    "products": {
      "total": 500,
      "in_stock": 450,
      "out_of_stock": 50
    },
    "customers": {
      "total": 1200,
      "new_this_period": 150
    },
    "shipping": {
      "labels_created": 1450,
      "average_delivery_days": 2.5
    }
  }
}
```

---

## Webhook Integration

### Webhook Security

All webhooks are validated using HMAC-SHA256 signatures:

```python
import hmac
import hashlib
import base64

def validate_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    return hmac.compare_digest(signature, expected)
```

### Webhook Events

#### Order Events

**order.created**
```json
{
  "id": 12345,
  "number": "12345",
  "status": "processing",
  "total": "99.99",
  "currency": "USD",
  "billing": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  },
  "shipping": {
    "first_name": "John",
    "last_name": "Doe",
    "address_1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postcode": "10001",
    "country": "US"
  },
  "line_items": [
    {
      "id": 1,
      "name": "Product Name",
      "product_id": 100,
      "quantity": 2,
      "subtotal": "99.98",
      "total": "99.98"
    }
  ]
}
```

**order.updated**
- Triggered when order status changes
- Contains full order data with updated fields

**order.deleted**
- Triggered when order is trashed or permanently deleted
- Contains order ID and deletion type

#### Product Events

**product.created**
```json
{
  "id": 100,
  "name": "Product Name",
  "slug": "product-name",
  "sku": "PROD-001",
  "price": "29.99",
  "regular_price": "39.99",
  "sale_price": "29.99",
  "stock_quantity": 100,
  "stock_status": "instock"
}
```

**product.updated**
- Triggered on any product change
- Includes stock updates

**product.deleted**
- Product removed from catalog

#### Customer Events

**customer.created**
**customer.updated**
**customer.deleted**

### Webhook Processing Flow

```mermaid
graph TD
    A[WooCommerce Event] -->|HTTP POST| B[Webhook Endpoint]
    B --> C{Validate Signature}
    C -->|Invalid| D[Return 401]
    C -->|Valid| E[Store Event in DB]
    E --> F[Queue for Processing]
    F --> G[Process Event]
    G --> H{Event Type}
    H -->|Order| I[Order Service]
    H -->|Product| J[Product Service]
    H -->|Customer| K[Customer Service]
    I --> L[Update Database]
    J --> L
    K --> L
    L --> M[Trigger Actions]
    M --> N[Send Notifications]
    M --> O[Create Shipping]
    M --> P[Update Inventory]
```

---

## Store Management

### Multi-Store Architecture

The service supports managing multiple WooCommerce stores simultaneously:

```python
# Store registration example
stores = [
    {
        "id": "store-us",
        "name": "US Store",
        "url": "https://us.mystore.com",
        "currency": "USD"
    },
    {
        "id": "store-eu",
        "name": "EU Store",
        "url": "https://eu.mystore.com",
        "currency": "EUR"
    }
]

for store in stores:
    await register_store(store)
```

### Store Configuration

Each store maintains its own:
- API credentials
- Webhook endpoints
- Sync schedules
- Shipping rules
- Notification templates

### Store Health Monitoring

```python
# Health check implementation
async def check_store_health(store_id: str) -> dict:
    store = await get_store(store_id)
    wc_client = WooCommerceClient(store)
    
    health = {
        "store_id": store_id,
        "api_connection": False,
        "last_sync": store.last_sync,
        "webhook_active": False,
        "errors": []
    }
    
    # Check API connection
    try:
        await wc_client.get_system_status()
        health["api_connection"] = True
    except Exception as e:
        health["errors"].append(f"API Error: {str(e)}")
    
    # Check webhook status
    webhooks = await wc_client.get_webhooks()
    health["webhook_active"] = any(w["status"] == "active" for w in webhooks)
    
    return health
```

---

## Order Processing

### Order Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Processing: Payment Confirmed
    Pending --> Cancelled: Cancelled
    Processing --> Shipping: Create Label
    Shipping --> InTransit: Picked Up
    InTransit --> Delivered: Delivered
    InTransit --> Failed: Delivery Failed
    Failed --> InTransit: Retry
    Delivered --> Completed: Confirmed
    Completed --> Refunded: Refund Requested
    Cancelled --> [*]
    Refunded --> [*]
    Completed --> [*]
```

### Automated Order Processing

When an order is created or updated:

1. **Validation**: Check shipping address and product availability
2. **Shipping Quote**: Get quotes from multiple carriers
3. **Label Creation**: Generate shipping label with best carrier
4. **Notification**: Send confirmation email to customer
5. **Tracking**: Monitor shipment progress
6. **Completion**: Mark order as completed when delivered

### Order Status Mapping

| WooCommerce Status | Quenty Status | Action |
|-------------------|---------------|---------|
| pending | PENDING | Wait for payment |
| processing | PROCESSING | Create shipping |
| on-hold | ON_HOLD | Pause operations |
| completed | COMPLETED | Archive order |
| cancelled | CANCELLED | Cancel shipping |
| refunded | REFUNDED | Process return |
| failed | FAILED | Notify admin |

---

## Product & Inventory

### Inventory Synchronization

Real-time inventory sync prevents overselling:

```python
async def sync_inventory(store_id: str, product_id: int):
    # Get current stock from WooCommerce
    wc_stock = await wc_client.get_product_stock(product_id)
    
    # Get warehouse stock
    warehouse_stock = await get_warehouse_stock(product_id)
    
    # Update if different
    if wc_stock != warehouse_stock:
        await wc_client.update_product_stock(
            product_id,
            warehouse_stock
        )
        
        # Log change
        await log_inventory_change(
            product_id,
            old_stock=wc_stock,
            new_stock=warehouse_stock,
            source="warehouse_sync"
        )
```

### Product Data Structure

```json
{
  "id": 100,
  "name": "Premium T-Shirt",
  "type": "variable",
  "sku": "TSHIRT-001",
  "status": "publish",
  "catalog_visibility": "visible",
  "description": "High-quality cotton t-shirt",
  "short_description": "Premium comfort",
  "price": "29.99",
  "regular_price": "39.99",
  "sale_price": "29.99",
  "on_sale": true,
  "manage_stock": true,
  "stock_quantity": 100,
  "stock_status": "instock",
  "backorders": "no",
  "weight": "0.2",
  "dimensions": {
    "length": "30",
    "width": "20",
    "height": "2"
  },
  "shipping_class": "standard",
  "categories": [
    {"id": 10, "name": "Clothing"},
    {"id": 15, "name": "T-Shirts"}
  ],
  "tags": [
    {"id": 20, "name": "Premium"},
    {"id": 21, "name": "Cotton"}
  ],
  "images": [
    {
      "id": 1000,
      "src": "https://store.com/image.jpg",
      "name": "product-image",
      "alt": "Product Image"
    }
  ],
  "attributes": [
    {
      "id": 1,
      "name": "Size",
      "options": ["S", "M", "L", "XL"],
      "variation": true,
      "visible": true
    },
    {
      "id": 2,
      "name": "Color",
      "options": ["Red", "Blue", "Green"],
      "variation": true,
      "visible": true
    }
  ],
  "variations": [101, 102, 103]
}
```

### Stock Management Rules

1. **Low Stock Alerts**: Notify when stock falls below threshold
2. **Out of Stock Handling**: Automatically mark products as out of stock
3. **Backorder Management**: Handle backorders based on settings
4. **Reserved Stock**: Reserve stock for pending orders

---

## Shipping Integration

### Carrier Integration Flow

```mermaid
sequenceDiagram
    participant WC as WooCommerce
    participant WIS as WooCommerce Integration
    participant CS as Carrier Service
    participant Carrier as Carrier API
    
    WC->>WIS: Order Created Webhook
    WIS->>WIS: Validate Order
    WIS->>CS: Request Shipping Quote
    CS->>Carrier: Get Rates
    Carrier->>CS: Return Rates
    CS->>WIS: Best Rate
    WIS->>CS: Create Label
    CS->>Carrier: Generate Label
    Carrier->>CS: Label Data
    CS->>WIS: Tracking Number
    WIS->>WC: Update Order
    WIS->>Customer: Send Notification
```

### Shipping Rules

Configure shipping rules per store:

```json
{
  "store_id": "store-123",
  "shipping_rules": {
    "default_carrier": "DHL",
    "preferred_service": "express",
    "free_shipping_threshold": 100.00,
    "excluded_countries": ["XX", "YY"],
    "weight_unit": "kg",
    "dimension_unit": "cm",
    "packaging": {
      "default_box": {
        "length": 40,
        "width": 30,
        "height": 20,
        "weight": 0.5
      }
    },
    "handling_time": {
      "standard": 1,
      "express": 0
    }
  }
}
```

### Tracking Updates

Automatic tracking synchronization:

```python
async def update_tracking_status():
    # Get all active shipments
    shipments = await get_active_shipments()
    
    for shipment in shipments:
        # Get tracking from carrier
        tracking = await carrier_service.get_tracking(
            shipment.carrier,
            shipment.tracking_number
        )
        
        # Update local database
        shipment.status = tracking.status
        shipment.location = tracking.current_location
        shipment.events = tracking.events
        
        # Update WooCommerce if delivered
        if tracking.status == "delivered":
            await wc_client.update_order_status(
                shipment.order_id,
                status="completed",
                note=f"Delivered on {tracking.delivered_at}"
            )
            
            # Send delivery notification
            await send_delivery_notification(
                shipment.order_id,
                tracking.proof_of_delivery
            )
```

---

## Synchronization

### Sync Strategies

#### Full Sync
Complete synchronization of all data:
```python
async def full_sync(store_id: str):
    # Orders
    await sync_all_orders(store_id)
    
    # Products
    await sync_all_products(store_id)
    
    # Customers
    await sync_all_customers(store_id)
    
    # Update last sync time
    await update_store_last_sync(store_id)
```

#### Incremental Sync
Sync only changes since last sync:
```python
async def incremental_sync(store_id: str):
    last_sync = await get_last_sync(store_id)
    
    # Get modified orders
    orders = await wc_client.get_orders(
        modified_after=last_sync
    )
    
    for order in orders:
        await process_order_update(order)
```

#### Real-time Sync
Via webhooks (preferred method)

### Sync Scheduling

Configure automatic sync schedules:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Hourly incremental sync
scheduler.add_job(
    incremental_sync,
    'interval',
    hours=1,
    args=['store-123']
)

# Daily full sync at 2 AM
scheduler.add_job(
    full_sync,
    'cron',
    hour=2,
    minute=0,
    args=['store-123']
)

scheduler.start()
```

### Conflict Resolution

Handle sync conflicts:

```python
async def resolve_conflict(local_data, remote_data):
    # Strategy 1: Last Modified Wins
    if local_data.modified > remote_data.modified:
        return local_data
    else:
        return remote_data
    
    # Strategy 2: Remote Always Wins
    return remote_data
    
    # Strategy 3: Manual Resolution
    await create_conflict_record(local_data, remote_data)
    return None  # Requires manual intervention
```

---

## Security

### Authentication & Authorization

#### API Key Management

```python
from passlib.hash import bcrypt

class APIKeyManager:
    async def create_api_key(self, user_id: str, scopes: List[str]) -> str:
        # Generate random key
        api_key = secrets.token_urlsafe(32)
        
        # Hash for storage
        hashed = bcrypt.hash(api_key)
        
        # Store with metadata
        await db.api_keys.insert({
            "user_id": user_id,
            "key_hash": hashed,
            "scopes": scopes,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "expires_at": datetime.utcnow() + timedelta(days=365)
        })
        
        return api_key
    
    async def validate_api_key(self, api_key: str) -> bool:
        # Find all active keys
        keys = await db.api_keys.find({"expires_at": {"$gt": datetime.utcnow()}})
        
        for key_record in keys:
            if bcrypt.verify(api_key, key_record["key_hash"]):
                # Update last used
                await db.api_keys.update_one(
                    {"_id": key_record["_id"]},
                    {"$set": {"last_used": datetime.utcnow()}}
                )
                return True
        
        return False
```

#### Credential Encryption

```python
from cryptography.fernet import Fernet

class CredentialManager:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt_credential(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_credential(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
```

### Data Protection

#### Sensitive Data Handling

- Customer PII is encrypted at rest
- Credit card data is never stored
- Passwords use bcrypt with salt rounds of 12
- API keys are hashed before storage

#### GDPR Compliance

```python
async def handle_gdpr_request(customer_email: str, request_type: str):
    if request_type == "export":
        # Collect all customer data
        data = await collect_customer_data(customer_email)
        return export_to_json(data)
    
    elif request_type == "delete":
        # Anonymize customer data
        await anonymize_customer_data(customer_email)
        return {"status": "deleted"}
    
    elif request_type == "rectify":
        # Update customer data
        return {"status": "update_link_sent"}
```

### Security Best Practices

1. **Rate Limiting**: Prevent API abuse
2. **Input Validation**: Sanitize all inputs
3. **SQL Injection Prevention**: Use parameterized queries
4. **XSS Protection**: Escape output data
5. **CORS Configuration**: Restrict allowed origins
6. **HTTPS Only**: Enforce TLS for all connections
7. **Security Headers**: Add security headers to responses

---

## Testing

### Unit Tests

```python
# tests/test_woocommerce_client.py
import pytest
from unittest.mock import AsyncMock, patch
from src.api.woocommerce_client import WooCommerceClient

@pytest.mark.asyncio
async def test_get_orders():
    client = WooCommerceClient(
        store_url="https://test.com",
        consumer_key="test_key",
        consumer_secret="test_secret"
    )
    
    with patch.object(client, '_request') as mock_request:
        mock_request.return_value.json.return_value = [
            {"id": 1, "status": "processing"}
        ]
        
        orders = await client.get_orders(status="processing")
        
        assert len(orders) == 1
        assert orders[0]["status"] == "processing"
        mock_request.assert_called_once()

@pytest.mark.asyncio
async def test_webhook_validation():
    from src.webhooks.webhook_handler import WooCommerceWebhookHandler
    
    handler = WooCommerceWebhookHandler(None, None, None)
    
    payload = b'{"test": "data"}'
    secret = "test_secret"
    
    # Generate valid signature
    import base64
    import hmac
    import hashlib
    
    signature = base64.b64encode(
        hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    ).decode()
    
    # Test validation
    assert handler.validate_signature(payload, signature, secret) == True
    assert handler.validate_signature(payload, "invalid", secret) == False
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_store_registration():
    store_data = {
        "id": "test-store",
        "name": "Test Store",
        "url": "https://test.woocommerce.com",
        "consumer_key": "ck_test",
        "consumer_secret": "cs_test"
    }
    
    response = client.post("/api/v1/stores", json=store_data)
    assert response.status_code == 201
    assert response.json()["id"] == "test-store"

@pytest.mark.asyncio
async def test_webhook_processing():
    # Register store first
    store_id = "test-store"
    
    # Send webhook
    webhook_data = {
        "id": 12345,
        "status": "processing",
        "total": "100.00"
    }
    
    response = client.post(
        f"/webhooks/woocommerce/{store_id}",
        json=webhook_data,
        headers={
            "X-WC-Webhook-Topic": "order.created",
            "X-WC-Webhook-Signature": "test_signature"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "received"
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

async def load_test(concurrent_requests=10, total_requests=1000):
    url = "http://localhost:8010/api/v1/stores/test/orders"
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        response_times = []
        
        for i in range(total_requests):
            task = make_request(session, url, {"test": i})
            tasks.append(task)
            
            if len(tasks) >= concurrent_requests:
                results = await asyncio.gather(*tasks)
                response_times.extend(results)
                tasks = []
                
                if i % 100 == 0:
                    print(f"Completed {i} requests")
                    print(f"Avg response time: {mean(response_times):.3f}s")
                    print(f"Std dev: {stdev(response_times):.3f}s")
        
        # Final batch
        if tasks:
            results = await asyncio.gather(*tasks)
            response_times.extend(results)
        
        print(f"\nLoad test complete:")
        print(f"Total requests: {total_requests}")
        print(f"Concurrent requests: {concurrent_requests}")
        print(f"Average response time: {mean(response_times):.3f}s")
        print(f"Min response time: {min(response_times):.3f}s")
        print(f"Max response time: {max(response_times):.3f}s")
        print(f"Standard deviation: {stdev(response_times):.3f}s")

if __name__ == "__main__":
    asyncio.run(load_test())
```

### Test Coverage

Run tests with coverage:

```bash
pytest --cov=src --cov-report=html --cov-report=term

# Coverage report
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
src/__init__.py                           0      0   100%
src/api/woocommerce_client.py          450     45    90%
src/webhooks/webhook_handler.py        320     32    90%
src/services/order_service.py          280     28    90%
src/models/entities.py                 150      0   100%
src/main.py                            200     20    90%
---------------------------------------------------------
TOTAL                                  1400    125    91%
```

---

## Deployment

### Docker Deployment

#### docker-compose.yml

```yaml
version: '3.8'

services:
  woocommerce-integration:
    build: .
    container_name: woocommerce-integration
    ports:
      - "8010:8010"
    environment:
      - DATABASE_URL=postgresql+asyncpg://wc_user:password@postgres:5432/woocommerce_db
      - REDIS_URL=redis://redis:6379/0
      - CARRIER_SERVICE_URL=http://carrier-service:8009
    depends_on:
      - postgres
      - redis
    networks:
      - quenty-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
      interval: 30s
      timeout: 3s
      retries: 3
  
  postgres:
    image: postgres:15-alpine
    container_name: wc-postgres
    environment:
      - POSTGRES_USER=wc_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=woocommerce_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    networks:
      - quenty-network
  
  redis:
    image: redis:7-alpine
    container_name: wc-redis
    ports:
      - "6380:6379"
    networks:
      - quenty-network
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:

networks:
  quenty-network:
    external: true
```

### Kubernetes Deployment

#### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: woocommerce-integration
  namespace: quenty
spec:
  replicas: 3
  selector:
    matchLabels:
      app: woocommerce-integration
  template:
    metadata:
      labels:
        app: woocommerce-integration
    spec:
      containers:
      - name: woocommerce-integration
        image: quenty/woocommerce-integration:v1.0.0
        ports:
        - containerPort: 8010
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: wc-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: wc-config
              key: redis-url
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
            port: 8010
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8010
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: woocommerce-integration
  namespace: quenty
spec:
  selector:
    app: woocommerce-integration
  ports:
  - protocol: TCP
    port: 8010
    targetPort: 8010
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: woocommerce-integration-hpa
  namespace: quenty
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: woocommerce-integration
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

### CI/CD Pipeline

#### GitHub Actions (.github/workflows/deploy.yml)

```yaml
name: Deploy WooCommerce Integration

on:
  push:
    branches: [main]
    paths:
      - 'microservices/woocommerce-integration/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd microservices/woocommerce-integration
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd microservices/woocommerce-integration
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        cd microservices/woocommerce-integration
        docker build -t quenty/woocommerce-integration:${{ github.sha }} .
    
    - name: Push to Registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push quenty/woocommerce-integration:${{ github.sha }}
        docker tag quenty/woocommerce-integration:${{ github.sha }} quenty/woocommerce-integration:latest
        docker push quenty/woocommerce-integration:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          microservices/woocommerce-integration/k8s/deployment.yaml
        images: |
          quenty/woocommerce-integration:${{ github.sha }}
```

---

## Monitoring & Observability

### Metrics

#### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'wc_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'wc_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics
orders_processed = Counter(
    'wc_orders_processed_total',
    'Total orders processed',
    ['store_id', 'status']
)

webhook_events = Counter(
    'wc_webhook_events_total',
    'Total webhook events',
    ['store_id', 'event_type', 'status']
)

sync_operations = Counter(
    'wc_sync_operations_total',
    'Total sync operations',
    ['store_id', 'sync_type', 'status']
)

active_stores = Gauge(
    'wc_active_stores',
    'Number of active stores'
)

# Error metrics
api_errors = Counter(
    'wc_api_errors_total',
    'Total API errors',
    ['store_id', 'error_type']
)
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "WooCommerce Integration Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(wc_http_requests_total[5m])"
        }]
      },
      {
        "title": "Orders Processing Rate",
        "targets": [{
          "expr": "rate(wc_orders_processed_total[1h])"
        }]
      },
      {
        "title": "Webhook Events",
        "targets": [{
          "expr": "sum by (event_type) (rate(wc_webhook_events_total[5m]))"
        }]
      },
      {
        "title": "API Errors",
        "targets": [{
          "expr": "rate(wc_api_errors_total[5m])"
        }]
      },
      {
        "title": "Response Time P95",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(wc_http_request_duration_seconds_bucket[5m]))"
        }]
      }
    ]
  }
}
```

### Logging

#### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Configure structured logging
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

# Usage
logger.info(
    "order_processed",
    store_id="store-123",
    order_id=12345,
    total=99.99,
    items_count=3,
    processing_time=0.234
)
```

#### Log Aggregation

Use ELK Stack or similar:

```yaml
# filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
    - add_docker_metadata:
        host: "unix:///var/run/docker.sock"
    - decode_json_fields:
        fields: ["message"]
        target: "json"
        overwrite_keys: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "woocommerce-%{+yyyy.MM.dd}"
```

### Tracing

#### OpenTelemetry Integration

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint="http://jaeger:4317",
    insecure=True
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Usage
async def process_order(order_id: int):
    with tracer.start_as_current_span(
        "process_order",
        attributes={
            "order.id": order_id,
            "service.name": "woocommerce-integration"
        }
    ) as span:
        # Process order
        span.add_event("order_validated")
        
        # Create shipping
        with tracer.start_as_current_span("create_shipping"):
            shipping = await create_shipping_label(order_id)
            span.set_attribute("shipping.tracking_number", shipping.tracking_number)
        
        span.add_event("order_completed")
```

### Alerting

#### Alert Rules

```yaml
# prometheus-alerts.yml
groups:
- name: woocommerce-integration
  rules:
  - alert: HighErrorRate
    expr: rate(wc_api_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High error rate detected
      description: "Error rate is {{ $value }} errors per second"
  
  - alert: WebhookProcessingDelay
    expr: rate(wc_webhook_events_total{status="pending"}[5m]) > 10
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: Webhook processing delay
      description: "{{ $value }} webhooks pending processing"
  
  - alert: SyncFailure
    expr: increase(wc_sync_operations_total{status="failed"}[1h]) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: Multiple sync failures
      description: "{{ $value }} sync operations failed in the last hour"
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Problem**: Getting 401 errors from WooCommerce API

**Solutions**:
```python
# Verify credentials
async def test_credentials(store_url, key, secret):
    client = WooCommerceClient(store_url, key, secret)
    try:
        result = await client.verify_credentials()
        print(f"Credentials valid: {result}")
        
        # Get store info for debugging
        info = await client.get_store_info()
        print(f"Store info: {info}")
    except Exception as e:
        print(f"Authentication failed: {e}")
    finally:
        await client.close()

# Check API permissions
# In WooCommerce admin, ensure the API key has Read/Write permissions
```

#### 2. Webhook Signature Validation Failures

**Problem**: Webhooks being rejected

**Debug Steps**:
```python
# Log raw webhook data
@app.post("/webhooks/debug/{store_id}")
async def debug_webhook(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    
    print(f"Headers: {headers}")
    print(f"Body: {body}")
    
    # Manually validate signature
    signature = headers.get("x-wc-webhook-signature")
    secret = "your_webhook_secret"
    
    expected = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    
    print(f"Expected: {expected}")
    print(f"Received: {signature}")
    print(f"Valid: {expected == signature}")
```

#### 3. Sync Performance Issues

**Problem**: Slow synchronization

**Solutions**:
```python
# Use batch operations
async def batch_sync_orders(store_id: str, batch_size: int = 100):
    page = 1
    while True:
        orders = await wc_client.get_orders(
            per_page=batch_size,
            page=page
        )
        
        if not orders:
            break
        
        # Process in parallel
        tasks = [process_order(order) for order in orders]
        await asyncio.gather(*tasks)
        
        page += 1
        
        # Add delay to avoid rate limiting
        await asyncio.sleep(1)

# Use caching for frequently accessed data
from aiocache import Cache

cache = Cache(Cache.REDIS)

@cache.cached(ttl=300)
async def get_product_cached(product_id: int):
    return await wc_client.get_product(product_id)
```

#### 4. Memory Leaks

**Problem**: Memory usage increasing over time

**Solutions**:
```python
# Close connections properly
async def process_with_cleanup():
    client = None
    try:
        client = WooCommerceClient(...)
        # Do work
    finally:
        if client:
            await client.close()

# Use connection pooling
from asyncio import Semaphore

connection_pool = Semaphore(10)

async def limited_request():
    async with connection_pool:
        # Make request
        pass
```

#### 5. Database Connection Issues

**Problem**: Connection pool exhausted

**Solutions**:
```python
# Configure connection pool properly
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)

# Use connection context manager
async def query_with_session():
    async with AsyncSession(engine) as session:
        # Perform queries
        result = await session.execute(query)
    # Session automatically closed
```

### Debug Mode

Enable debug logging:

```python
# .env
LOG_LEVEL=DEBUG
DEBUG_MODE=true

# main.py
if os.getenv("DEBUG_MODE") == "true":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Log all HTTP requests
    import httpx
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG)
    
    # Log SQL queries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
```

### Health Checks

```python
@app.get("/debug/health-detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    health = {
        "service": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "carrier_service": "unknown",
        "stores": []
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        import redis.asyncio as redis
        r = redis.from_url(os.getenv("REDIS_URL"))
        await r.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"unhealthy: {str(e)}"
    
    # Check carrier service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{CARRIER_SERVICE_URL}/health")
            if response.status_code == 200:
                health["carrier_service"] = "healthy"
    except Exception as e:
        health["carrier_service"] = f"unhealthy: {str(e)}"
    
    # Check stores
    stores = await db.execute(select(Store).where(Store.active == True))
    for store in stores.scalars():
        store_health = await check_store_health(store.id)
        health["stores"].append(store_health)
    
    return health
```

---

## Best Practices

### 1. Store Management

- **Credential Rotation**: Rotate API keys every 90 days
- **Store Isolation**: Use separate database schemas per store
- **Rate Limiting**: Implement per-store rate limits
- **Monitoring**: Track API usage per store

### 2. Order Processing

- **Idempotency**: Ensure webhook processing is idempotent
- **Retry Logic**: Implement exponential backoff for failed operations
- **Status Mapping**: Maintain clear status mappings between systems
- **Audit Trail**: Log all order state changes

### 3. Performance Optimization

- **Caching**: Cache product data and customer information
- **Batch Operations**: Use batch endpoints when available
- **Async Processing**: Process webhooks asynchronously
- **Connection Pooling**: Reuse HTTP and database connections

### 4. Security

- **Encryption**: Encrypt sensitive data at rest
- **Authentication**: Use strong authentication methods
- **Validation**: Validate all inputs and webhook signatures
- **Least Privilege**: Grant minimum required permissions

### 5. Error Handling

```python
class ErrorHandler:
    @staticmethod
    async def handle_with_retry(
        func,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ):
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries - 1:
                    delay = backoff_factor ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s",
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {max_retries} attempts failed",
                        error=str(e)
                    )
        
        raise last_exception
```

### 6. Documentation

- **API Documentation**: Keep OpenAPI specs updated
- **Change Log**: Maintain detailed change logs
- **Runbooks**: Create runbooks for common operations
- **Architecture Diagrams**: Keep diagrams current

---

## Conclusion

The WooCommerce Integration Service provides a robust, scalable solution for integrating WooCommerce stores with the Quenty logistics platform. By following the best practices and utilizing the monitoring tools provided, you can ensure reliable operation and quick issue resolution.

For additional support or questions, please contact:
- **Technical Support**: support@quenty.com
- **API Issues**: api-team@quenty.com
- **Security Concerns**: security@quenty.com

---

## Appendix

### A. WooCommerce REST API Reference

- [Official Documentation](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [Authentication Guide](https://woocommerce.github.io/woocommerce-rest-api-docs/#authentication)
- [Webhooks Documentation](https://woocommerce.github.io/woocommerce-rest-api-docs/#webhooks)

### B. Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 409 | Conflict |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### C. Glossary

- **SKU**: Stock Keeping Unit
- **PII**: Personally Identifiable Information
- **HMAC**: Hash-based Message Authentication Code
- **OAuth**: Open Authorization
- **REST**: Representational State Transfer
- **API**: Application Programming Interface
- **CI/CD**: Continuous Integration/Continuous Deployment

---

*Documentation Version: 1.0.0*
*Last Updated: 2024-08-27*
*Maintained by: Quenty Engineering Team*