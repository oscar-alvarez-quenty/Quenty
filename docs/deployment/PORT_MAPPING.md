# Quenty Microservices Port Mapping

This document lists all exposed ports for Quenty microservices and databases when running with `docker-compose.microservices.yml`.

## Service Ports

### API Gateway & Web Interface
| Service | Host Port | Container Port | Description |
|---------|-----------|----------------|-------------|
| API Gateway | 8000 | 8000 | Main API Gateway - All requests go through here |
| Nginx Load Balancer | 80 | 80 | HTTP Load Balancer |
| Nginx Load Balancer | 443 | 443 | HTTPS Load Balancer |

### Microservices (Direct Access)
| Service | Host Port | Container Port | Description |
|---------|-----------|----------------|-------------|
| Auth Service | 8009 | 8009 | Authentication & User Management |
| Customer Service | 8001 | 8001 | Customer Profile Management |
| Order Service | 8002 | 8002 | Order Processing & Management |
| Pickup Service | 8003 | 8003 | Pickup Scheduling & Management |
| International Shipping | 8004 | 8004 | International Shipping Operations |
| Microcredit Service | 8005 | 8005 | Microcredit & Financial Services |
| Analytics Service | 8006 | 8006 | Analytics & Reporting |
| Reverse Logistics | 8007 | 8007 | Returns & Reverse Logistics |
| Franchise Service | 8008 | 8008 | Franchise Management |

## Database Ports

### PostgreSQL Databases
| Database | Host Port | Container Port | Description | Credentials |
|----------|-----------|----------------|-------------|-------------|
| Auth DB | 5441 | 5432 | Authentication data | auth:auth_pass@auth_db |
| Customer DB | 5433 | 5432 | Customer profiles | customer:customer_pass@customer_db |
| Order DB | 5434 | 5432 | Orders & products | order:order_pass@order_db |
| Pickup DB | 5435 | 5432 | Pickup schedules | pickup:pickup_pass@pickup_db |
| Intl Shipping DB | 5436 | 5432 | International shipping | intlship:intlship_pass@intl_shipping_db |
| Microcredit DB | 5437 | 5432 | Microcredit data | credit:credit_pass@microcredit_db |
| Analytics DB | 5438 | 5432 | Analytics metrics | analytics:analytics_pass@analytics_db |
| Reverse Logistics DB | 5439 | 5432 | Returns & refunds | reverse:reverse_pass@reverse_logistics_db |
| Franchise DB | 5440 | 5432 | Franchise data | franchise:franchise_pass@franchise_db |

## Shared Services

### Infrastructure Services
| Service | Host Port | Container Port | Description | Credentials |
|---------|-----------|----------------|-------------|-------------|
| Redis | 6379 | 6379 | Cache & Session Store | No auth |
| RabbitMQ | 5672 | 5672 | Message Queue (AMQP) | quenty:quenty_pass |
| RabbitMQ Management | 15672 | 15672 | RabbitMQ Web UI | quenty:quenty_pass |

### Monitoring & Management
| Service | Host Port | Container Port | Description | Credentials |
|---------|-----------|----------------|-------------|-------------|
| Consul | 8500 | 8500 | Service Discovery UI | No auth |
| Prometheus | 9090 | 9090 | Metrics Collection | No auth |
| Grafana | 3000 | 3000 | Monitoring Dashboards | admin:admin |
| Jaeger | 16686 | 16686 | Distributed Tracing UI | No auth |
| Jaeger Collector | 14268 | 14268 | Trace Collection | No auth |

## Usage Examples

### Connecting to Databases

#### Using psql command line:
```bash
# Auth Database
psql -h localhost -p 5441 -U auth -d auth_db

# Customer Database  
psql -h localhost -p 5433 -U customer -d customer_db

# Order Database
psql -h localhost -p 5434 -U order -d order_db
```

#### Using database tools (pgAdmin, DBeaver, etc.):
```
Host: localhost
Port: [see table above]
Database: [see table above]
Username: [see table above]
Password: [see table above]
```

### Connecting to Services

#### Direct API calls:
```bash
# Through API Gateway (recommended)
curl http://localhost:8000/api/v1/auth/login

# Direct service access (for debugging)
curl http://localhost:8009/health  # Auth service
curl http://localhost:8001/health  # Customer service
curl http://localhost:8002/health  # Order service
```

#### Service documentation:
```bash
# API Gateway docs (aggregated)
http://localhost:8000/docs

# Individual service docs
http://localhost:8009/docs  # Auth service
http://localhost:8001/docs  # Customer service
http://localhost:8002/docs  # Order service
```

### Monitoring Access

```bash
# RabbitMQ Management
http://localhost:15672
Username: quenty
Password: quenty_pass

# Consul Service Discovery
http://localhost:8500

# Prometheus Metrics
http://localhost:9090

# Grafana Dashboards  
http://localhost:3000
Username: admin
Password: admin

# Jaeger Tracing
http://localhost:16686
```

### Redis Access

```bash
# Redis CLI
redis-cli -h localhost -p 6379

# Redis GUI tools
Host: localhost
Port: 6379
No authentication required
```

## Security Notes

⚠️ **Warning**: These port exposures are intended for development environments only.

For production deployments:
1. **Remove direct database access** - Only allow access through services
2. **Use proper authentication** - Change default passwords
3. **Implement network security** - Use VPNs, firewalls, and network policies
4. **Limit service exposure** - Only expose the API Gateway (port 8000)
5. **Use TLS encryption** - Enable HTTPS and database encryption

## Development Workflow

### Starting Services
```bash
# Start all services with exposed ports
docker compose -f docker-compose.microservices.yml up -d

# Check service health
curl http://localhost:8000/services/health
```

### Debugging Individual Services
```bash
# Check specific service logs
docker logs quenty-auth-service
docker logs quenty-customer-service

# Access service directly for debugging
curl http://localhost:8009/health
curl http://localhost:8001/health
```

### Database Administration
```bash
# Connect to any database for debugging
psql -h localhost -p 5432 -U auth -d auth_db
psql -h localhost -p 5433 -U customer -d customer_db

# Run SQL scripts
psql -h localhost -p 5432 -U auth -d auth_db < scripts/init_companies.sql
```

## Port Conflict Resolution

If you have port conflicts, you can modify the host ports in `docker-compose.microservices.yml`:

```yaml
# Example: Change API Gateway from 8000 to 8080
api-gateway:
  ports:
    - "8080:8000"  # Host:Container

# Example: Change Auth DB from 5432 to 15432  
auth-db:
  ports:
    - "15432:5432"  # Host:Container
```

Remember to update any scripts or documentation that reference the old ports.

## Quick Reference

**Main Entry Points:**
- API Gateway: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- System Health: http://localhost:8000/services/health

**Admin Interfaces:**
- RabbitMQ: http://localhost:15672 (quenty:quenty_pass)
- Grafana: http://localhost:3000 (admin:admin)
- Consul: http://localhost:8500
- Jaeger: http://localhost:16686

**Primary Database:** localhost:5441 (auth:auth_pass@auth_db)