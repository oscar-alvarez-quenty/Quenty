# Carrier Integration Service - Credential Management

## Overview
This document describes how to manage and configure credentials for the carrier integration service.

## Supported Carriers

### International Carriers
- **DHL Express** - Global express shipping
- **FedEx** - International courier delivery
- **UPS** - Worldwide logistics

### Colombian Carriers
- **Servientrega** - National courier service
- **Interrapidisimo** - Regional logistics provider
- **Deprisa** - Express courier and logistics service
- **Coordinadora** - Nationwide transportation and logistics network

### Financial Services
- **Banco de la República** - TRM (Tasa Representativa del Mercado) exchange rates

## Credential Configuration Methods

### 1. Environment Variables
Set credentials as environment variables in `.env` file or system environment:

```bash
# DHL Credentials
export DHL_API_KEY="your-dhl-api-key"
export DHL_API_SECRET="your-dhl-secret"
export DHL_ACCOUNT_NUMBER="your-dhl-account"

# FedEx Credentials
export FEDEX_CLIENT_ID="your-fedex-client-id"
export FEDEX_CLIENT_SECRET="your-fedex-secret"
export FEDEX_ACCOUNT_NUMBER="your-fedex-account"

# UPS Credentials
export UPS_CLIENT_ID="your-ups-client-id"
export UPS_CLIENT_SECRET="your-ups-secret"
export UPS_ACCOUNT_NUMBER="your-ups-account"

# Servientrega Credentials
export SERVIENTREGA_USER="your-servientrega-user"
export SERVIENTREGA_PASSWORD="your-servientrega-password"
export SERVIENTREGA_BILLING_CODE="your-billing-code"

# Interrapidisimo Credentials
export INTERRAPIDISIMO_API_KEY="your-inter-api-key"
export INTERRAPIDISIMO_CLIENT_CODE="your-client-code"

# Deprisa Credentials
export DEPRISA_API_KEY="your-deprisa-api-key"
export DEPRISA_CLIENT_ID="your-deprisa-client-id"
export DEPRISA_CLIENT_SECRET="your-deprisa-secret"

# Coordinadora Credentials
export COORDINADORA_API_KEY="your-coordinadora-api-key"
export COORDINADORA_API_PASSWORD="your-coordinadora-password"
export COORDINADORA_NIT="your-coordinadora-nit"
export COORDINADORA_CLIENT_CODE="your-coordinadora-client-code"
```

### 2. API Endpoints
Use the credential management API to store/update credentials:

#### Store Credential
```bash
curl -X POST http://localhost:8009/credentials/store \
  -H "Authorization: Bearer admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "carrier": "DHL",
    "credential_type": "API_KEY",
    "credential_value": "your-api-key",
    "description": "DHL Production API Key"
  }'
```

#### Rotate Credential
```bash
curl -X POST http://localhost:8009/credentials/rotate \
  -H "Authorization: Bearer admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "carrier": "DHL",
    "credential_type": "API_KEY",
    "new_value": "new-api-key"
  }'
```

#### Check Credential Status
```bash
curl -X GET http://localhost:8009/credentials/status \
  -H "Authorization: Bearer admin-secret-key"
```

### 3. JSON File Import
Create a `credentials.json` file:

```json
{
  "DHL": {
    "API_KEY": "your-dhl-api-key",
    "API_SECRET": "your-dhl-secret",
    "ACCOUNT_NUMBER": "your-account"
  },
  "FEDEX": {
    "CLIENT_ID": "your-fedex-id",
    "CLIENT_SECRET": "your-fedex-secret",
    "ACCOUNT_NUMBER": "your-account"
  }
}
```

Import using the initialization script:
```bash
python scripts/init_credentials.py --production
```

## Security Features

### Encryption
- All credentials are encrypted using AES-256 before storage
- Encryption key must be set via `CARRIER_ENCRYPTION_KEY` environment variable
- Never commit encryption keys to version control

### Access Control
- Admin API key required for credential management operations
- Set via `ADMIN_API_KEY` environment variable
- Use strong, randomly generated keys in production

### Credential Rotation
- Support for credential rotation without downtime
- Old credentials marked as inactive but retained for audit
- Automatic failover to backup credentials if available

## Development Setup

### Quick Start with Test Credentials
```bash
# Initialize test credentials
python scripts/init_credentials.py

# Or via API
curl -X POST http://localhost:8009/credentials/initialize \
  -H "Authorization: Bearer admin-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"environment": "development"}'
```

### Docker Compose
The service includes credential volume mounting:
```yaml
volumes:
  - carrier_credentials:/app/credentials
```

## Production Setup

### 1. Generate Security Keys
```python
# Generate encryption key
from cryptography.fernet import Fernet
encryption_key = Fernet.generate_key()
print(f"CARRIER_ENCRYPTION_KEY={encryption_key.decode()}")

# Generate admin API key
import secrets
admin_key = secrets.token_urlsafe(32)
print(f"ADMIN_API_KEY={admin_key}")
```

### 2. Set Environment Variables
```bash
# Copy template
cp .env.production.template .env.production

# Edit with actual values
nano .env.production
```

### 3. Initialize Credentials
```bash
# From environment variables
python scripts/init_credentials.py --production

# Or via API
curl -X POST https://your-domain/credentials/initialize \
  -H "Authorization: Bearer your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"environment": "production"}'
```

## Monitoring

### Health Check
The service includes credential validation in health checks:
```bash
curl http://localhost:8009/health
```

### Metrics
Prometheus metrics track:
- Credential rotation events
- Failed authentication attempts
- API call success rates per carrier

## Troubleshooting

### Common Issues

1. **Missing Credentials**
   - Check environment variables are set
   - Verify credential initialization completed
   - Check database connectivity

2. **Authentication Failures**
   - Verify credentials are correct for environment (sandbox vs production)
   - Check carrier API status
   - Review error logs for specific error codes

3. **Encryption Errors**
   - Ensure `CARRIER_ENCRYPTION_KEY` is set and valid
   - Check key format (32 bytes for AES-256)
   - Verify database write permissions

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
```

## API Documentation

### Credential Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/credentials/store` | POST | Store new credential | Yes |
| `/credentials/rotate` | POST | Rotate existing credential | Yes |
| `/credentials/status` | GET | Get all credential status | Yes |
| `/credentials/status/{carrier}` | GET | Get carrier credential status | Yes |
| `/credentials/{carrier}/{type}` | DELETE | Deactivate credential | Yes |
| `/credentials/initialize` | POST | Initialize from environment | Yes |

## Best Practices

1. **Never hardcode credentials** in source code
2. **Use different credentials** for development/staging/production
3. **Rotate credentials regularly** (recommended: every 90 days)
4. **Monitor credential usage** for anomalies
5. **Implement rate limiting** to prevent credential abuse
6. **Use webhook authentication** for carrier callbacks
7. **Audit credential access** and modifications
8. **Backup encryption keys** securely
9. **Test credential rotation** in staging before production
10. **Document credential dependencies** for disaster recovery

## Support

For credential-related issues:
1. Check this documentation
2. Review service logs
3. Contact carrier support for API issues
4. Open internal ticket for credential rotation