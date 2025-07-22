# Franchise Service Documentation

## Overview

The Franchise Service manages franchise operations, territory allocation, contract management, and performance tracking within the Quenty platform. It provides comprehensive franchise management capabilities including territory management, performance metrics, and financial tracking.

## Service Details

- **Port**: 8008
- **Database**: PostgreSQL (franchise_db)
- **Base URL**: `http://localhost:8008`
- **Health Check**: `GET /health`

## Core Features

### 1. Franchise Management
- Franchise registration and onboarding
- Profile and business information management
- Status tracking and lifecycle management
- Franchise directory and search

### 2. Territory Management
- Territory definition and allocation
- Availability tracking and reservations
- Geographic boundaries and market analysis
- Territory performance metrics

### 3. Contract Management
- Franchise agreement creation and management
- Contract terms and conditions tracking
- Renewal and amendment processing
- Compliance monitoring

### 4. Performance Tracking
- Revenue and sales performance monitoring
- Operational metrics and KPIs
- Comparative performance analysis
- Performance-based rankings

### 5. Financial Management
- Payment processing and tracking
- Fee management (franchise fees, royalties)
- Financial reporting and reconciliation
- Performance-based incentives

## Data Models

### Franchise Model
```python
class Franchise(Base):
    __tablename__ = "franchises"
    
    id = Column(Integer, primary_key=True, index=True)
    franchise_id = Column(String(255), unique=True, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    franchisee_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50))
    
    # Address Information
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Business Information
    business_license = Column(String(100))
    tax_id = Column(String(100))
    territory_code = Column(String(50), ForeignKey("territories.territory_code"))
    
    # Contract Information
    contract_start_date = Column(Date)
    contract_end_date = Column(Date)
    contract_terms = Column(JSON)
    
    # Operational Information
    status = Column(String(50), default="pending")
    opening_date = Column(Date)
    closure_date = Column(Date)
    operational_hours = Column(JSON)
    services_offered = Column(JSON)
    equipment_list = Column(JSON)
    
    # Financial Information
    initial_fee = Column(Numeric(10, 2))
    monthly_fee = Column(Numeric(10, 2))
    royalty_rate = Column(Numeric(5, 2))  # Percentage
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_by = Column(String(255))
    updated_by = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    territory = relationship("Territory", back_populates="franchises")
    contracts = relationship("FranchiseContract", back_populates="franchise")
    payments = relationship("FranchisePayment", back_populates="franchise")
    performance_records = relationship("FranchisePerformance", back_populates="franchise")
```

### Territory Model
```python
class Territory(Base):
    __tablename__ = "territories"
    
    id = Column(Integer, primary_key=True, index=True)
    territory_code = Column(String(50), unique=True, index=True)
    
    # Territory Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    country = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    region = Column(String(100))
    
    # Geographic Information
    boundaries = Column(JSON)  # GeoJSON polygon
    area_size = Column(Numeric(10, 2))  # km²
    population = Column(Integer)
    
    # Market Information
    market_potential = Column(String(20))  # high, medium, low
    competition_level = Column(String(20))  # high, medium, low
    average_income = Column(Numeric(12, 2))
    demographic_data = Column(JSON)
    
    # Availability
    status = Column(String(20), default="available")  # available, reserved, assigned
    reserved_until = Column(DateTime)
    reserved_by = Column(String(255))
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    franchises = relationship("Franchise", back_populates="territory")
```

### Franchise Performance Model
```python
class FranchisePerformance(Base):
    __tablename__ = "franchise_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    performance_id = Column(String(255), unique=True, index=True)
    
    # Reference
    franchise_id = Column(Integer, ForeignKey("franchises.id"))
    
    # Period Information
    period_type = Column(String(20))  # daily, weekly, monthly, quarterly, annual
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Financial Metrics
    revenue = Column(Numeric(12, 2), default=0)
    costs = Column(Numeric(12, 2), default=0)
    profit = Column(Numeric(12, 2), default=0)
    royalties_paid = Column(Numeric(12, 2), default=0)
    
    # Operational Metrics
    orders_count = Column(Integer, default=0)
    customers_served = Column(Integer, default=0)
    average_order_value = Column(Numeric(10, 2), default=0)
    customer_satisfaction_score = Column(Numeric(3, 2), default=0)
    
    # Performance Indicators
    performance_score = Column(Numeric(5, 2), default=0)  # 0-100
    ranking = Column(Integer)  # Ranking among all franchises
    improvement_areas = Column(JSON)
    
    # System Fields
    calculated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    franchise = relationship("Franchise", back_populates="performance_records")
```

## API Endpoints

### Franchise Management

