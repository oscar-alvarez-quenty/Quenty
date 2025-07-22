# Quenty Microservices Architecture Overview

## System Architecture

The Quenty platform is built using a microservices architecture pattern, providing scalability, maintainability, and technology diversity. The system is designed to handle logistics and shipping operations with high availability and performance.

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
│ Customer Service│    │  Order Service  │    │ Shipping Service│
│   Port: 8001    │    │   Port: 8002    │    │   Port: 8004    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  Customer DB    │    │   Order DB     │    │  Shipping DB    │
│  PostgreSQL     │    │  PostgreSQL    │    │  PostgreSQL     │
└─────────────────┘    └─────────────────┘    └─────────────────┘

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

### 2. Microservices

#### Customer Service (Port 8001)
- **Responsibility**: User and company management
- **Key Features**:
  - User registration, authentication, and profile management
  - Company onboarding and configuration
  - Role-based access control
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

### 3. Infrastructure Services

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

### 4. Data Layer

#### Database Per Service Pattern
Each microservice has its own dedicated database:
- **Customer DB**: User accounts, companies, roles, documents
- **Order DB**: Products, inventory, orders, stock movements
- **Shipping DB**: Manifests, carriers, countries, shipping rates

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

### 2. Asynchronous Communication  
- **Event-Driven**: Using RabbitMQ for loose coupling
- **Message Types**:
  - Order events (created, updated, shipped)
  - User events (registered, activated)
  - Inventory events (stock updates, low stock alerts)

### 3. Data Consistency
- **Eventual Consistency**: For cross-service data synchronization
- **Saga Pattern**: For distributed transactions
- **Event Sourcing**: For audit trails and state reconstruction

## Security Architecture

### 1. Authentication & Authorization
- **JWT Tokens**: For stateless authentication
- **Role-Based Access Control**: Service-level permission management
- **API Key Management**: For third-party integrations

### 2. Network Security
- **Container Isolation**: Docker network segmentation
- **TLS/SSL**: Encrypted communication
- **API Gateway**: Security policy enforcement

### 3. Data Security
- **Database Encryption**: At rest and in transit
- **Secrets Management**: Environment-based configuration
- **Access Logging**: Comprehensive audit trails

## Scalability & Performance

### 1. Horizontal Scaling
- **Stateless Services**: Easy horizontal scaling
- **Load Balancing**: Nginx for traffic distribution
- **Auto-scaling**: Container orchestration support

### 2. Performance Optimization
- **Caching Strategy**: Multi-layer caching with Redis
- **Connection Pooling**: Efficient database connections
- **Async Processing**: Non-blocking I/O operations

### 3. Monitoring & Observability
- **Health Checks**: Service availability monitoring
- **Metrics Collection**: Performance and business metrics
- **Distributed Tracing**: Request flow visibility
- **Log Aggregation**: Centralized logging strategy

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