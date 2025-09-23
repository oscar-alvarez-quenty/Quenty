# Carrier Integration Setup Guide

This guide explains how to configure the shipping carrier integrations for Quenty.

## Supported Carriers

- **DHL Express** - International express shipping
- **UPS** - United Parcel Service
- **FedEx** - Federal Express
- **Servientrega** - Colombian national carrier
- **InterRapidisimo** - Colombian national carrier
- **Pasarex** - International mailbox service (optional)
- **Aeropost** - International mailbox service (optional)

## Configuration Steps

### 1. Copy the Environment Template

```bash
cp .env.carriers.example .env.carriers
```

### 2. Add Your Carrier Credentials

Edit the `.env.carriers` file and add your actual carrier credentials:

```bash
nano .env.carriers
```

### 3. Configure Each Carrier

#### DHL Express
```env
DHL_API_KEY=your-actual-api-key
DHL_API_SECRET=your-actual-secret
DHL_USERNAME=your-username
DHL_PASSWORD=your-password
DHL_ACCOUNT_NUMBER=123456789
DHL_ENVIRONMENT=sandbox  # Use 'production' for live
```

#### UPS
```env
UPS_CLIENT_ID=your-client-id
UPS_CLIENT_SECRET=your-client-secret
UPS_ACCOUNT_NUMBER=your-account
UPS_ACCESS_LICENSE_NUMBER=your-license
UPS_USERNAME=your-username
UPS_PASSWORD=your-password
UPS_ENVIRONMENT=sandbox  # Use 'production' for live
```

#### FedEx
```env
FEDEX_CLIENT_ID=your-client-id
FEDEX_CLIENT_SECRET=your-client-secret
FEDEX_ACCOUNT_NUMBER=your-account
FEDEX_METER_NUMBER=your-meter
FEDEX_KEY=your-key
FEDEX_PASSWORD=your-password
FEDEX_ENVIRONMENT=sandbox  # Use 'production' for live
```

#### Servientrega (Colombia)
```env
SERVIENTREGA_USER=your-user
SERVIENTREGA_PASSWORD=your-password
SERVIENTREGA_BILLING_CODE=your-billing-code
SERVIENTREGA_ID_CLIENT=your-client-id
SERVIENTREGA_NAME_PACK=your-pack-name
SERVIENTREGA_ENVIRONMENT=test  # Use 'production' for live
```

#### InterRapidisimo (Colombia)
```env
INTERRAPIDISIMO_API_KEY=your-api-key
INTERRAPIDISIMO_CLIENT_CODE=your-client-code
INTERRAPIDISIMO_USERNAME=your-username
INTERRAPIDISIMO_PASSWORD=your-password
INTERRAPIDISIMO_CONTRACT_NUMBER=your-contract
INTERRAPIDISIMO_ENVIRONMENT=sandbox  # Use 'production' for live
```

### 4. Start the Services

With Docker Compose:
```bash
docker-compose up -d
```

Or restart if already running:
```bash
docker-compose restart carrier-integration carrier-worker carrier-beat
```

### 5. Verify Configuration

Check if carriers are properly initialized:

```bash
# Check carrier status
curl http://localhost:8009/api/v1/carriers/status

# Check specific carrier health
curl http://localhost:8009/api/v1/carriers/DHL/health
```

## Environment Variables

### Required Variables

Each carrier requires specific credentials. The system will automatically detect which carriers are configured based on the presence of their credentials in the environment.

### Security Configuration

```env
# Encryption key for storing credentials (32 bytes)
ENCRYPTION_KEY=your-32-byte-encryption-key-here!!

# JWT Secret for API authentication
CARRIER_SECRET_KEY=your-secret-key-for-jwt-tokens
```

### Optional Settings

```env
# Logging
CARRIER_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# API Configuration
CARRIER_API_TIMEOUT=30   # Timeout in seconds
CARRIER_MAX_RETRIES=3    # Number of retries
CARRIER_RETRY_DELAY=1    # Delay between retries
```

## Testing the Integration

### 1. Get a Shipping Quote

```bash
curl -X POST http://localhost:8009/api/v1/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "carrier": "DHL",
    "origin": {
      "country": "CO",
      "city": "Bogota",
      "postal_code": "110111",
      "street": "Calle 100 #10-20"
    },
    "destination": {
      "country": "US",
      "city": "Miami",
      "postal_code": "33101",
      "street": "123 Main St"
    },
    "packages": [{
      "weight_kg": 1.5,
      "length_cm": 30,
      "width_cm": 20,
      "height_cm": 10
    }]
  }'
```

### 2. Track a Shipment

```bash
curl -X POST http://localhost:8009/api/v1/tracking \
  -H "Content-Type: application/json" \
  -d '{
    "carrier": "DHL",
    "tracking_number": "1234567890"
  }'
```

## Monitoring

### View Logs

```bash
# Carrier integration service logs
docker logs quenty-carrier-integration -f

# Worker logs
docker logs quenty-carrier-worker -f

# Celery monitoring
open http://localhost:5555  # Flower UI
```

### Check Health

```bash
# Overall health check
curl http://localhost:8009/health

# Metrics
curl http://localhost:8009/metrics
```

## Troubleshooting

### Common Issues

1. **Carrier not initializing**
   - Check that credentials are properly set in `.env.carriers`
   - Verify environment is correct (sandbox vs production)
   - Check logs for specific error messages

2. **Authentication failures**
   - Ensure credentials are valid and active
   - Check if API access is enabled for your account
   - Verify environment matches your credentials

3. **Connection timeouts**
   - Check network connectivity
   - Verify firewall rules allow outbound HTTPS
   - Increase `CARRIER_API_TIMEOUT` if needed

### Debug Mode

Enable debug logging:
```env
CARRIER_LOG_LEVEL=DEBUG
```

Then restart services and check logs for detailed information.

## API Documentation

Once running, access the interactive API documentation:

- Swagger UI: http://localhost:8009/docs
- ReDoc: http://localhost:8009/redoc

## Support

For carrier-specific support:
- DHL: https://developer.dhl.com/support
- UPS: https://www.ups.com/upsdeveloperkit
- FedEx: https://developer.fedex.com/support
- Servientrega: Contact your account manager
- InterRapidisimo: Contact technical support

## Security Notes

1. **Never commit `.env.carriers` to version control**
2. Use strong encryption keys in production
3. Rotate credentials regularly
4. Use separate credentials for sandbox/production
5. Monitor API usage and set rate limits
6. Enable webhook authentication for production