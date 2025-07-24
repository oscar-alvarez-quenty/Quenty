# Quenty Postman Collections - Setup Guide

## 📦 What's Included

This folder contains complete Postman collections for testing the Quenty microservices platform:

### Collections
1. **`Quenty_Microservices_Collection.json`** - Complete API collection (89 endpoints)
2. **`Quenty_Test_Workflows.json`** - Pre-built workflow scenarios
3. **`Quenty_Local_Environment.json`** - Environment variables

### Documentation
- **`README.md`** - Comprehensive usage guide
- **`SETUP_GUIDE.md`** - This quick setup guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Import into Postman
1. Open Postman
2. Click **Import** → **Choose Files**
3. Select all 3 JSON files:
   - `Quenty_Microservices_Collection.json`
   - `Quenty_Test_Workflows.json` 
   - `Quenty_Local_Environment.json`

### Step 2: Set Environment
1. In Postman, click the environment dropdown (top right)
2. Select **"Quenty Local Environment"**

### Step 3: Start Services
```bash
# In your terminal
cd /path/to/Quenty
docker compose -f docker-compose.microservices.yml up -d

# Verify all services are healthy
curl http://localhost:8000/services/health
```

### Step 4: Test Authentication
1. Open **Quenty Microservices API Collection**
2. Go to **Authentication & Users** → **Login**
3. Click **Send**
4. ✅ You should see a 200 response with access_token

## 🎯 What to Test First

### Option A: Individual Endpoints
Start with the main collection and test endpoints one by one:
1. **Login** (Authentication & Users)
2. **Create Customer** (Customer Management)
3. **Create Product** (Product & Order Management)
4. **Create Order** (Product & Order Management)

### Option B: Complete Workflows
Use the workflow collection for end-to-end testing:
1. **Complete Order Workflow** - Full order lifecycle
2. **Microcredit Application Workflow** - Credit processing
3. **Return Processing Workflow** - Product returns
4. **Analytics Data Population** - Metrics testing

## 🔧 Troubleshooting

### Services Not Running?
```bash
# Check service status
docker compose -f docker-compose.microservices.yml ps

# Check specific service logs
docker logs quenty-api-gateway
```

### Authentication Issues?
- Ensure you're using the "Quenty Local Environment"
- Run the Login request first
- Check if the access_token variable is set

### 500 Internal Server Errors?
- Verify all services are healthy: `curl http://localhost:8000/services/health`
- Check Docker container logs for specific services

## 📋 Collection Coverage

### ✅ Complete API Coverage (89 endpoints)
- **Authentication** (12 endpoints)
- **Customer Management** (8 endpoints)  
- **Product & Orders** (15 endpoints)
- **Pickup & Routes** (10 endpoints)
- **International Shipping** (12 endpoints)
- **Microcredit Services** (8 endpoints)
- **Analytics & Reporting** (6 endpoints)
- **Reverse Logistics** (10 endpoints)
- **Franchise Management** (8 endpoints)

### 🔄 Pre-Built Workflows
- **Complete Order Workflow** (6 steps)
- **Microcredit Application** (5 steps)
- **Return Processing** (6 steps)
- **Analytics Population** (5 steps)

## 💡 Pro Tips

### 1. Use Collection Runner
For automated testing:
1. Right-click on a workflow collection
2. Select **Run collection**
3. Configure iterations and delays
4. Run automated tests

### 2. Environment Variables
Key variables auto-set by workflows:
- `access_token` - Set by Login requests
- `test_customer_id` - Set by Create Customer
- `test_order_id` - Set by Create Order
- `test_return_id` - Set by Create Return

### 3. Save Response IDs
After creating resources, copy important IDs to environment variables:
```javascript
// In Tests tab of requests
pm.environment.set('customer_id', responseJson.id);
```

## 📚 Next Steps

1. **Read the full README.md** for detailed usage instructions
2. **Test workflows** to understand business processes
3. **Customize requests** for your specific testing needs
4. **Add new workflows** based on your use cases

## 🆘 Need Help?

- **API Docs**: `http://localhost:8000/docs` (when services are running)
- **Service Logs**: `docker logs <service-name>`
- **Health Check**: `http://localhost:8000/services/health`
- **Collection Issues**: Check the detailed README.md

## 🎉 You're Ready!

Your Postman collections are set up and ready to test all 89 endpoints across 9 microservices. Start with the Login request and explore the complete Quenty platform API!