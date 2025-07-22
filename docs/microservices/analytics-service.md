# Analytics Service Documentation

## Overview

The Analytics Service provides comprehensive business intelligence, metrics collection, and reporting capabilities for the Quenty platform. It collects and processes data from all microservices to provide insights, dashboards, and automated reports.

## Service Details

- **Port**: 8006
- **Database**: PostgreSQL (analytics_db)
- **Base URL**: `http://localhost:8006`
- **Health Check**: `GET /health`

## Core Features

### 1. Metrics Collection
- Real-time metrics ingestion from all services
- Time-series data storage and indexing
- Flexible tagging and metadata support
- Automatic data aggregation and rollups

### 2. Dashboard Management
- Dynamic dashboard creation and configuration
- Real-time data visualization
- Customizable widgets and layouts
- Role-based dashboard access

### 3. Report Generation
- Scheduled and on-demand reports
- Multiple export formats (JSON, CSV, PDF)
- Template-based report generation
- Automated report distribution

### 4. Business Intelligence
- Revenue and financial analytics
- Customer behavior analysis
- Operational performance metrics
- Predictive analytics and trends

### 5. Alerting System
- Threshold-based alerts
- Anomaly detection
- Multi-channel notifications
- Alert escalation workflows

## Data Models

### Metric Model
```python
class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(String(255), unique=True, index=True)
    
    # Metric Information
    metric_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Value and Metadata
    value = Column(Numeric(20, 4), nullable=False)
    unit = Column(String(50))  # currency, percentage, count, etc.
    tags = Column(JSON, default=dict)  # Key-value tags for filtering
    
    # Time Information
    timestamp = Column(DateTime, nullable=False, index=True)
    period = Column(String(20))  # daily, weekly, monthly, etc.
    
    # Source Information
    source_service = Column(String(100))  # Which service generated this metric
    source_entity_id = Column(String(255))  # ID of the entity
    source_entity_type = Column(String(100))  # Type of entity
    
    # System Fields
    created_at = Column(DateTime, default=func.now(), nullable=False)
```

### Dashboard Model
```python
class Dashboard(Base):
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(String(255), unique=True, index=True)
    
    # Dashboard Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    dashboard_type = Column(String(50), default="standard")
    
    # Configuration
    widgets = Column(JSON, default=list)  # Widget configurations
    layout = Column(JSON, default=dict)  # Layout configuration
    filters = Column(JSON, default=dict)  # Default filters
    refresh_interval = Column(Integer, default=300)  # Seconds
    
    # Access Control
    owner_id = Column(String(255))
    is_public = Column(Boolean, default=False)
    allowed_users = Column(JSON, default=list)
    allowed_roles = Column(JSON, default=list)
    
    # System Fields
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### Report Model
```python
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(255), unique=True, index=True)
    
    # Report Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False)
    format = Column(String(20), default="json")  # json, csv, pdf, excel
    
    # Generation Parameters
    parameters = Column(JSON, default=dict)
    filters = Column(JSON, default=dict)
    date_range = Column(JSON)  # start_date, end_date
    
    # Status and Results
    status = Column(String(20), default="pending", nullable=False)
    progress_percentage = Column(Integer, default=0)
    file_url = Column(String(500))
    file_size = Column(Integer)
    
    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_expression = Column(String(100))  # Cron expression
    next_run = Column(DateTime)
    
    # System Fields
    requested_by = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
