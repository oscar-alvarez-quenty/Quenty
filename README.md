# Quenty Platform - Enterprise Logistics & E-Commerce Solution

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Services](https://img.shields.io/badge/microservices-14-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Status](https://img.shields.io/badge/status-production--ready-success)

## 🚀 Overview

Quenty is a comprehensive enterprise-grade logistics and e-commerce platform built with a microservices architecture. It provides end-to-end solutions for order management, multi-carrier shipping, international logistics, microcredit services, and seamless integration with major e-commerce platforms.

### Key Features

- 🌐 **Multi-Carrier Integration**: DHL, FedEx, UPS, Servientrega, Interrapidisimo, Pickit
- 🛍️ **E-Commerce Platform Integration**: Shopify, MercadoLibre
- 📦 **Complete Order Management**: From creation to delivery
- 🌍 **International Shipping**: Customs management and international manifests
- 💳 **Microcredit Services**: Built-in financing options for customers  
- 🔄 **Reverse Logistics**: Returns and exchanges management
- 🏢 **Franchise Management**: Multi-location support
- 📊 **Advanced Analytics**: Real-time metrics and reporting
- 🤖 **AI-Powered Features**: RAG-based intelligent search and assistance

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Services](#-services)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Security](#-security)

## 🏗 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL CLIENTS                          │
│           (Web Apps, Mobile Apps, Partner APIs, Webhooks)           │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   NGINX Load Balancer    │
                    │      (Port 80/443)       │
                    └──────────┬───────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │             API GATEWAY                      │
        │            (Port 8080)                       │
        │     [PUBLIC - JWT Authentication]            │
        └──────────────────┬───────────────────────────┘
                           │
        ┌──────────────────┼───────────────────────────┐
        │                  │                           │
        ▼                  ▼                           ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Auth Service   │ │ Customer Service│ │  Order Service  │
│   [PRIVATE]     │ │    [PRIVATE]    │ │   [PRIVATE]     │
│  Port: 8019     │ │   Port: 8001    │ │   Port: 8002    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Microservices Architecture

The platform consists of **44 containerized services** organized into:

- **14 Business Microservices**: Core business logic
- **11 PostgreSQL Databases**: Data persistence with pgvector support
- **7 Background Workers**: Async processing with Celery
- **12 Infrastructure Services**: Supporting services

## 🔧 Services

### Core Business Services

| Service | Port | Description | Status |
|---------|------|-------------|---------|
| **API Gateway** | 8080 | Central entry point for all external requests | ✅ Active |
| **Auth Service** | 8019 | Authentication, authorization, user management | ✅ Active |
| **Customer Service** | 8001 | Customer management, support tickets | ✅ Active |
| **Order Service** | 8002 | Order processing, products, inventory | ✅ Active |
| **Pickup Service** | 8003 | Package pickup scheduling, route optimization | ✅ Active |
| **International Shipping** | 8004 | International manifests, customs management | ✅ Active |
| **Microcredit Service** | 8005 | Credit applications, payments, scoring | ✅ Active |
| **Analytics Service** | 8006 | Business metrics, reporting, dashboards | ✅ Active |
| **Reverse Logistics** | 8007 | Returns, exchanges, inspection | ✅ Active |
| **Franchise Service** | 8008 | Franchise management, territories | ✅ Active |

### Integration Services

| Service | Port | Description | Platforms |
|---------|------|-------------|-----------|
| **Carrier Integration** | 8020 | Multi-carrier logistics | DHL, FedEx, UPS, Servientrega, Interrapidisimo, Pickit |
| **Shopify Integration** | 8010 | E-commerce sync | Shopify stores |
| **MercadoLibre Integration** | 8012 | Marketplace sync | MercadoLibre Colombia |
| **RAG Service** | 8011 | AI-powered search | OpenAI, Local models |

### Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| **PostgreSQL** | 5433 | Primary database with pgvector |
| **Redis** | 6380 | Cache, session store, message broker |
| **RabbitMQ** | 5672/15672 | Message queue for async operations |
| **Consul** | 8500 | Service discovery and configuration |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Metrics visualization |
| **Jaeger** | 16686 | Distributed tracing |
| **Loki** | 3100 | Log aggregation |

## 💻 Technology Stack

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15 with pgvector
- **Cache**: Redis 7
- **Message Queue**: RabbitMQ 3
- **Task Queue**: Celery 5.3

### Infrastructure
- **Container**: Docker & Docker Compose
- **Service Discovery**: Consul
- **API Gateway**: Custom FastAPI gateway
- **Load Balancer**: Nginx
- **Monitoring**: Prometheus + Grafana
- **Tracing**: Jaeger
- **Logging**: Loki + Promtail

### Security
- **Authentication**: JWT (RS256)
- **OAuth**: Google, Facebook, Shopify, MercadoLibre
- **Encryption**: Fernet for sensitive data
- **API Security**: Rate limiting, CORS, API keys

## 🚀 Getting Started

### Prerequisites

- Docker Desktop 4.0+
- Docker Compose 2.0+
- Git
- 16GB RAM minimum
- 20GB free disk space

### Quick Start

1. **Clone the repository**
```bash
git clone git@github.com:oscar-alvarez-quenty/Quenty.git
cd Quenty
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
# Start infrastructure and business services
docker compose up -d
docker compose -f docker-compose.microservices.yml up -d
```

4. **Verify deployment**
```bash
# Check all services are running
docker ps | wc -l  # Should show 44+ containers

# Check API Gateway health
curl http://localhost:8080/health
```

5. **Access services**
- API Gateway: http://localhost:8080
- API Documentation: http://localhost:8080/docs
- Grafana Dashboard: http://localhost:3000
- RabbitMQ Management: http://localhost:15672
- PgAdmin: http://localhost:5050
- Flower (Celery): http://localhost:5555

## 📚 API Documentation

### Authentication

All API requests (except public endpoints) require JWT authentication:

```bash
# 1. Login to get token
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# 2. Use token in requests
curl http://localhost:8080/api/v1/orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Main API Endpoints

#### Authentication & Users
```
POST   /auth/register          - Register new user
POST   /auth/login             - Login
POST   /auth/refresh           - Refresh token
GET    /auth/me                - Current user info
POST   /auth/logout            - Logout
```

#### Customer Management
```
GET    /api/v1/customers       - List customers
POST   /api/v1/customers       - Create customer
GET    /api/v1/customers/{id}  - Get customer details
PUT    /api/v1/customers/{id}  - Update customer
DELETE /api/v1/customers/{id}  - Delete customer
```

#### Order Management
```
GET    /api/v1/orders          - List orders
POST   /api/v1/orders          - Create order
GET    /api/v1/orders/{id}     - Get order details
PUT    /api/v1/orders/{id}     - Update order
POST   /api/v1/orders/{id}/cancel - Cancel order
```

#### Shipping & Logistics
```
POST   /api/v1/quotes          - Get shipping quote
POST   /api/v1/labels          - Generate shipping label
POST   /api/v1/tracking        - Track shipment
POST   /api/v1/pickups         - Schedule pickup
```

#### Carrier Integration
```
GET    /api/v1/carriers        - List available carriers
POST   /api/v1/carriers/{carrier}/credentials - Save carrier credentials
GET    /api/v1/carriers/{carrier}/health - Check carrier status
```

#### E-Commerce Integration
```
# Shopify
POST   /api/v1/shopify/connect - Connect Shopify store
GET    /api/v1/shopify/products - Sync products
GET    /api/v1/shopify/orders  - Sync orders

# MercadoLibre
GET    /api/v1/mercadolibre/auth - OAuth authorization
GET    /api/v1/mercadolibre/products - List products
POST   /api/v1/mercadolibre/publish - Publish product
```

#### Analytics
```
GET    /api/v1/analytics/dashboard - Dashboard metrics
GET    /api/v1/analytics/reports   - Generate reports
GET    /api/v1/analytics/metrics   - Real-time metrics
```

### Webhook Endpoints

```
POST   /webhooks/shopify       - Shopify webhooks
POST   /webhooks/mercadolibre  - MercadoLibre notifications
POST   /webhooks/carriers      - Carrier status updates
```

## ⚙️ Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:quenty123@db:5433/quenty_db
POSTGRES_PASSWORD=quenty123

# Redis
REDIS_URL=redis://:quenty123@redis:6380/0
REDIS_PASSWORD=quenty123

# RabbitMQ
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Carrier Credentials (Optional)
DHL_API_KEY=
FEDEX_CLIENT_ID=
UPS_USERNAME=

# E-Commerce Integration (Optional)
SHOPIFY_API_KEY=
SHOPIFY_API_SECRET=
MELI_CLIENT_ID=
MELI_CLIENT_SECRET=

# OpenAI (Optional for RAG)
OPENAI_API_KEY=
```

### Service Configuration

Each microservice has its own configuration in:
- `microservices/[service-name]/config/`
- `microservices/[service-name]/.env`

## 🛠 Development

### Local Development Setup

1. **Install dependencies for a specific service**
```bash
cd microservices/order-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Run tests**
```bash
# Run all tests
pytest

# Run specific service tests
cd microservices/order-service
pytest tests/
```

3. **Code quality**
```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

### Adding a New Microservice

1. Create service directory structure:
```bash
microservices/
└── new-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── alembic.ini
    ├── alembic/
    ├── src/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── models.py
    │   ├── schemas.py
    │   ├── database.py
    │   └── routers/
    └── tests/
```

2. Add to `docker-compose.microservices.yml`
3. Configure service discovery in Consul
4. Update API Gateway routing

## 📦 Deployment

### Production Deployment

1. **Build production images**
```bash
docker compose -f docker-compose.prod.yml build
```

2. **Deploy with Docker Swarm**
```bash
docker stack deploy -c docker-compose.prod.yml quenty
```

3. **Kubernetes deployment** (coming soon)
```bash
kubectl apply -f k8s/
```

### Health Checks

All services implement health endpoints:
- `/health` - Basic health status
- `/ready` - Readiness probe
- `/metrics` - Prometheus metrics

## 📊 Monitoring

### Accessing Monitoring Tools

- **Grafana**: http://localhost:3000
  - Username: admin
  - Password: admin

- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686
- **Flower**: http://localhost:5555

### Key Metrics to Monitor

1. **Service Metrics**
   - Request rate, error rate, duration (RED)
   - Service availability
   - Database connections
   - Cache hit rates

2. **Business Metrics**
   - Orders processed
   - Shipping success rate
   - Customer satisfaction
   - Revenue metrics

3. **Infrastructure Metrics**
   - CPU/Memory usage
   - Network latency
   - Disk I/O
   - Message queue depth

## 🔒 Security

### Security Features

- **JWT Authentication**: Short-lived access tokens (30 min)
- **OAuth Integration**: Google, Facebook, Shopify, MercadoLibre
- **Rate Limiting**: API Gateway level protection
- **CORS Protection**: Configured for allowed origins
- **Data Encryption**: Fernet encryption for sensitive data
- **Network Isolation**: Private services not exposed
- **TLS/SSL**: HTTPS for all external communication

### Security Best Practices

1. **Regular Updates**: Keep all dependencies updated
2. **Secret Management**: Use environment variables, never commit secrets
3. **Access Control**: Role-based access control (RBAC)
4. **Audit Logging**: All operations logged
5. **Container Security**: Regular vulnerability scanning

## 📝 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For support and questions:
- Technical Issues: Create an issue in the repository
- Business Inquiries: contact@quenty.com
- Documentation: See `/docs` directory

## 🙏 Acknowledgments

Built with modern open-source technologies including FastAPI, PostgreSQL, Docker, and many other excellent projects.

---

**Version**: 1.0.0  
**Last Updated**: September 2025  
**Maintained by**: Quenty Platform Engineering Team