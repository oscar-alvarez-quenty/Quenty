# Docker Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Quenty microservices platform using Docker and Docker Compose. The platform is designed to run efficiently in containerized environments with full orchestration support.

## Prerequisites

### System Requirements
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **System Memory**: Minimum 8GB RAM recommended
- **Disk Space**: Minimum 20GB free space
- **CPU**: Multi-core processor recommended

### Software Dependencies
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Quick Start Deployment

### 1. Clone Repository
```bash
git clone <repository-url>
cd Quenty
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Build and Deploy
```bash
# Build all services
docker-compose -f docker-compose.microservices.yml build

# Deploy all services
docker-compose -f docker-compose.microservices.yml up -d

# Verify deployment
docker-compose -f docker-compose.microservices.yml ps
```

### 4. Health Check
```bash
# Check service health
curl http://localhost:8001/health  # Customer Service
curl http://localhost:8002/health  # Order Service
curl http://localhost:8004/health  # International Shipping Service
```

## Architecture Overview

### Container Network Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Host                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Nginx         │    │  API Gateway    │    │  Web UI      │ │
│  │   Port: 80,443  │    │   Port: 8000    │    │ Port: 3000   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                     │       │
│  ┌────────┴───────────────────────┴─────────────────────┴────┐  │
│  │                 quenty-network (bridge)                   │  │
│  └─────────────────────────────────────────────────────────────┘ │
│    │                │                │                │         │
│  ┌─┴────┐    ┌──────┴─────┐    ┌────┴────┐    ┌───────┴──────┐  │
│  │Customer│    │   Order    │    │Shipping │    │   Other      │  │
│  │Service │    │  Service   │    │Service  │    │  Services    │  │
│  │:8001   │    │   :8002    │    │  :8004  │    │   :800X      │  │
│  └─┬──────┘    └──────┬─────┘    └────┬────┘    └───────┬──────┘  │
│    │                  │               │                 │         │
│  ┌─┴────┐    ┌───────┴──────┐   ┌────┴────┐    ┌───────┴──────┐  │
│  │Cust  │    │   Order      │   │Shipping │    │   Other      │  │
│  │DB    │    │    DB        │   │   DB    │    │    DBs       │  │
│  │:5432 │    │   :5432      │   │  :5432  │    │   :5432      │  │
│  └──────┘    └──────────────┘   └─────────┘    └──────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               Shared Infrastructure                         │ │
│  │  Redis    RabbitMQ   Consul   Prometheus  Grafana  Jaeger  │ │
│  │  :6379     :5672     :8500      :9090     :3000   :16686  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Service Configuration

### Docker Compose Files Structure
```
├── docker-compose.microservices.yml    # Main services
├── docker-compose.infrastructure.yml   # Infrastructure only
├── docker-compose.monitoring.yml       # Monitoring stack
├── docker-compose.development.yml      # Development overrides
└── docker-compose.production.yml       # Production overrides
```

### Core Services Configuration

#### Customer Service
```yaml
customer-service:
  build:
    context: ./microservices/customer
    dockerfile: Dockerfile
  container_name: quenty-customer-service
  environment:
    - SERVICE_NAME=customer-service
    - DATABASE_URL=postgresql+asyncpg://customer:customer_pass@customer-db:5432/customer_db
    - REDIS_URL=redis://redis:6379/1
    - LOG_LEVEL=INFO
  ports:
    - "8001:8001"
  depends_on:
    - customer-db
    - redis
  networks:
    - quenty-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

#### Order Service
```yaml
order-service:
  build:
    context: ./microservices/order
    dockerfile: Dockerfile
  container_name: quenty-order-service
  environment:
    - SERVICE_NAME=order-service
    - DATABASE_URL=postgresql+asyncpg://order:order_pass@order-db:5432/order_db
    - REDIS_URL=redis://redis:6379/2
    - LOG_LEVEL=INFO
    - CUSTOMER_SERVICE_URL=http://customer-service:8001
  ports:
    - "8002:8002"
  depends_on:
    - order-db
    - redis
    - customer-service
  networks:
    - quenty-network
  restart: unless-stopped
```

