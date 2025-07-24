# Quenty Grafana Monitoring Guide

This comprehensive guide explains how to use Grafana for monitoring the Quenty microservices platform, including setup, dashboards, alerts, and troubleshooting.

## Overview

Grafana is configured to provide comprehensive monitoring for the entire Quenty ecosystem including:
- **9 Microservices**: All application services with health, performance, and business metrics
- **9 PostgreSQL Databases**: Database performance and health monitoring
- **Infrastructure Services**: Redis, RabbitMQ, Nginx, and Consul
- **System Metrics**: Server resources and container performance

## Quick Access

**Grafana URL**: http://localhost:3000
**Default Credentials**:
- Username: `admin`
- Password: `admin`

## Initial Setup

### 1. First Login
```bash
# Start the monitoring stack
docker compose -f docker-compose.microservices.yml up -d

# Access Grafana
open http://localhost:3000
```

1. Login with `admin:admin`
2. Change the default password when prompted
3. Navigate to **Configuration** → **Data Sources** to verify Prometheus connection

### 2. Verify Data Sources
- **Prometheus**: Should be automatically configured at `http://prometheus:9090`
- Test the connection by clicking **"Save & Test"**
- Should show green checkmark: "✅ Data source is working"

## Monitored Services

### Application Services
| Service | Port | Metrics Endpoint | Dashboard Panel |
|---------|------|------------------|-----------------|
| API Gateway | 8000 | `/metrics` | Gateway Overview |
| Auth Service | 8009 | `/metrics` | Authentication Metrics |
| Customer Service | 8001 | `/metrics` | Customer Operations |
| Order Service | 8002 | `/metrics` | Order Processing |
| Pickup Service | 8003 | `/metrics` | Pickup Operations |
| International Shipping | 8004 | `/metrics` | Shipping Metrics |
| Microcredit Service | 8005 | `/metrics` | Credit Operations |
| Analytics Service | 8006 | `/metrics` | Analytics Processing |
| Reverse Logistics | 8007 | `/metrics` | Returns & Refunds |
| Franchise Service | 8008 | `/metrics` | Franchise Operations |

### Infrastructure Services
| Service | Port | Purpose | Metrics |
|---------|------|---------|---------|
| Redis | 6379 | Cache & Sessions | Memory usage, hit rates, connections |
| RabbitMQ | 15692 | Message Queue | Queue depth, message rates, consumers |
| PostgreSQL | 5432-5440 | Databases | Connections, queries, performance |
| Nginx | 9113 | Load Balancer | Request rates, response times |
| Consul | 8500 | Service Discovery | Service health, cluster status |

## Default Dashboards

### 1. Quenty Overview Dashboard
**Purpose**: High-level platform health and key business metrics

**Key Panels**:
- **Service Health**: Green/red status for all 9 microservices
- **Request Volume**: Total API requests per minute across all services
- **Error Rates**: 4xx and 5xx error percentages
- **Response Times**: P50, P95, P99 latencies
- **Business Metrics**: Orders/hour, revenue trends, active users

**Useful Queries**:
```promql
# Service availability
up{job=~".*-service"}

# Request rate across all services
sum(rate(http_requests_total[5m])) by (service)

# Error rate percentage
(sum(rate(http_requests_total{status=~"4..|5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# 95th percentile response time
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))
```

### 2. Service-Specific Dashboards

#### Auth Service Dashboard
- Login success/failure rates
- Token generation rates
- User session metrics
- JWT validation performance
- Database connection pool usage

#### Order Service Dashboard
- Order creation rates
- Order status distribution
- Average order value trends
- Inventory changes
- Payment processing times

#### Customer Service Dashboard
- Customer registration rates
- Profile update frequency
- Support ticket metrics
- Customer satisfaction scores

### 3. Infrastructure Dashboards

#### Database Performance
- Connection pool usage per database
- Query execution times
- Lock waits and deadlocks
- Cache hit ratios
- Disk I/O metrics

#### Message Queue Health
- Queue depths by service
- Message processing rates
- Dead letter queue monitoring
- Consumer lag metrics

