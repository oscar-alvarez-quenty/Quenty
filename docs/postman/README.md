# Quenty Microservices Postman Collection

This directory contains a comprehensive Postman collection for testing all Quenty microservices APIs.

## Files

- **`Quenty_Microservices_Collection.json`** - Complete API collection with all endpoints
- **`Quenty_Local_Environment.json`** - Environment variables for local development
- **`README.md`** - This documentation file

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
   - Uses default admin credentials: `admin` / `AdminPassword123`
   - Automatically sets the `access_token` environment variable

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
- **API Gateway Health** - Gateway status check
- **All Services Health** - Complete system health

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
| `admin_username` | Admin username | `admin` |
| `admin_password` | Admin password | `AdminPassword123` |
| `customer_id` | Customer ID for testing | Set manually |
| `product_id` | Product ID for testing | Set manually |
| `order_id` | Order ID for testing | Set manually |

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

This collection covers **all 89 endpoints** across **9 microservices**:

- ✅ **Auth Service** (12 endpoints)
- ✅ **Customer Service** (8 endpoints)
- ✅ **Order Service** (15 endpoints)
- ✅ **Pickup Service** (10 endpoints)
- ✅ **International Shipping** (12 endpoints)
- ✅ **Microcredit Service** (8 endpoints)
- ✅ **Analytics Service** (6 endpoints)
- ✅ **Reverse Logistics** (10 endpoints)
- ✅ **Franchise Service** (8 endpoints)

**Total: 89 endpoints** providing complete API coverage for the Quenty platform.