#### International Shipping Service
```yaml
international-shipping-service:
  build:
    context: ./microservices/international-shipping
    dockerfile: Dockerfile
  container_name: quenty-intl-shipping-service
  environment:
    - SERVICE_NAME=international-shipping-service
    - DATABASE_URL=postgresql+asyncpg://intlship:intlship_pass@intl-shipping-db:5432/intl_shipping_db
    - REDIS_URL=redis://redis:6379/4
    - LOG_LEVEL=INFO
    - CUSTOMER_SERVICE_URL=http://customer-service:8001
  ports:
    - "8004:8004"
  depends_on:
    - intl-shipping-db
    - redis
    - customer-service
  networks:
    - quenty-network
  restart: unless-stopped
```

### Database Configuration

#### PostgreSQL Services
```yaml
customer-db:
  image: postgres:15-alpine
  container_name: quenty-customer-db
  environment:
    - POSTGRES_USER=customer
    - POSTGRES_PASSWORD=customer_pass
    - POSTGRES_DB=customer_db
  volumes:
    - customer-db-data:/var/lib/postgresql/data
    - ./docker/postgres/init-customer-db.sql:/docker-entrypoint-initdb.d/init.sql
  networks:
    - quenty-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U customer -d customer_db"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Infrastructure Services

#### Redis Cache
```yaml
redis:
  image: redis:7-alpine
  container_name: quenty-redis
  command: redis-server --appendonly yes --requirepass redis_password
  volumes:
    - redis-data:/data
    - ./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf
  networks:
    - quenty-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

#### RabbitMQ Message Queue
```yaml
rabbitmq:
  image: rabbitmq:3-management-alpine
  container_name: quenty-rabbitmq
  environment:
    - RABBITMQ_DEFAULT_USER=quenty
    - RABBITMQ_DEFAULT_PASS=quenty_pass
    - RABBITMQ_DEFAULT_VHOST=quenty_vhost
  volumes:
    - rabbitmq-data:/var/lib/rabbitmq
    - ./docker/rabbitmq/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
  ports:
    - "15672:15672"  # Management UI
    - "5672:5672"    # AMQP
  networks:
    - quenty-network
  restart: unless-stopped
```

#### Service Discovery (Consul)
```yaml
consul:
  image: consul:1.15
  container_name: quenty-consul
  command: agent -server -bootstrap-expect=1 -ui -client=0.0.0.0 -datacenter=dc1
  volumes:
    - consul-data:/consul/data
    - ./docker/consul/consul.json:/consul/config/consul.json
  ports:
    - "8500:8500"
  networks:
    - quenty-network
  restart: unless-stopped
```

### Monitoring Stack

#### Prometheus
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: quenty-prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.console.libraries=/etc/prometheus/console_libraries'
    - '--web.console.templates=/etc/prometheus/consoles'
    - '--storage.tsdb.retention.time=200h'
    - '--web.enable-lifecycle'
  volumes:
    - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus-data:/prometheus
  ports:
    - "9090:9090"
  networks:
    - quenty-network
  restart: unless-stopped
```

#### Grafana
```yaml
grafana:
  image: grafana/grafana:latest
  container_name: quenty-grafana
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
    - GF_USERS_ALLOW_SIGN_UP=false
  volumes:
    - grafana-data:/var/lib/grafana
    - ./docker/grafana/provisioning:/etc/grafana/provisioning
    - ./docker/grafana/dashboards:/var/lib/grafana/dashboards
  ports:
    - "3000:3000"
  depends_on:
    - prometheus
  networks:
    - quenty-network
  restart: unless-stopped
```

### Load Balancer (Nginx)
```yaml
nginx:
  image: nginx:alpine
  container_name: quenty-nginx
  volumes:
    - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
    - ./docker/nginx/ssl:/etc/nginx/ssl
  ports:
    - "80:80"
    - "443:443"
  depends_on:
    - api-gateway
  networks:
    - quenty-network
  restart: unless-stopped
