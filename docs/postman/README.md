# Quenty Microservices Postman Collection

This directory contains a comprehensive Postman collection for testing all Quenty microservices APIs, updated with all tested endpoints and Prometheus metrics support.

## Files

- **`Quenty_Microservices_Collection.json`** - Complete API collection with all endpoints and metrics
- **`Quenty_Local_Environment.json`** - Environment variables for local development with service URLs
- **`Quenty_Test_Workflows.json`** - Pre-configured test workflows for common operations
- **`README.md`** - This documentation file
- **`SETUP_GUIDE.md`** - Detailed setup and configuration guide

## Quick Start

### 1. Import Collection and Environment

1. Open Postman
2. Click **Import** button
3. Import both files:
   - `Quenty_Microservices_Collection.json`
   - `Quenty_Local_Environment.json`
4. Select the "Quenty Local Environment" from the environment dropdown

### 2. Start the Application

Make sure your Quenty microservices are running:

```bash
cd /path/to/Quenty
docker compose -f docker-compose.microservices.yml up -d
```

Verify all services are healthy:
```bash
curl http://localhost:8000/services/health
```

### 3. Authenticate

1. Open the **Authentication & Users** folder
2. Run the **Login** request
   - Uses default admin credentials: `admin@quenty.com` / `AdminPassword123`
   - Automatically sets the `access_token` environment variable
   - Or use the pre-configured `admin_token` for immediate testing

## Collection Structure

### 🔐 Authentication & Users
- **Login** - Authenticate and get access token
- **Register User** - Create new user accounts
- **Get Profile** - Get current user profile
- **List Users** - View all users
- **Refresh Token** - Refresh authentication token

### 👥 Customer Management
- **Create Customer** - Add new customer profiles
- **List Customers** - View customer list
- **Get Customer by ID** - Retrieve specific customer
- **Create Support Ticket** - Customer support functionality
- **Get Customer Analytics** - Customer metrics and insights

### 📦 Product & Order Management
- **Create Product** - Add products to catalog
- **List Products** - View product inventory
- **Create Order** - Place new orders
- **List Orders** - View order history
- **Update Order Status** - Manage order lifecycle
- **Get Inventory** - Check stock levels

### 🚚 Pickup & Routes
- **Schedule Pickup** - Arrange item collection
- **List Pickups** - View pickup schedules
- **Assign Pickup** - Assign drivers to pickups
- **Complete Pickup** - Mark pickups as completed
- **Check Pickup Availability** - Verify pickup slots
- **Create Route** - Plan delivery routes

### 🌍 International Shipping
- **Create Country** - Add shipping destinations
- **List Countries** - View available countries
- **Create Carrier** - Add shipping carriers
- **List Carriers** - View carrier list
- **Create Manifest** - Generate shipping manifests
- **List Manifests** - View manifest history
- **Get Shipping Rates** - Calculate shipping costs
- **Track Shipment** - Track package status

### 💰 Microcredit Services
- **Create Credit Application** - Apply for microcredit
- **List Credit Applications** - View applications
- **Make Credit Decision** - Approve/reject applications
- **List Credit Accounts** - View active accounts
- **Disburse Credit** - Release approved funds
- **Make Payment** - Process loan payments
- **Get Credit Score** - Check customer credit rating

### 📊 Analytics & Reporting
- **Get Dashboard Metrics** - Business overview metrics
- **Ingest Metric** - Add new data points
- **Query Analytics** - Custom data queries
- **Generate Report** - Create business reports
- **Get Report Status** - Check report progress
- **Get Business Trends** - Trend analysis

### ↩️ Reverse Logistics
- **Create Return Request** - Initiate product returns
- **List Returns** - View return requests
- **Approve Return** - Approve return requests
- **Schedule Return Pickup** - Arrange return collection
- **Create Inspection Report** - Document item condition
- **Process Return** - Complete return processing
- **Track Return** - Monitor return status

### 🏢 Franchise Management
- **Create Franchise** - Register new franchises
- **List Franchises** - View franchise network
- **Update Franchise Status** - Manage franchise status
- **List Territories** - View available territories
- **Get Territory by Code** - Territory details
- **Get Franchise Performance** - Performance metrics

### 🏥 System Health & Monitoring
- **API Gateway Health** - Gateway status check (port 8000)
- **API Gateway Metrics** - Prometheus metrics for gateway
- **Service Health Checks** - Individual health checks for all 10 microservices
- **Service Metrics** - Prometheus metrics for all microservices
- **Direct Service Access** - Bypass gateway for individual service testing

## Usage Tips

### Authentication Flow
1. **Always start with Login** - Run the Login request first
2. **Token Auto-Setting** - The login request automatically sets the `access_token` variable
3. **Token Expiry** - If you get 401 errors, run the Login request again

