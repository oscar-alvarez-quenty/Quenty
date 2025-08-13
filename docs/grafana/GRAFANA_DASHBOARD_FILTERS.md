# Grafana Dashboard Filters - Quenty Microservices Logs

## 🎯 Overview

The Quenty Microservices Logs dashboard has been enhanced with comprehensive filtering capabilities to help you analyze logs more effectively across all 10 microservices.

## 📊 Dashboard Access

- **URL**: http://localhost:3000
- **Dashboard**: "Quenty Microservices Logs"
- **Default Credentials**: admin/admin

## 🔍 Available Filters

### 1. **Service Filter** (Multi-select)
Filter logs by specific microservices:
- **All** - Show logs from all services
- **API Gateway** - Central routing and request handling
- **Auth Service** - Authentication and authorization
- **Customer Service** - Customer management operations
- **Order Service** - Order processing and management
- **Pickup Service** - Pickup scheduling and logistics
- **International Shipping** - Cross-border shipping management
- **Microcredit Service** - Financial credit operations
- **Analytics Service** - Business intelligence and metrics
- **Reverse Logistics** - Returns and reverse shipping
- **Franchise Service** - Franchise operations management

### 2. **Log Level Filter** (Multi-select)
Filter by log severity:
- **ERROR** - Critical errors and exceptions
- **WARNING** - Warning messages and potential issues
- **INFO** - Informational messages and events
- **DEBUG** - Detailed debugging information

### 3. **Search Text Filter** (Text Input)
Free-text search across log messages:
- Search for specific error messages
- Look for customer IDs, order numbers, etc.
- Find specific function names or operations
- Example searches:
  - `authentication failed`
  - `customer-123`
  - `order created`
  - `database connection`

### 4. **Message Code Filter** (Multi-select)
Filter by structured message codes:
- **AGW_** - API Gateway messages
- **AUTH_** - Authentication service messages
- **CUST_** - Customer service messages
- **ORD_** - Order service messages
- **PKP_** - Pickup service messages
- **INTL_** - International shipping messages
- **MC_** - Microcredit service messages
- **ANL_** - Analytics service messages
- **RL_** - Reverse logistics messages
- **FRN_** - Franchise service messages

## 📈 Dashboard Panels

### 1. **All Microservices Logs (Filtered)**
- Main log viewer with all filters applied
- Shows raw log entries with timestamps
- Sortable table format

### 2. **Structured Logs (JSON Parsed)**
- Parses JSON structured logs
- Formatted display: `timestamp [LEVEL] service: event`
- Better readability for structured messages

### 3. **Error & Exception Logs**
- Automatically filters for error-related content
- Includes: error, exception, failed, failure keywords
- Respects service filter selection

### 4. **Service Activity & Events**
- Shows service lifecycle events
- Includes: started, initialized, registered, created, updated
- Useful for monitoring service health

### 5. **Business Events & Transactions**
- Filters business-related activities
- Includes: order, customer, payment, credit, shipment, pickup
- Combines with message code filters

### 6. **Log Volume by Service (5min rate)**
- Time series chart showing log volume
- Grouped by service logger
- 5-minute rate calculation
- Helps identify chatty services or issues

## 🚀 Usage Examples

### Example 1: Debug Authentication Issues
1. Set **Service** filter to "Auth Service"
2. Set **Log Level** to "ERROR"
3. Set **Search Text** to "authentication"
4. Review results in all panels

### Example 2: Monitor Order Processing
1. Set **Service** filter to "Order Service"
2. Set **Message Code** to "ORD_"
3. Set **Search Text** to "order"
4. Check "Business Events & Transactions" panel

### Example 3: System Health Check
1. Leave **Service** as "All"
2. Set **Log Level** to "ERROR" and "WARNING"
3. Check "Error & Exception Logs" panel
4. Monitor "Log Volume" for spikes

### Example 4: Trace Customer Journey
1. Set **Search Text** to specific customer ID
2. Leave other filters as "All"
3. Review "All Microservices Logs" for complete journey

## 🔧 Advanced Tips

### Filter Combinations
- Use multiple service filters to compare specific services
- Combine log level and search text for precise filtering
- Message codes work great with service filters

### Time Range Selection
- Use Grafana's time picker (top right) for specific periods
- Default: Last 1 hour
- Useful ranges: Last 5 minutes, Last 30 minutes, Last 24 hours

### Refresh Settings
- Auto-refresh: 30 seconds (configurable)
- Manual refresh: Refresh button or Ctrl+R

### Sharing and Alerts
- Use Grafana's share feature for specific filtered views
- Set up alerts based on error log volume
- Export data for further analysis

## 📝 Structured Log Message Format

Our enhanced logging provides structured JSON messages:

```json
{
  "code": "CUST_I001",
  "message": "Customer created successfully",
  "level": "info",
  "description": "New customer account created",
  "event": "Customer created successfully with ID: 12345",
  "logger": "customer-service",
  "timestamp": "2025-07-24T02:50:15.123Z"
}
```

### Message Code Format
- **Prefix**: Service identifier (CUST_, ORD_, etc.)
- **Type**: E=Error, W=Warning, I=Info, D=Debug
- **Number**: Sequential number (001, 002, etc.)
- **Example**: `CUST_E001`, `ORD_I005`, `AUTH_W003`

## 🎛️ Dashboard Customization

### Adding New Filters
Edit `/docker/grafana/provisioning/dashboards/quenty-microservices-logs.json`:
1. Add new template variable in `templating.list`
2. Update panel queries to use the new variable
3. Restart Grafana container

### Modifying Queries
- Panel queries use LogQL (Loki Query Language)
- Template variables: `$variable_name`
- Regex filters: `logger=~".*($service).*"`
- Text search: `|~ "search_term"`

## 🔄 Testing the Dashboard

Run the test script to generate sample logs:
```bash
python3 test-logging.py
```

This will:
- Hit health endpoints across all services
- Generate authentication errors (403s)
- Create various log entries for testing filters

## 📞 Support

For issues with the dashboard:
1. Check Loki is receiving logs: http://localhost:3100/ready
2. Verify Grafana data source: Settings → Data Sources → Loki
3. Check service logs: `docker logs quenty-<service-name>`
4. Restart Grafana: `docker restart quenty-grafana`