```

## Environment Configuration

### Environment Variables File (.env)
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
POSTGRES_PASSWORD=secure_postgres_password
CUSTOMER_DB_PASSWORD=secure_customer_password
ORDER_DB_PASSWORD=secure_order_password
SHIPPING_DB_PASSWORD=secure_shipping_password

# Redis
REDIS_PASSWORD=secure_redis_password

# RabbitMQ
RABBITMQ_USER=quenty
RABBITMQ_PASSWORD=secure_rabbitmq_password

# External APIs
DHL_API_KEY=your_dhl_api_key
FEDEX_API_KEY=your_fedex_api_key
UPS_API_KEY=your_ups_api_key

# JWT
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=3600

# Monitoring
GRAFANA_PASSWORD=secure_grafana_password
```

### Service-Specific Configuration

#### Customer Service (.env.customer)
```bash
SERVICE_NAME=customer-service
DATABASE_URL=postgresql+asyncpg://customer:${CUSTOMER_DB_PASSWORD}@customer-db:5432/customer_db
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CONSUL_HOST=consul
CONSUL_PORT=8500
```

#### Order Service (.env.order)
```bash
SERVICE_NAME=order-service
DATABASE_URL=postgresql+asyncpg://order:${ORDER_DB_PASSWORD}@order-db:5432/order_db
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/2
CUSTOMER_SERVICE_URL=http://customer-service:8001
SHIPPING_SERVICE_URL=http://international-shipping-service:8004
```

## Deployment Commands

### Development Deployment
```bash
# Build development images
docker-compose -f docker-compose.microservices.yml -f docker-compose.development.yml build

# Start development environment
docker-compose -f docker-compose.microservices.yml -f docker-compose.development.yml up -d

# View logs
docker-compose -f docker-compose.microservices.yml logs -f
```

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.microservices.yml -f docker-compose.production.yml build

# Start production environment
docker-compose -f docker-compose.microservices.yml -f docker-compose.production.yml up -d

# Verify deployment
docker-compose -f docker-compose.microservices.yml ps
```

### Staged Deployment
```bash
# Deploy infrastructure first
docker-compose -f docker-compose.infrastructure.yml up -d

# Wait for infrastructure to be ready
sleep 30

# Deploy core services
docker-compose -f docker-compose.microservices.yml up -d customer-service order-service international-shipping-service

# Deploy additional services
docker-compose -f docker-compose.microservices.yml up -d
```

### Selective Service Deployment
```bash
# Deploy only specific services
docker-compose -f docker-compose.microservices.yml up -d customer-service customer-db redis

# Scale specific services
docker-compose -f docker-compose.microservices.yml up -d --scale customer-service=3
```

## Database Initialization

### Database Migration
```bash
# Run migrations for all services
docker-compose -f docker-compose.microservices.yml exec customer-service alembic upgrade head
docker-compose -f docker-compose.microservices.yml exec order-service alembic upgrade head
docker-compose -f docker-compose.microservices.yml exec international-shipping-service alembic upgrade head
```

### Seed Data
```bash
# Load initial data
docker-compose -f docker-compose.microservices.yml exec customer-service python scripts/seed_data.py
docker-compose -f docker-compose.microservices.yml exec order-service python scripts/seed_products.py
```

## Monitoring and Health Checks

### Service Health Monitoring
```bash
# Check all service health
./scripts/health-check.sh

# Individual service health
curl http://localhost:8001/health  # Customer Service
curl http://localhost:8002/health  # Order Service
curl http://localhost:8004/health  # International Shipping
```

### Container Resource Monitoring
```bash
# Monitor container resource usage
docker stats

# View container logs
docker-compose -f docker-compose.microservices.yml logs -f customer-service

