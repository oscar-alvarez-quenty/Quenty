# Database Schema Documentation

## Overview

This document provides detailed database schema information for all microservices in the Quenty platform, including table structures, data types, constraints, and relationships.

## Customer Service Database (customer_db)

### Connection Details
- **Database**: customer_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    unique_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(50) DEFAULT 'customer',
    active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    company_id VARCHAR(255) REFERENCES companies(company_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_unique_id ON users(unique_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(active);
```

#### companies
```sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500),
    business_name VARCHAR(500),
    document_type VARCHAR(50),
    document_number VARCHAR(100) UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_companies_company_id ON companies(company_id);
CREATE INDEX idx_companies_document_number ON companies(document_number);
CREATE INDEX idx_companies_active ON companies(active);
CREATE INDEX idx_companies_name ON companies(name);
```

#### document_types
```sql
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_document_types_code ON document_types(code);
CREATE INDEX idx_document_types_active ON document_types(active);
```

### Constraints and Foreign Keys

```sql
-- Foreign Key Constraints
ALTER TABLE users 
ADD CONSTRAINT fk_users_company 
FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE SET NULL;

-- Check Constraints
ALTER TABLE users 
ADD CONSTRAINT chk_users_role 
CHECK (role IN ('admin', 'manager', 'customer', 'viewer'));

ALTER TABLE users 
ADD CONSTRAINT chk_users_email_format 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
```

### Triggers

```sql
-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON companies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Order Service Database (order_db)

### Connection Details
- **Database**: order_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### products
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    sku VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2),
    weight DECIMAL(8,3),
    dimensions JSONB, -- {"length": 10.0, "width": 5.0, "height": 3.0}
    active BOOLEAN DEFAULT TRUE,
    company_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_company_id ON products(company_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_active ON products(active);
CREATE INDEX idx_products_name_gin ON products USING GIN (to_tsvector('english', name));
```

#### orders
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    customer_id VARCHAR(255) NOT NULL,
    company_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_company_id ON orders(company_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

#### order_items
```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
```

#### inventory_items
```sql
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 0 NOT NULL,
    reserved_quantity INTEGER DEFAULT 0 NOT NULL,
    min_stock_level INTEGER DEFAULT 0,
    max_stock_level INTEGER,
    location VARCHAR(255),
    batch_number VARCHAR(255),
    expiry_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_inventory_items_product_id ON inventory_items(product_id);
CREATE INDEX idx_inventory_items_location ON inventory_items(location);
CREATE INDEX idx_inventory_items_quantity ON inventory_items(quantity);
CREATE INDEX idx_inventory_items_expiry ON inventory_items(expiry_date);
```

#### stock_movements
```sql
CREATE TABLE stock_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    movement_type VARCHAR(50) NOT NULL, -- 'IN', 'OUT', 'ADJUSTMENT'
    quantity INTEGER NOT NULL,
    reference_number VARCHAR(255),
    notes TEXT,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_stock_movements_product_id ON stock_movements(product_id);
CREATE INDEX idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX idx_stock_movements_created_at ON stock_movements(created_at DESC);
CREATE INDEX idx_stock_movements_created_by ON stock_movements(created_by);
```

### Constraints and Foreign Keys

```sql
-- Check Constraints
ALTER TABLE orders 
ADD CONSTRAINT chk_orders_status 
CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'in_transit', 'delivered', 'cancelled'));

ALTER TABLE orders 
ADD CONSTRAINT chk_orders_total_amount 
CHECK (total_amount >= 0);

ALTER TABLE stock_movements 
ADD CONSTRAINT chk_movement_type 
CHECK (movement_type IN ('IN', 'OUT', 'ADJUSTMENT'));

ALTER TABLE inventory_items 
ADD CONSTRAINT chk_inventory_quantity 
CHECK (quantity >= 0 AND reserved_quantity >= 0);
```

### Computed Columns and Views

```sql
-- Available inventory view
CREATE VIEW available_inventory AS
SELECT 
    i.product_id,
    p.name AS product_name,
    p.sku,
    i.quantity,
    i.reserved_quantity,
    (i.quantity - i.reserved_quantity) AS available_quantity,
    i.min_stock_level,
    i.max_stock_level,
    i.location,
    CASE 
        WHEN (i.quantity - i.reserved_quantity) <= i.min_stock_level THEN 'LOW_STOCK'
        WHEN (i.quantity - i.reserved_quantity) = 0 THEN 'OUT_OF_STOCK'
        ELSE 'IN_STOCK'
    END AS stock_status
