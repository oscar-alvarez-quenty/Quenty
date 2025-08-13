# Prometheus Metrics Documentation for Quenty Microservices

## Overview

All Quenty microservices expose Prometheus-compatible metrics through a `/metrics` endpoint. These metrics are automatically scraped by Prometheus and visualized in Grafana.

## Accessing Metrics

Each microservice exposes metrics at:
```
http://<service-host>:<service-port>/metrics
```

### Service Endpoints

| Service | Container Name | Port | Metrics URL |
|---------|---------------|------|-------------|
| Auth Service | quenty-auth-service | 8003 | http://localhost:8003/metrics |
| Customer Service | quenty-customer-service | 8004 | http://localhost:8004/metrics |
| Order Service | quenty-order-service | 8005 | http://localhost:8005/metrics |
| Analytics Service | quenty-analytics-service | 8006 | http://localhost:8006/metrics |
| Franchise Service | quenty-franchise-service | 8007 | http://localhost:8007/metrics |
| International Shipping | quenty-intl-shipping-service | 8008 | http://localhost:8008/metrics |
| Microcredit Service | quenty-microcredit-service | 8009 | http://localhost:8009/metrics |
| Pickup Service | quenty-pickup-service | 8010 | http://localhost:8010/metrics |
| Reverse Logistics | quenty-reverse-logistics-service | 8011 | http://localhost:8011/metrics |
| API Gateway | quenty-api-gateway | 8000 | http://localhost:8000/metrics |

## Common Metrics

All services expose these standard HTTP metrics:

### HTTP Request Metrics
- `http_requests_total` - Total number of HTTP requests
  - Labels: `service`, `method`, `endpoint`, `status`
- `http_request_duration_seconds` - Duration of HTTP requests in seconds
  - Labels: `service`, `method`, `endpoint`
- `http_requests_in_progress` - Number of HTTP requests currently being processed
  - Labels: `service`, `method`, `endpoint`

### Service-Specific Metrics

Each service also exposes its own business metrics:

#### Auth Service
- `auth_requests_total` - Total authentication requests
  - Labels: `method`, `endpoint`, `status`
- `auth_request_duration_seconds` - Authentication request duration
  - Labels: `method`, `endpoint`
- `auth_active_sessions_total` - Active user sessions
  - Labels: `token_type`
- `auth_failed_login_attempts_total` - Failed login attempts

#### Customer Service
- `customer_operations_total` - Customer operations count
  - Labels: `operation`, `status`
- `customer_request_duration_seconds` - Customer request duration
  - Labels: `method`, `endpoint`
- `customer_support_tickets_total` - Support tickets created
  - Labels: `status`, `priority`

#### Order Service
- `order_operations_total` - Order operations count
  - Labels: `operation`, `status`
- `order_request_duration_seconds` - Order request duration
  - Labels: `method`, `endpoint`

#### Analytics Service
- `analytics_operations_total` - Analytics operations count
  - Labels: `operation`, `status`
- `analytics_request_duration_seconds` - Analytics request duration
  - Labels: `method`, `endpoint`

#### Franchise Service
- `franchise_operations_total` - Franchise operations count
  - Labels: `operation`, `status`
- `franchise_request_duration_seconds` - Franchise request duration
  - Labels: `method`, `endpoint`

#### International Shipping Service
- `intl_shipping_operations_total` - International shipping operations count
  - Labels: `operation`, `status`
- `intl_shipping_request_duration_seconds` - International shipping request duration
  - Labels: `method`, `endpoint`

#### Microcredit Service
- `microcredit_operations_total` - Microcredit operations count
  - Labels: `operation`, `status`
- `microcredit_request_duration_seconds` - Microcredit request duration
  - Labels: `method`, `endpoint`

#### Pickup Service
- `pickup_operations_total` - Pickup operations count
  - Labels: `operation`, `status`
- `pickup_request_duration_seconds` - Pickup request duration
  - Labels: `method`, `endpoint`

#### Reverse Logistics Service
- `reverse_logistics_operations_total` - Reverse logistics operations count
  - Labels: `operation`, `status`
- `reverse_logistics_request_duration_seconds` - Reverse logistics request duration
  - Labels: `method`, `endpoint`

#### API Gateway
- `api_gateway_operations_total` - API gateway operations count
  - Labels: `operation`, `status`
- `api_gateway_request_duration_seconds` - API gateway request duration
  - Labels: `method`, `endpoint`

## Prometheus Configuration

The Prometheus configuration (`prometheus.yml`) is already set up to scrape all microservices:

```yaml
scrape_configs:
  - job_name: 'quenty-microservices'
    static_configs:
      - targets:
        - 'auth-service:8003'
        - 'customer-service:8004'
        - 'order-service:8005'
        - 'analytics-service:8006'
        - 'franchise-service:8007'
        - 'intl-shipping-service:8008'
        - 'microcredit-service:8009'
        - 'pickup-service:8010'
        - 'reverse-logistics-service:8011'
        - 'api-gateway:8000'
```

## Viewing Metrics in Grafana

1. Access Grafana at http://localhost:3000
2. Default credentials: admin/admin
3. Navigate to Dashboards → Quenty Overview
4. The dashboard displays:
   - Request rates per service
   - Response time distributions
   - Error rates
   - Active sessions (auth service)
   - Business operation metrics

## Example Prometheus Queries

### Request Rate (requests per second)
```promql
rate(http_requests_total[5m])
```

### Average Response Time
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### Error Rate
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

### 95th Percentile Response Time
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Active Sessions (Auth Service)
```promql
auth_active_sessions_total
```

## Adding Custom Metrics

To add custom metrics to a service:

1. Import the required Prometheus client:
```python
from prometheus_client import Counter, Histogram, Gauge
```

2. Define your metric:
```python
my_custom_metric = Counter(
    'service_custom_operations_total',
    'Description of the metric',
    ['label1', 'label2']
)
```

3. Increment/observe the metric in your code:
```python
my_custom_metric.labels(label1='value1', label2='value2').inc()
```

## Best Practices

1. **Naming Convention**: Use lowercase with underscores, include unit suffix (_total, _seconds, _bytes)
2. **Labels**: Keep cardinality low, avoid user IDs or unbounded values
3. **Help Text**: Provide clear descriptions for each metric
4. **Units**: Always include units in metric names
5. **Buckets**: For histograms, choose bucket boundaries that match your SLAs

## Troubleshooting

### Metrics Not Appearing
1. Check service health: `curl http://service:port/health`
2. Verify metrics endpoint: `curl http://service:port/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Review service logs for errors

### High Memory Usage
- Reduce metric cardinality by removing high-cardinality labels
- Increase Prometheus retention settings if needed
- Consider using recording rules for frequently-queried metrics

### Missing Data Points
- Check service availability during the time period
- Verify Prometheus scrape interval (default: 15s)
- Ensure services are properly registered in Prometheus configuration