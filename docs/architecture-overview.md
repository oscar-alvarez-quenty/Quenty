# Quenty Microservices Architecture Overview

## System Architecture

The Quenty platform is built using a microservices architecture pattern, providing scalability, maintainability, and technology diversity. The system is designed to handle comprehensive logistics and shipping operations with high availability and performance across 9 specialized microservices.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile Client  │    │  Third Party    │
│                 │    │                 │    │     APIs        │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   Nginx         │
                        │ Load Balancer   │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  API Gateway    │
                        │   Port: 8000    │
                        └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│   Auth Service  │    │ Customer Service│    │  Order Service  │
│   Port: 8009    │    │   Port: 8001    │    │   Port: 8002    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│    Auth DB      │    │  Customer DB    │    │   Order DB      │
│  PostgreSQL     │    │  PostgreSQL     │    │  PostgreSQL     │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ Intl Shipping  │    │ Pickup Service │    │Analytics Service│
│   Port: 8004   │    │   Port: 8005   │    │   Port: 8006   │
└────────┬───────┘    └────────┬───────┘    └────────┬───────┘
         │                     │                     │
┌────────▼───────┐    ┌────────▼───────┐    ┌────────▼───────┐
│  Shipping DB   │    │   Pickup DB    │    │ Analytics DB   │
│  PostgreSQL    │    │  PostgreSQL    │    │  PostgreSQL    │
└────────────────┘    └────────────────┘    └────────────────┘

┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│Reverse Logistics│    │Franchise Service│    │Microcredit Svc │
│   Port: 8007   │    │   Port: 8008   │    │   Port: 8005   │
└────────┬───────┘    └────────┬───────┘    └────────┬───────┘
         │                     │                     │
