# Grafana Raw Microservice Logs Dashboard

## 🎯 Overview

The "Quenty Raw Microservice Logs" dashboard provides a simplified, focused view of raw log data from all microservices with just two essential filters for efficient log analysis.

## 📊 Dashboard Access

- **URL**: http://localhost:3000
- **Dashboard Name**: "Quenty Raw Microservice Logs"
- **UID**: `quenty-raw-logs`
- **Credentials**: admin / F3l1p301
- **Auto-refresh**: 10 seconds
- **Default Time Range**: Last 30 minutes

## 🔍 Available Filters

### 1. **Service Filter** (Multi-select)
Select one or more specific microservices to focus your log analysis:

- **All** - Show logs from all services (default)
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

**Usage Tips:**
- Select multiple services to compare their activity
- Choose specific services when troubleshooting issues
- Use "All" for system-wide monitoring

### 2. **Search Text Filter** (Free Text Input)
Search for specific text within log messages:

**Common Search Examples:**
- **Error Keywords**: `error`, `exception`, `failed`, `timeout`
- **Business Events**: `order created`, `customer registered`, `payment processed`
- **System Events**: `started`, `initialized`, `connected`, `shutdown`
- **Identifiers**: `user-123`, `order-456`, `transaction-789`
- **API Endpoints**: `/api/v1/customers`, `/health`, `/login`
- **Status Codes**: `200`, `401`, `403`, `500`

**Search Features:**
- Case-insensitive matching
- Supports regex patterns
- Real-time filtering as you type
- Works across all log fields

## 📈 Dashboard Panels

### 1. **Raw Microservice Logs Stream** (Main Panel)
- **Type**: Table view
- **Purpose**: Real-time stream of raw log entries
- **Features**:
  - Sortable by timestamp (newest first)
  - Shows: Time, Log Message, Service Name, Log Level
  - Filterable table columns
  - Color-coded log levels
  - Responsive column widths
  - Up to 1000 recent entries

**Column Details:**
- **Time**: Precise timestamp (180px width)
- **Line**: Full log message content (800px width)
- **Service Name**: Source microservice (150px width)
- **Level**: Log level with color background (80px width)

### 2. **Log Volume by Service** (Time Series)
- **Type**: Time series chart
- **Purpose**: Visualize log activity patterns over time
- **Features**:
  - 1-minute aggregation buckets
  - Separate line per service
  - Legend with last values
  - Interactive tooltips
  - Zoom and pan capabilities

**Use Cases:**
- Identify chatty services
- Spot unusual activity spikes
- Monitor service health patterns
- Detect system issues

### 3. **Log Level Distribution** (Pie Chart)
- **Type**: Pie chart
- **Purpose**: Show proportion of different log levels
- **Features**:
  - Color-coded by log level (ERROR=red, WARNING=orange, INFO=blue, DEBUG=green)
  - Shows both count and percentage
  - Interactive legend
  - Real-time updates

**Insights:**
- High ERROR/WARNING ratios indicate issues
- DEBUG level distribution shows verbosity
- INFO levels show normal operations
- Helps prioritize investigation areas

### 4. **Recent Errors & Warnings** (Error Focus Panel)
- **Type**: Table view
- **Purpose**: Quick access to recent problems
- **Features**:
  - Filters automatically for ERROR and WARNING levels
  - Same layout as main panel
  - Sorted by most recent first
  - Respects service and search filters

**Benefits:**
- Fast troubleshooting access
- No need to scroll through INFO/DEBUG logs
- Quick problem identification
- Focused error analysis

## 🚀 Usage Examples

### Example 1: Monitor Specific Service
1. Set **Service** filter to "Customer Service"
2. Leave **Search Text** empty
3. Observe all customer service activity in real-time
4. Check log volume trends and error ratios

### Example 2: Search for Authentication Issues
1. Set **Service** filter to "Auth Service"
2. Set **Search Text** to "authentication"
3. Review authentication-related logs
4. Check error panel for auth failures

### Example 3: Track Order Processing
1. Set **Service** filter to "Order Service"
2. Set **Search Text** to "order"
3. Monitor order creation and processing logs
4. Analyze order volume patterns

### Example 4: System-wide Error Monitoring
1. Set **Service** filter to "All"
2. Leave **Search Text** empty
3. Focus on "Recent Errors & Warnings" panel
4. Monitor "Log Level Distribution" for error ratios

### Example 5: Debug Specific Transaction
1. Set **Service** filter to "All"
2. Set **Search Text** to specific transaction ID (e.g., "order-12345")
3. Trace transaction across all services
4. Follow the complete request flow

## 🔧 Advanced Features

