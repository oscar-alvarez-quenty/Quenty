# Local Development Guide

## Overview

This guide provides detailed instructions for setting up a local development environment for the Quenty microservices platform, including prerequisites, installation steps, and development workflows.

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+ with WSL2
- **Memory**: Minimum 8GB RAM (16GB recommended for full stack)
- **Storage**: Minimum 20GB free disk space
- **CPU**: Multi-core processor (4+ cores recommended)

### Required Software

#### 1. Docker and Docker Compose
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect

# Verify installation
docker --version
docker-compose --version
```

#### 2. Python 3.11+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip

# macOS (using Homebrew)
brew install python@3.11

# Verify installation
python3.11 --version
```

#### 3. Node.js 18+ (for development tools)
```bash
# Using Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18

# Verify installation
node --version
npm --version
```

#### 4. Git
```bash
# Ubuntu/Debian
sudo apt install git

# macOS
brew install git

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Optional Development Tools

#### 1. PostgreSQL Client
```bash
# Ubuntu/Debian
sudo apt install postgresql-client

# macOS
brew install postgresql
```

#### 2. Redis CLI
```bash
# Ubuntu/Debian
sudo apt install redis-tools

# macOS
brew install redis
```

## Project Setup

### 1. Clone Repository
```bash
# Clone the main repository
git clone https://github.com/your-org/Quenty.git
cd Quenty

# Initialize and update submodules if any
git submodule update --init --recursive
```

### 2. Environment Configuration

#### Create Environment Files
```bash
# Copy environment templates
cp .env.example .env
cp microservices/customer/.env.example microservices/customer/.env
cp microservices/order/.env.example microservices/order/.env
cp microservices/international-shipping/.env.example microservices/international-shipping/.env
```

#### Configure Main Environment (.env)
```bash
# Application Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database Passwords
POSTGRES_PASSWORD=dev_postgres_password
CUSTOMER_DB_PASSWORD=dev_customer_password
ORDER_DB_PASSWORD=dev_order_password  
SHIPPING_DB_PASSWORD=dev_shipping_password

# Redis
REDIS_PASSWORD=dev_redis_password

# RabbitMQ
RABBITMQ_USER=dev_user
RABBITMQ_PASSWORD=dev_password

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_for_development
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=3600

# External API Keys (for testing)
DHL_API_KEY=test_dhl_key
FEDEX_API_KEY=test_fedex_key
UPS_API_KEY=test_ups_key

# Monitoring
GRAFANA_PASSWORD=admin
```

#### Service-Specific Environment Files

**Customer Service (.env.customer):**
```bash
SERVICE_NAME=customer-service
DATABASE_URL=postgresql+asyncpg://customer:dev_customer_password@localhost:5433/customer_db
REDIS_URL=redis://:dev_redis_password@localhost:6379/1
CONSUL_HOST=localhost
CONSUL_PORT=8500
LOG_LEVEL=DEBUG
```

**Order Service (.env.order):**
```bash
SERVICE_NAME=order-service
DATABASE_URL=postgresql+asyncpg://order:dev_order_password@localhost:5434/order_db
REDIS_URL=redis://:dev_redis_password@localhost:6379/2
CUSTOMER_SERVICE_URL=http://localhost:8001
CONSUL_HOST=localhost
CONSUL_PORT=8500
LOG_LEVEL=DEBUG
```

**International Shipping Service (.env.shipping):**
```bash
SERVICE_NAME=international-shipping-service
DATABASE_URL=postgresql+asyncpg://intlship:dev_shipping_password@localhost:5435/intl_shipping_db
REDIS_URL=redis://:dev_redis_password@localhost:6379/4
CUSTOMER_SERVICE_URL=http://localhost:8001
CONSUL_HOST=localhost
CONSUL_PORT=8500
LOG_LEVEL=DEBUG
```

### 3. Development Setup with Docker

#### Quick Start - All Services
```bash
# Start all services with development configuration
docker-compose -f docker-compose.microservices.yml -f docker-compose.development.yml up --build

# Or start in detached mode
docker-compose -f docker-compose.microservices.yml -f docker-compose.development.yml up -d --build
```

#### Selective Service Development
```bash
# Start only infrastructure services
docker-compose -f docker-compose.microservices.yml up -d postgres redis rabbitmq consul

# Start specific service for development
docker-compose -f docker-compose.microservices.yml up -d customer-service customer-db
```

#### Development with Live Reload
```bash
# Create development override file
cat > docker-compose.development.yml << 'EOF'
version: '3.8'