# Check container processes
docker-compose -f docker-compose.microservices.yml top
```

### Database Health Checks
```bash
# Check database connectivity
docker-compose -f docker-compose.microservices.yml exec customer-db pg_isready -U customer -d customer_db
docker-compose -f docker-compose.microservices.yml exec order-db pg_isready -U order -d order_db
```

## Backup and Recovery

### Database Backups
```bash
# Create database backups
docker-compose -f docker-compose.microservices.yml exec customer-db pg_dump -U customer customer_db > backup_customer_$(date +%Y%m%d).sql
docker-compose -f docker-compose.microservices.yml exec order-db pg_dump -U order order_db > backup_order_$(date +%Y%m%d).sql

# Automated backup script
./scripts/backup-databases.sh
```

### Data Volume Backups
```bash
# Backup Docker volumes
docker run --rm -v quenty_customer-db-data:/data -v $(pwd):/backup alpine tar czf /backup/customer-db-backup.tar.gz -C /data .
docker run --rm -v quenty_redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .
```

### Recovery Procedures
```bash
# Restore database from backup
docker-compose -f docker-compose.microservices.yml exec -T customer-db psql -U customer -d customer_db < backup_customer_20250722.sql

# Restore volume from backup
docker run --rm -v quenty_customer-db-data:/data -v $(pwd):/backup alpine tar xzf /backup/customer-db-backup.tar.gz -C /data
```

## Performance Optimization

### Resource Limits
```yaml
# Add to service definitions
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Database Optimization
```bash
# Optimize PostgreSQL settings
echo "shared_preload_libraries = 'pg_stat_statements'" >> docker/postgres/postgresql.conf
echo "max_connections = 200" >> docker/postgres/postgresql.conf
echo "shared_buffers = 256MB" >> docker/postgres/postgresql.conf
```

### Redis Optimization
```bash
# Redis configuration
echo "maxmemory 512mb" >> docker/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> docker/redis/redis.conf
```

## Security Configuration

### Network Security
```yaml
networks:
  quenty-network:
    driver: bridge
    driver_opts:
      com.docker.network.enable_ipv6: "false"
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
```

### SSL/TLS Configuration
```bash
# Generate SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/quenty.key \
  -out docker/nginx/ssl/quenty.crt
```

### Secret Management
```bash
# Use Docker secrets for sensitive data
echo "your_secret" | docker secret create db_password -
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check container logs
docker-compose -f docker-compose.microservices.yml logs customer-service

# Check container status
docker-compose -f docker-compose.microservices.yml ps

# Restart specific service
docker-compose -f docker-compose.microservices.yml restart customer-service
```

#### Database Connection Issues
```bash
# Check database container
docker-compose -f docker-compose.microservices.yml exec customer-db psql -U customer -d customer_db -c "SELECT 1;"

# Check network connectivity
docker-compose -f docker-compose.microservices.yml exec customer-service ping customer-db
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check system resources
free -h
df -h

# Optimize container resources
docker-compose -f docker-compose.microservices.yml up -d --scale customer-service=2
```

### Debugging Commands
```bash
# Execute commands in running containers
docker-compose -f docker-compose.microservices.yml exec customer-service bash

# View container filesystem
docker-compose -f docker-compose.microservices.yml exec customer-service ls -la /app

# Check environment variables
docker-compose -f docker-compose.microservices.yml exec customer-service env
```

## Maintenance Tasks

### Updates and Upgrades
```bash
# Update base images
docker-compose -f docker-compose.microservices.yml pull

# Rebuild with latest changes
docker-compose -f docker-compose.microservices.yml build --no-cache

# Rolling update
docker-compose -f docker-compose.microservices.yml up -d --force-recreate --no-deps customer-service
```

### Cleanup Tasks
```bash
# Remove unused containers
docker container prune -f

# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Complete cleanup
docker system prune -af
```

### Log Management
```bash
# Configure log rotation
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' > /etc/docker/daemon.json
systemctl restart docker

# View and manage logs
docker-compose -f docker-compose.microservices.yml logs --tail=100 customer-service
```