```

## API Endpoints

### Dashboard Endpoints

#### Get Dashboard Metrics
```http
GET /api/v1/analytics/dashboard?days=30
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "total_revenue": 125000.50,
    "total_orders": 1847,
    "total_customers": 523,
    "avg_order_value": 67.75,
    "revenue_growth": 12.5,
    "order_growth": 8.3,
    "top_performing_services": [
        {
            "service": "International Shipping",
            "revenue": 45000.00,
            "orders": 678
        }
    ],
    "recent_trends": [
        {
            "date": "2025-07-21",
            "revenue": 4250.00,
            "orders": 63
        }
    ]
}
```

### Metrics Ingestion

#### Ingest Metric
```http
POST /api/v1/analytics/metrics
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "metric_type": "revenue",
    "name": "order_revenue",
    "value": 125.50,
    "unit": "USD",
    "tags": {
        "service": "order-service",
        "customer_type": "premium",
        "region": "mexico"
    },
    "source_service": "order-service",
    "source_entity_id": "ORDER-123456",
    "source_entity_type": "order"
}
```

**Response:**
```json
{
    "metric_id": "METRIC-ABCD1234",
    "status": "ingested",
    "timestamp": "2025-07-22T10:30:00.000Z"
}
```

### Analytics Queries

#### Query Analytics Data
```http
POST /api/v1/analytics/query
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "metric_type": "revenue",
    "start_date": "2025-07-01",
    "end_date": "2025-07-22",
    "granularity": "daily",
    "filters": {
        "source_service": "order-service",
        "region": "mexico"
    },
    "aggregation": "sum"
}
```

**Response:**
```json
{
    "query": {
        "metric_type": "revenue",
        "start_date": "2025-07-01",
        "end_date": "2025-07-22",
        "granularity": "daily"
    },
    "data": [
        {
            "period": "2025-07-21",
            "value": 4250.00,
            "count": 63
        },
        {
            "period": "2025-07-22",
            "value": 3180.75,
            "count": 47
        }
    ],
    "total_records": 110,
    "aggregated_periods": 22
}
```

### Report Generation

#### Generate Report
```http
POST /api/v1/analytics/reports
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Monthly Revenue Report",
    "report_type": "financial",
    "parameters": {
        "period": "monthly",
        "include_breakdown": true,
        "include_trends": true
    },
    "filters": {
        "date_range": {
            "start": "2025-07-01",
            "end": "2025-07-31"
        }
    },
    "format": "pdf"
}
```

**Response:**
```json
{
    "report_id": "RPT-MNTH2507",
    "status": "processing",
    "estimated_completion": "2025-07-22T10:35:00.000Z"
}
```

#### Get Report Status
```http
GET /api/v1/analytics/reports/RPT-MNTH2507
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "report_id": "RPT-MNTH2507",
    "name": "Monthly Revenue Report",
    "status": "completed",
    "progress_percentage": 100,
    "created_at": "2025-07-22T10:30:00.000Z",
    "completed_at": "2025-07-22T10:34:15.000Z",
    "file_url": "/reports/RPT-MNTH2507.pdf",
    "file_size": 2048576
}
```

### Business Intelligence

#### Get Business Trends
```http
GET /api/v1/analytics/trends?days=30
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "period": "30 days",
    "trends": {
        "revenue": [
            {
                "date": "2025-07-21",
                "value": 4250.00
            },
            {
                "date": "2025-07-22",
                "value": 3180.75
            }
        ],
        "orders": [
            {
                "date": "2025-07-21",
                "value": 63
            }
        ],
        "customers": [
            {
                "date": "2025-07-21",
                "value": 15
            }
        ]
    },
    "insights": [
        {
            "type": "revenue",
            "message": "Revenue trend shows 12.5% growth",
            "impact": "positive"
        },
        {
            "type": "growth",
            "message": "Steady customer acquisition",
            "impact": "positive"
        }
    ]
}
```

## Metrics Types and Categories

### Revenue Metrics
- `revenue.total` - Total revenue
- `revenue.monthly` - Monthly recurring revenue
- `revenue.per_customer` - Average revenue per customer
- `revenue.per_order` - Average order value

### Order Metrics
- `orders.count` - Total number of orders
- `orders.completed` - Completed orders
- `orders.cancelled` - Cancelled orders
- `orders.processing_time` - Average processing time

### Customer Metrics
- `customers.total` - Total customers
- `customers.new` - New customer acquisitions
- `customers.active` - Active customers
- `customers.retention_rate` - Customer retention rate

### Service Performance
- `performance.response_time` - API response times
- `performance.error_rate` - Service error rates
- `performance.throughput` - Request throughput
- `performance.availability` - Service availability

### Financial Metrics
- `finance.profit_margin` - Profit margins
- `finance.cost_per_acquisition` - Customer acquisition cost
- `finance.lifetime_value` - Customer lifetime value
- `finance.churn_rate` - Customer churn rate

## Dashboard Configuration

### Widget Types
1. **Line Chart**: Time-series data visualization
2. **Bar Chart**: Categorical data comparison
3. **Pie Chart**: Proportion and percentage displays
4. **Number Widget**: Single metric display
5. **Table Widget**: Tabular data presentation
6. **Gauge Widget**: Progress and threshold indicators

### Example Dashboard Config
```json
{
    "name": "Executive Dashboard",
    "widgets": [
        {
            "type": "number",
            "title": "Total Revenue",
            "metric": "revenue.total",
            "period": "30d",
            "format": "currency"
        },
        {
            "type": "line_chart",
            "title": "Revenue Trend",
            "metrics": ["revenue.total"],
            "period": "30d",
            "granularity": "daily"
        },
        {
            "type": "bar_chart",
            "title": "Orders by Service",
            "metric": "orders.count",
            "group_by": "source_service",
            "period": "7d"
        }
    ],
    "layout": {
        "columns": 3,
        "rows": 2
    },
    "filters": {
        "region": "mexico",
        "customer_type": "all"
    },
    "refresh_interval": 300
}
```

## Data Collection Patterns

### Automatic Metrics Collection
Services automatically send metrics for:
- API endpoint usage
- Response times and error rates
- Database query performance
- Business events (orders, payments, etc.)

### Custom Metrics
Services can send custom business metrics:

```python
import requests

