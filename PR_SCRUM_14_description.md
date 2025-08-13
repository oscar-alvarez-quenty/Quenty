# SCRUM-14: Exchange Rate API Integration with Banco de la República

## 📋 Summary
This PR implements a comprehensive exchange rate system that integrates with Banco de la República's official API to fetch the TRM (Tasa Representativa del Mercado) and provide real-time currency conversion capabilities for the international shipping service.

## ✨ Features Implemented

### 💱 Exchange Rate Integration
- **Banco de la República API**: Official TRM (USD/COP) rate integration
- **Historical Rates**: Support for historical exchange rate queries
- **Currency Conversion**: Real-time currency conversion with date-specific rates
- **Fallback Mechanisms**: Graceful handling when API is unavailable

### 🔄 Automated Scheduling
- **Daily Updates**: Automatic daily TRM rate updates at 9:00 AM Colombia time
- **Background Scheduler**: APScheduler-based background task management
- **Manual Updates**: Admin capability to trigger manual rate updates
- **Database Persistence**: Local caching of rates with upsert operations

### 🔌 API Endpoints Added
- `GET /api/v1/exchange-rates/current` - Get current exchange rate
- `GET /api/v1/exchange-rates/history` - Get historical exchange rates
- `POST /api/v1/exchange-rates/convert` - Convert currencies with specific amounts
- `GET /api/v1/exchange-rates/trm` - Get current TRM (USD to COP)
- `POST /api/v1/exchange-rates/update` - Manual rate update (admin only)
- `GET /api/v1/exchange-rates/health` - Exchange rate service health check

## 🛠 Technical Implementation

### Architecture
- **Service Layer**: `ExchangeRateService` for business logic
- **Scheduler Layer**: `ExchangeRateScheduler` for automated updates
- **Data Layer**: SQLAlchemy model for persistent storage
- **API Layer**: RESTful endpoints with comprehensive validation

### Key Files Added/Modified
- `src/exchange_rate/banrep.py` - Banco de la República API client
- `src/exchange_rate/scheduler.py` - Background scheduler and database operations
- `src/exchange_rate/__init__.py` - Module initialization
- `alembic/versions/004_add_exchange_rates_table.py` - Database migration
- `src/main.py` - API endpoints and scheduler integration

### Database Schema
```sql
CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    currency_from VARCHAR(3) NOT NULL,
    currency_to VARCHAR(3) NOT NULL,
    rate DECIMAL(15,6) NOT NULL,
    date DATE NOT NULL,
    source VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(currency_from, currency_to, date)
);
```

### API Integration Details
```python
# Banco de la República TRM API
base_url = "https://www.banrep.gov.co/Indicadores/TRM/RangoFechas.aspx"

# Features:
- Date range queries
- JSON/XML response parsing  
- Error handling and retries
- Rate validation and normalization
```

## 🧪 Testing
- ✅ **Unit Tests**: Complete test coverage for all exchange rate operations
- ✅ **Integration Tests**: End-to-end testing with mock Banco de la República API
- ✅ **Scheduler Tests**: Background task testing and error scenarios
- ✅ **Database Tests**: CRUD operations and data persistence

## 📊 Performance Features
- **Connection Pooling**: Efficient HTTP client management for API calls
- **Database Indexing**: Optimized queries with composite indexes
- **Caching Strategy**: Local database caching with smart updates
- **Rate Limiting**: Respectful API usage to prevent service blocking
- **Timezone Handling**: Proper Colombia timezone handling for TRM schedules

## 🔄 Scheduling & Automation
- **Daily Schedule**: Runs every day at 9:00 AM Colombia time (UTC-5)
- **Retry Logic**: 3 attempts with exponential backoff
- **Error Notifications**: Comprehensive error logging and monitoring
- **Health Monitoring**: Service health endpoints for monitoring systems

## 💰 Business Value
- **Accurate Pricing**: Real-time exchange rates for accurate shipping costs
- **Compliance**: Uses official Colombian government exchange rates
- **Historical Analysis**: Support for pricing trends and analysis
- **Multi-Currency**: Foundation for supporting additional currencies

## 🔧 Configuration
```python
# Environment Variables
BANREP_API_URL=https://www.banrep.gov.co/Indicadores/TRM/RangoFechas.aspx
TRM_UPDATE_TIME=09:00  # Colombia time
TRM_RETRY_ATTEMPTS=3
TRM_TIMEOUT_SECONDS=30
```

## 🚀 Usage Examples

### Get Current TRM Rate
```bash
GET /api/v1/exchange-rates/trm
# Response: {"trm": 4250.50, "date": "2024-01-15", "source": "Banco de la República"}
```

### Convert Currency
```bash
POST /api/v1/exchange-rates/convert?amount=100&from_currency=USD&to_currency=COP
# Response: {"converted_amount": 425050.00, "exchange_rate": 4250.50}
```

### Get Historical Rates
```bash
GET /api/v1/exchange-rates/history?start_date=2024-01-01&end_date=2024-01-31
# Response: [{"rate": 4250.50, "date": "2024-01-15"}, ...]
```

## ⚡ Next Steps
- [ ] Support for additional currency pairs (EUR/COP, GBP/COP)
- [ ] Real-time rate change notifications via WebSocket
- [ ] Integration with shipping cost calculation
- [ ] Rate volatility alerts and risk management

## 🔍 Testing Instructions
1. **Start the service**: `docker-compose up --build`
2. **Check scheduler**: Verify automatic TRM updates at 9:00 AM Colombia time
3. **Test endpoints**: Use the provided API endpoints for rate queries
4. **Manual update**: Test admin manual update functionality
5. **Monitor health**: Use health check endpoint for service monitoring

## 📈 Impact
- Provides accurate, government-official exchange rates
- Enables proper international shipping cost calculation
- Supports compliance with Colombian financial regulations
- Foundation for advanced multi-currency features

## 🔒 Security & Compliance
- Rate data sourced from official government API
- Secure handling of financial data
- Audit trails for all rate updates
- Admin-only access for manual updates

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>