### Working with IDs
Many requests require IDs from previous requests. The collection includes variables for common IDs:
- `customer_id` - Set after creating a customer
- `product_id` - Set after creating a product
- `order_id` - Set after creating an order
- etc.

**Tip:** After creating resources, copy their IDs into the environment variables for easy reuse.

### Sample Data Flow
Here's a typical workflow for testing the complete system:

1. **Authentication** → Login
2. **Customer Management** → Create Customer (copy customer_id)
3. **Product Management** → Create Product (copy product_id)
4. **Order Management** → Create Order using customer_id and product_id
5. **Pickup Management** → Schedule Pickup for the order
6. **Analytics** → Ingest metrics and view dashboard

### Testing Different Scenarios

#### Happy Path
- Login → Create Customer → Create Product → Create Order → Schedule Pickup

#### Return Flow
- Create Order → Create Return Request → Approve Return → Schedule Return Pickup

#### Credit Flow
- Create Customer → Create Credit Application → Make Credit Decision → Disburse Credit

## Environment Variables

The environment includes these key variables:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `base_url` | API Gateway URL | `http://localhost:8000` |
| `access_token` | JWT authentication token | Auto-set by login |
| `admin_username` | Admin username | `admin@quenty.com` |
| `admin_password` | Admin password | `AdminPassword123` |
| `customer_id` | Customer ID for testing | Set manually |
| `product_id` | Product ID for testing | Set manually |
| `order_id` | Order ID for testing | Set manually |
| `admin_token` | Pre-configured admin JWT token | Ready to use |
| `auth_service_url` | Direct auth service URL | `http://localhost:8009` |
| `customer_service_url` | Direct customer service URL | `http://localhost:8001` |
| Other service URLs | Direct access to all microservices | Ports 8001-8009 |

## Error Troubleshooting

### Common Issues

**401 Unauthorized**
- Solution: Run the Login request to refresh your token

**500 Internal Server Error**
- Check if all microservices are running: `curl http://localhost:8000/services/health`
- Check Docker container logs: `docker logs quenty-api-gateway`

**Connection Refused**
- Ensure Docker services are running: `docker compose ps`
- Verify port 8000 is accessible: `curl http://localhost:8000/health`

**Validation Errors**
- Check request body format matches the expected schema
- Ensure required fields are included
- Verify data types (strings, numbers, booleans)

## API Documentation

For detailed API documentation for each service, see:
- `/docs/microservices/` - Individual service documentation
- `http://localhost:8000/docs` - Interactive API documentation (when running)

## Support

For issues or questions:
1. Check the service logs: `docker logs <service-name>`
2. Verify service health: `curl http://localhost:8000/services/health`
3. Review the microservice documentation in `/docs/microservices/`

## Collection Coverage

This collection covers **all endpoints** across **10 microservices** with **comprehensive testing**:

| Service | Port | Health | Metrics | Business Endpoints | Status |
|---------|------|--------|---------|-------------------|---------|
| **API Gateway** | 8000 | ✅ | ✅ | Routes all services | ✅ Working |
| **Auth Service** | 8009 | ✅ | ✅ | User management | ✅ Working |
| **Customer Service** | 8001 | ✅ | ✅ | Customer CRUD | ✅ Working |
| **Order Service** | 8002 | ✅ | ✅ | Order management | ✅ Working |
| **Pickup Service** | 8003 | ✅ | ✅ | Pickup scheduling | ✅ Working |
| **Intl Shipping** | 8004 | ✅ | ✅ | Shipping & manifests | ✅ Working |
| **Microcredit** | 8005 | ✅ | ✅ | Credit applications | ✅ Working |
| **Analytics** | 8006 | ✅ | ✅ | Dashboard (DB issue) | ⚠️ Migration needed |
| **Reverse Logistics** | 8007 | ✅ | ✅ | Returns processing | ✅ Working |
| **Franchise** | 8008 | ✅ | ✅ | Franchise management | ✅ Working |

## Testing Status

- **Services Tested**: 10/10
- **Fully Working**: 9/10 (90%)
- **Health Checks**: 100% ✅
- **Metrics Collection**: 100% ✅
- **Authentication**: Working with admin@quenty.com
- **Wildcard Permissions**: ✅ Implemented for superusers

### Known Issues

**Analytics Service**
- Health and metrics work perfectly
- Dashboard endpoint needs database migration
- Error: `relation "metrics" does not exist`

### Key Features Added

1. **Complete Health Monitoring**
   - Individual health checks for all 10 services
   - Prometheus metrics endpoints for all services
   - Direct service access (bypass API Gateway)

2. **Enhanced Authentication**
   - Updated admin credentials: admin@quenty.com
   - Pre-configured admin token for immediate testing
   - Wildcard permission support for superusers

3. **Service Architecture Documentation**
   - Complete port mapping and service URLs
   - Direct service access capabilities
   - Comprehensive testing coverage

**Total Coverage**: Complete API testing for the entire Quenty microservices platform.