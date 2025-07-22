# International Shipping Service Documentation

## Overview

The International Shipping Service manages all aspects of international logistics, shipping manifests, carrier integrations, and customs documentation within the Quenty platform. It provides comprehensive shipping capabilities adapted from the quentyhub-api.

## Service Details

- **Port**: 8004
- **Database**: PostgreSQL (intl_shipping_db)
- **Base URL**: `http://localhost:8004`
- **Health Check**: `GET /health`

## Core Features

### 1. Manifest Management
- International shipping manifest creation and management
- Manifest item tracking and documentation
- Status lifecycle management
- Customs documentation generation

### 2. Shipping Rate Calculation
- Real-time rate quotes from multiple carriers
- Zone-based pricing calculations
- Weight and volume-based pricing
- Insurance and surcharge calculations

### 3. Carrier Integration
- Multi-carrier support (DHL, FedEx, UPS)
- API integration for live rates
- Service type management
- Carrier performance tracking

### 4. Country & Zone Management
- International destination management
- Shipping zone configuration
- Customs regulations per country
- Restricted items management

### 5. Shipment Tracking
- Real-time tracking integration
- Status updates and notifications
- Delivery confirmation
- Exception handling

## Data Models

### Manifest Model
```python
class Manifest(Base):
    __tablename__ = "manifests"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default=ManifestStatus.DRAFT.value)
    total_weight = Column(Float, default=0.0)
    total_volume = Column(Float, default=0.0)
    total_value = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    origin_country = Column(String(100), nullable=False)
    destination_country = Column(String(100), nullable=False)
    shipping_zone = Column(String(50))
    estimated_delivery = Column(DateTime)
    tracking_number = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    company_id = Column(String(255), nullable=False)
    created_by = Column(String(255), nullable=False)
    
    # Relationships
    manifest_items = relationship("ManifestItem", back_populates="manifest")
    shipping_rates = relationship("ShippingRate", back_populates="manifest")
```

### Manifest Item Model
```python
class ManifestItem(Base):
    __tablename__ = "manifest_items"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    volume = Column(Float)
    value = Column(Float, nullable=False)
    hs_code = Column(String(50))  # Harmonized System code
    country_of_origin = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    manifest_id = Column(Integer, ForeignKey("manifests.id"), nullable=False)
    product_id = Column(Integer)  # Reference to Product from Order service
    
    # Relationships
    manifest = relationship("Manifest", back_populates="manifest_items")
```

### Shipping Rate Model
```python
class ShippingRate(Base):
    __tablename__ = "shipping_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    carrier_name = Column(String(255), nullable=False)
    service_type = Column(String(255), nullable=False)
    base_rate = Column(Float, nullable=False)
    weight_rate = Column(Float, default=0.0)
    volume_rate = Column(Float, default=0.0)
    fuel_surcharge = Column(Float, default=0.0)
    insurance_rate = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    transit_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    manifest_id = Column(Integer, ForeignKey("manifests.id"), nullable=False)
    
    # Relationships
    manifest = relationship("Manifest", back_populates="shipping_rates")
```

### Country Model
```python
class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    iso_code = Column(String(10), unique=True, nullable=False)
    zone = Column(String(50))  # ShippingZone enum
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Shipping Carrier Model
```python
class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    api_endpoint = Column(String(500))
    api_key = Column(String(500))
    active = Column(Boolean, default=True)
    supported_services = Column(JSON)  # List of service types
    created_at = Column(DateTime, default=datetime.utcnow)
