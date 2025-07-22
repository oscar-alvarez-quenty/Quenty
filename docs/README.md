# Quenty Microservices Documentation

This documentation provides comprehensive guidance for understanding, deploying, and integrating the Quenty microservices platform adapted from quentyhub-api.

## Table of Contents

1. [Architecture Overview](./architecture-overview.md)
2. [Microservices Documentation](./microservices/)
   - [Auth Service](./microservices/auth-service.md)
   - [Customer Service](./microservices/customer-service.md)
   - [Order Service](./microservices/order-service.md)
   - [Pickup Service](./microservices/pickup-service.md)
   - [International Shipping Service](./microservices/international-shipping-service.md)
   - [Microcredit Service](./microservices/microcredit-service.md)
   - [Analytics Service](./microservices/analytics-service.md)
   - [Reverse Logistics Service](./microservices/reverse-logistics-service.md)
   - [Franchise Service](./microservices/franchise-service.md)
3. [Database Documentation](./database/)
   - [Database Schema](./database/schema.md)
   - [Entity Relationship Models](./database/er-models.md)
4. [Deployment Guide](./deployment/)
   - [Docker Deployment](./deployment/docker-deployment.md)
   - [Production Deployment](./deployment/production-deployment.md)
5. [Integration Guide](./integration/)
   - [API Integration](./integration/api-integration.md)
   - [Service Communication](./integration/service-communication.md)
6. [Development Guide](./development/)
   - [Local Development](./development/local-development.md)
   - [Testing Guide](./development/testing.md)

## Quick Start

1. **Prerequisites**: Docker, Docker Compose
2. **Clone**: `git clone <repository>`
3. **Build**: `docker-compose -f docker-compose.microservices.yml build`
4. **Deploy**: `docker-compose -f docker-compose.microservices.yml up -d`
5. **Verify**: Check service health via API Gateway at http://localhost:8000/health

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Request routing and rate limiting |
| Customer Service | 8001 | User and company management |
| Order Service | 8002 | Order and inventory management |
| Pickup Service | 8003 | Pickup scheduling and logistics |
| International Shipping | 8004 | Shipping and manifest management |
| Microcredit Service | 8005 | Financial services and credit management |
| Analytics Service | 8006 | Business intelligence and metrics |
| Reverse Logistics Service | 8007 | Returns and reverse logistics |
| Franchise Service | 8008 | Franchise management and territories |
| Auth Service | 8009 | Authentication and authorization |

## Key Features

- ✅ **Microservices Architecture**: Modular, scalable design
- ✅ **Database Per Service**: Independent data storage
- ✅ **API Gateway**: Centralized routing and authentication
- ✅ **Service Discovery**: Consul-based service registration
- ✅ **Monitoring**: Prometheus + Grafana observability
- ✅ **Distributed Tracing**: Jaeger integration
- ✅ **Message Queue**: RabbitMQ for async communication

## Technology Stack

- **Runtime**: Python 3.11, FastAPI, Uvicorn
- **Database**: PostgreSQL with AsyncPG
- **ORM**: SQLAlchemy with async support
- **Migration**: Alembic
- **Caching**: Redis
- **Containerization**: Docker & Docker Compose
- **Service Discovery**: Consul
- **Monitoring**: Prometheus, Grafana, Jaeger
- **Message Queue**: RabbitMQ
- **Load Balancer**: Nginx

## Support

For questions and support, refer to the specific documentation sections or check the troubleshooting guide in the deployment section.