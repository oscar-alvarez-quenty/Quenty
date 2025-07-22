# Order Service Documentation

## Overview

The Order Service manages the complete order lifecycle, product catalog, and inventory operations within the Quenty platform. It provides comprehensive order management capabilities adapted from the quentyhub-api.

## Service Details

- **Port**: 8002
- **Database**: PostgreSQL (order_db)
- **Base URL**: `http://localhost:8002`
- **Health Check**: `GET /health`

## Core Features

### 1. Product Management
- Product catalog creation and management
- Product categorization and attributes
- Pricing and cost management
- Product status and lifecycle

### 2. Order Management
- Order creation and processing
- Order status tracking and updates
- Multi-item order support
- Order analytics and reporting

### 3. Inventory Management
- Real-time inventory tracking
- Stock movement recording
- Low stock alerts and notifications
- Warehouse location management

### 4. Stock Operations
- Stock adjustments and transfers
- Inventory auditing and reconciliation
- Batch and expiry date tracking
- Reserved quantity management

## Data Models

### Product Model
```python
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    sku = Column(String(255), unique=True, nullable=False)
    category = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float)
    weight = Column(Float)
    dimensions = Column(JSON)  # {"length": 10, "width": 5, "height": 3}
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(String(255), nullable=False)
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
```

### Order Model
```python
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default="pending")
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    customer_id = Column(String(255), nullable=False)
    company_id = Column(String(255), nullable=False)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order")
```

### Inventory Model
```python
class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    min_stock_level = Column(Integer, default=0)
    max_stock_level = Column(Integer)
    location = Column(String(255))
    batch_number = Column(String(255))
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_items")
```

### Stock Movement Model
```python
class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    movement_type = Column(String(50), nullable=False)  # IN, OUT, ADJUSTMENT
    quantity = Column(Integer, nullable=False)
    reference_number = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")
```

## API Endpoints

### Product Endpoints

#### Get Products
```http
GET /api/v1/products
```
**Query Parameters:**
- `limit` (int): Number of records to return (default: 20, max: 100)
- `offset` (int): Number of records to skip (default: 0)
- `category` (string): Filter by product category
- `active` (boolean): Filter by active status

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "unique_id": "PROD-20250122001",
      "code": "SKU-001",
      "name": "Electronics Package",
      "description": "High-value electronics item",
      "price": 1299.99,
      "status": "active",
      "company_id": "COMP-001"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Product by ID
```http
GET /api/v1/products/{product_id}
```
**Response:**
```json
{
  "id": 1,
  "unique_id": "PROD-10000000",
  "code": "SKU-1",
  "name": "Sample Product",
  "description": "A sample product for testing",
  "unit_measure": "PCS",
  "weight_kg": 1.5,
  "width_cm": 20.0,
  "height_cm": 15.0,
  "length_cm": 10.0,
  "is_packing": false,
  "price": 25.99,
  "company_id": "COMP-001",
  "category_id": 1,
  "status": "active",
  "reorder_point": 10,
  "created_at": "2025-06-22T02:10:47.504386",
  "updated_at": "2025-07-22T02:10:47.504393"
}
```

#### Create Product
```http
POST /api/v1/products
```
**Request Body:**
```json
{
  "name": "New Product",
  "description": "Product description",
  "sku": "SKU-NEW-001",
  "category": "Electronics",
  "price": 299.99,
  "cost": 150.00,
  "weight": 2.5,
  "dimensions": {
    "length": 30.0,
    "width": 20.0,
    "height": 15.0
  },
  "company_id": "COMP-001"
}
```

#### Update Product
```http
PUT /api/v1/products/{product_id}
```
**Request Body:** (Partial update supported)
```json
{
  "name": "Updated Product Name",
  "price": 349.99,
  "active": true
}
```

#### Delete Product
```http
DELETE /api/v1/products/{product_id}
```

### Order Endpoints

#### Get Orders
```http
GET /api/v1/orders
```
**Query Parameters:**
- `limit` (int): Number of records to return
- `offset` (int): Number of records to skip
- `status` (string): Filter by order status
- `customer_id` (string): Filter by customer