### Real-time Monitoring
- **Auto-refresh**: 10-second intervals
- **Live Updates**: New logs appear automatically
- **Time Range**: Configurable (default: last 30 minutes)
- **Refresh Options**: 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d

### Performance Optimization
- **Efficient Queries**: Optimized LogQL for fast results
- **Limited Results**: Max 1000 entries to prevent browser overload
- **Smart Filtering**: Client and server-side filtering
- **Responsive Design**: Adapts to different screen sizes

### Data Visualization
- **Color Coding**: Log levels have distinct colors
- **Responsive Layout**: Panels adjust to screen size
- **Interactive Elements**: Click, zoom, and hover interactions
- **Export Options**: Data export capabilities

## 🎛️ Customization Options

### Time Range Modification
- Use Grafana's time picker (top right)
- Common ranges: Last 5m, 15m, 1h, 6h, 24h
- Custom ranges: Specify exact start/end times
- Relative ranges: "now-1h" to "now"

### Panel Customization
- Resize panels by dragging corners
- Reorder panels by drag and drop
- Modify queries through panel edit mode
- Adjust refresh rates per panel

### Filter Enhancement
To add more filters, edit the dashboard JSON:
1. Add new template variables in `templating.list`
2. Update panel queries to use new variables
3. Restart Grafana to apply changes

## 📝 Query Details

### Main Log Stream Query
```logql
{job="microservices", service_name=~".*($service).*"} |~ "$search_text"
```

### Log Volume Query
```logql
sum by (service_name) (count_over_time({job="microservices", service_name=~".*($service).*"} |~ "$search_text" [1m]))
```

### Log Level Distribution Query
```logql
sum by (level) (count_over_time({job="microservices", service_name=~".*($service).*"} |~ "$search_text" [$__range]))
```

### Errors & Warnings Query
```logql
{job="microservices", service_name=~".*($service).*", level=~"(error|warning)"} |~ "$search_text"
```

## 🔍 Troubleshooting

### No Data Showing
1. **Check Time Range**: Ensure logs exist in selected timeframe
2. **Verify Filters**: Remove filters to see if data appears
3. **Check Loki**: Ensure Loki is receiving logs (`http://localhost:3100/ready`)
4. **Service Status**: Verify microservices are running and logging

### Slow Performance
1. **Narrow Time Range**: Use shorter time windows (5-15 minutes)
2. **Add Filters**: Use service filter to reduce data volume
3. **Specific Search**: Use search text to limit results
4. **Check Resources**: Monitor Grafana/Loki resource usage

### Missing Services
1. **Check Service Names**: Ensure service names match filter options
2. **Log Format**: Verify logs include `service_name` label
3. **Loki Ingestion**: Check if Loki is receiving logs from all services
4. **Promtail Config**: Verify log shipping configuration

## 🌟 Best Practices

### Efficient Monitoring
- **Start Broad**: Begin with "All" services, then narrow down
- **Use Time Windows**: Focus on relevant time periods
- **Combine Filters**: Use both service and search filters together
- **Monitor Patterns**: Watch log volume and level distribution

### Troubleshooting Workflow
1. **Check Error Panel**: Look for recent errors/warnings
2. **Identify Service**: Use service filter to isolate problem area
3. **Search Keywords**: Use specific error terms in search
4. **Follow Timeline**: Use time range to trace issue progression
5. **Cross-reference**: Compare with other monitoring dashboards

### Performance Tips
- **Limit Time Range**: Avoid querying days/weeks of data
- **Use Filters**: Always apply service or search filters
- **Monitor Auto-refresh**: Disable if not needed for investigation
- **Export Data**: Use export for detailed analysis

## 📊 Integration with Other Dashboards

This raw logs dashboard complements other Quenty dashboards:

- **Microservices Logs Dashboard**: More complex filtering and analysis
- **Business Metrics Dashboard**: Correlate logs with business KPIs
- **Infrastructure Dashboard**: System-level monitoring
- **Executive Dashboard**: High-level system health

**Navigation Tip**: Use Grafana's dashboard links to switch between views during investigation.

## ✅ Dashboard Benefits

### Simplified Interface
- ✅ Only 2 essential filters (Service + Search)
- ✅ Clean, uncluttered design
- ✅ Fast loading and responsive
- ✅ Intuitive for all skill levels

### Comprehensive Coverage
- ✅ All 10 microservices included
- ✅ Real-time log streaming
- ✅ Multiple visualization types
- ✅ Error-focused troubleshooting panel

### Production Ready
- ✅ Optimized queries for performance
- ✅ Auto-refresh for monitoring
- ✅ Proper error handling
- ✅ Scalable design

The Raw Microservice Logs dashboard provides the perfect balance of simplicity and power for effective log analysis and troubleshooting! 🚀