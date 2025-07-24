# Quenty Data Prefill Guide

This guide explains how to populate all Quenty microservices databases with realistic test data using the provided prefill scripts.

## Overview

The Quenty platform includes several prefill scripts located in the `/scripts/` folder that help populate all microservices databases with comprehensive test data. These scripts create realistic business scenarios including users, customers, orders, pickups, returns, credit applications, and more.

## Available Prefill Scripts

### 1. **Comprehensive Prefill Script** (`comprehensive_prefill.py`)
- **Purpose**: Complete database population for all microservices
- **Coverage**: All 9 microservices with realistic business data
- **Data Created**: 
  - Countries and carriers for international shipping
  - Products and customer profiles
  - Orders and pickup schedules
  - Returns and refund requests
  - Franchise territories and locations
  - Shipping manifests
  - Microcredit applications
  - Analytics metrics

### 2. **Simple Prefill Script** (`prefill_data_simple.py`)
- **Purpose**: Basic data setup for core functionality
- **Coverage**: Essential data for authentication and basic operations
- **Data Created**:
  - Company profiles
  - User accounts with different roles
  - Basic customer profiles
  - Simple order data

### 3. **Quick Prefill Script** (`quick_prefill.sh`)
- **Purpose**: Bash-based quick setup for immediate testing
- **Coverage**: Users and customers only
- **Data Created**:
  - User accounts with credentials
  - Individual and business customers

### 4. **Company Initialization** (`init_companies.sql`)
- **Purpose**: Initialize company records in auth database
- **Coverage**: Company profiles required for user creation
- **Data Created**:
  - Tech Solutions Inc (enterprise plan)
  - Global Logistics Co (pro plan)
  - Local Store (basic plan)

### 5. **Main Prefill Runner** (`run_prefill.sh`)
- **Purpose**: Orchestrates the complete prefill process
- **Process**: Runs SQL initialization + Python prefill scripts

## Prerequisites

Before running any prefill scripts, ensure:

1. **Services are running**: All Quenty microservices must be active
   ```bash
   docker compose -f docker-compose.microservices.yml up -d
   ```

2. **Services are healthy**: Verify all services are responding
   ```bash
   curl http://localhost:8000/services/health
   ```

3. **Python dependencies**: Ensure requests library is available
   ```bash
   pip install requests
   ```

## Quick Start (Recommended)

### Option 1: Full Comprehensive Setup
For complete testing with all business scenarios:

```bash
# Navigate to project root
cd /path/to/Quenty

# Start all services
docker compose -f docker-compose.microservices.yml up -d

# Wait for services to be ready (check health)
curl http://localhost:8000/services/health

# Run comprehensive prefill
python3 scripts/comprehensive_prefill.py
```

### Option 2: Using the Main Runner Script
For automated setup including SQL initialization:

```bash
# Start services first
docker compose -f docker-compose.microservices.yml up -d

# Run the complete prefill process
bash scripts/run_prefill.sh
```

### Option 3: Quick Basic Setup
For minimal setup to start testing immediately:

```bash
# Start services
docker compose -f docker-compose.microservices.yml up -d

# Initialize companies in auth database
docker exec -i quenty-auth-db psql -U auth -d auth_db < scripts/init_companies.sql

# Run quick prefill
bash scripts/quick_prefill.sh
```

## Detailed Script Usage

### Comprehensive Prefill Script

**File**: `scripts/comprehensive_prefill.py`

This is the most complete prefill script that populates all microservices with realistic test data.

```bash
python3 scripts/comprehensive_prefill.py
```

**What it creates**:

#### International Shipping Data
- **8 Countries**: US, Canada, Mexico, Brazil, Argentina, Colombia, Spain, France
- **5 Carriers**: DHL Express, FedEx International, UPS Worldwide, TNT Express, Servientrega

#### Product Catalog
- **8 Products**: Electronics (laptops, phones, monitors), accessories (mouse, keyboard), audio equipment
- Categories: Electronics, Accessories, Audio
- Price range: 280,000 - 4,800,000 COP
- Stock quantities: 20-100 units per product

#### Customer Profiles
- **3 Customer types**: Individual customers, business customers
- Different credit limits: 3M - 50M COP
- Various payment terms: 15-45 days
- Addresses in Bogotá and Medellín

#### Orders and Business Workflow
- **6 Orders**: Various order types (standard, express, scheduled)
- Multiple items per order
- Different statuses: pending, confirmed, processing
- **4 Pickup requests**: Scheduled pickups for orders
- **3 Return requests**: Product returns with different reasons

#### Franchise Network
- **4 Territories**: Bogotá Centro, Bogotá Norte, Medellín Centro, Cali Valle
- **2 Active franchises**: With franchisee details and contract information

#### Microcredit System
- **2 Credit applications**: Business expansion and equipment financing
- Different credit scores and income levels
- Various application statuses

#### Analytics Data
- Revenue metrics
- Order count metrics
- Customer activity metrics
- Pickup status metrics

**Script Output Example**:
```
[2025-07-24 10:30:15] INFO: Starting comprehensive Quenty database prefill...
[2025-07-24 10:30:16] INFO: ✓ API Gateway is ready
[2025-07-24 10:30:17] INFO: ✓ Successfully logged in as admin
[2025-07-24 10:30:18] INFO: Creating countries...
[2025-07-24 10:30:19] INFO: ✓ Created country: United States
...
[2025-07-24 10:30:45] INFO: === COMPREHENSIVE PREFILL SUMMARY ===
[2025-07-24 10:30:45] INFO: Countries: 8
[2025-07-24 10:30:45] INFO: Carriers: 5
[2025-07-24 10:30:45] INFO: Products: 8
[2025-07-24 10:30:45] INFO: Customers: 3
[2025-07-24 10:30:45] INFO: Orders: 6
[2025-07-24 10:30:45] INFO: Pickups: 4
[2025-07-24 10:30:45] INFO: Returns: 3
[2025-07-24 10:30:45] INFO: Territories: 4
[2025-07-24 10:30:45] INFO: Franchises: 2
[2025-07-24 10:30:45] INFO: Manifests: 2
[2025-07-24 10:30:45] INFO: Credit Applications: 2
```

