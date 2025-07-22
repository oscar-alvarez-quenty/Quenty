# Quenty Microservices Architecture with Authentication

This directory contains the enhanced microservices implementation of the Quenty application with **centralized authentication and role-based access control (RBAC)**.

## 🔐 Architecture Overview

The application has been redesigned with a **secure-by-default** microservices architecture featuring centralized authentication and authorization.

### 🎯 Core Authentication-Enabled Services

1. **🔐 Authentication Service** (Port 8003) - **NEW CENTRAL HUB**
   - **Primary Role**: Central authentication, authorization, and user management
   - JWT-based authentication with refresh tokens
   - OAuth integration (Google, Azure)
   - Role-Based Access Control (RBAC) with granular permissions
   - User and company management
   - Session management and security auditing
   - **All other services authenticate through this service**

2. **👥 Customer Service** (Port 8001) - **REFACTORED FOR SECURITY**
   - **Primary Role**: Customer relationship management and support
   - Customer profile management (linked to auth users)
   - Support ticket system with full lifecycle
   - Customer analytics and reporting
   - **Security**: Ownership-based access control, admin permissions for management

3. **📦 Order Service** (Port 8002) - **ENHANCED WITH PERMISSIONS**
   - **Primary Role**: Order processing, product catalog, and inventory
   - Order creation and management with role-based access
   - Product catalog with permission controls
   - Inventory management with restricted access
   - **Security**: Permission-based operations, customer order isolation

4. **🚢 International Shipping Service** (Port 8004) - **PERMISSION-CONTROLLED**
   - **Primary Role**: International shipping and logistics
   - Manifest creation with role restrictions
   - Shipping rate calculation and validation
   - Carrier integration (DHL, FedEx, UPS)
   - **Security**: Admin controls for configuration, role-based shipping access

### 🏗️ Legacy Services (To Be Enhanced)

5. **🚚 Pickup Service** (Port 8005) - *Awaiting auth integration*
6. **💳 Microcredit Service** (Port 8006) - *Awaiting auth integration*
7. **📊 Analytics Service** (Port 8007) - *Awaiting auth integration*
8. **↩️ Reverse Logistics Service** (Port 8008) - *Awaiting auth integration*
9. **🏢 Franchise Service** (Port 8009) - *Awaiting auth integration*

### Infrastructure Services

- **PostgreSQL**: Separate database for each microservice
- **Redis**: Shared caching and session storage
- **RabbitMQ**: Message queue for async communication
- **Consul**: Service discovery and health checking
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Jaeger**: Distributed tracing
- **Nginx**: Load balancer and reverse proxy

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Make (optional, for convenience commands)

### Running the Microservices

1. **Start all services:**
   ```bash
   docker-compose -f docker-compose.microservices.yml up -d
   ```

2. **Check service health:**
   ```bash
   curl http://localhost:8000/services/health
   ```

3. **View logs:**
   ```bash
   docker-compose -f docker-compose.microservices.yml logs -f [service-name]
   ```

4. **Stop all services:**
   ```bash
   docker-compose -f docker-compose.microservices.yml down
   ```

### Service URLs

- API Gateway: http://localhost:8000
- Consul UI: http://localhost:8500
- RabbitMQ Management: http://localhost:15672 (user: quenty, pass: quenty_pass)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (user: admin, pass: admin)
- Jaeger UI: http://localhost:16686

## Development

### Adding a New Microservice

1. Create a new directory under `microservices/`
2. Add a Dockerfile based on the template
3. Create the service implementation
4. Add the service to `docker-compose.microservices.yml`
5. Update the API Gateway to route to the new service
6. Add service discovery registration

### Database Migrations

Each service has its own database and manages its own migrations using Alembic:

```bash
# Run migrations for a specific service
docker-compose -f docker-compose.microservices.yml exec [service-name] alembic upgrade head
```

### Inter-Service Communication

Services communicate through:
1. **Synchronous**: HTTP/REST via API Gateway
2. **Asynchronous**: RabbitMQ for events and background tasks

### Service Discovery

Services register themselves with Consul on startup. The API Gateway uses Consul to discover service endpoints dynamically.

## Monitoring and Observability

### Metrics
- Each service exposes Prometheus metrics at `/metrics`
- Grafana dashboards available at http://localhost:3000

### Logging
- Structured logging with correlation IDs
- Logs aggregated in Docker compose

### Tracing
- Distributed tracing with Jaeger
- Trace spans across service boundaries

## 🔐 Security Architecture

### Centralized Authentication & Authorization
- **JWT-based authentication** with access and refresh tokens
- **OAuth 2.0 integration** with Google and Azure providers
- **Role-Based Access Control (RBAC)** with granular permissions
- **Session management** with token revocation capabilities
- **Audit logging** for all authentication and authorization events

### Service Security
- **Service-to-service authentication** via auth service verification
- **Permission validation** for all protected endpoints
- **Ownership-based access control** (users can only access their own data)
- **Admin role separation** for management operations
- Each service runs as non-root user in Docker containers
- Separate database credentials per service

### Default Security Roles
| Role | Access Level | Key Permissions |
|------|--------------|-----------------|
| **Super Administrator** | Full system access | `*` (all permissions) |
| **Administrator** | Administrative access | `users:*`, `companies:*`, `customers:*`, `orders:*` |
| **Manager** | Operations management | `customers:*`, `orders:*`, `reports:view` |
| **Customer Service** | Customer support | `customers:read:all`, `orders:read:all` |
| **Customer** | Own data access | `profile:*`, `orders:read:own`, `customers:read:own` |
| **Shipping Coordinator** | Logistics management | `shipping:*`, `manifests:*` |

### Security Best Practices Implemented
- ✅ Password hashing with bcrypt
- ✅ JWT token signing and validation
- ✅ Session timeout and token refresh
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention
- ✅ Rate limiting on auth endpoints
- ✅ Comprehensive audit logging
- ✅ Principle of least privilege

## Deployment

### Production Considerations

1. Use Kubernetes or Docker Swarm for orchestration
2. Implement proper secrets management (e.g., HashiCorp Vault)
3. Set up proper TLS/SSL certificates
4. Configure horizontal pod autoscaling
5. Implement proper backup strategies for databases
6. Use managed services where appropriate (RDS, ElastiCache, etc.)

### Environment Variables

Configure services using environment variables. See `.env.microservices` for all available options.

## Testing

### Unit Tests
Run tests for individual services:
```bash
docker-compose -f docker-compose.microservices.yml exec [service-name] pytest
```

### Integration Tests
Test service interactions:
```bash
python -m pytest tests/integration/
```

### Load Testing
Use tools like k6 or Locust to test performance and scalability.

## Troubleshooting

### Service Won't Start
- Check logs: `docker-compose logs [service-name]`
- Verify database connection
- Check if ports are already in use

### Service Discovery Issues
- Verify Consul is running: http://localhost:8500
- Check service registration in logs
- Ensure health checks are passing

### Database Connection Issues
- Verify database is running
- Check connection strings in environment variables
- Ensure network connectivity between services