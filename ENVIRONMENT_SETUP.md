# Environment Variables Setup Guide

Complete documentation for configuring Quenty platform environment variables.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Main Application](#main-application)
4. [Microservices](#microservices)
5. [Security Best Practices](#security-best-practices)
6. [Environment-Specific Configurations](#environment-specific-configurations)
7. [Troubleshooting](#troubleshooting)

## Overview

Quenty uses environment variables to configure various aspects of the platform. Each service has its own `.env` file for isolation and security.

### File Structure

```
quenty/
├── .env                          # Main application
├── .env.carriers                 # Carrier integrations
├── .env.example                  # Main app template
├── .env.carriers.example         # Carriers template
└── microservices/
    ├── auth-service/.env.example
    ├── customer/.env.example
    ├── order/.env.example
    ├── api-gateway/.env.example
    ├── carrier-integration/.env.example
    ├── shopify-integration/.env.example
    ├── woocommerce-integration/.env.example
    └── mercadolibre-integration/.env.example
```

## Quick Start

### 1. Copy All Templates

```bash
# Main application
cp .env.example .env

# Carrier integrations
cp .env.carriers.example .env.carriers

# For each microservice
for service in microservices/*; do
  if [ -f "$service/.env.example" ]; then
    cp "$service/.env.example" "$service/.env"
  fi
done
```

### 2. Generate Security Keys

```bash
# Generate JWT secret (32 bytes)
openssl rand -hex 32

# Generate encryption key (32 bytes)
openssl rand -base64 32

# Generate API key
uuidgen
```

### 3. Configure Essential Variables

Minimum required variables for local development:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/quenty_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=<generated-key>
JWT_SECRET_KEY=<generated-key>

# Environment
ENVIRONMENT=development
```

## Main Application

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment mode | `development` | Yes |
| `API_HOST` | API host binding | `0.0.0.0` | Yes |
| `API_PORT` | API port | `8000` | Yes |
| `SECRET_KEY` | Application secret | - | Yes |

### Database Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `DATABASE_POOL_SIZE` | Connection pool size | `20` |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections | `40` |
| `DATABASE_POOL_TIMEOUT` | Pool timeout (seconds) | `30` |

### Redis Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection | `redis://:password@host:6379/0` |
| `REDIS_POOL_MIN_SIZE` | Min pool size | `10` |
| `REDIS_POOL_MAX_SIZE` | Max pool size | `50` |
| `REDIS_TTL` | Default TTL (seconds) | `3600` |

### Security Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` |
| `BCRYPT_ROUNDS` | Password hashing rounds | `12` |

## Microservices

### Auth Service

Essential authentication service variables:

```env
# Service
SERVICE_NAME=auth-service
SERVICE_PORT=8001

# JWT Configuration
JWT_SECRET_KEY=must-match-main-app-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth2 (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# 2FA (optional)
TOTP_ENABLED=true
SMS_2FA_ENABLED=false
```

### API Gateway

Gateway routing and security:

```env
# Gateway
SERVICE_NAME=api-gateway
SERVICE_PORT=8000

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8001
CUSTOMER_SERVICE_URL=http://customer-service:8002
ORDER_SERVICE_URL=http://order-service:8003

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW=60000

# CORS
CORS_ORIGINS=http://localhost:3000
CORS_CREDENTIALS=true
```

### Carrier Integration

Shipping carrier credentials:

```env
# DHL
DHL_API_KEY=your-api-key
DHL_USERNAME=your-username
DHL_PASSWORD=your-password
DHL_ACCOUNT_NUMBER=123456789
DHL_ENVIRONMENT=sandbox

# UPS
UPS_CLIENT_ID=your-client-id
UPS_CLIENT_SECRET=your-secret
UPS_ACCOUNT_NUMBER=your-account

# FedEx
FEDEX_CLIENT_ID=your-client-id
FEDEX_CLIENT_SECRET=your-secret
FEDEX_ACCOUNT_NUMBER=your-account

# Colombian Carriers
SERVIENTREGA_USER=your-user
SERVIENTREGA_PASSWORD=your-password
INTERRAPIDISIMO_API_KEY=your-api-key
```

### E-commerce Integrations

#### Shopify

```env
SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
SHOPIFY_API_KEY=your-api-key
SHOPIFY_API_SECRET=your-secret
SHOPIFY_ACCESS_TOKEN=your-token
SHOPIFY_WEBHOOK_SECRET=your-webhook-secret
```

#### WooCommerce

```env
WOOCOMMERCE_URL=https://your-store.com
WOOCOMMERCE_CONSUMER_KEY=ck_your_key
WOOCOMMERCE_CONSUMER_SECRET=cs_your_secret
```

#### MercadoLibre

```env
MELI_APP_ID=your-app-id
MELI_CLIENT_SECRET=your-secret
MELI_SITE_ID=MCO  # Colombia
MELI_USER_ID=your-user-id
```

## Security Best Practices

### 1. Never Commit Secrets

```bash
# Add to .gitignore
.env
.env.*
!.env.example
!.env.*.example
```

### 2. Use Strong Keys

```bash
# Generate strong keys
openssl rand -hex 32  # For JWT secrets
openssl rand -base64 32  # For encryption keys
pwgen -s 32 1  # For API keys
```

### 3. Rotate Credentials

- Rotate production credentials every 90 days
- Use different credentials per environment
- Implement key versioning

### 4. Encrypt Sensitive Data

```env
# Enable encryption
ENCRYPT_PII=true
PII_ENCRYPTION_KEY=your-32-byte-key
```

### 5. Restrict Access

```env
# IP whitelisting
IP_WHITELIST_ENABLED=true
ALLOWED_IPS=10.0.0.0/8,172.16.0.0/12
```

## Environment-Specific Configurations

### Development

```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DOCS_ENABLED=true
RATE_LIMIT_ENABLED=false
```

### Staging

```env
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DOCS_ENABLED=true
RATE_LIMIT_ENABLED=true
```

### Production

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DOCS_ENABLED=false
RATE_LIMIT_ENABLED=true
SSL_REQUIRED=true
```

## Docker Compose Configuration

### Using Environment Files

```yaml
services:
  app:
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}

  carrier-integration:
    env_file:
      - .env.carriers
```

### Override for Development

Create `docker-compose.override.yml`:

```yaml
services:
  app:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

## Validation Script

Create a validation script `validate-env.sh`:

```bash
#!/bin/bash

# Check required variables
required_vars=(
  "DATABASE_URL"
  "REDIS_URL"
  "SECRET_KEY"
  "JWT_SECRET_KEY"
)

missing_vars=()

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    missing_vars+=($var)
  fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
  echo "Missing required environment variables:"
  printf '%s\n' "${missing_vars[@]}"
  exit 1
fi

echo "Environment validation passed!"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps db

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### 2. Redis Connection Failed

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -u $REDIS_URL ping
```

#### 3. Service Discovery Issues

```bash
# Check service registration
curl http://localhost:8000/health

# Check network
docker network ls
docker network inspect quenty-network
```

#### 4. Authentication Failures

```bash
# Verify JWT secrets match
echo $JWT_SECRET_KEY | md5sum

# Check token expiry
jwt decode $ACCESS_TOKEN
```

### Debug Mode

Enable debug logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text
SQL_ECHO=true
```

### Health Checks

Monitor service health:

```bash
# Main app
curl http://localhost:8000/health

# Auth service
curl http://localhost:8001/health

# API Gateway
curl http://localhost:8000/health
```

## Environment Variable Reference

### Complete List by Category

#### Application
- `ENVIRONMENT` - development/staging/production
- `APP_NAME` - Application name
- `APP_VERSION` - Application version
- `DEBUG` - Debug mode

#### Database
- `DATABASE_URL` - Primary database
- `TEST_DATABASE_URL` - Test database
- `DATABASE_POOL_SIZE` - Connection pool
- `DATABASE_ECHO` - SQL logging

#### Caching
- `REDIS_URL` - Redis connection
- `CACHE_TTL` - Default cache TTL
- `CACHE_ENABLED` - Enable caching

#### Security
- `SECRET_KEY` - App secret
- `JWT_SECRET_KEY` - JWT secret
- `ENCRYPTION_KEY` - Data encryption
- `API_KEY` - API authentication

#### Email
- `SMTP_HOST` - Mail server
- `SMTP_PORT` - Mail port
- `SMTP_USERNAME` - Mail user
- `SMTP_PASSWORD` - Mail password

#### External Services
- `AWS_ACCESS_KEY_ID` - AWS key
- `AWS_SECRET_ACCESS_KEY` - AWS secret
- `STRIPE_SECRET_KEY` - Stripe key
- `TWILIO_AUTH_TOKEN` - Twilio token

#### Monitoring
- `LOG_LEVEL` - Log verbosity
- `SENTRY_DSN` - Error tracking
- `METRICS_ENABLED` - Enable metrics
- `JAEGER_ENABLED` - Tracing

## Support

For environment configuration issues:

1. Check the example files for reference
2. Verify all required variables are set
3. Review service logs for specific errors
4. Contact the development team

## Next Steps

1. Set up your `.env` files
2. Configure service-specific variables
3. Run validation script
4. Start services with Docker Compose
5. Verify health checks
6. Test integrations