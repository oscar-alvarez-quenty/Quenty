# Shopify Integration API Documentation

## Base URL
```
http://localhost:8010/api/v1
```

## Authentication

All API endpoints require authentication using one of the following methods:

### Method 1: API Key
Include API key in headers:
```http
X-API-Key: your-api-key-here
```

### Method 2: Bearer Token
Include JWT token in headers:
```http
Authorization: Bearer your-jwt-token-here
```

## Endpoints

### Store Management

#### List Stores
```http
GET /stores
```

**Response:**
```json
{
  "stores": [
    {
      "id": 1,
      "store_domain": "myshop.myshopify.com",
      "store_name": "My Shop",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

#### Create Store
```http
POST /stores
```

**Request Body:**
```json
{
  "store_domain": "myshop.myshopify.com",
  "access_token": "shpat_xxx",
  "api_key": "xxx",
  "api_secret": "xxx"
}
```

### Products

#### List Products
```http
GET /products?store_id=1&limit=50&page=1
```

**Query Parameters:**
- `store_id` (required): Store ID
- `limit`: Results per page (default: 50, max: 250)
- `page`: Page number
- `status`: Filter by status (active, archived, draft)
- `vendor`: Filter by vendor
- `product_type`: Filter by type
- `created_at_min`: Products created after date
- `created_at_max`: Products created before date

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "shopify_product_id": "1234567890",
      "title": "Sample Product",
      "body_html": "<p>Description</p>",
      "vendor": "Vendor Name",
      "product_type": "Type",
      "handle": "sample-product",
      "status": "active",
      "tags": "tag1, tag2",
      "variants": [
        {
          "id": 1,
          "title": "Default",
          "sku": "SKU001",
          "price": 29.99,
          "inventory_quantity": 100
        }
      ],
      "images": [
        {
          "id": 1,
          "src": "https://cdn.shopify.com/...",
          "alt": "Product image"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "pages": 3
  }
}
```

#### Create Product
```http
POST /products
```

**Request Body:**
```json
{
  "store_id": 1,
  "title": "New Product",
  "body_html": "<p>Product description</p>",
  "vendor": "Vendor Name",
  "product_type": "Type",
  "tags": ["tag1", "tag2"],
  "variants": [
    {
      "price": 29.99,
      "sku": "SKU001",
      "inventory_quantity": 100,
      "option1": "Size",
      "option2": "Color"
    }
  ],
  "images": [
    {
      "src": "https://example.com/image.jpg"
    }
  ]
}
```

#### Update Product
```http
PUT /products/{product_id}
```

**Request Body:**
```json
{
  "title": "Updated Product Title",
  "body_html": "<p>Updated description</p>",
  "tags": ["new-tag"]
}
```

#### Delete Product
```http
DELETE /products/{product_id}
```

#### Bulk Import Products
```http
POST /products/import
```

**Request Body (multipart/form-data):**
- `file`: CSV file with product data
- `store_id`: Store ID

**CSV Format:**
```csv
title,body_html,vendor,product_type,tags,variant_sku,variant_price,variant_inventory
Product 1,Description,Vendor,Type,"tag1,tag2",SKU001,29.99,100
```

### Orders

#### List Orders
```http
GET /orders?store_id=1&status=any&limit=50
```

**Query Parameters:**
- `store_id` (required): Store ID
- `status`: Order status (open, closed, cancelled, any)
- `financial_status`: Financial status (pending, paid, refunded, etc.)
- `fulfillment_status`: Fulfillment status (fulfilled, partial, unfulfilled)
- `created_at_min`: Orders created after date
- `created_at_max`: Orders created before date
- `limit`: Results per page
- `page`: Page number

#### Get Order
```http
GET /orders/{order_id}
```

#### Create Order
```http
POST /orders
```

**Request Body:**
```json
{
  "store_id": 1,
  "customer": {
    "email": "customer@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "line_items": [
    {
      "variant_id": "123456",
      "quantity": 2,
      "price": 29.99
    }
  ],
  "shipping_address": {
    "first_name": "John",
    "last_name": "Doe",
    "address1": "123 Main St",
    "city": "New York",
    "province_code": "NY",
    "country_code": "US",
    "zip": "10001"
  }
}
```

#### Fulfill Order
```http
POST /orders/{order_id}/fulfill
```

**Request Body:**
```json
{
  "tracking_number": "1234567890",
  "tracking_company": "UPS",
  "notify_customer": true,
  "line_items": [
    {
      "id": 123456,
      "quantity": 2
    }
  ]
}
```

#### Cancel Order
```http
POST /orders/{order_id}/cancel
```

**Request Body:**
```json
{
  "reason": "customer",
  "email": true,
  "restock": true
}
```

#### Refund Order
```http
POST /orders/{order_id}/refund
```