┌────────▼───────┐    ┌────────▼───────┐    ┌────────▼───────┐
│Rev Logistics DB│    │ Franchise DB   │    │Microcredit DB  │
│  PostgreSQL    │    │  PostgreSQL    │    │  PostgreSQL    │
└────────────────┘    └────────────────┘    └────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Shared Infrastructure                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ Service Discovery│   Monitoring    │       Message Queue         │
│     Consul      │ Prometheus +    │        RabbitMQ             │
│   Port: 8500    │   Grafana       │       Port: 5672            │
│                 │ Ports: 9090,3000│                             │
└─────────────────┴─────────────────┴─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Cache & Tracing                           │
├─────────────────────────────┬───────────────────────────────────┤
│           Redis             │        Jaeger Tracing             │
│         Port: 6379          │         Port: 16686               │
└─────────────────────────────┴───────────────────────────────────┘
```

## Core Components

### 1. API Gateway (Port 8000)
- **Purpose**: Single entry point for all client requests
- **Features**: 
  - Request routing to appropriate microservices
  - Authentication and authorization
  - Rate limiting and request validation
  - API versioning support
- **Technology**: FastAPI with custom routing logic

### 2. Authentication & Authorization

#### Auth Service (Port 8009)
- **Responsibility**: Centralized authentication and authorization
- **Key Features**:
  - JWT token generation and validation
  - Role-based access control (RBAC)
  - User registration and authentication
  - Permission management
  - Refresh token handling
  - Multi-factor authentication support
- **Database**: PostgreSQL (auth_db)

### 3. Core Business Microservices

#### Customer Service (Port 8001)
- **Responsibility**: User and company management
- **Key Features**:
  - User registration, authentication, and profile management
  - Company onboarding and configuration
  - Role-based access control integration
  - Document type management
  - User analytics and reporting
- **Database**: PostgreSQL (customer_db)

#### Order Service (Port 8002)  
- **Responsibility**: Order and inventory management
- **Key Features**:
  - Product catalog management
  - Inventory tracking and stock movements
  - Order creation and lifecycle management
  - Low stock alerts and reorder management
  - Order analytics and reporting
- **Database**: PostgreSQL (order_db)

#### International Shipping Service (Port 8004)
- **Responsibility**: International shipping and logistics
- **Key Features**:
  - Manifest creation and management
  - Shipping rate calculation
  - Carrier integration (DHL, FedEx, UPS)
  - Customs documentation
  - Shipment tracking
  - Country and zone management
- **Database**: PostgreSQL (intl_shipping_db)

#### Pickup Service (Port 8005)
- **Responsibility**: Package pickup scheduling and management
- **Key Features**:
  - Pickup request scheduling (on-demand, scheduled, recurring, express)
  - Route optimization and driver assignment
  - Service area and capacity management
  - Pickup attempt tracking and rescheduling
  - Real-time pickup tracking
  - Driver performance monitoring
- **Database**: PostgreSQL (pickup_db)

#### Analytics Service (Port 8006)
- **Responsibility**: Business intelligence and metrics collection
- **Key Features**:
  - Real-time metrics ingestion from all services
  - Dynamic dashboard creation and management
  - Scheduled and on-demand report generation
  - Business intelligence and predictive analytics
  - Threshold-based alerting system
  - Performance monitoring and visualization
- **Database**: PostgreSQL (analytics_db)

#### Reverse Logistics Service (Port 8007)
- **Responsibility**: Returns and reverse supply chain management
- **Key Features**:
  - Return request processing and validation
  - Quality inspection and condition assessment
  - Inventory disposition management
  - Customer communication and tracking
  - Environmental impact tracking
  - Recovery value calculation
- **Database**: PostgreSQL (reverse_logistics_db)

#### Franchise Service (Port 8008)
- **Responsibility**: Franchise operations and territory management
- **Key Features**:
  - Franchise registration and onboarding
  - Territory allocation and management
  - Contract management and compliance
  - Performance tracking and analytics
  - Financial management and fee processing
  - Territory availability and optimization
- **Database**: PostgreSQL (franchise_db)

#### Microcredit Service (Port 8005)
- **Responsibility**: Financial services and credit management
- **Key Features**:
  - Credit application processing and approval
  - Dynamic credit scoring and risk assessment
  - Loan management and disbursement
  - Payment processing and collection
  - Credit history tracking and reporting
  - Regulatory compliance and audit trails
- **Database**: PostgreSQL (microcredit_db)

### 4. Infrastructure Services

#### Service Discovery - Consul (Port 8500)
- **Purpose**: Service registration and discovery
- **Features**:
  - Health checking
  - Configuration management
  - Service mesh coordination

#### Message Queue - RabbitMQ (Port 5672)
- **Purpose**: Asynchronous communication between services
- **Features**:
  - Event-driven architecture
  - Reliable message delivery
  - Dead letter queues
  - Message routing and filtering

#### Caching - Redis (Port 6379)
- **Purpose**: High-performance caching
- **Use Cases**:
  - Session storage
  - API response caching
  - Rate limiting counters
  - Temporary data storage

#### Monitoring - Prometheus & Grafana (Ports 9090, 3000)
- **Purpose**: System observability and alerting
- **Features**:
  - Metrics collection and storage
  - Custom dashboards and visualization
  - Alerting and notification
  - Performance monitoring

#### Distributed Tracing - Jaeger (Port 16686)
- **Purpose**: Request tracing across microservices
- **Features**:
  - End-to-end request tracking
  - Performance bottleneck identification
  - Service dependency mapping
  - Error tracking and debugging

### 5. Data Layer

#### Database Per Service Pattern
Each microservice has its own dedicated database:
- **Auth DB**: Users, roles, permissions, refresh tokens
- **Customer DB**: User accounts, companies, roles, documents
- **Order DB**: Products, inventory, orders, stock movements
- **Shipping DB**: Manifests, carriers, countries, shipping rates
- **Pickup DB**: Pickup requests, routes, packages, drivers
- **Analytics DB**: Metrics, dashboards, reports, alerts
- **Reverse Logistics DB**: Returns, inspections, dispositions
- **Franchise DB**: Franchises, territories, contracts, performance
- **Microcredit DB**: Credit applications, loans, payments, scores

#### Database Technology
- **RDBMS**: PostgreSQL 15
- **Connection**: Async connections using AsyncPG
- **ORM**: SQLAlchemy with async support
- **Migrations**: Alembic for schema versioning

## Communication Patterns

### 1. Synchronous Communication
- **HTTP/REST APIs**: For real-time data exchange
- **Service-to-Service**: Direct HTTP calls when immediate response needed
- **Client-to-Service**: Through API Gateway
- **Authentication**: JWT tokens validated through Auth Service

### 2. Asynchronous Communication  
- **Event-Driven**: Using RabbitMQ for loose coupling
- **Message Types**:
  - Authentication events (user login/logout, permission changes)
  - Order events (created, updated, shipped, delivered)
  - User events (registered, activated)
  - Pickup events (scheduled, completed, failed)
  - Return events (requested, processed, completed)
  - Analytics events (metrics, alerts)
  - Credit events (application, approval, payment)
  - Franchise events (performance updates, territory changes)

### 3. Data Consistency
- **Eventual Consistency**: For cross-service data synchronization
- **Saga Pattern**: For distributed transactions
- **Event Sourcing**: For audit trails and state reconstruction

## Security Architecture

### 1. Authentication & Authorization
- **Centralized Auth**: Auth Service manages all authentication
- **JWT Tokens**: For stateless authentication across services
- **Role-Based Access Control**: Fine-grained permission management
- **API Key Management**: For third-party integrations
- **Token Refresh**: Automatic token renewal mechanism

### 2. Network Security
- **Container Isolation**: Docker network segmentation
- **TLS/SSL**: Encrypted communication between services
- **API Gateway**: Security policy enforcement
- **Service Mesh**: Secure inter-service communication

### 3. Data Security
- **Database Encryption**: At rest and in transit
- **Secrets Management**: Environment-based configuration
- **Access Logging**: Comprehensive audit trails
- **PCI Compliance**: For credit and payment processing
- **GDPR Compliance**: For personal data protection

## Service Integration Patterns

### 1. Service Communication Matrix
```
┌─────────────────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│     Service     │Auth │Cust │Order│Ship │Pick │Anal │Rev  │Fran │Micro│
├─────────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ Auth Service    │  -  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │
│ Customer        │  ✓  │  -  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │  ✓  │
│ Order           │  ✓  │  ✓  │  -  │  ✓  │  ✓  │  ✓  │  ✓  │  -  │  ✓  │
│ Shipping        │  ✓  │  ✓  │  ✓  │  -  │  ✓  │  ✓  │  -  │  -  │  -  │
│ Pickup          │  ✓  │  ✓  │  ✓  │  -  │  -  │  ✓  │  -  │  -  │  -  │
│ Analytics       │  ✓  │  -  │  -  │  -  │  -  │  -  │  -  │  -  │  -  │
│ Reverse Log.    │  ✓  │  ✓  │  ✓  │  -  │  -  │  ✓  │  -  │  -  │  -  │
│ Franchise       │  ✓  │  ✓  │  ✓  │  -  │  ✓  │  ✓  │  -  │  -  │  -  │
│ Microcredit     │  ✓  │  ✓  │  -  │  -  │  -  │  ✓  │  -  │  -  │  -  │
└─────────────────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