### Company Initialization

**File**: `scripts/init_companies.sql`

Creates the basic company records required for user creation.

```bash
docker exec -i quenty-auth-db psql -U auth -d auth_db < scripts/init_companies.sql
```

**Companies Created**:
1. **Tech Solutions Inc** (COMP-TECH0001)
   - Industry: Technology
   - Size: Medium
   - Plan: Enterprise
   - Currency: COP

2. **Global Logistics Co** (COMP-GLOB0002)
   - Industry: Logistics
   - Size: Large
   - Plan: Pro
   - Currency: USD

3. **Local Store** (COMP-LOCA0003)
   - Industry: Retail
   - Size: Small
   - Plan: Basic
   - Currency: COP

### Quick Prefill Script

**File**: `scripts/quick_prefill.sh`

Bash script for rapid user and customer creation.

```bash
bash scripts/quick_prefill.sh
```

**Test Accounts Created**:
- **john.doe** / Password123! (Tech Solutions admin)
- **jane.smith** / Password123! (Tech Solutions manager)
- **carlos.garcia** / Password123! (Global Logistics admin)

**Customers Created**:
- Ana Lopez (Individual customer, Bogotá)
- Tech Startup SAS (Business customer, Bogotá)

## Postman Integration

After running prefill scripts, you can immediately test with the provided Postman collections:

1. **Import collections** from `/docs/postman/`
2. **Set environment** to "Quenty Local Environment"
3. **Login** using any of the created test accounts
4. **Test workflows** with pre-populated data

## Data Dependencies

The prefill scripts follow a logical dependency order:

```
1. Companies (SQL) → 2. Users → 3. Customers
                           ↓
4. Countries/Carriers → 5. Products → 6. Orders
                                        ↓
7. Territories → 8. Franchises    9. Pickups/Returns
                                        ↓
                               10. Credit Applications
                                        ↓
                               11. Analytics Data
```

## Troubleshooting

### Common Issues

**Services not ready**
```bash
# Check service status
curl http://localhost:8000/services/health

# View container logs
docker logs quenty-api-gateway
docker logs quenty-auth-service
```

**Authentication failures**
```bash
# Verify admin user exists
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "admin", "password": "AdminPassword123"}'
```

**Database connection errors**
```bash
# Check database containers
docker ps | grep db

# Check database logs
docker logs quenty-auth-db
docker logs quenty-customer-db
```

**Script execution errors**
```bash
# Run with verbose output
python3 -v scripts/comprehensive_prefill.py

# Check Python dependencies
pip list | grep requests
```

## Customization

### Adding Custom Data

To add your own test data, modify the data arrays in the scripts:

**Products** (`comprehensive_prefill.py`):
```python
products_data = [
    {
        "name": "Your Product Name",
        "sku": "YOUR-SKU-001",
        "description": "Product description",
        "price": 1000000,  # Price in COP
        "weight": 1.0,     # Weight in kg
        "dimensions": {"length": 10, "width": 10, "height": 5},
        "category": "Your Category",
        "stock_quantity": 50,
        "is_active": True
    }
]
```

**Customers**:
```python
customers_data = [
    {
        "user_id": "custom_user_id",
        "customer_type": "individual",  # or "business"
        "credit_limit": 5000000,
        "default_shipping_address": {
            "street": "Your Address",
            "city": "Your City",
            "state": "Your State",
            "country": "Colombia",
            "postal_code": "123456"
        }
    }
]
```

### Creating Custom Prefill Scripts

For specific testing scenarios, create custom scripts following this pattern:

```python
#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8000"

class CustomPrefiller:
    def __init__(self):
        self.access_token = None
    
    def login_admin(self):
        login_data = {
            "username_or_email": "admin",
            "password": "AdminPassword123"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
            return True
        return False
    
    def create_custom_data(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        # Your custom data creation logic here
        
    def run(self):
        if self.login_admin():
            self.create_custom_data()

if __name__ == "__main__":
    prefiller = CustomPrefiller()
    prefiller.run()
```

## Data Reset

To reset all data and start fresh:

```bash
# Stop services
docker compose -f docker-compose.microservices.yml down

# Remove volumes (WARNING: This deletes all data)
docker volume prune -f

# Restart services
docker compose -f docker-compose.microservices.yml up -d

# Wait for services to be ready
sleep 30

# Run prefill again
python3 scripts/comprehensive_prefill.py
```

## Best Practices

1. **Always check service health** before running prefill scripts
2. **Start with company initialization** if creating new users
3. **Use comprehensive prefill** for complete testing scenarios
4. **Use quick prefill** for rapid development setup
5. **Reset data regularly** during development to ensure clean test states
6. **Backup important test data** before making schema changes
7. **Document custom modifications** for team collaboration

## Integration with Development Workflow

### Development Setup
```bash
# 1. Start services
make dev-up

# 2. Initialize with test data
make prefill-data

# 3. Run tests
make test
```

### CI/CD Pipeline
```bash
# In your CI pipeline
docker compose -f docker-compose.microservices.yml up -d
bash scripts/run_prefill.sh
npm run test:api
```

This guide ensures you can quickly populate your Quenty platform with realistic test data for development, testing, and demonstration purposes.