**Response:**
```json
{
  "orders": [
    {
      "order_id": "ORD-20250122001",
      "customer_id": "CUST-001",
      "status": "in_transit",
      "order_type": "express",
      "total_amount": 15252.5,
      "estimated_delivery": "2025-07-23",
      "tracking_number": "QTYORD-20250122001"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Order by ID
```http
GET /api/v1/orders/{order_id}
```
**Response:**
```json
{
  "order_id": "ORD-001",
  "customer_id": "CUST-001",
  "order_type": "express",
  "status": "in_transit",
  "payment_status": "completed",
  "delivery_method": "home_delivery",
  "pickup_address": "123 Warehouse St, Mexico City",
  "delivery_address": {
    "street_address": "456 Customer Ave",
    "city": "Mexico City",
    "state": "CDMX",
    "postal_code": "01000",
    "country": "MX"
  },
  "items": [
    {
      "item_id": "ITEM-001",
      "name": "Electronics Package",
      "quantity": 1,
      "weight_kg": 3.5,
      "dimensions": {
        "length": 40.0,
        "width": 30.0,
        "height": 10.0
      },
      "value": 15000.0,
      "fragile": true
    }
  ],
  "total_weight_kg": 3.5,
  "total_value": 15000.0,
  "shipping_cost": 102.5,
  "total_amount": 15252.5,
  "tracking_number": "QTYORD-001",
  "created_at": "2025-07-20T02:10:58.781364",
  "updated_at": "2025-07-22T02:10:58.781365"
}
```

#### Create Order
```http
POST /api/v1/orders
```
**Request Body:**
```json
{
  "customer_id": "CUST-001",
  "company_id": "COMP-001",
  "items": [
    {
      "item_id": "ITEM-001",
      "name": "Product Name",
      "quantity": 2,
      "weight_kg": 1.5,
      "dimensions": {
        "length": 20.0,
        "width": 15.0,
        "height": 10.0
      },
      "value": 200.0,
      "fragile": false
    }
  ],
  "total_amount": 465.0
}
```

#### Update Order Status
```http
PUT /api/v1/orders/{order_id}/status?status=confirmed
```
**Response:**
```json
{
  "order_id": "ORD-123",
  "status": "confirmed",
  "updated_at": "2025-07-22T02:12:35.206723",
  "message": "Order ORD-123 status updated to confirmed"
}
```

### Inventory Endpoints

#### Get Inventory
```http
GET /api/v1/inventory
```
**Query Parameters:**
- `limit` (int): Number of records to return
- `offset` (int): Number of records to skip
- `location` (string): Filter by warehouse location
- `low_stock` (boolean): Show only low stock items

**Response:**
```json
{
  "inventory": [
    {
      "product_id": 1,
      "product_name": "Electronics Package",
      "quantity_available": 150,
      "quantity_reserved": 25,
      "min_stock_level": 50,
      "max_stock_level": 500,
      "location": "Warehouse A",
      "status": "in_stock"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Low Stock Products
```http
GET /api/v1/products/low-stock
```
**Response:**
```json
{
  "low_stock_products": [
    {
      "product_id": 3,
      "product_name": "Special Item",
      "current_stock": 5,
      "min_stock_level": 20,
      "reorder_quantity": 100,
      "status": "low_stock",
      "urgent": true
    }
  ],
  "total": 1
}
```

#### Get Stock Movements
```http
GET /api/v1/inventory/movements
```
**Query Parameters:**
- `product_id` (string): Filter by specific product
- `movement_type` (string): Filter by movement type (IN, OUT, ADJUSTMENT)
- `date_from` (date): Filter from date
- `date_to` (date): Filter to date

**Response:**
```json
{
  "product_id": "movements",
  "warehouses": [
    {
      "warehouse_id": 1,
      "warehouse_name": "Main Warehouse",
      "quantity_available": 150,
      "quantity_reserved": 25,
      "quantity_allocated": 10,
      "status": "available"
    }
  ],
  "total_available": 225,
  "total_reserved": 40,
  "reorder_needed": false
}
```

#### Create Stock Movement
```http
POST /api/v1/inventory/movements
```
**Request Body:**
```json
{
  "product_id": 1,
  "movement_type": "IN",
  "quantity": 100,
  "reference_number": "PO-12345",
  "notes": "Received shipment from supplier",
  "created_by": "USER-001"
}
```

## Database Schema

### Tables
1. **products** - Product catalog and specifications
2. **orders** - Order header information
3. **order_items** - Individual items within orders
4. **inventory_items** - Current inventory levels per product
5. **stock_movements** - Historical record of stock changes

### Relationships
- **Product → InventoryItems**: One-to-Many
- **Product → StockMovements**: One-to-Many
- **Order → OrderItems**: One-to-Many
- **OrderItem → Product**: Many-to-One

### Indexes
- `products.sku` (unique)
- `products.company_id` (index)
- `orders.order_number` (unique)
- `orders.customer_id` (index)
- `stock_movements.product_id` (index)
- `stock_movements.created_at` (index)

## Business Logic

### Order Lifecycle
1. **Pending** - Order created, awaiting processing
2. **Confirmed** - Order validated and accepted
3. **Processing** - Items being prepared
4. **Shipped** - Order dispatched
5. **In Transit** - Order in delivery
6. **Delivered** - Order completed
7. **Cancelled** - Order cancelled

### Inventory Management
- **Stock Reservation**: Automatic reservation on order creation
- **Low Stock Alerts**: Notifications when below minimum levels
- **Stock Movements**: All changes tracked with audit trail
- **Batch Tracking**: Support for expiry dates and batch numbers

### Pricing Strategy
- **Base Price**: Standard product pricing
- **Cost Tracking**: Purchase cost for margin calculation
- **Dynamic Pricing**: Support for promotional pricing
- **Currency Support**: Multi-currency pricing

## Configuration

### Environment Variables
```bash
SERVICE_NAME=order-service
DATABASE_URL=postgresql+asyncpg://order:order_pass@order-db:5432/order_db
REDIS_URL=redis://redis:6379/2
CONSUL_HOST=consul
CONSUL_PORT=8500
CUSTOMER_SERVICE_URL=http://customer-service:8001
SHIPPING_SERVICE_URL=http://international-shipping-service:8004
LOG_LEVEL=INFO
```

## Integration Points

### Service Dependencies
- **Customer Service**: Customer and company validation
- **International Shipping Service**: Shipping calculations and manifests
- **Payment Service**: Payment processing (future integration)

### External Integrations
- **ERP Systems**: Product catalog synchronization
- **Warehouse Management**: Inventory updates
- **Accounting Systems**: Financial record keeping

## Monitoring & Alerts

### Key Metrics
- Order creation rate
- Order processing time
- Inventory turnover
- Low stock alerts
- Order fulfillment rate

### Health Checks
- Database connectivity
- Service dependencies
- Inventory data consistency
- Order processing queue

## Error Handling

### Business Rules Validation
- Insufficient inventory for orders
- Invalid product configurations
- Order modification restrictions
- Stock movement validations

### Error Response Examples
```json
{
  "detail": "Insufficient inventory for product SKU-001",
  "error_code": "INSUFFICIENT_INVENTORY",
  "available_quantity": 5,
  "requested_quantity": 10
}
```

## Security Considerations

### Data Access
- Company-level data isolation
- User permission validation
- Audit trail for all operations

### API Security
- Input validation and sanitization
- Rate limiting for bulk operations
- Authentication requirement for all endpoints

## Performance Optimization

### Database Optimization
- Proper indexing strategy
- Query optimization
- Connection pooling
- Read replicas for reporting

### Caching Strategy
- Product catalog caching
- Inventory level caching
- Frequently accessed order data

### Async Processing
- Non-blocking inventory updates
- Async order processing
- Background stock level calculations