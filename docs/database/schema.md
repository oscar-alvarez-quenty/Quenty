# Database Schema Documentation

## Overview

This document provides detailed database schema information for all microservices in the Quenty platform, including table structures, data types, constraints, and relationships across 9 specialized microservices.

## Auth Service Database (auth_db)

### Connection Details
- **Database**: auth_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
```

#### roles
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    role_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_roles_role_id ON roles(role_id);
CREATE INDEX idx_roles_name ON roles(name);
CREATE INDEX idx_roles_active ON roles(is_active);
```

#### permissions
```sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    permission_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) UNIQUE NOT NULL,
    resource VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_permissions_permission_id ON permissions(permission_id);
CREATE INDEX idx_permissions_name ON permissions(name);
CREATE INDEX idx_permissions_resource_action ON permissions(resource, action);
```

#### user_roles
```sql
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(255),
    UNIQUE(user_id, role_id)
);

-- Indexes
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
```

#### refresh_tokens
```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

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

## Pickup Service Database (pickup_db)

### Connection Details
- **Database**: pickup_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### pickups
```sql
CREATE TABLE pickups (
    id SERIAL PRIMARY KEY,
    pickup_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    pickup_type VARCHAR(50) NOT NULL, -- on_demand, scheduled, recurring, express
    status VARCHAR(50) DEFAULT 'scheduled' NOT NULL,
    pickup_date DATE NOT NULL,
    time_window_start TIME NOT NULL,
    time_window_end TIME NOT NULL,
    pickup_address TEXT NOT NULL,
    pickup_latitude REAL,
    pickup_longitude REAL,
    postal_code VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(10) DEFAULT 'MX',
    contact_name VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    contact_email VARCHAR(255),
    package_count INTEGER NOT NULL,
    estimated_weight_kg REAL NOT NULL,
    actual_weight_kg REAL,
    estimated_volume_m3 REAL,
    actual_volume_m3 REAL,
    requires_packaging BOOLEAN DEFAULT FALSE,
    fragile_items BOOLEAN DEFAULT FALSE,
    special_instructions TEXT,
    assigned_driver_id VARCHAR(255),
    assigned_vehicle_type VARCHAR(50),
    assigned_route_id INTEGER REFERENCES pickup_routes(id),
    estimated_arrival_time TIMESTAMP WITH TIME ZONE,
    actual_pickup_time TIMESTAMP WITH TIME ZONE,
    completion_notes TEXT,
    customer_signature TEXT,
    driver_notes TEXT,
    completion_photos JSONB,
    pickup_cost REAL,
    currency VARCHAR(10) DEFAULT 'MXN',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_pickups_pickup_id ON pickups(pickup_id);
CREATE INDEX idx_pickups_customer_id ON pickups(customer_id);
CREATE INDEX idx_pickups_status ON pickups(status);
CREATE INDEX idx_pickups_pickup_date ON pickups(pickup_date);
CREATE INDEX idx_pickups_assigned_driver_id ON pickups(assigned_driver_id);
```

#### pickup_routes
```sql
CREATE TABLE pickup_routes (
    id SERIAL PRIMARY KEY,
    route_id VARCHAR(255) UNIQUE NOT NULL,
    driver_id VARCHAR(255) NOT NULL,
    route_name VARCHAR(255),
    route_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'planned' NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    vehicle_license_plate VARCHAR(50),
    total_distance_km REAL,
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    total_pickups INTEGER DEFAULT 0,
    completed_pickups INTEGER DEFAULT 0,
    optimized_waypoints JSONB,
    route_start_time TIMESTAMP WITH TIME ZONE,
    route_end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_pickup_routes_route_id ON pickup_routes(route_id);
CREATE INDEX idx_pickup_routes_driver_id ON pickup_routes(driver_id);
CREATE INDEX idx_pickup_routes_date ON pickup_routes(route_date);
CREATE INDEX idx_pickup_routes_status ON pickup_routes(status);
```

#### pickup_packages
```sql
CREATE TABLE pickup_packages (
    id SERIAL PRIMARY KEY,
    pickup_id INTEGER REFERENCES pickups(id) ON DELETE CASCADE,
    package_reference VARCHAR(255),
    description VARCHAR(500),
    category VARCHAR(100),
    weight_kg REAL,
    length_cm REAL,
    width_cm REAL,
    height_cm REAL,
    is_fragile BOOLEAN DEFAULT FALSE,
    requires_signature BOOLEAN DEFAULT TRUE,
    insurance_value REAL,
    destination_address TEXT,
    destination_contact_name VARCHAR(255),
    destination_contact_phone VARCHAR(50),
    tracking_number VARCHAR(255) UNIQUE,
    order_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_pickup_packages_pickup_id ON pickup_packages(pickup_id);
CREATE INDEX idx_pickup_packages_tracking_number ON pickup_packages(tracking_number);
CREATE INDEX idx_pickup_packages_order_id ON pickup_packages(order_id);
```

#### pickup_attempts
```sql
CREATE TABLE pickup_attempts (
    id SERIAL PRIMARY KEY,
    pickup_id INTEGER REFERENCES pickups(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    driver_id VARCHAR(255),
    attempt_status VARCHAR(50) NOT NULL,
    failure_reason VARCHAR(500),
    failure_category VARCHAR(100),
    reschedule_date DATE,
    reschedule_time_start TIME,
    reschedule_time_end TIME,
    driver_notes TEXT,
    attempt_photos JSONB,
    gps_coordinates JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_pickup_attempts_pickup_id ON pickup_attempts(pickup_id);
CREATE INDEX idx_pickup_attempts_driver_id ON pickup_attempts(driver_id);
CREATE INDEX idx_pickup_attempts_attempted_at ON pickup_attempts(attempted_at);
```

## Analytics Service Database (analytics_db)

### Connection Details
- **Database**: analytics_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### metrics
```sql
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    metric_id VARCHAR(255) UNIQUE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    value NUMERIC(20,4) NOT NULL,
    unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    period VARCHAR(20),
    source_service VARCHAR(100),
    source_entity_id VARCHAR(255),
    source_entity_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes with GIN for JSONB
CREATE INDEX idx_metrics_metric_id ON metrics(metric_id);
CREATE INDEX idx_metrics_type ON metrics(metric_type);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_source_service ON metrics(source_service);
CREATE INDEX idx_metrics_tags_gin ON metrics USING GIN (tags);
CREATE INDEX idx_metrics_type_timestamp ON metrics(metric_type, timestamp DESC);
```

#### dashboards
```sql
CREATE TABLE dashboards (
    id SERIAL PRIMARY KEY,
    dashboard_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dashboard_type VARCHAR(50) DEFAULT 'standard',
    widgets JSONB DEFAULT '[]',
    layout JSONB DEFAULT '{}',
    filters JSONB DEFAULT '{}',
    refresh_interval INTEGER DEFAULT 300,
    owner_id VARCHAR(255),
    is_public BOOLEAN DEFAULT FALSE,
    allowed_users JSONB DEFAULT '[]',
    allowed_roles JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_dashboards_dashboard_id ON dashboards(dashboard_id);
CREATE INDEX idx_dashboards_owner_id ON dashboards(owner_id);
CREATE INDEX idx_dashboards_is_public ON dashboards(is_public);
CREATE INDEX idx_dashboards_is_active ON dashboards(is_active);
```

#### reports
```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) DEFAULT 'json',
    parameters JSONB DEFAULT '{}',
    filters JSONB DEFAULT '{}',
    date_range JSONB,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    progress_percentage INTEGER DEFAULT 0,
    file_url VARCHAR(500),
    file_size INTEGER,
    is_scheduled BOOLEAN DEFAULT FALSE,
    schedule_expression VARCHAR(100),
    next_run TIMESTAMP WITH TIME ZONE,
    requested_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_reports_report_id ON reports(report_id);
CREATE INDEX idx_reports_type ON reports(report_type);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_requested_by ON reports(requested_by);
CREATE INDEX idx_reports_is_scheduled ON reports(is_scheduled);
CREATE INDEX idx_reports_next_run ON reports(next_run) WHERE is_scheduled = true;
```

#### alerts
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metric_type VARCHAR(50) NOT NULL,
    condition_expression VARCHAR(500) NOT NULL,
    threshold_value NUMERIC(20,4),
    comparison_operator VARCHAR(10),
    time_window VARCHAR(20),
    notification_channels JSONB DEFAULT '[]',
    recipients JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_alerts_alert_id ON alerts(alert_id);
CREATE INDEX idx_alerts_metric_type ON alerts(metric_type);
CREATE INDEX idx_alerts_is_active ON alerts(is_active);
CREATE INDEX idx_alerts_created_by ON alerts(created_by);
```

## Reverse Logistics Service Database (reverse_logistics_db)

### Connection Details
- **Database**: reverse_logistics_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### returns
```sql
CREATE TABLE returns (
    id SERIAL PRIMARY KEY,
    return_id VARCHAR(255) UNIQUE NOT NULL,
    original_order_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    return_type VARCHAR(50) NOT NULL DEFAULT 'return',
    return_reason VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'requested',
    description TEXT,
    preferred_resolution VARCHAR(50),
    return_authorization_number VARCHAR(255) UNIQUE,
    original_order_value NUMERIC(10,2),
    estimated_refund_amount NUMERIC(10,2),
    actual_refund_amount NUMERIC(10,2),
    return_shipping_cost NUMERIC(10,2) DEFAULT 0,
    processing_fee NUMERIC(10,2) DEFAULT 0,
    pickup_address TEXT,
    return_address TEXT,
    tracking_number VARCHAR(255) UNIQUE,
    carrier VARCHAR(100),
    estimated_pickup_date DATE,
    actual_pickup_date DATE,
    estimated_processing_time VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    approval_notes TEXT,
    rejection_reason TEXT,
    processing_notes TEXT,
    photos JSONB DEFAULT '[]',
    customer_action_required VARCHAR(255),
    requires_customer_action BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255),
    processed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_returns_return_id ON returns(return_id);
CREATE INDEX idx_returns_customer_id ON returns(customer_id);
CREATE INDEX idx_returns_original_order_id ON returns(original_order_id);
CREATE INDEX idx_returns_status ON returns(status);
CREATE INDEX idx_returns_created_at ON returns(created_at DESC);
CREATE INDEX idx_returns_tracking_number ON returns(tracking_number);
```

#### return_items
```sql
CREATE TABLE return_items (
    id SERIAL PRIMARY KEY,
    return_item_id VARCHAR(255) UNIQUE NOT NULL,
    return_id INTEGER REFERENCES returns(id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL,
    item_name VARCHAR(255),
    sku VARCHAR(100),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10,2),
    return_reason VARCHAR(50),
    reason_details TEXT,
    condition_received VARCHAR(50),
    photos JSONB DEFAULT '[]',
    inspection_result VARCHAR(50),
    resale_value NUMERIC(10,2),
    refund_eligible BOOLEAN DEFAULT TRUE,
    refund_amount NUMERIC(10,2),
    exchange_item_id VARCHAR(255),
    exchange_quantity INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_return_items_return_item_id ON return_items(return_item_id);
CREATE INDEX idx_return_items_return_id ON return_items(return_id);
CREATE INDEX idx_return_items_item_id ON return_items(item_id);
```

#### inspection_reports
```sql
CREATE TABLE inspection_reports (
    id SERIAL PRIMARY KEY,
    inspection_id VARCHAR(255) UNIQUE NOT NULL,
    return_id INTEGER REFERENCES returns(id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL,
    inspector_id VARCHAR(255) NOT NULL,
    inspector_name VARCHAR(255),
    inspection_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    overall_condition VARCHAR(50) NOT NULL,
    functional_status VARCHAR(50),
    cosmetic_condition VARCHAR(50),
    completeness VARCHAR(50),
    defects_found JSONB DEFAULT '[]',
    photos JSONB DEFAULT '[]',
    notes TEXT,
    original_value NUMERIC(10,2),
    current_market_value NUMERIC(10,2),
    resale_value NUMERIC(10,2),
    salvage_value NUMERIC(10,2),
    recommended_action VARCHAR(100),
    disposition_recommendation VARCHAR(50),
    repair_cost_estimate NUMERIC(10,2),
    refurbishment_cost NUMERIC(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_inspection_reports_inspection_id ON inspection_reports(inspection_id);
CREATE INDEX idx_inspection_reports_return_id ON inspection_reports(return_id);
CREATE INDEX idx_inspection_reports_item_id ON inspection_reports(item_id);
CREATE INDEX idx_inspection_reports_inspector_id ON inspection_reports(inspector_id);
```

## Franchise Service Database (franchise_db)

### Connection Details
- **Database**: franchise_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### franchises
```sql
CREATE TABLE franchises (
    id SERIAL PRIMARY KEY,
    franchise_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    franchisee_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    business_license VARCHAR(100),
    tax_id VARCHAR(100),
    territory_code VARCHAR(50) REFERENCES territories(territory_code),
    contract_start_date DATE,
    contract_end_date DATE,
    contract_terms JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    opening_date DATE,
    closure_date DATE,
    operational_hours JSONB,
    services_offered JSONB,
    equipment_list JSONB,
    initial_fee NUMERIC(10,2),
    monthly_fee NUMERIC(10,2),
    royalty_rate NUMERIC(5,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_franchises_franchise_id ON franchises(franchise_id);
CREATE INDEX idx_franchises_email ON franchises(email);
CREATE INDEX idx_franchises_territory_code ON franchises(territory_code);
CREATE INDEX idx_franchises_status ON franchises(status);
CREATE INDEX idx_franchises_is_active ON franchises(is_active);
```

#### territories
```sql
CREATE TABLE territories (
    id SERIAL PRIMARY KEY,
    territory_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    boundaries JSONB,
    area_size NUMERIC(10,2),
    population INTEGER,
    market_potential VARCHAR(20),
    competition_level VARCHAR(20),
    average_income NUMERIC(12,2),
    demographic_data JSONB,
    status VARCHAR(20) DEFAULT 'available',
    reserved_until TIMESTAMP WITH TIME ZONE,
    reserved_by VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_territories_territory_code ON territories(territory_code);
CREATE INDEX idx_territories_status ON territories(status);
CREATE INDEX idx_territories_country_state ON territories(country, state);
CREATE INDEX idx_territories_is_active ON territories(is_active);
```

#### franchise_performance
```sql
CREATE TABLE franchise_performance (
    id SERIAL PRIMARY KEY,
    performance_id VARCHAR(255) UNIQUE NOT NULL,
    franchise_id INTEGER REFERENCES franchises(id) ON DELETE CASCADE,
    period_type VARCHAR(20),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    revenue NUMERIC(12,2) DEFAULT 0,
    costs NUMERIC(12,2) DEFAULT 0,
    profit NUMERIC(12,2) DEFAULT 0,
    royalties_paid NUMERIC(12,2) DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    customers_served INTEGER DEFAULT 0,
    average_order_value NUMERIC(10,2) DEFAULT 0,
    customer_satisfaction_score NUMERIC(3,2) DEFAULT 0,
    performance_score NUMERIC(5,2) DEFAULT 0,
    ranking INTEGER,
    improvement_areas JSONB,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_franchise_performance_performance_id ON franchise_performance(performance_id);
CREATE INDEX idx_franchise_performance_franchise_id ON franchise_performance(franchise_id);
CREATE INDEX idx_franchise_performance_period ON franchise_performance(period_start, period_end);
CREATE INDEX idx_franchise_performance_score ON franchise_performance(performance_score DESC);
```

## Microcredit Service Database (microcredit_db)

### Connection Details
- **Database**: microcredit_db
- **Port**: 5432
- **Driver**: PostgreSQL with AsyncPG
- **Schema**: public

### Tables

#### credit_applications
```sql
CREATE TABLE credit_applications (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    customer_type VARCHAR(50) DEFAULT 'individual',
    requested_amount NUMERIC(12,2) NOT NULL,
    requested_term_months INTEGER NOT NULL,
    purpose VARCHAR(100) NOT NULL,
    application_type VARCHAR(50) DEFAULT 'new',
    monthly_income NUMERIC(12,2),
    employment_status VARCHAR(50),
    employment_duration INTEGER,
    existing_debts NUMERIC(12,2) DEFAULT 0,
    credit_score INTEGER,
    risk_category VARCHAR(20),
    approved_amount NUMERIC(12,2),
    approved_term_months INTEGER,
    interest_rate NUMERIC(5,4),
    status VARCHAR(50) DEFAULT 'pending',
    decision_reason TEXT,
    processed_by VARCHAR(255),
    decision_date TIMESTAMP WITH TIME ZONE,
    documents_submitted JSONB DEFAULT '[]',
    verification_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_credit_applications_application_id ON credit_applications(application_id);
CREATE INDEX idx_credit_applications_customer_id ON credit_applications(customer_id);
CREATE INDEX idx_credit_applications_status ON credit_applications(status);
CREATE INDEX idx_credit_applications_created_at ON credit_applications(created_at DESC);
```

#### loans
```sql
CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    loan_id VARCHAR(255) UNIQUE NOT NULL,
    application_id INTEGER REFERENCES credit_applications(id),
    customer_id VARCHAR(255) NOT NULL,
    principal_amount NUMERIC(12,2) NOT NULL,
    interest_rate NUMERIC(5,4) NOT NULL,
    term_months INTEGER NOT NULL,
    monthly_payment NUMERIC(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    disbursement_date DATE NOT NULL,
    first_payment_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    total_amount_due NUMERIC(12,2),
    amount_paid NUMERIC(12,2) DEFAULT 0,
    outstanding_balance NUMERIC(12,2),
    accrued_interest NUMERIC(12,2) DEFAULT 0,
    late_fees NUMERIC(10,2) DEFAULT 0,
    next_payment_date DATE,
    next_payment_amount NUMERIC(10,2),
    payments_made INTEGER DEFAULT 0,
    payments_remaining INTEGER,
    days_past_due INTEGER DEFAULT 0,
    risk_category VARCHAR(20),
    collection_status VARCHAR(50),
    restructured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_loans_loan_id ON loans(loan_id);
CREATE INDEX idx_loans_customer_id ON loans(customer_id);
CREATE INDEX idx_loans_application_id ON loans(application_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loans_next_payment_date ON loans(next_payment_date);
CREATE INDEX idx_loans_days_past_due ON loans(days_past_due);
```

#### loan_payments
```sql
CREATE TABLE loan_payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(255) UNIQUE NOT NULL,
    loan_id INTEGER REFERENCES loans(id) ON DELETE CASCADE,
    payment_amount NUMERIC(10,2) NOT NULL,
    principal_amount NUMERIC(10,2) NOT NULL,
    interest_amount NUMERIC(10,2) NOT NULL,
    late_fee_amount NUMERIC(10,2) DEFAULT 0,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(255),
    payment_status VARCHAR(50) DEFAULT 'completed',
    remaining_balance NUMERIC(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_loan_payments_payment_id ON loan_payments(payment_id);
CREATE INDEX idx_loan_payments_loan_id ON loan_payments(loan_id);
CREATE INDEX idx_loan_payments_payment_date ON loan_payments(payment_date DESC);
CREATE INDEX idx_loan_payments_status ON loan_payments(payment_status);
```

#### credit_scores
```sql
CREATE TABLE credit_scores (
    id SERIAL PRIMARY KEY,
    score_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL, -- 300-850 range
    score_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    score_version VARCHAR(10) DEFAULT 'v2.0',
    payment_history_score INTEGER,
    credit_utilization_score INTEGER,
    length_of_history_score INTEGER,
    credit_mix_score INTEGER,
    new_credit_score INTEGER,
    risk_category VARCHAR(20),
    default_probability NUMERIC(5,4),
    recommended_limit NUMERIC(12,2),
    positive_factors JSONB DEFAULT '[]',
    negative_factors JSONB DEFAULT '[]',
    improvement_suggestions JSONB DEFAULT '[]',
    previous_score INTEGER,
    score_change INTEGER,
    calculated_by VARCHAR(100) DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_credit_scores_score_id ON credit_scores(score_id);
CREATE INDEX idx_credit_scores_customer_id ON credit_scores(customer_id);
CREATE INDEX idx_credit_scores_score_date ON credit_scores(score_date DESC);
CREATE INDEX idx_credit_scores_score ON credit_scores(score);
```

## Cross-Service Constraints and Foreign Keys

### Referential Integrity Across Services
Since each service has its own database, cross-service references are maintained through external IDs:

```sql
-- Customer Service references
-- These are logical references maintained by application code
-- customers.unique_id is referenced by:
--   - orders.customer_id (Order Service)
--   - manifests.created_by (Shipping Service)
--   - pickups.customer_id (Pickup Service)
--   - returns.customer_id (Reverse Logistics Service)
--   - credit_applications.customer_id (Microcredit Service)

-- companies.company_id is referenced by:
--   - products.company_id (Order Service)
--   - manifests.company_id (Shipping Service)
--   - franchises.* (Franchise Service)

-- Order Service references
-- products.id is referenced by:
--   - manifest_items.product_id (Shipping Service)
--   - pickup_packages.order_id (Pickup Service)
--   - return_items.item_id (Reverse Logistics Service)

-- orders.order_number is referenced by:
--   - returns.original_order_id (Reverse Logistics Service)
```

## Database Performance and Optimization

### Partitioning Strategy

```sql
-- Partition large time-series tables by date
-- Metrics table partitioned by month
CREATE TABLE metrics (
    id SERIAL,
    metric_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    value NUMERIC(20,4) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    tags JSONB DEFAULT '{}',
    source_service VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for metrics
CREATE TABLE metrics_2025_01 PARTITION OF metrics 
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE metrics_2025_02 PARTITION OF metrics 
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Stock movements partitioned by date
CREATE TABLE stock_movements_2025_01 PARTITION OF stock_movements 
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Loan payments partitioned by payment date
CREATE TABLE loan_payments_2025_01 PARTITION OF loan_payments 
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Composite Indexes for Common Query Patterns

```sql
-- Auth Service
CREATE INDEX idx_users_email_active ON users(email, is_active) WHERE is_active = true;
CREATE INDEX idx_user_roles_user_role ON user_roles(user_id, role_id);

-- Customer Service  
CREATE INDEX idx_users_company_active ON users(company_id, active);
CREATE INDEX idx_companies_active_name ON companies(active, name) WHERE active = true;

-- Order Service
CREATE INDEX idx_products_company_category_active ON products(company_id, category, active);
CREATE INDEX idx_orders_customer_status_date ON orders(customer_id, status, created_at DESC);
CREATE INDEX idx_inventory_low_stock ON inventory_items(product_id) 
    WHERE (quantity - reserved_quantity) <= min_stock_level;

-- Shipping Service
CREATE INDEX idx_manifests_company_status_date ON manifests(company_id, status, created_at DESC);
CREATE INDEX idx_shipping_rates_manifest_carrier_cost ON shipping_rates(manifest_id, carrier_name, total_cost);

-- Pickup Service
CREATE INDEX idx_pickups_date_status ON pickups(pickup_date, status);
CREATE INDEX idx_pickups_customer_date ON pickups(customer_id, pickup_date DESC);
CREATE INDEX idx_pickup_routes_driver_date ON pickup_routes(driver_id, route_date);

-- Analytics Service
CREATE INDEX idx_metrics_type_timestamp_service ON metrics(metric_type, timestamp DESC, source_service);
CREATE INDEX idx_reports_type_status_created ON reports(report_type, status, created_at DESC);

-- Reverse Logistics Service
CREATE INDEX idx_returns_customer_status_date ON returns(customer_id, status, created_at DESC);
CREATE INDEX idx_returns_order_status ON returns(original_order_id, status);

-- Franchise Service
CREATE INDEX idx_franchises_territory_status ON franchises(territory_code, status);
CREATE INDEX idx_franchise_performance_franchise_period ON franchise_performance(franchise_id, period_start, period_end);

-- Microcredit Service
CREATE INDEX idx_credit_applications_customer_status_date ON credit_applications(customer_id, status, created_at DESC);
CREATE INDEX idx_loans_customer_status_payment ON loans(customer_id, status, next_payment_date);
CREATE INDEX idx_loan_payments_loan_date ON loan_payments(loan_id, payment_date DESC);
```

## Backup and Recovery Strategy

### Database Backup Configuration

```bash
#!/bin/bash
# Backup script for all microservice databases

BACKUP_DIR="/backup/databases"
DATE=$(date +%Y%m%d_%H%M%S)

# Auth Service
pg_dump -h auth-db -U auth -d auth_db -F c -f ${BACKUP_DIR}/auth_db_${DATE}.backup

# Customer Service  
pg_dump -h customer-db -U customer -d customer_db -F c -f ${BACKUP_DIR}/customer_db_${DATE}.backup

# Order Service
pg_dump -h order-db -U order -d order_db -F c -f ${BACKUP_DIR}/order_db_${DATE}.backup

# International Shipping Service
pg_dump -h intl-shipping-db -U intlship -d intl_shipping_db -F c -f ${BACKUP_DIR}/shipping_db_${DATE}.backup

# Pickup Service
pg_dump -h pickup-db -U pickup -d pickup_db -F c -f ${BACKUP_DIR}/pickup_db_${DATE}.backup

# Analytics Service
pg_dump -h analytics-db -U analytics -d analytics_db -F c -f ${BACKUP_DIR}/analytics_db_${DATE}.backup

# Reverse Logistics Service
pg_dump -h reverse-logistics-db -U revlog -d reverse_logistics_db -F c -f ${BACKUP_DIR}/reverse_logistics_db_${DATE}.backup

# Franchise Service
pg_dump -h franchise-db -U franchise -d franchise_db -F c -f ${BACKUP_DIR}/franchise_db_${DATE}.backup

# Microcredit Service
pg_dump -h microcredit-db -U microcredit -d microcredit_db -F c -f ${BACKUP_DIR}/microcredit_db_${DATE}.backup

# Cleanup backups older than 30 days
find ${BACKUP_DIR} -name "*.backup" -mtime +30 -delete
```

## Connection Pooling Configuration

### PgBouncer Configuration for Each Service

```ini
# /etc/pgbouncer/pgbouncer.ini

[databases]
auth_db = host=auth-db port=5432 dbname=auth_db
customer_db = host=customer-db port=5432 dbname=customer_db
order_db = host=order-db port=5432 dbname=order_db
intl_shipping_db = host=intl-shipping-db port=5432 dbname=intl_shipping_db
pickup_db = host=pickup-db port=5432 dbname=pickup_db
analytics_db = host=analytics-db port=5432 dbname=analytics_db
reverse_logistics_db = host=reverse-logistics-db port=5432 dbname=reverse_logistics_db
franchise_db = host=franchise-db port=5432 dbname=franchise_db
microcredit_db = host=microcredit-db port=5432 dbname=microcredit_db

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 5
max_db_connections = 50
```

## Migration Management

### Alembic Configuration Per Service

```python
# Each service has its own alembic configuration
SERVICES_CONFIG = {
    'auth': {
        'sqlalchemy.url': 'postgresql+asyncpg://auth:auth_pass@auth-db:5432/auth_db',
        'version_table': 'alembic_version_auth'
    },
    'customer': {
        'sqlalchemy.url': 'postgresql+asyncpg://customer:customer_pass@customer-db:5432/customer_db',
        'version_table': 'alembic_version_customer'
    },
    'order': {
        'sqlalchemy.url': 'postgresql+asyncpg://order:order_pass@order-db:5432/order_db',
        'version_table': 'alembic_version_order'
    },
    'shipping': {
        'sqlalchemy.url': 'postgresql+asyncpg://intlship:intlship_pass@intl-shipping-db:5432/intl_shipping_db',
        'version_table': 'alembic_version_shipping'
    },
    'pickup': {
        'sqlalchemy.url': 'postgresql+asyncpg://pickup:pickup_pass@pickup-db:5432/pickup_db',
        'version_table': 'alembic_version_pickup'
    },
    'analytics': {
        'sqlalchemy.url': 'postgresql+asyncpg://analytics:analytics_pass@analytics-db:5432/analytics_db',
        'version_table': 'alembic_version_analytics'
    },
    'reverse_logistics': {
        'sqlalchemy.url': 'postgresql+asyncpg://revlog:revlog_pass@reverse-logistics-db:5432/reverse_logistics_db',
        'version_table': 'alembic_version_reverse_logistics'
    },
    'franchise': {
        'sqlalchemy.url': 'postgresql+asyncpg://franchise:franchise_pass@franchise-db:5432/franchise_db',
        'version_table': 'alembic_version_franchise'
    },
    'microcredit': {
        'sqlalchemy.url': 'postgresql+asyncpg://microcredit:microcredit_pass@microcredit-db:5432/microcredit_db',
        'version_table': 'alembic_version_microcredit'
    }
}
```

This comprehensive database schema documentation covers all 9 microservices in the Quenty platform, providing detailed table structures, indexes, constraints, and performance optimization strategies for each service's database.