### 2. Common Integration Patterns
- **Authentication**: All services validate tokens with Auth Service
- **Customer Validation**: Services verify customer/company data with Customer Service
- **Analytics Reporting**: All services send metrics to Analytics Service
- **Event Publishing**: Services publish domain events to message queue
- **Service Discovery**: Services register and discover each other via Consul

## Scalability & Performance

### 1. Horizontal Scaling
- **Stateless Services**: Easy horizontal scaling
- **Load Balancing**: Nginx for traffic distribution
- **Auto-scaling**: Container orchestration support
- **Database Read Replicas**: For heavy read workloads

### 2. Performance Optimization
- **Caching Strategy**: Multi-layer caching with Redis
- **Connection Pooling**: Efficient database connections
- **Async Processing**: Non-blocking I/O operations
- **Database Indexing**: Optimized query performance

### 3. Monitoring & Observability
- **Health Checks**: Service availability monitoring
- **Metrics Collection**: Performance and business metrics
- **Distributed Tracing**: Request flow visibility
- **Log Aggregation**: Centralized logging strategy

## Service Dependencies

### 1. Critical Dependencies
- **Auth Service**: Required by all services for authentication
- **Customer Service**: Required by most services for user/company validation
- **Analytics Service**: Receives data from all services

### 2. Business Flow Dependencies
- **Order → Pickup**: Orders trigger pickup requests
- **Order → Shipping**: Orders generate shipping manifests
- **Order → Returns**: Completed orders enable return requests
- **Pickup → Order**: Pickup completion updates order status
- **Franchise → Order**: Franchise performance affects order routing

## Deployment Architecture

### 1. Containerization
- **Docker**: Application containerization
- **Docker Compose**: Local development orchestration
- **Multi-stage Builds**: Optimized container images

### 2. Environment Management
- **Development**: Local Docker Compose setup
- **Staging**: Kubernetes cluster with reduced resources
- **Production**: High-availability Kubernetes deployment

### 3. CI/CD Pipeline
- **Build**: Automated testing and Docker image creation
- **Deploy**: Rolling deployments with health checks
- **Monitor**: Post-deployment verification and monitoring

## Design Principles

### 1. Domain-Driven Design (DDD)
- **Bounded Contexts**: Clear service boundaries
- **Ubiquitous Language**: Consistent terminology
- **Aggregate Patterns**: Data consistency boundaries

### 2. Twelve-Factor App
- **Configuration**: Environment-based settings
- **Dependencies**: Explicit dependency declaration
- **Processes**: Stateless application processes

### 3. Microservices Best Practices
- **Single Responsibility**: One service per business capability
- **Database Per Service**: Data ownership and independence
- **API-First Design**: Contract-driven development
- **Failure Isolation**: Circuit breaker patterns

## Service Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8000 | Main entry point |
| Customer Service | 8001 | User/company management |
| Order Service | 8002 | Order/inventory management |
| Auth Service | 8009 | Authentication/authorization |
| International Shipping | 8004 | Shipping/logistics |
| Pickup Service | 8005 | Pickup scheduling |
| Analytics Service | 8006 | Metrics/reporting |
| Reverse Logistics | 8007 | Returns management |
| Franchise Service | 8008 | Franchise operations |
| Microcredit Service | 8005* | Financial services |

*Note: Microcredit Service shares port 8005 but runs in isolated environment*

## Future Architecture Considerations

### 1. Service Mesh
- **Istio/Linkerd**: Advanced traffic management
- **Mutual TLS**: Enhanced security between services
- **Circuit Breakers**: Improved resilience

### 2. Event Streaming
- **Apache Kafka**: High-throughput event streaming
- **Event Sourcing**: Complete audit trail
- **CQRS**: Command Query Responsibility Segregation

### 3. Advanced Analytics
- **Real-time Processing**: Stream processing with Apache Flink
- **Machine Learning**: Predictive analytics integration
- **Data Lake**: Long-term analytics storage

This architecture provides a solid foundation for the Quenty logistics platform, enabling scalability, maintainability, and extensibility while maintaining strong data consistency and security across all business domains.