#### Create Franchise
```http
POST /api/v1/franchises
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Quenty Express Polanco",
    "franchisee_name": "María González",
    "email": "maria.gonzalez@example.com",
    "phone": "+52 55 1234 5678",
    "address": "Av. Polanco 123, Col. Polanco",
    "city": "Mexico City",
    "state": "CDMX",
    "country": "Mexico",
    "postal_code": "11560",
    "territory_code": "CDMX-POL-001",
    "business_license": "BL-2024-001234",
    "tax_id": "RFC-GOMA850123ABC",
    "services_offered": ["express_delivery", "international_shipping"],
    "operational_hours": {
        "monday": "08:00-20:00",
        "tuesday": "08:00-20:00",
        "wednesday": "08:00-20:00",
        "thursday": "08:00-20:00",
        "friday": "08:00-20:00",
        "saturday": "09:00-18:00",
        "sunday": "10:00-16:00"
    }
}
```

**Response:**
```json
{
    "franchise_id": "FRAN-ABCD1234",
    "name": "Quenty Express Polanco",
    "franchisee_name": "María González",
    "email": "maria.gonzalez@example.com",
    "status": "pending",
    "territory_code": "CDMX-POL-001",
    "return_authorization_number": "RMA-FRAN-ABCD1234",
    "estimated_opening_date": "2025-08-15",
    "created_at": "2025-07-22T10:30:00.000Z"
}
```

#### List Franchises
```http
GET /api/v1/franchises?limit=20&offset=0&status=active&city=Mexico%20City
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "franchises": [
        {
            "franchise_id": "FRAN-ABCD1234",
            "name": "Quenty Express Polanco",
            "franchisee_name": "María González",
            "city": "Mexico City",
            "state": "CDMX",
            "territory_code": "CDMX-POL-001",
            "status": "active",
            "opening_date": "2025-08-15",
            "performance_score": 87.5
        }
    ],
    "total": 45,
    "limit": 20,
    "offset": 0,
    "has_next": true,
    "has_previous": false
}
```

#### Get Franchise Details
```http
GET /api/v1/franchises/FRAN-ABCD1234
Authorization: Bearer <access_token>
```

#### Update Franchise Status
```http
PUT /api/v1/franchises/FRAN-ABCD1234/status
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "status": "active",
    "effective_date": "2025-08-15",
    "reason": "All requirements completed, franchise approved for operation"
}
```

### Territory Management

#### List Available Territories
```http
GET /api/v1/territories?status=available&country=Mexico&state=CDMX
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "territories": [
        {
            "territory_code": "CDMX-POL-002",
            "name": "Polanco Norte",
            "country": "Mexico",
            "state": "CDMX",
            "status": "available",
            "market_potential": "high",
            "competition_level": "medium",
            "population": 125000,
            "area_size_km2": 15.5
        }
    ],
    "total": 12,
    "limit": 20,
    "offset": 0
}
```

#### Check Territory Availability
```http
GET /api/v1/territories/CDMX-POL-002
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "territory_code": "CDMX-POL-002",
    "name": "Polanco Norte",
    "status": "available",
    "available": true,
    "reserved_until": null,
    "nearby_franchises": 3,
    "market_potential": "high",
    "competition_level": "medium",
    "population": 125000,
    "area_size_km2": 15.5,
    "average_income": 85000.00
}
```

### Performance Tracking

#### Get Franchise Performance
```http
GET /api/v1/franchises/FRAN-ABCD1234/performance?period_type=monthly&start_date=2025-01-01&end_date=2025-07-31
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "franchise_id": "FRAN-ABCD1234",
    "performance_history": [
        {
            "performance_id": "PERF-202507-001",
            "period_type": "monthly",
            "period_start": "2025-07-01",
            "period_end": "2025-07-31",
            "revenue": 45000.00,
            "profit": 13500.00,
            "orders_count": 287,
            "customers_served": 156,
            "average_order_value": 156.79,
            "customer_satisfaction_score": 4.2,
            "performance_score": 87.5,
            "ranking": 3
        }
    ],
    "summary": {
        "total_periods": 7,
        "avg_revenue": 42500.00,
        "avg_performance_score": 85.2,
        "current_ranking": 3
    }
}
```

## Business Logic

### Franchise Lifecycle

1. **Application Submission**
   - Franchisee submits application with required documents
   - System validates territory availability
   - Initial background checks initiated

2. **Review and Approval**
   - Admin reviews application and documents
   - Credit and background checks completed
   - Territory reserved during review process

3. **Contract Execution**
   - Contract terms negotiated and agreed
   - Initial franchise fee payment processed
   - Territory officially assigned

4. **Setup and Training**
   - Location setup and equipment installation
   - Franchisee training program completion
   - System integration and testing

5. **Launch and Operation**
   - Grand opening and marketing launch
   - Regular performance monitoring
   - Ongoing support and compliance checks

### Territory Management

#### Territory Assignment Rules
- One territory per franchise
- Minimum distance between franchises: 5km in urban areas, 15km in rural areas
- Market potential must justify franchise density
- Territory cannot be reassigned for 2 years after closure

#### Reservation System
- Territory reserved for 30 days during application review
- Extension possible with valid justification
- Automatic release if application rejected or withdrawn

### Performance Evaluation