async def send_metric(metric_type: str, name: str, value: float, tags: dict = None):
    payload = {
        "metric_type": metric_type,
        "name": name,
        "value": value,
        "unit": "USD",
        "tags": tags or {},
        "source_service": "order-service",
        "source_entity_id": entity_id,
        "source_entity_type": "order"
    }
    
    response = requests.post(
        f"{ANALYTICS_SERVICE_URL}/api/v1/analytics/metrics",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    return response.json()

# Usage example
await send_metric(
    metric_type="revenue",
    name="order_completed",
    value=125.50,
    tags={"customer_type": "premium", "region": "mexico"}
)
```

## Alerting and Notifications

### Alert Configuration
```json
{
    "name": "Revenue Drop Alert",
    "metric_type": "revenue",
    "condition": "revenue.total < 1000",
    "threshold_value": 1000.00,
    "comparison_operator": "<",
    "time_window": "1h",
    "notification_channels": ["email", "slack"],
    "recipients": ["admin@quenty.com", "#alerts"]
}
```

### Supported Alert Types
- **Threshold Alerts**: Value above/below threshold
- **Trend Alerts**: Percentage change over time
- **Anomaly Alerts**: Statistical anomaly detection
- **Missing Data Alerts**: No data received in time window

## Performance and Scalability

### Data Retention
- **Raw Metrics**: 90 days
- **Hourly Aggregates**: 1 year
- **Daily Aggregates**: 5 years
- **Monthly Aggregates**: Indefinite

### Indexing Strategy
- Time-based partitioning for metrics table
- GIN index on tags for flexible filtering
- Composite indexes on (metric_type, timestamp)
- Service and entity indexes for source tracking

### Caching
- Dashboard data cached for 5 minutes
- Report results cached for 1 hour
- Aggregated metrics cached for 15 minutes

## Integration Examples

### Order Service Integration
```python
# In order service when order is completed
await send_analytics_metric({
    "metric_type": "revenue",
    "name": "order_revenue",
    "value": order.total_amount,
    "tags": {
        "customer_id": order.customer_id,
        "region": order.shipping_address.country,
        "service_type": order.service_type
    },
    "source_entity_id": order.order_id,
    "source_entity_type": "order"
})
```

### Customer Service Integration
```python
# Track customer acquisition
await send_analytics_metric({
    "metric_type": "customers",
    "name": "customer_registered",
    "value": 1,
    "tags": {
        "acquisition_source": "website",
        "customer_type": customer.customer_type
    },
    "source_entity_id": customer.customer_id,
    "source_entity_type": "customer"
})
```

## Monitoring and Health Checks

### Service Health
- **Database Connectivity**: Connection pool status
- **Metric Ingestion Rate**: Metrics per second
- **Query Performance**: Average query response time
- **Storage Usage**: Database and file storage metrics

### Debug Endpoints
```bash
# Service health
curl http://localhost:8006/health

# Check recent metrics
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8006/api/v1/analytics/metrics/recent"

# Performance stats
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8006/api/v1/analytics/stats"
```

## Troubleshooting

### Common Issues

#### 1. Missing Metrics
**Problem**: Dashboard showing no data
**Solution**:
- Check if source services are sending metrics
- Verify time range and filters
- Check service connectivity to analytics service

#### 2. Slow Dashboard Loading
**Problem**: Dashboards taking too long to load
**Solution**:
- Reduce time range or add more specific filters
- Check database performance and indexes
- Consider pre-aggregating frequently accessed metrics

#### 3. Report Generation Failures
**Problem**: Reports stuck in processing status
**Solution**:
- Check disk space for report storage
- Verify report parameters and date ranges
- Check background job processing

### Performance Tuning
- Use time-based partitioning for large datasets
- Implement data archiving for old metrics
- Consider read replicas for heavy analytical workloads
- Use materialized views for complex aggregations