## Creating Custom Dashboards

### 1. Business Metrics Dashboard

**Step-by-step Creation**:

1. **Create New Dashboard**
   - Click **+** → **Dashboard**
   - Click **Add new panel**

2. **Revenue Tracking Panel**
   ```promql
   # Daily revenue from analytics service
   sum(analytics_revenue_total{currency="COP"})
   
   # Revenue rate (per hour)
   rate(analytics_revenue_total{currency="COP"}[1h]) * 3600
   ```

3. **Order Volume Panel**
   ```promql
   # Total orders created today
   increase(order_created_total[24h])
   
   # Orders per minute
   rate(order_created_total[5m]) * 60
   ```

4. **Customer Activity Panel**
   ```promql
   # Active customers
   customer_active_count
   
   # New registrations per day
   increase(customer_registered_total[24h])
   ```

### 2. SLA Monitoring Dashboard

**Key SLA Metrics**:

```promql
# Service availability (should be > 99.9%)
avg(up{job=~".*-service"}) * 100

# API response time (should be < 200ms for 95% of requests)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Error rate (should be < 1%)
(sum(rate(http_requests_total{status=~"4..|5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100
```

### 3. Operational Dashboard

**System Health Panels**:

```promql
# CPU usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage
100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)

# Network I/O
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])
```

## Alerting Setup

### 1. Configure Alert Channels

**Slack Integration**:
1. Go to **Alerting** → **Notification channels**
2. Click **Add channel**
3. Select **Slack**
4. Configure webhook URL and channel

**Email Alerts**:
1. Configure SMTP in Grafana settings
2. Create email notification channel
3. Test with sample alert

### 2. Critical Alerts

#### Service Down Alert
```promql
# Alert when any service is down for > 1 minute
up{job=~".*-service"} == 0
```

**Alert Configuration**:
- **Threshold**: `IS BELOW 1`
- **Evaluation**: Every `10s` for `1m`
- **Message**: `🚨 CRITICAL: {{$labels.job}} service is DOWN`

#### High Error Rate Alert
```promql
# Alert when error rate > 5% for 5 minutes
(sum(rate(http_requests_total{status=~"4..|5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)) * 100 > 5
```

#### Database Connection Alert
```promql
# Alert when DB connections > 80% of pool
(pg_stat_database_numbackends / pg_settings_max_connections) * 100 > 80
```

#### High Response Time Alert
```promql
# Alert when 95th percentile > 1 second
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)) > 1
```

### 3. Warning Alerts

```promql
# Memory usage > 80%
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80

# Disk usage > 85%
100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100) > 85

# Queue depth > 1000 messages
rabbitmq_queue_messages > 1000
```

## Business Intelligence Dashboards

### 1. Executive Dashboard
**KPIs for Management**:
- Daily/Monthly revenue trends
- Customer acquisition rates
- Order fulfillment metrics
- Geographic performance
- Service adoption rates

### 2. Operations Dashboard
**For Operations Teams**:
- Pickup completion rates
- Delivery performance
- Return processing times
- Customer satisfaction scores
- Inventory turnover

### 3. Finance Dashboard
**For Financial Analysis**:
- Microcredit portfolio health
- Credit approval rates
- Payment collection rates
- Franchise performance
- Cost per transaction

## Advanced Monitoring

### 1. Custom Metrics

**Application-Specific Metrics**:
```python
# Example: Custom business metrics in Python services
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
orders_created = Counter('orders_created_total', 'Total orders created', ['customer_type'])
order_value = Histogram('order_value_cop', 'Order value in COP')
active_customers = Gauge('active_customers_count', 'Number of active customers')

# Usage in your service
orders_created.labels(customer_type='business').inc()
order_value.observe(order_amount)
active_customers.set(customer_count)
```

### 2. Distributed Tracing Integration
**Connecting Jaeger with Grafana**:
1. Add Jaeger as data source: `http://jaeger:16686`
2. Create tracing dashboards
3. Correlate metrics with traces

### 3. Log Aggregation
**Integrating with Loki** (if implemented):
1. Add Loki data source
2. Create log-based alerts
3. Correlate logs with metrics