FROM inventory_items i
JOIN products p ON i.product_id = p.id
WHERE p.active = true;
```

## International Shipping Service Database (intl_shipping_db)

### Connection Details
- **Database**: intl_shipping_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### manifests
```sql
CREATE TABLE manifests (
    id SERIAL PRIMARY KEY,
    unique_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    total_weight DECIMAL(8,3) DEFAULT 0.0,
    total_volume DECIMAL(8,3) DEFAULT 0.0,
    total_value DECIMAL(10,2) DEFAULT 0.0,
    currency VARCHAR(10) DEFAULT 'USD',
    origin_country VARCHAR(100) NOT NULL,
    destination_country VARCHAR(100) NOT NULL,
    shipping_zone VARCHAR(50),
    estimated_delivery TIMESTAMP WITH TIME ZONE,
    tracking_number VARCHAR(255) UNIQUE,
    company_id VARCHAR(255) NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_manifests_unique_id ON manifests(unique_id);
CREATE INDEX idx_manifests_tracking_number ON manifests(tracking_number);
CREATE INDEX idx_manifests_company_id ON manifests(company_id);
CREATE INDEX idx_manifests_status ON manifests(status);
CREATE INDEX idx_manifests_created_at ON manifests(created_at DESC);
CREATE INDEX idx_manifests_destination ON manifests(destination_country);
```

#### manifest_items
```sql
CREATE TABLE manifest_items (
    id SERIAL PRIMARY KEY,
    manifest_id INTEGER REFERENCES manifests(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    weight DECIMAL(8,3) NOT NULL,
    volume DECIMAL(8,3),
    value DECIMAL(10,2) NOT NULL,
    hs_code VARCHAR(50), -- Harmonized System code
    country_of_origin VARCHAR(100),
    product_id INTEGER, -- Reference to Product from Order service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_manifest_items_manifest_id ON manifest_items(manifest_id);
CREATE INDEX idx_manifest_items_product_id ON manifest_items(product_id);
CREATE INDEX idx_manifest_items_hs_code ON manifest_items(hs_code);
```

#### shipping_rates
```sql
CREATE TABLE shipping_rates (
    id SERIAL PRIMARY KEY,
    manifest_id INTEGER REFERENCES manifests(id) ON DELETE CASCADE,
    carrier_name VARCHAR(255) NOT NULL,
    service_type VARCHAR(255) NOT NULL,
    base_rate DECIMAL(10,2) NOT NULL,
    weight_rate DECIMAL(10,2) DEFAULT 0.0,
    volume_rate DECIMAL(10,2) DEFAULT 0.0,
    fuel_surcharge DECIMAL(10,2) DEFAULT 0.0,
    insurance_rate DECIMAL(10,2) DEFAULT 0.0,
    total_cost DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    transit_days INTEGER,
    valid_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_shipping_rates_manifest_id ON shipping_rates(manifest_id);
CREATE INDEX idx_shipping_rates_carrier ON shipping_rates(carrier_name);
CREATE INDEX idx_shipping_rates_total_cost ON shipping_rates(total_cost);
```

#### countries
```sql
CREATE TABLE countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    iso_code VARCHAR(10) UNIQUE NOT NULL,
    zone VARCHAR(50), -- ShippingZone enum
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_countries_iso_code ON countries(iso_code);
CREATE INDEX idx_countries_zone ON countries(zone);
CREATE INDEX idx_countries_active ON countries(active);
```

#### shipping_carriers
```sql
CREATE TABLE shipping_carriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    api_endpoint VARCHAR(500),
    api_key VARCHAR(500),
    active BOOLEAN DEFAULT TRUE,
    supported_services JSONB, -- List of service types
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_shipping_carriers_code ON shipping_carriers(code);
CREATE INDEX idx_shipping_carriers_active ON shipping_carriers(active);
```

### Constraints and Foreign Keys

```sql
-- Check Constraints
ALTER TABLE manifests 
ADD CONSTRAINT chk_manifests_status 
CHECK (status IN ('draft', 'submitted', 'approved', 'rejected', 'shipped', 'delivered'));

ALTER TABLE manifests 
ADD CONSTRAINT chk_manifests_weights 
CHECK (total_weight >= 0 AND total_volume >= 0 AND total_value >= 0);

ALTER TABLE manifest_items 
ADD CONSTRAINT chk_manifest_items_quantities 
CHECK (quantity > 0 AND weight > 0 AND value >= 0);

ALTER TABLE shipping_rates 
ADD CONSTRAINT chk_shipping_rates_amounts 
CHECK (base_rate >= 0 AND total_cost >= 0 AND transit_days > 0);
```

## Database Performance and Optimization

### Indexing Strategy

```sql
-- Composite Indexes for Common Query Patterns

-- Customer Service
CREATE INDEX idx_users_company_active ON users(company_id, active);
CREATE INDEX idx_users_email_active ON users(email, active) WHERE active = true;

-- Order Service  
CREATE INDEX idx_products_company_category_active ON products(company_id, category, active);
CREATE INDEX idx_orders_customer_status_date ON orders(customer_id, status, created_at DESC);
CREATE INDEX idx_inventory_low_stock ON inventory_items(product_id) 
    WHERE (quantity - reserved_quantity) <= min_stock_level;

-- Shipping Service
CREATE INDEX idx_manifests_company_status_date ON manifests(company_id, status, created_at DESC);
CREATE INDEX idx_shipping_rates_manifest_carrier_cost ON shipping_rates(manifest_id, carrier_name, total_cost);
```

### Partitioning Strategy

```sql
-- Partition large tables by date for better performance
-- Example: Stock movements table partitioned by month

CREATE TABLE stock_movements (
    id SERIAL,
    product_id INTEGER NOT NULL,
    movement_type VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    reference_number VARCHAR(255),
    notes TEXT,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE stock_movements_2025_01 PARTITION OF stock_movements 
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE stock_movements_2025_02 PARTITION OF stock_movements 
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

## Backup and Recovery Strategy

### Backup Configuration

```sql
-- Point-in-time recovery setup
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'cp %p /backup/archive/%f';

-- Backup commands for each database
-- Customer DB
pg_dump -h customer-db -U customer -d customer_db -F c -f /backup/customer_db_$(date +%Y%m%d_%H%M%S).backup

-- Order DB  
pg_dump -h order-db -U order -d order_db -F c -f /backup/order_db_$(date +%Y%m%d_%H%M%S).backup

-- Shipping DB
pg_dump -h intl-shipping-db -U intlship -d intl_shipping_db -F c -f /backup/shipping_db_$(date +%Y%m%d_%H%M%S).backup
```

### Recovery Procedures

```sql
-- Database restore from backup
pg_restore -h customer-db -U customer -d customer_db -c /backup/customer_db_20250122_120000.backup

-- Point-in-time recovery
pg_basebackup -D /backup/basebackup -h customer-db -U customer
# Edit recovery.conf with target time
# Restart PostgreSQL
```

## Connection Pooling and Performance

### Connection Pool Configuration

```python
# Database connection settings for each service
DATABASE_POOL_SETTINGS = {
    "min_size": 10,
    "max_size": 20,
    "command_timeout": 60,
    "server_settings": {
        "jit": "off",
        "application_name": "quenty_microservice"
    }
}
```

### Query Performance Monitoring

```sql
-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Monitor slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
WHERE mean_time > 100 
ORDER BY mean_time DESC 
LIMIT 10;
```

## Migration Management

### Alembic Configuration

Each service has its own Alembic configuration:

```python
# alembic.ini for each service
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://user:password@host:port/database

# Version table naming
version_table = alembic_version_customer  # customer service
version_table = alembic_version_order     # order service  
version_table = alembic_version_shipping  # shipping service
```

### Migration Commands

```bash
# Initialize Alembic for each service
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create initial tables"

# Apply migrations
alembic upgrade head

# Downgrade if needed
alembic downgrade -1
```

## Security Configurations

### Database Security

```sql
-- Create service-specific users
CREATE USER customer_user WITH PASSWORD 'secure_password';
CREATE USER order_user WITH PASSWORD 'secure_password';  
CREATE USER shipping_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT CONNECT ON DATABASE customer_db TO customer_user;
GRANT USAGE ON SCHEMA public TO customer_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO customer_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO customer_user;

-- Enable row-level security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY company_isolation ON users 
FOR ALL TO customer_user 
USING (company_id = current_setting('app.current_company_id'));
```

### SSL Configuration

```sql
-- SSL settings in postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'  
ssl_ca_file = 'root.crt'
ssl_crl_file = ''
```