```

## API Endpoints

### Manifest Endpoints

#### Get Manifests
```http
GET /api/v1/manifests
```
**Query Parameters:**
- `limit` (int): Number of records to return (default: 20, max: 100)
- `offset` (int): Number of records to skip (default: 0)
- `status` (string): Filter by manifest status
- `company_id` (string): Filter by company

**Response:**
```json
{
  "manifests": [
    {
      "id": 1,
      "unique_id": "MAN-20250122001",
      "date": "2025-07-21T02:11:29.940444",
      "guides_created": 15,
      "total_items": 45,
      "manifest_status": "open",
      "company_id": "COMP-001"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Manifest by ID
```http
GET /api/v1/manifests/{manifest_id}
```
**Response:**
```json
{
  "id": 1,
  "unique_id": "MAN-00000001",
  "date": "2025-07-21T02:11:40.846734",
  "guides_created": 15,
  "total_items": 45,
  "manifest_type": 2,
  "company_id": "COMP-001",
  "warehouse_id": 1,
  "manifest_status": "open",
  "created_at": "2025-07-21T02:11:40.846742",
  "updated_at": "2025-07-22T02:11:40.846743"
}
```

#### Create Manifest
```http
POST /api/v1/manifests
```
**Request Body:**
```json
{
  "origin_country": "MX",
  "destination_country": "US",
  "total_weight": 15.5,
  "total_volume": 0.05,
  "total_value": 2500.00,
  "currency": "USD",
  "company_id": "COMP-001",
  "created_by": "USER-001"
}
```

#### Update Manifest
```http
PUT /api/v1/manifests/{manifest_id}
```
**Request Body:** (Partial update supported)
```json
{
  "status": "submitted",
  "total_weight": 16.0,
  "shipped_at": "2025-07-22T10:00:00Z"
}
```

#### Delete Manifest
```http
DELETE /api/v1/manifests/{manifest_id}
```

### Manifest Item Endpoints

#### Get Manifest Items
```http
GET /api/v1/manifests/{manifest_id}/items
```
**Response:**
```json
[
  {
    "id": 1,
    "manifest_id": 1,
    "description": "Electronics - Smartphones",
    "quantity": 10,
    "weight": 5.5,
    "volume": 0.02,
    "value": 5000.0,
    "hs_code": "8517.12",
    "country_of_origin": "CN",
    "product_id": 1,
    "created_at": "2025-07-22T02:12:35.206723"
  }
]
```

#### Add Manifest Item
```http
POST /api/v1/manifests/{manifest_id}/items
```
**Request Body:**
```json
{
  "description": "Electronic Device",
  "quantity": 5,
  "weight": 2.5,
  "volume": 0.01,
  "value": 1250.00,
  "hs_code": "8517.12",
  "country_of_origin": "CN",
  "product_id": 123
}
```

### Shipping Rate Endpoints

#### Get Shipping Rates
```http
GET /api/v1/shipping/rates?origin=MX&destination=US&weight=5.0&value=500
```
**Response:**
```json
[
  {
    "carrier_name": "DHL Express",
    "service_type": "Express Worldwide",
    "base_rate": 45.0,
    "weight_rate": 8.5,
    "volume_rate": 0.0,
    "fuel_surcharge": 5.5,
    "insurance_rate": 2.5,
    "total_cost": 95.5,
    "currency": "USD",
    "transit_days": 3,
    "valid_until": "2025-07-23T02:12:35.206723"
  },
  {
    "carrier_name": "FedEx International",
    "service_type": "International Priority",
    "base_rate": 42.0,
    "weight_rate": 7.8,
    "volume_rate": 0.0,
    "fuel_surcharge": 4.8,
    "insurance_rate": 2.0,
    "total_cost": 89.8,
    "currency": "USD",
    "transit_days": 4,
    "valid_until": "2025-07-23T02:12:35.206723"
  }
]
```

#### Validate Shipping
```http
POST /api/v1/shipping/validate
```
**Request Body:**
```json
{
  "origin": "MX",
  "destination": "US",
  "weight": 5.0,
  "value": 500.0
}
```
**Response:**
```json
{
  "valid": true,
  "origin_country": "MX",
  "destination_country": "US",
  "weight_kg": 5.0,
  "value_usd": 500.0,
  "shipping_zone": "Zone_2",
  "restricted_items": [],
  "required_documents": ["Commercial Invoice", "Packing List"],
  "estimated_transit_days": 3,
  "customs_value_limit": 2500.0,
  "weight_limit_kg": 70.0,
  "warnings": [
    "High value shipment - additional insurance recommended"
  ]
}
```

### Country Management Endpoints

#### Get Countries
```http
GET /api/v1/countries
```
**Response:**
```json
[
  {
    "id": 1,
    "name": "United States",
    "iso_code": "US",
    "zone": "Zone_1",
    "active": true,
    "created_at": "2025-07-22T02:12:35.206723"
  },
  {
    "id": 2,
    "name": "Mexico",
    "iso_code": "MX",
    "zone": "Zone_1",
    "active": true,
    "created_at": "2025-07-22T02:12:35.206723"
  }
]
```

#### Create Country
```http
POST /api/v1/countries
```
**Request Body:**
```json
{
  "name": "Canada",
  "iso_code": "CA",
  "zone": "Zone_1"
}
```

### Carrier Management Endpoints

#### Get Carriers
```http
GET /api/v1/carriers
```
**Response:**
```json
[
  {
    "id": 1,
    "name": "DHL Express",
    "code": "DHL",
    "api_endpoint": "https://api.dhl.com/v1",
    "active": true,
    "supported_services": [
      "Express Worldwide",
      "Express 12:00",
      "Express 9:00"
    ],
    "created_at": "2025-07-22T02:12:35.206723"
  }
]
```

#### Create Carrier
```http
POST /api/v1/carriers
```
**Request Body:**
```json
{
  "name": "New Carrier",
  "code": "NEWCAR",
  "api_endpoint": "https://api.newcarrier.com/v1",
  "api_key": "encrypted_api_key",
  "supported_services": ["Standard", "Express"]
}
```

### Tracking Endpoints

#### Track Shipment
```http
GET /api/v1/tracking/{tracking_number}
```
**Response:**
```json
{
  "tracking_number": "1234567890",
  "status": "in_transit",
  "origin": "Mexico City, MX",
  "destination": "Miami, FL, US",
  "estimated_delivery": "2025-07-24T15:00:00Z",
  "carrier": "DHL Express",
  "service_type": "Express Worldwide",
  "events": [
    {
      "timestamp": "2025-07-21T08:00:00Z",
      "location": "Mexico City, MX",
      "status": "picked_up",
      "description": "Package picked up from origin"
    },
    {
      "timestamp": "2025-07-21T20:00:00Z",
      "location": "Mexico City Airport, MX",
      "status": "in_transit",
      "description": "Departed from origin facility"
    },
    {
      "timestamp": "2025-07-22T02:00:00Z",
      "location": "Miami Airport, FL, US",
      "status": "in_transit",
      "description": "Arrived at destination facility"
    }
  ]
}
```

## Database Schema

### Tables
1. **manifests** - Shipping manifest headers
2. **manifest_items** - Individual items within manifests
3. **shipping_rates** - Rate quotes from carriers
4. **countries** - Supported destination countries
5. **shipping_carriers** - Integrated shipping carriers

### Relationships
- **Manifest → ManifestItems**: One-to-Many
- **Manifest → ShippingRates**: One-to-Many
- **ManifestItem → Product**: Many-to-One (cross-service reference)

### Indexes
- `manifests.unique_id` (unique)
- `manifests.tracking_number` (unique)
- `manifests.company_id` (index)
- `manifest_items.manifest_id` (index)
- `countries.iso_code` (unique)
- `shipping_carriers.code` (unique)

## Business Logic

### Manifest Lifecycle
1. **Draft** - Manifest created, items can be added/modified
2. **Submitted** - Manifest submitted for processing
3. **Approved** - Manifest approved by customs/carrier
4. **Rejected** - Manifest rejected, requires modification
5. **Shipped** - Manifest dispatched by carrier
6. **Delivered** - All items delivered successfully

### Shipping Zones
- **Zone 1**: North America (US, CA, MX)
- **Zone 2**: Central & South America
- **Zone 3**: Europe & UK
- **Zone 4**: Asia Pacific & Rest of World

### Rate Calculation
- **Base Rate**: Minimum charge per shipment
- **Weight Rate**: Per kilogram pricing
- **Volume Rate**: Dimensional weight pricing
- **Fuel Surcharge**: Variable fuel adjustment
- **Insurance Rate**: Percentage of declared value

### Customs & Compliance
- **HS Codes**: Harmonized System classification
- **Value Limits**: Per-country customs thresholds
- **Restricted Items**: Country-specific restrictions
- **Documentation**: Required customs paperwork

## Configuration

### Environment Variables
```bash
SERVICE_NAME=international-shipping-service
DATABASE_URL=postgresql+asyncpg://intlship:intlship_pass@intl-shipping-db:5432/intl_shipping_db
REDIS_URL=redis://redis:6379/4
CONSUL_HOST=consul
CONSUL_PORT=8500
CUSTOMER_SERVICE_URL=http://customer-service:8001
DHL_API_KEY=your_dhl_api_key
FEDEX_API_KEY=your_fedex_api_key
UPS_API_KEY=your_ups_api_key
LOG_LEVEL=INFO
```

### Carrier API Configuration
```python
CARRIER_CONFIGS = {
    "DHL": {
        "api_endpoint": "https://express.api.dhl.com/mydhlapi/v2",
        "auth_url": "https://express.api.dhl.com/mydhlapi/v2/authentication",
        "services": ["EXPRESS_WORLDWIDE", "EXPRESS_12", "EXPRESS_9"]
    },
    "FEDEX": {
        "api_endpoint": "https://apis.fedex.com/v1",
        "auth_url": "https://apis.fedex.com/oauth/token",
        "services": ["INTERNATIONAL_PRIORITY", "INTERNATIONAL_ECONOMY"]
    },
    "UPS": {
        "api_endpoint": "https://onlinetools.ups.com/rest",
        "auth_url": "https://onlinetools.ups.com/security/v1/oauth/token",
        "services": ["EXPRESS_PLUS", "EXPRESS", "EXPRESS_SAVER"]
    }
}
```

## Integration Points

### Service Dependencies
- **Customer Service**: Company and user validation
- **Order Service**: Product information and order details
- **Payment Service**: Shipping cost calculations

### External Integrations
- **Carrier APIs**: Real-time rates and tracking
- **Customs Systems**: Documentation and clearance
- **Currency Exchange**: Multi-currency rate conversion

### Webhook Integrations
- **Tracking Updates**: Real-time status notifications
- **Delivery Confirmations**: Proof of delivery
- **Exception Notifications**: Delivery issues and delays

## Monitoring & Alerts

### Key Metrics
- Manifest creation rate
- Shipping rate accuracy
- Delivery performance by carrier
- Customs clearance times
- API response times from carriers

### Business Intelligence
- Popular shipping destinations
- Average shipping costs by zone
- Carrier performance comparison
- Seasonal shipping patterns

### Alert Conditions
- Carrier API failures
- Unusual shipping cost variations
- Delayed shipments
- Customs holds and rejections

## Error Handling

### Carrier Integration Errors
```json
{
  "detail": "Carrier API temporarily unavailable",
  "error_code": "CARRIER_API_ERROR",
  "carrier": "DHL",
  "retry_after": "300"
}
```

### Validation Errors
```json
{
  "detail": "Destination country does not support this service",
  "error_code": "UNSUPPORTED_DESTINATION",
  "country": "XX",
  "supported_countries": ["US", "CA", "MX"]
}
```

### Rate Calculation Errors
```json
{
  "detail": "Package exceeds weight limit for selected service",
  "error_code": "WEIGHT_LIMIT_EXCEEDED",
  "actual_weight": 75.0,
  "max_weight": 70.0,
  "alternative_services": ["FREIGHT_SERVICE"]
}
```

## Security Considerations

### API Security
- Encrypted API keys for carrier integrations
- Rate limiting for rate quote requests
- Input validation for all shipping parameters

### Data Protection
- PII handling in shipping addresses
- Customs declaration data encryption
- Audit trail for all manifest operations

### Compliance
- GDPR compliance for EU shipments
- Export control regulations
- Country-specific shipping restrictions

## Performance Optimization

### Caching Strategy
- Country and zone data caching
- Carrier service configuration caching
- Recent rate quotes caching (short TTL)

### Database Optimization
- Proper indexing for tracking queries
- Partitioning for large manifest tables
- Archive strategy for old shipments

### API Optimization
- Async carrier API calls
- Request batching for multiple quotes
- Connection pooling for external APIs

## Testing Strategy

### Unit Tests
- Rate calculation logic
- Manifest validation rules
- Country/zone assignment

### Integration Tests
- Carrier API integration tests
- Database transaction tests
- Service-to-service communication

### End-to-End Tests
- Complete shipping workflow
- Multi-carrier rate comparison
- Tracking update processing