**Request Body:**
```json
{
  "refund": {
    "currency": "USD",
    "notify": true,
    "note": "Refund reason",
    "refund_line_items": [
      {
        "line_item_id": 123456,
        "quantity": 1,
        "restock_type": "return"
      }
    ]
  }
}
```

### Customers

#### List Customers
```http
GET /customers?store_id=1&limit=50
```

#### Search Customers
```http
GET /customers/search?store_id=1&query=john@example.com
```

#### Create Customer
```http
POST /customers
```

**Request Body:**
```json
{
  "store_id": 1,
  "email": "customer@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "accepts_marketing": true,
  "tags": ["vip", "wholesale"],
  "addresses": [
    {
      "address1": "123 Main St",
      "city": "New York",
      "province_code": "NY",
      "country_code": "US",
      "zip": "10001",
      "default": true
    }
  ]
}
```

#### Update Customer
```http
PUT /customers/{customer_id}
```

#### Delete Customer
```http
DELETE /customers/{customer_id}
```

#### Add Customer Address
```http
POST /customers/{customer_id}/addresses
```

### Inventory

#### Get Inventory Levels
```http
GET /inventory/levels?store_id=1&location_id=123
```

#### Adjust Inventory
```http
POST /inventory/adjust
```

**Request Body:**
```json
{
  "store_id": 1,
  "location_id": 123456,
  "inventory_item_id": 789012,
  "available_adjustment": 10
}
```

#### Set Inventory Level
```http
POST /inventory/set
```

**Request Body:**
```json
{
  "store_id": 1,
  "location_id": 123456,
  "inventory_item_id": 789012,
  "available": 100
}
```

#### Transfer Inventory
```http
POST /inventory/transfer
```

**Request Body:**
```json
{
  "store_id": 1,
  "from_location_id": 123456,
  "to_location_id": 789012,
  "inventory_item_id": 345678,
  "quantity": 10
}
```

#### List Locations
```http
GET /inventory/locations?store_id=1
```

### Webhooks

#### List Webhooks
```http
GET /webhooks?store_id=1
```

#### Register Webhook
```http
POST /webhooks
```

**Request Body:**
```json
{
  "store_id": 1,
  "topic": "orders/create",
  "address": "https://yourapp.com/webhooks/orders-create"
}
```

#### Register All Webhooks
```http
POST /webhooks/register-all
```

**Request Body:**
```json
{
  "store_id": 1,
  "base_url": "https://yourapp.com",
  "topics": [
    "orders/create",
    "orders/updated",
    "products/create",
    "products/update",
    "customers/create"
  ]
}
```

#### Delete Webhook
```http
DELETE /webhooks/{webhook_id}
```

#### Process Webhook (Incoming)
```http
POST /webhooks/process
```

**Headers:**
- `X-Shopify-Topic`: Webhook topic
- `X-Shopify-Hmac-Sha256`: HMAC signature
- `X-Shopify-Shop-Domain`: Shop domain
- `X-Shopify-API-Version`: API version

### Synchronization

#### Sync Products
```http
POST /sync/products
```

**Request Body:**
```json
{
  "store_id": 1,
  "full_sync": true,
  "since_date": "2024-01-01T00:00:00Z"
}
```

#### Sync Orders
```http
POST /sync/orders
```

**Request Body:**
```json
{
  "store_id": 1,
  "full_sync": false,
  "since_date": "2024-01-01T00:00:00Z"
}
```

#### Sync Status
```http
GET /sync/status?store_id=1
```

**Response:**
```json
{
  "store_id": 1,
  "last_sync": {
    "products": "2024-01-01T10:00:00Z",
    "orders": "2024-01-01T10:00:00Z",
    "customers": "2024-01-01T10:00:00Z",
    "inventory": "2024-01-01T10:00:00Z"
  },
  "sync_in_progress": {
    "products": false,
    "orders": true,
    "customers": false,
    "inventory": false
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request parameters",
  "status_code": 400,
  "details": {
    "field": "error message"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "status_code": 401
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "status_code": 404
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "status_code": 429,
  "retry_after": 2
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "status_code": 500,
  "request_id": "abc123"
}
```

## Rate Limiting

The API implements rate limiting following Shopify's standards:
- 2 requests per second (bucket size: 40)
- Headers returned:
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when limit resets

## Pagination

All list endpoints support pagination:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 250)

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 500,
    "pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

## Webhooks Verification

To verify incoming webhooks:

```python
import hmac
import hashlib
import base64

def verify_webhook(data: bytes, hmac_header: str, secret: str) -> bool:
    calculated_hmac = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).digest()
    ).decode()
    return hmac.compare_digest(calculated_hmac, hmac_header)
```

## GraphQL Queries

The service also supports GraphQL queries:

```http
POST /graphql
```

**Request Body:**
```json
{
  "query": "{ products(first: 10) { edges { node { id title } } } }",
  "variables": {}
}
```