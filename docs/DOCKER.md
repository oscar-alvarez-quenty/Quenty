# Docker Setup for Quenty Logistics Platform

This document provides instructions for running the Quenty application using Docker containers.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB of available RAM
- At least 10GB of available disk space

## Quick Start

### Development Environment

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd Quenty/DDD
   cp .env.example .env
   # Edit .env file with your local settings
   ```

2. **Start the development environment**:
   ```bash
   docker-compose up -d
   ```

3. **Initialize the database**:
   ```bash
   # Run database migrations
   docker-compose exec app alembic upgrade head
   
   # Optional: Load sample data
   docker-compose exec app python scripts/load_sample_data.py
   ```

4. **Access the application**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

### Production Environment

1. **Setup production environment**:
   ```bash
   cp .env.prod .env
   # Edit .env file with secure production values
   ```

2. **Deploy with production compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Services Overview

### Core Services

- **app**: FastAPI application server
- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **nginx**: Reverse proxy and load balancer

### Monitoring Stack

- **prometheus**: Metrics collection
- **grafana**: Metrics visualization
- **node-exporter**: System metrics
- **postgres-exporter**: PostgreSQL metrics
- **redis-exporter**: Redis metrics

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db
POSTGRES_USER=quenty_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# Application
DEBUG=false
SECRET_KEY=your-secure-secret-key
LOG_LEVEL=INFO
```

### Service Configuration

Service configurations are located in the `docker/` directory:

- `docker/postgres/`: PostgreSQL configuration and init scripts
- `docker/redis/`: Redis configuration
- `docker/nginx/`: Nginx configuration
- `docker/prometheus/`: Prometheus configuration and alert rules
- `docker/grafana/`: Grafana dashboards and datasources

## Development Workflow

### Running Tests

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=src --cov-report=html

# Run specific test file
docker-compose exec app pytest tests/test_customer.py
```

### Database Operations

```bash
# Create new migration
docker-compose exec app alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec app alembic upgrade head

# Rollback migration
docker-compose exec app alembic downgrade -1

# Reset database
docker-compose exec app alembic downgrade base
docker-compose exec app alembic upgrade head
```

### Logs and Debugging

```bash
# View application logs
docker-compose logs -f app

# View all services logs
docker-compose logs -f

# Execute shell in app container
docker-compose exec app bash

# Connect to PostgreSQL
docker-compose exec postgres psql -U quenty_user -d quenty_db

# Connect to Redis
docker-compose exec redis redis-cli
```

## Performance and Scaling

### Production Scaling

The production compose file includes scaling configuration:

```bash
# Scale application instances
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# Monitor resource usage
docker stats
```

### Resource Limits

Default resource limits are configured in `docker-compose.prod.yml`:

- **app**: 1GB RAM, 1 CPU
- **postgres**: 2GB RAM, 2 CPU
- **redis**: 512MB RAM, 0.5 CPU

### Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# View health check logs
docker inspect quenty_app_1 | grep -A 10 Health
```

## Monitoring and Alerting

### Grafana Dashboards

Pre-configured dashboards available:

1. **Quenty Overview**: Application metrics and performance
2. **System Metrics**: Server resource utilization
3. **Database Metrics**: PostgreSQL performance

### Prometheus Alerts

Configured alerts for:

- Application downtime
- High response times
- Database connectivity
- System resource exhaustion

### Accessing Monitoring

```bash
# Grafana (admin/admin)
http://localhost:3000

# Prometheus
http://localhost:9090

# View alert status
curl http://localhost:9090/api/v1/alerts
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   # Check port usage
   netstat -tulpn | grep :8000
   
   # Change ports in docker-compose.yml if needed
   ```

2. **Database Connection Issues**:
   ```bash
   # Check PostgreSQL container
   docker-compose logs postgres
   
   # Test connection
   docker-compose exec app python -c "from src.infrastructure.database import engine; print('OK')"
   ```

3. **Memory Issues**:
   ```bash
   # Check container memory usage
   docker stats
   
   # Increase limits in docker-compose.yml
   ```

### Reset Everything

```bash
# Stop and remove all containers
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Start fresh
docker-compose up -d --build
```

## Security Considerations

### Production Security

1. **Change all default passwords** in `.env.prod`
2. **Use secrets management** for sensitive data
3. **Enable SSL/TLS** with proper certificates
4. **Configure firewall** to restrict access
5. **Regular security updates** of base images

### Container Security

- All containers run as non-root users
- Minimal base images (alpine/slim)
- Read-only file systems where possible
- Security scanning with `docker scan`

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U quenty_user quenty_db > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U quenty_user quenty_db < backup.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v quenty_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volumes
docker run --rm -v quenty_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## Support

For issues and questions:

1. Check the logs: `docker-compose logs`
2. Review this documentation
3. Check the application health endpoints
4. Consult the API documentation at `/docs`