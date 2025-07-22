# Quenty Microservices Documentation

This documentation provides comprehensive guidance for understanding, deploying, and integrating the Quenty microservices platform adapted from quentyhub-api.

## Table of Contents

1. [Architecture Overview](./architecture-overview.md)
2. [Microservices Documentation](./microservices/)
   - [Customer Service](./microservices/customer-service.md)
   - [Order Service](./microservices/order-service.md)
   - [International Shipping Service](./microservices/international-shipping-service.md)
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
5. **Verify**: Check service health at respective ports (8001, 8002, 8004)

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| Customer Service | 8001 | User and company management |
| Order Service | 8002 | Order and inventory management |
| International Shipping | 8004 | Shipping and manifest management |

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