services:
  customer-service:
    volumes:
      - ./microservices/customer:/app
      - customer-service-venv:/app/.venv
    environment:
      - PYTHONPATH=/app
      - RELOAD=true
    command: uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

  order-service:
    volumes:
      - ./microservices/order:/app
      - order-service-venv:/app/.venv
    environment:
      - PYTHONPATH=/app
      - RELOAD=true
    command: uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload

  international-shipping-service:
    volumes:
      - ./microservices/international-shipping:/app
      - shipping-service-venv:/app/.venv
    environment:
      - PYTHONPATH=/app
      - RELOAD=true
    command: uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload

volumes:
  customer-service-venv:
  order-service-venv:
  shipping-service-venv:
EOF
```

## Native Development Setup

### 1. Python Virtual Environments

#### Customer Service
```bash
cd microservices/customer
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Order Service
```bash
cd ../order
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### International Shipping Service
```bash
cd ../international-shipping
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Database Setup

#### Start PostgreSQL Containers
```bash
# Start database containers only
docker-compose -f docker-compose.microservices.yml up -d customer-db order-db intl-shipping-db
```

#### Run Database Migrations
```bash
# Customer Service
cd microservices/customer
source venv/bin/activate
alembic upgrade head

# Order Service  
cd ../order
source venv/bin/activate
alembic upgrade head

# International Shipping Service
cd ../international-shipping
source venv/bin/activate
alembic upgrade head
```

### 3. Start Services Natively

#### Terminal 1 - Customer Service
```bash
cd microservices/customer
source venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://customer:dev_customer_password@localhost:5433/customer_db"
export REDIS_URL="redis://:dev_redis_password@localhost:6379/1"
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 2 - Order Service
```bash
cd microservices/order
source venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://order:dev_order_password@localhost:5434/order_db"
export REDIS_URL="redis://:dev_redis_password@localhost:6379/2"
export CUSTOMER_SERVICE_URL="http://localhost:8001"
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

#### Terminal 3 - International Shipping Service
```bash
cd microservices/international-shipping
source venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://intlship:dev_shipping_password@localhost:5435/intl_shipping_db"
export REDIS_URL="redis://:dev_redis_password@localhost:6379/4"
export CUSTOMER_SERVICE_URL="http://localhost:8001"
uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

## Development Workflow

### 1. Code Structure

```
Quenty/
├── microservices/
│   ├── customer/
│   │   ├── src/
│   │   │   ├── main.py          # FastAPI application
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   ├── database.py      # Database connection
│   │   │   ├── schemas.py       # Pydantic schemas
│   │   │   └── config.py        # Configuration
│   │   ├── alembic/            # Database migrations
│   │   ├── tests/              # Test files
│   │   ├── requirements.txt    # Dependencies
│   │   └── Dockerfile         # Container definition
│   ├── order/                 # Similar structure
│   └── international-shipping/# Similar structure
├── docker-compose.microservices.yml
├── docker-compose.development.yml
├── .env.example
└── docs/                      # Documentation
```

### 2. Making Changes

#### Adding New Endpoints
```python
# In microservices/customer/src/main.py
from fastapi import FastAPI, HTTPException
from typing import List
from .schemas import UserCreate, UserResponse

