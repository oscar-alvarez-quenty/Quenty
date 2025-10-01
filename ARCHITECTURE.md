# Quenty Platform - Microservices Architecture Document

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Service Catalog](#service-catalog)
4. [Authentication & Security](#authentication--security)
5. [Network Architecture](#network-architecture)
6. [Data Architecture](#data-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Monitoring & Observability](#monitoring--observability)

---

## Executive Summary

Quenty is a comprehensive logistics and e-commerce platform built using a microservices architecture. The platform consists of 15 core microservices, 14 PostgreSQL databases, and a robust infrastructure stack for monitoring, messaging, and service coordination.

### Key Statistics
- **Total Services**: 15 business microservices + 7 infrastructure services
- **Total Containers**: 45+ running containers in production
- **Databases**: 14 PostgreSQL instances (including pgvector support)
- **API Endpoints**: 200+ REST endpoints across all services
- **Authentication**: JWT-based with OAuth integration (Google, Shopify, MercadoLibre, WooCommerce)
- **API Gateway**: Centralized entry point for all external requests
- **Carriers Integrated**: 10 (DHL, FedEx, UPS, Servientrega, InterRapidisimo, Coordinadora, Deprisa, Pickit, Pasarex, Aeropost)

---

## Architecture Overview

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

---

## Service Catalog

### Core Business Services

| Service | Port | Access | Purpose | Authentication |
|---------|------|--------|---------|----------------|
| **API Gateway** | 8080 | PUBLIC | Central entry point, request routing, auth forwarding | JWT forwarding |
| **Auth Service** | 8019 | PRIVATE | Authentication, authorization, user management | Self-validating JWT |
| **Customer Service** | 8001 | PRIVATE | Customer management, support tickets | JWT via Auth Service |
| **Order Service** | 8002 | PRIVATE | Orders, products, inventory management | JWT via Auth Service |
| **Pickup Service** | 8003 | PRIVATE | Package pickup scheduling, route management | JWT via Auth Service |
| **International Shipping** | 8004 | PRIVATE | International manifests, shipping rates | JWT via Auth Service |
| **Microcredit Service** | 8005 | PRIVATE | Credit applications, payments, scoring | JWT via Auth Service |
| **Analytics Service** | 8006 | PRIVATE | Business metrics, reporting, dashboards | JWT via Auth Service |
| **Reverse Logistics** | 8007 | PRIVATE | Returns, exchanges, inspection | JWT via Auth Service |
| **Franchise Service** | 8008 | PRIVATE | Franchise management, territories | JWT via Auth Service |

### Integration Services

| Service | Port | Access | Purpose | Authentication |
|---------|------|--------|---------|----------------|
| **Carrier Integration** | 8009/8020 | PRIVATE | Multi-carrier logistics integration (10 carriers) | Rate limiting, webhook auth |
| **Shopify Integration** | 8010 | PRIVATE | Shopify marketplace sync | Shopify OAuth |
| **MercadoLibre Integration** | 8012 | PRIVATE | MercadoLibre marketplace sync | MercadoLibre OAuth |
| **WooCommerce Integration** | 8013 | PRIVATE | WooCommerce store integration | WooCommerce API Keys |
| **RAG Service** | 8011 | PRIVATE | AI-powered chat and search (pgvector) | Internal only |

### Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| **PostgreSQL (Main)** | 5433 | Primary database with pgvector |
| **Redis** | 6380 | Cache, session store, message broker |
| **RabbitMQ** | 5672/15672 | Message queue for async operations |
| **Consul** | 8500 | Service discovery and configuration |
| **Nginx** | 80/443 | Load balancer and reverse proxy |
| **Flower** | 5555 | Celery task monitoring |
| **PgAdmin** | 5050 | Database administration |

---

## Authentication & Security

### Authentication Flow

```
1. Client → API Gateway → Auth Service → JWT Token
2. Client → API Gateway (with JWT) → Target Service
3. Target Service → Auth Service (validate JWT) → Response
```

### Security Levels

#### PUBLIC Services (External Access)
- **API Gateway Only**: All external traffic must go through the API Gateway
- **Authentication Required**: JWT tokens for all protected endpoints
- **Rate Limiting**: Applied at gateway level
- **CORS Protection**: Configured for allowed origins

#### PRIVATE Services (Internal Only)
- **Network Isolation**: Services communicate via internal Docker network
- **Service-to-Service Auth**: Internal JWT validation
- **No Direct External Access**: Only accessible through API Gateway
- **Encrypted Credentials**: Fernet encryption for sensitive data

### Authentication Methods

1. **JWT Authentication**
   - Primary authentication method
   - 30-minute access tokens
   - 7-day refresh tokens
   - Role-based access control (RBAC)

2. **OAuth Integration**
   - Google OAuth
   - Facebook OAuth
   - Shopify OAuth (for merchants)
   - MercadoLibre OAuth (for sellers)

3. **API Keys**
   - Carrier integrations
   - Webhook endpoints
   - Partner APIs

---

## Network Architecture

### Network Topology

```yaml
Networks:
  quenty-network:
    - Internal service communication
    - Docker bridge network
    - Service discovery via Consul
    
External Ports:
  - 80/443: Nginx (HTTPS/SSL)
  - 8080: API Gateway
  - 5433: PostgreSQL (development only)
  - 6380: Redis (development only)
  - 5555: Flower UI
  - 5050: PgAdmin UI
```

### Service Communication Patterns

1. **Synchronous (HTTP/REST)**
   - Service-to-service API calls
   - Request/Response pattern
   - Circuit breaker for resilience

2. **Asynchronous (Message Queue)**
   - RabbitMQ for event-driven communication
   - Celery for background tasks
   - Redis pub/sub for real-time updates

3. **Service Discovery**
   - Consul for dynamic service registration
   - Health checks for service availability
   - Load balancing across instances

---

## Data Architecture

### Database Distribution

| Database | Service | Port | Purpose | Tables |
|----------|---------|------|---------|--------|
| quenty_db | Main App | 5433 | Core platform data (pgvector enabled) | Legacy monolith data |
| auth_db | Auth Service | 5441 | Users, roles, permissions | 5 tables |
| customer_db | Customer Service | 5433 | Customer data, support tickets | 4 tables |
| order_db | Order Service | 5434 | Orders, products, inventory | 6 tables |
| pickup_db | Pickup Service | 5435 | Pickup schedules, routes | 5 tables |
| intl_shipping_db | International Shipping | 5436 | Manifests, shipping data | 12 tables |
| microcredit_db | Microcredit | 5437 | Credit applications, payments | 6 tables |
| analytics_db | Analytics | 5438 | Metrics, reports, dashboards | 3 tables |
| reverse_logistics_db | Reverse Logistics | 5439 | Returns, exchanges | 5 tables |
| franchise_db | Franchise | 5440 | Franchise data, territories | 4 tables |
| carrier_db | Carrier Integration | 5442 | Carrier credentials, rates | 8 tables |
| shopify_db | Shopify Integration | 5443 | Shopify stores, orders, products | 6 tables |
| meli_db | MercadoLibre Integration | 5444 | MercadoLibre orders, products | 5 tables |
| rag_db | RAG Service | 5445 | Documents, embeddings (pgvector) | 3 tables |
| woocommerce_db | WooCommerce Integration | 5446 | WooCommerce stores, orders | 11 tables |

**Total:** 14 databases, ~90 tables

### Data Patterns

1. **Database per Service**: Each service owns its data
2. **Event Sourcing**: Analytics service consumes events
3. **CQRS**: Separate read models for analytics
4. **Data Synchronization**: Background jobs for data sync

---

## Deployment Architecture

### Container Orchestration

```yaml
Deployment Strategy:
  - Docker Compose for development/staging
  - 44 containers in production
  - Health checks for all services
  - Automatic restart policies
  
Resource Allocation:
  - CPU limits per service
  - Memory limits configured
  - Volume mounts for persistence
  - Network isolation
```

### Service Dependencies

```
API Gateway
    ├── Auth Service (required)
    ├── Customer Service
    ├── Order Service
    ├── Pickup Service
    ├── International Shipping
    ├── Microcredit Service
    ├── Analytics Service
    ├── Reverse Logistics
    └── Franchise Service

Background Workers (Celery)
    ├── Carrier Integration Worker
    ├── Shopify Integration Worker
    └── MercadoLibre Integration Worker
```

### Scaling Strategy

1. **Horizontal Scaling**
   - API Gateway: Multiple instances behind Nginx
   - Service replicas for high-traffic services
   - Database read replicas for analytics

2. **Vertical Scaling**
   - Resource limits adjustment
   - Database performance tuning
   - Cache optimization

---

## Monitoring & Observability

### Monitoring Stack

| Component | Port | Purpose |
|-----------|------|---------|
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Dashboards and visualization |
| **Jaeger** | 16686 | Distributed tracing |
| **Loki** | 3100 | Log aggregation |
| **Promtail** | - | Log collection |

### Key Metrics

1. **Service Metrics**
   - Request rate, error rate, duration (RED)
   - Service availability (uptime)
   - Database connection pools
   - Cache hit rates

2. **Business Metrics**
   - Orders processed
   - Pickup success rate
   - Customer satisfaction scores
   - Revenue analytics

3. **Infrastructure Metrics**
   - Container resource usage
   - Network latency
   - Database performance
   - Message queue depth

### Health Checks

All services implement health check endpoints:
- `/health` - Basic health status
- `/metrics` - Prometheus metrics
- `/ready` - Readiness probe

---

## Security Recommendations

### Access Control Matrix

| Service | External Access | Internal Access | Authentication Required |
|---------|----------------|-----------------|------------------------|
| API Gateway | ✅ Yes | ✅ Yes | JWT for protected routes |
| Auth Service | ❌ No | ✅ Yes | Self-validating |
| Business Services | ❌ No | ✅ Yes | JWT validation |
| Integration Services | ❌ No | ✅ Yes | OAuth + Internal JWT |
| Infrastructure | ❌ No | ✅ Yes | Admin credentials |

### Security Best Practices

1. **Network Security**
   - All PRIVATE services behind firewall
   - Only API Gateway exposed publicly
   - TLS/SSL for all external communication
   - Network segmentation via Docker networks

2. **Authentication Security**
   - JWT tokens with short expiration
   - Refresh token rotation
   - Rate limiting on auth endpoints
   - Account lockout policies

3. **Data Security**
   - Encryption at rest (database)
   - Encryption in transit (TLS)
   - Fernet encryption for credentials
   - PII data anonymization

4. **Operational Security**
   - Regular security updates
   - Container vulnerability scanning
   - Audit logging for all operations
   - Incident response procedures

---

## Disaster Recovery

### Backup Strategy
- Daily database backups
- Configuration backups (Consul)
- Docker image registry
- Volume snapshots

### Recovery Procedures
- RTO: 4 hours
- RPO: 24 hours
- Automated failover for critical services
- Manual intervention for data recovery

---

## Future Enhancements

1. **Kubernetes Migration**
   - Container orchestration improvement
   - Auto-scaling capabilities
   - Multi-region deployment

2. **Service Mesh (Istio)**
   - Advanced traffic management
   - Enhanced security policies
   - Observability improvements

3. **API Gateway Enhancements**
   - GraphQL federation
   - WebSocket support
   - Advanced rate limiting

4. **Additional Services**
   - Notification service
   - Payment processing service
   - Real-time tracking service
   - Mobile backend service

---

## Appendix

### Service URLs (Development)

| Service | Internal URL | External URL |
|---------|-------------|--------------|
| API Gateway | http://api-gateway:8000 | http://localhost:8080 |
| Auth Service | http://auth-service:8009 | N/A (Private) |
| Customer Service | http://customer-service:8001 | N/A (Private) |
| Order Service | http://order-service:8002 | N/A (Private) |
| Grafana Dashboard | http://grafana:3000 | http://localhost:3000 |
| PgAdmin | http://pgadmin:80 | http://localhost:5050 |

### Environment Variables

Critical environment variables for deployment:
- `JWT_SECRET_KEY`: JWT signing key
- `DATABASE_URL`: Database connections
- `REDIS_URL`: Redis connection
- `RABBITMQ_URL`: RabbitMQ connection
- `ENCRYPTION_KEY`: Fernet encryption key
- `OAUTH_CLIENT_ID/SECRET`: OAuth credentials

---

---

## API Gateway Endpoints

The API Gateway provides **200+ endpoints** organized by service:

### Core Business Services (140+ endpoints)
- **Auth Service**: `/api/v1/auth/*` - Login, register, OAuth, user management
- **Customer Service**: `/api/v1/customers/*` - Customer CRUD, support tickets, analytics
- **Order Service**: `/api/v1/orders/*`, `/api/v1/products/*`, `/api/v1/inventory/*`
- **Pickup Service**: `/api/v1/pickups/*`, `/api/v1/routes/*` - Pickup scheduling, route management
- **International Shipping**: `/api/v1/manifests/*`, `/api/v1/rates/*`, `/api/v1/catalogs/*`, `/api/v1/client-ratebook/*`
- **Microcredit Service**: `/api/v1/microcredit/*` - Applications, accounts, payments, credit scores
- **Analytics Service**: `/api/v1/analytics/*` - Dashboards, metrics, reports, trends
- **Reverse Logistics**: `/api/v1/returns/*` - Returns, inspections, refunds
- **Franchise Service**: `/api/v1/franchises/*`, `/api/v1/territories/*` - Franchise management

### Integration Services (60+ endpoints)
- **Carrier Integration**: `/api/v1/carrier/*` - Quotes, labels, tracking, credentials, mailboxes
- **Shopify Integration**: `/api/v1/shopify/*` - Store management, order/product sync, webhooks
- **MercadoLibre Integration**: `/api/v1/mercadolibre/*` - OAuth, orders, products, questions
- **WooCommerce Integration**: `/api/v1/woocommerce/*` - Store connections, order/product sync
- **RAG Service**: `/api/v1/rag/*` - Chat, document ingestion, semantic search

See `microservices/api-gateway/src/main.py` for complete endpoint definitions.

---

## Carrier Integration Details

### Supported Carriers (10 Total)

#### International Carriers
1. **DHL Express** - Global express shipping
   - Status: ✅ Active (Sandbox credentials configured)
   - Services: EXPRESS, ECONOMY, DOMESTIC

2. **FedEx** - International logistics
   - Status: ⚠️ Credentials needed
   - Services: INTERNATIONAL_PRIORITY, INTERNATIONAL_ECONOMY

3. **UPS** - Worldwide shipping
   - Status: ⚠️ Credentials needed
   - Services: EXPRESS, EXPEDITED, STANDARD

#### Colombian Domestic Carriers
4. **Servientrega** - Colombian nationwide
5. **InterRapidisimo** - Express delivery
6. **Coordinadora** - General cargo
7. **Deprisa** - Express and package delivery

#### Specialized Services
8. **Pickit** - Pickup point network (500+ locations in Colombia)
9. **Pasarex** - International mailbox service (US addresses for Colombians)
10. **Aeropost** - International mailbox service (Miami addresses)

### Carrier Integration Architecture

```
┌─────────────────────────────────────────────────┐
│     Carrier Integration Service (Port 8009)     │
│  ┌───────────────────────────────────────────┐  │
│  │  FastAPI App                              │  │
│  │  - Quote comparison                       │  │
│  │  - Label generation                       │  │
│  │  - Tracking                               │  │
│  │  - Webhook processing                     │  │
│  └───────────────┬───────────────────────────┘  │
│                  │                               │
│  ┌───────────────▼───────────────────────────┐  │
│  │  Celery Workers (Port 8020)               │  │
│  │  - Async quote requests                   │  │
│  │  - Batch tracking updates                 │  │
│  │  - Exchange rate sync (Banco República)   │  │
│  │  - Webhook event processing               │  │
│  └───────────────┬───────────────────────────┘  │
│                  │                               │
│  ┌───────────────▼───────────────────────────┐  │
│  │  PostgreSQL (carrier_db)                  │  │
│  │  - Encrypted credentials (AES-256)        │  │
│  │  - Shipments & tracking events            │  │
│  │  - Quote cache                            │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## E-Commerce Integration Details

### Shopify Integration (Port 8010)
- **Purpose**: Sync Shopify stores with Quenty platform
- **Features**:
  - OAuth-based store connection
  - Bidirectional product sync
  - Automatic order import
  - Fulfillment updates back to Shopify
  - Real-time webhooks (orders, products, inventory)
- **Background Workers**: Celery for async sync
- **Database**: 6 tables (stores, orders, products, customers, webhooks, sync_logs)

### MercadoLibre Integration (Port 8012)
- **Purpose**: Integrate with Latin America's largest marketplace
- **Features**:
  - OAuth 2.0 authentication
  - Multi-site support (MLA, MLM, MLC, etc.)
  - Order synchronization
  - Product listing management
  - Automatic question answering via RAG
  - Webhook notifications
- **Background Workers**: Celery for order processing
- **Database**: 5 tables (accounts, orders, products, questions, notifications)

### WooCommerce Integration (Port 8013)
- **Purpose**: Connect WooCommerce stores
- **Features**:
  - REST API v3 integration
  - Multi-store support
  - Product catalog sync
  - Order import and fulfillment
  - Inventory updates
  - Webhook event processing
- **Status**: ✅ Database and models complete, needs deployment
- **Database**: 11 tables (stores, orders, products, customers, shipping_requests, etc.)

---

## AI/ML Services

### RAG Service (Port 8011)
- **Purpose**: Retrieval-Augmented Generation for intelligent chat and search
- **Technology**:
  - **pgvector**: PostgreSQL extension for vector similarity search
  - **Embeddings**: 1536-dimensional vectors (OpenAI compatible)
  - **Semantic Search**: Find relevant documents by meaning, not just keywords
- **Use Cases**:
  - Customer support chatbot
  - Product recommendation
  - Policy/FAQ question answering
  - MercadoLibre automatic question responses
- **Database**: 3 tables (documents, conversations, chat_messages)

---

*Document Version: 2.1*
*Last Updated: 2025-10-01*
*Architecture Team: Quenty Platform Engineering*