#### Performance Score Calculation
```python
def calculate_performance_score(metrics):
    weights = {
        'revenue_target': 0.30,
        'profit_margin': 0.25,
        'customer_satisfaction': 0.20,
        'order_volume': 0.15,
        'operational_compliance': 0.10
    }
    
    score = 0
    for metric, weight in weights.items():
        score += metrics[metric] * weight
    
    return min(100, max(0, score))
```

#### Ranking System
- Monthly ranking among all active franchises
- Regional and national leaderboards
- Performance-based incentives and recognition

## Fee Structure

### Initial Fees
- **Franchise Fee**: $25,000 USD (one-time)
- **Territory Development**: $10,000 USD (varies by territory)
- **Equipment Package**: $15,000 USD (mandatory)
- **Training Fee**: $3,000 USD (per franchisee)

### Ongoing Fees
- **Royalty Fee**: 6% of monthly gross revenue
- **Marketing Fee**: 2% of monthly gross revenue
- **Technology Fee**: $200 USD monthly
- **Insurance Fee**: $150 USD monthly

### Performance Incentives
- Top 10% performers: 1% royalty reduction next quarter
- Customer satisfaction >4.5: $500 monthly bonus
- Revenue growth >20% YoY: Marketing fee waived for 3 months

## Integration with Other Services

### Order Service Integration
```python
# Track franchise performance from orders
async def process_franchise_order(order):
    if order.franchise_id:
        await update_franchise_metrics(
            franchise_id=order.franchise_id,
            revenue=order.total_amount,
            order_count=1,
            customer_id=order.customer_id
        )
```

### Analytics Service Integration
```python
# Send performance metrics to analytics
await send_analytics_metric({
    "metric_type": "franchise_performance",
    "name": "monthly_revenue",
    "value": performance.revenue,
    "tags": {
        "franchise_id": franchise.franchise_id,
        "territory": franchise.territory_code,
        "region": franchise.state
    }
})
```

### Payment Integration
```python
# Process franchise fees
async def process_franchise_payment(franchise_id, payment_type, amount):
    payment_record = FranchisePayment(
        franchise_id=franchise_id,
        payment_type=payment_type,
        amount=amount,
        due_date=calculate_due_date(),
        status="pending"
    )
    
    # Integration with payment processor
    result = await payment_service.process_payment(payment_record)
    
    if result.success:
        payment_record.status = "completed"
        payment_record.transaction_id = result.transaction_id
    
    return payment_record
```

## Reporting and Analytics

### Standard Reports
1. **Franchise Performance Report**
   - Revenue and profit analysis
   - Ranking and benchmarking
   - Trend analysis and forecasting

2. **Territory Analysis Report**
   - Market penetration analysis
   - Territory performance comparison
   - Expansion opportunity identification

3. **Financial Summary Report**
   - Fee collection status
   - Revenue sharing breakdown
   - Financial health indicators

4. **Operational Compliance Report**
   - Standards adherence tracking
   - Training completion status
   - Audit findings and corrections

### Key Performance Indicators (KPIs)
- **Growth Metrics**: New franchise acquisitions, territory expansion
- **Performance Metrics**: Average performance score, top/bottom performers
- **Financial Metrics**: Total franchise revenue, fee collection rate
- **Operational Metrics**: Customer satisfaction, compliance scores

## Security and Compliance

### Data Protection
- Franchisee personal information encryption
- Financial data secured with PCI compliance
- Contract documents digitally signed and stored securely
- Access controls based on user roles

### Regulatory Compliance
- Franchise disclosure documents (FDD) management
- State and federal franchise law compliance
- Tax reporting and documentation
- International franchise regulations

### Audit Trails
- All franchise modifications logged
- Performance calculation history maintained
- Payment transaction records preserved
- Territory assignment history tracked

## Monitoring and Health Checks

### Service Health Indicators
- **Database Performance**: Query response times, connection pool status
- **Territory System**: Availability calculations, boundary validations
- **Performance Engine**: Calculation accuracy, update frequencies
- **Integration Health**: External service connectivity

### Business Metrics Monitoring
- New franchise application rate
- Territory utilization percentage
- Average performance scores
- Fee collection efficiency

## Troubleshooting

### Common Issues

#### 1. Territory Availability Conflicts
**Problem**: Multiple applications for same territory
**Solution**:
- Check reservation timestamps
- First-come-first-served basis
- Manual admin resolution for edge cases

#### 2. Performance Calculation Discrepancies
**Problem**: Performance scores don't match expected values
**Solution**:
- Verify data source accuracy
- Check calculation weights and formulas
- Recalculate from source data if needed

#### 3. Payment Processing Failures
**Problem**: Franchise fee payments failing
**Solution**:
- Verify payment method and details
- Check integration with payment processor
- Manual payment recording if necessary

### Debug Commands
```bash
# Check franchise service health
curl http://localhost:8008/health

# Get franchise performance details
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8008/api/v1/franchises/FRAN-123/performance"

# Check territory availability
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8008/api/v1/territories/CDMX-POL-001"
```