@app.post("/api/v1/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Implementation here
    pass

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    # Implementation here
    pass
```

#### Database Migrations
```bash
# Create new migration
cd microservices/customer
source venv/bin/activate
alembic revision --autogenerate -m "Add new user fields"

# Review and edit migration file in alembic/versions/
# Then apply migration
alembic upgrade head
```

#### Adding Dependencies
```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Install in development
pip install -r requirements.txt

# Update Docker image
docker-compose -f docker-compose.microservices.yml build customer-service
```

### 3. Testing

#### Unit Tests
```bash
# Run tests for specific service
cd microservices/customer
source venv/bin/activate
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

#### Integration Tests
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

#### API Testing with curl
```bash
# Health check
curl http://localhost:8001/health

# Create user
curl -X POST "http://localhost:8001/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }'

# Get user
curl http://localhost:8001/api/v1/users/1
```

## Development Tools

### 1. Code Quality

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### Linting and Formatting
```bash
# Install development tools
pip install black isort flake8 mypy

# Format code
black microservices/customer/src/
isort microservices/customer/src/

# Lint code
flake8 microservices/customer/src/
mypy microservices/customer/src/
```

### 2. Database Management

#### Database Client Tools
```bash
# Connect to customer database
psql -h localhost -p 5433 -U customer -d customer_db

# Connect to order database  
psql -h localhost -p 5434 -U order -d order_db

# Connect to shipping database
psql -h localhost -p 5435 -U intlship -d intl_shipping_db
```

#### Database GUI Tools
- **pgAdmin**: Web-based PostgreSQL administration
- **DBeaver**: Universal database tool
- **TablePlus**: Native database client (macOS/Windows)

### 3. API Documentation

#### OpenAPI/Swagger
Each service provides interactive API documentation:
- Customer Service: http://localhost:8001/docs
- Order Service: http://localhost:8002/docs  
- Shipping Service: http://localhost:8004/docs

#### Postman Collection
```bash
# Export OpenAPI specs
curl http://localhost:8001/openapi.json > customer-service-api.json
curl http://localhost:8002/openapi.json > order-service-api.json
curl http://localhost:8004/openapi.json > shipping-service-api.json

# Import into Postman or other API tools
```

### 4. Monitoring and Debugging

#### Application Logs
```bash
# View service logs
docker-compose -f docker-compose.microservices.yml logs -f customer-service

# View all logs
docker-compose -f docker-compose.microservices.yml logs -f

# Filter logs by level
docker-compose -f docker-compose.microservices.yml logs | grep ERROR
```

#### Debug with pdb
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Run service in foreground to interact with debugger
docker-compose -f docker-compose.microservices.yml run --service-ports customer-service
```

#### Monitoring Endpoints
- Prometheus Metrics: http://localhost:9090
- Grafana Dashboards: http://localhost:3000 (admin/admin)
- Consul UI: http://localhost:8500
- RabbitMQ Management: http://localhost:15672 (guest/guest)

## Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check what's using a port
sudo netstat -tulpn | grep :8001
sudo lsof -i :8001

# Kill process using port
sudo kill -9 <PID>
```

#### 2. Database Connection Issues
```bash
# Check database containers
docker-compose -f docker-compose.microservices.yml ps

# Check database logs
docker-compose -f docker-compose.microservices.yml logs customer-db

# Reset database
docker-compose -f docker-compose.microservices.yml down -v
docker-compose -f docker-compose.microservices.yml up -d customer-db
```

#### 3. Service Discovery Issues
```bash
# Check Consul
curl http://localhost:8500/v1/agent/services

# Re-register services
docker-compose -f docker-compose.microservices.yml restart customer-service
```

#### 4. Permission Issues
```bash
# Fix Docker permissions
sudo chown -R $USER:$USER /var/run/docker.sock

# Fix file permissions
sudo chown -R $USER:$USER .
```

### Performance Issues

#### 1. Slow Database Queries
```sql
-- Enable query logging (development only)
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 100;
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### 2. Memory Issues
```bash
# Monitor container resources
docker stats

# Increase Docker memory limits
# Edit docker-compose.yml to add memory limits
```

### Development Scripts

#### setup.sh - Complete Environment Setup
```bash
#!/bin/bash
set -e

echo "Setting up Quenty development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required"; exit 1; }

# Copy environment files
cp .env.example .env
for service in customer order international-shipping; do
    cp microservices/$service/.env.example microservices/$service/.env
done

# Start infrastructure
docker-compose -f docker-compose.microservices.yml up -d postgres redis consul rabbitmq

# Wait for services to be ready
sleep 30

# Run database migrations
for service in customer order international-shipping; do
    docker-compose -f docker-compose.microservices.yml run --rm ${service}-service alembic upgrade head
done

# Start all services
docker-compose -f docker-compose.microservices.yml up -d

echo "Environment setup complete!"
echo "Services available at:"
echo "  Customer Service: http://localhost:8001/docs"
echo "  Order Service: http://localhost:8002/docs"
echo "  Shipping Service: http://localhost:8004/docs"
```

#### test.sh - Run All Tests
```bash
#!/bin/bash
set -e

echo "Running all tests..."

# Unit tests
for service in customer order international-shipping; do
    echo "Running tests for $service service..."
    cd microservices/$service
    python -m pytest tests/ -v --cov=src
    cd ../..
done

echo "All tests completed!"
```

## Next Steps

After setting up your development environment:

1. **Explore the API Documentation**: Visit the Swagger UI for each service
2. **Run the Test Suite**: Execute all tests to ensure everything works
3. **Review the Architecture**: Study the microservices architecture documentation
4. **Make Your First Change**: Try adding a simple endpoint or field
5. **Join the Development Chat**: Connect with the development team

For production deployment, see the [Docker Deployment Guide](../deployment/docker-deployment.md) and [Production Deployment Guide](../deployment/production-deployment.md).