## Troubleshooting

### Common Issues

#### 1. No Data in Dashboards
**Check**:
```bash
# Verify Prometheus is scraping targets
curl http://localhost:9090/api/v1/targets

# Check service metrics endpoints
curl http://localhost:8000/metrics  # API Gateway
curl http://localhost:8009/metrics  # Auth Service
```

**Fix**:
- Ensure services expose `/metrics` endpoint
- Verify network connectivity between Prometheus and services
- Check Prometheus configuration syntax

#### 2. Services Not Appearing in Targets
**Check Prometheus logs**:
```bash
docker logs quenty-prometheus
```

**Common fixes**:
- Update service names in `prometheus.yml`
- Restart Prometheus: `docker restart quenty-prometheus`
- Verify service discovery configuration

#### 3. Database Metrics Missing
**Setup PostgreSQL Exporter**:
```yaml
# Add to docker-compose.microservices.yml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://auth:auth_pass@auth-db:5432/auth_db?sslmode=disable"
  ports:
    - "9187:9187"
```

#### 4. Performance Issues
**Optimize Queries**:
- Use longer time ranges for heavy queries
- Reduce dashboard refresh rates
- Implement query caching
- Use recording rules for complex calculations

### Debugging Commands

```bash
# Check all containers are running
docker ps | grep quenty

# Verify Prometheus configuration
docker exec quenty-prometheus promtool check config /etc/prometheus/prometheus.yml

# Test metrics endpoints
for port in {8000..8009}; do
  echo "Testing localhost:$port/metrics"
  curl -s "http://localhost:$port/metrics" | head -n 5
done

# Check Grafana logs
docker logs quenty-grafana

# Restart monitoring services
docker restart quenty-prometheus quenty-grafana
```

## Best Practices

### 1. Dashboard Design
- **Group related metrics** in the same dashboard
- **Use consistent time ranges** across panels
- **Include context** with annotations and descriptions
- **Optimize query performance** with appropriate intervals

### 2. Alert Strategy
- **Create actionable alerts** - every alert should have a clear response
- **Use alert hierarchies** - critical, warning, info
- **Implement escalation** - different channels for different severities
- **Document runbooks** - link alerts to troubleshooting guides

### 3. Metric Naming
```promql
# Good naming conventions
http_requests_total{service="order", status="200"}
order_processing_duration_seconds
customer_satisfaction_score

# Avoid
requests  # too generic
time      # ambiguous units
count     # missing context
```

### 4. Performance Optimization
- **Use recording rules** for expensive queries
- **Set appropriate retention** periods
- **Monitor Prometheus itself** - watch for high memory/CPU usage
- **Use federation** for multi-cluster setups

## Integration with Development Workflow

### 1. Development Environment
```bash
# Local development with monitoring
docker compose -f docker-compose.microservices.yml up -d
make dev-monitor  # Custom make target for dev monitoring
```

### 2. CI/CD Pipeline Monitoring
- Monitor deployment success rates
- Track deployment duration
- Alert on deployment failures
- Monitor post-deployment metrics

### 3. Feature Flag Monitoring
```promql
# Monitor feature adoption
feature_flag_usage_total{flag="new_checkout_flow", enabled="true"}

# A/B test metrics
conversion_rate{experiment="checkout_v2", variant="control"}
```

## Security Considerations

### 1. Access Control
- **Change default passwords** immediately
- **Use LDAP/OAuth** for production environments
- **Implement role-based access** - different dashboards for different teams
- **Audit dashboard access** and modifications

### 2. Data Privacy
- **Avoid logging sensitive data** in metrics
- **Mask PII** in dashboard queries
- **Use secure connections** (HTTPS) in production
- **Regular security updates** for Grafana and Prometheus

### 3. Network Security
```yaml
# Production network configuration
networks:
  monitoring:
    driver: overlay
    encrypted: true
    attachable: false
```

This comprehensive guide provides everything needed to effectively monitor the Quenty platform using Grafana, from basic setup to advanced business intelligence dashboards.