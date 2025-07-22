# Quenty Microservices Architecture

This directory contains the microservices implementation of the Quenty application, breaking down the monolithic application into independent, scalable services.

## Architecture Overview

The application has been decomposed into the following microservices:

### Core Services

1. **API Gateway** (Port 8000)
   - Central entry point for all client requests
   - Routes requests to appropriate microservices
   - Implements circuit breakers and retry logic
   - Handles authentication and rate limiting

2. **Customer Service** (Port 8001)
   - Customer registration and management
   - KYC validation
   - Wallet management
   - Customer profiles

3. **Order Service** (Port 8002)
   - Order creation and management
   - Quotation generation
   - Order confirmation
   - Guide generation

4. **Pickup Service** (Port 8003)
   - Pickup scheduling
   - Route optimization
   - Pickup attempts tracking

5. **International Shipping Service** (Port 8004)
   - International KYC validation
   - Customs documentation
   - International shipping restrictions

6. **Microcredit Service** (Port 8005)
   - Credit scoring
   - Loan disbursement
   - Payment tracking

7. **Analytics Service** (Port 8006)
   - Business dashboards
   - KPIs and metrics
   - Reporting

8. **Reverse Logistics Service** (Port 8007)
   - Returns processing
   - Inspections
   - Refunds

9. **Franchise Service** (Port 8008)
   - Franchise operations
   - Logistics operators management
   - Commission management

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

## Security

- JWT-based authentication at API Gateway
- Service-to-service communication within Docker network
- Each service runs as non-root user
- Separate database credentials per service

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