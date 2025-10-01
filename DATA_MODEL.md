# Quenty Platform - Complete Data Model Documentation

**Last Updated:** 2025-10-01
**Version:** 2.0
**Architecture:** Microservices with Database-per-Service Pattern

---

## Table of Contents

1. [Overview](#overview)
2. [Database Architecture](#database-architecture)
3. [Core Business Services](#core-business-services)
4. [Integration Services](#integration-services)
5. [Entity Relationship Summary](#entity-relationship-summary)
6. [Migration Status](#migration-status)

---

## Overview

Quenty uses a **microservices architecture** with the **Database-per-Service** pattern. Each service has its own PostgreSQL database, ensuring loose coupling and independent scalability.

### Key Principles

- ✅ **Database Independence**: Each service owns its data
- ✅ **Async ORM**: SQLAlchemy 2.x with AsyncPG driver
- ✅ **Soft Deletes**: Most entities use `deleted_at` for soft deletion
- ✅ **Audit Trails**: `created_at`, `updated_at`, `created_by` fields
- ✅ **String References**: Cross-service relationships use String IDs (no FK constraints)

---

## Database Architecture

| Service | Database Name | Port | Tables | Migration Status |
|---------|---------------|------|--------|------------------|
| auth-service | auth_db | 5441 | 5 | ⚠️ Needs migrations |
| customer | customer_db | 5433 | 4 | ⚠️ Needs migrations |
| order | order_db | 5434 | 6 | ⚠️ Needs migrations |
| pickup | pickup_db | 5435 | 5 | ⚠️ Needs migrations |
| international-shipping | intl_shipping_db | 5436 | 12 | ⚠️ Needs migrations |
| microcredit | microcredit_db | 5437 | 6 | ⚠️ Needs migrations |
| analytics | analytics_db | 5438 | 3 | ⚠️ Needs Alembic init |
| reverse-logistics | reverse_logistics_db | 5439 | 5 | ⚠️ Needs Alembic init |
| franchise | franchise_db | 5440 | 4 | ⚠️ Needs Alembic init |
| carrier-integration | carrier_db | 5442 | 8 | ✅ Complete |
| shopify-integration | shopify_db | 5443 | 6 | ⚠️ Needs migrations |
| mercadolibre-integration | meli_db | 5444 | 5 | ⚠️ Needs migrations |
| rag-service | rag_db | 5445 | 3 | ⚠️ Needs migrations |
| woocommerce-integration | woocommerce_db | 5446 | 11 | ⚠️ Needs Alembic init |

**Total Databases:** 14
**Total Tables:** ~90

---

## Core Business Services

### 1. auth-service (auth_db)

**Purpose:** User authentication, authorization, and role management

#### Tables

**users**
```python
- id: Integer (PK)
- unique_id: String(255) UNIQUE  # Used for cross-service references
- email: String(255) UNIQUE
- username: String(100) UNIQUE
- password_hash: String(255)
- first_name: String(100)
- last_name: String(100)
- is_active: Boolean
- is_superuser: Boolean
- email_verified: Boolean
- phone: String(20)
- created_at: DateTime
- updated_at: DateTime
- last_login: DateTime
- deleted_at: DateTime  # Soft delete
```

**roles**
```python
- id: Integer (PK)
- name: String(50) UNIQUE  # admin, customer, driver, franchise_owner
- description: String(255)
- permissions: JSON  # {\"orders\": [\"read\", \"write\"], ...}
- created_at: DateTime
```

**user_roles** (Many-to-Many)
```python
- id: Integer (PK)
- user_id: Integer FK(users.id)
- role_id: Integer FK(roles.id)
- assigned_at: DateTime
- assigned_by: Integer FK(users.id)
```

**companies**
```python
- id: Integer (PK)
- company_id: String(255) UNIQUE
- name: String(255)
- tax_id: String(50)
- owner_user_id: Integer FK(users.id)
- active: Boolean
- created_at: DateTime
```

**oauth_tokens** (OAuth integration)
```python
- id: Integer (PK)
- user_id: Integer FK(users.id)
- provider: String(50)  # google, shopify, mercadolibre
- access_token: Text  # Encrypted
- refresh_token: Text  # Encrypted
- expires_at: DateTime
- created_at: DateTime
```

**Key Relationships:**
- User →→ Role (Many-to-Many via user_roles)
- User → Company (One-to-Many)

---

### 2. customer (customer_db)

**Purpose:** Customer profiles, support tickets, and customer analytics

#### Tables

**customers**
```python
- id: Integer (PK)
- customer_id: String(255) UNIQUE
- user_id: String(255) INDEX  # Reference to auth.users.unique_id
- company_id: String(255) INDEX
- customer_type: String(50)  # individual, business
- full_name: String(255)
- email: String(255)
- phone: String(20)
- address: Text
- city: String(100)
- state: String(100)
- country: String(100)
- postal_code: String(20)
- created_at: DateTime
- updated_at: DateTime
- deleted_at: DateTime
```

**support_tickets**
```python
- id: Integer (PK)
- ticket_id: String(255) UNIQUE
- customer_id: String(255) INDEX
- title: String(500)
- description: Text
- status: String(50)  # open, in_progress, resolved, closed
- priority: String(20)  # low, medium, high, urgent
- assigned_to: String(255)  # Reference to user_id
- created_at: DateTime
- updated_at: DateTime
- resolved_at: DateTime
```

**ticket_messages**
```python
- id: Integer (PK)
- ticket_id: Integer FK(support_tickets.id)
- sender_id: String(255)  # user_id
- sender_type: String(20)  # customer, agent
- message: Text
- created_at: DateTime
```

**customer_analytics**
```python
- id: Integer (PK)
- customer_id: String(255) INDEX
- metric_type: String(50)  # orders_count, total_spent, avg_order_value
- metric_value: Float
- calculated_at: DateTime
```

---

### 3. order (order_db)

**Purpose:** Orders, products, inventory management

#### Tables

**orders**
```python
- id: Integer (PK)
- order_number: String(255) UNIQUE
- customer_id: String(255) INDEX
- order_date: DateTime
- status: String(50)  # pending, confirmed, shipped, delivered, cancelled
- total_amount: Float
- currency: String(10)
- shipping_address: Text
- billing_address: Text
- payment_method: String(50)
- payment_status: String(50)
- created_at: DateTime
- updated_at: DateTime
```

**order_items**
```python
- id: Integer (PK)
- order_id: Integer FK(orders.id)
- product_id: Integer FK(products.id)
- quantity: Integer
- unit_price: Numeric(10, 2)
- total_price: Numeric(10, 2)
- discount: Numeric(10, 2)
```

**products**
```python
- id: Integer (PK)
- product_id: String(255) UNIQUE
- sku: String(100) UNIQUE
- name: String(500)
- description: Text
- category: String(100)
- price: Numeric(10, 2)
- cost: Numeric(10, 2)
- weight_kg: Float
- dimensions: JSON  # {length, width, height}
- active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

**inventory**
```python
- id: Integer (PK)
- product_id: Integer FK(products.id)
- warehouse_id: String(255) INDEX
- quantity: Integer
- reserved_quantity: Integer
- min_stock_level: Integer
- last_updated: DateTime
```

**inventory_movements**
```python
- id: Integer (PK)
- product_id: Integer FK(products.id)
- warehouse_id: String(255)
- movement_type: String(50)  # inbound, outbound, adjustment, return
- quantity: Integer
- reference_id: String(255)  # Order ID, Return ID, etc.
- created_at: DateTime
- created_by: String(255)
```

**warehouses**
```python
- id: Integer (PK)
- warehouse_id: String(255) UNIQUE
- name: String(255)
- address: Text
- city: String(100)
- country: String(100)
- active: Boolean
```

---

### 4. pickup (pickup_db)

**Purpose:** Package pickup scheduling and route management

#### Tables

**pickups**
```python
- id: Integer (PK)
- pickup_id: String(255) UNIQUE
- customer_id: String(255) INDEX
- pickup_type: String(50)  # on_demand, scheduled, recurring
- status: String(50)  # scheduled, assigned, in_progress, completed, cancelled
- pickup_date: Date
- time_window_start: Time
- time_window_end: Time
- actual_pickup_time: DateTime
- pickup_address: Text
- pickup_latitude: Float
- pickup_longitude: Float
- contact_name: String(255)
- contact_phone: String(50)
- package_count: Integer
- estimated_weight_kg: Float
- assigned_driver_id: String(255) INDEX
- order_id: String(255) INDEX
- created_at: DateTime
- updated_at: DateTime
```

**pickup_packages**
```python
- id: Integer (PK)
- package_id: String(255) UNIQUE
- pickup_id: Integer FK(pickups.id)
- description: String(500)
- weight_kg: Float
- dimensions: JSON
- tracking_number: String(255) UNIQUE INDEX
- destination_address: Text
- order_id: String(255) INDEX
- created_at: DateTime
```

**pickup_routes**
```python
- id: Integer (PK)
- route_id: String(255) UNIQUE
- driver_id: String(255) INDEX
- route_date: Date
- status: String(50)  # planned, in_progress, completed
- total_pickups: Integer
- completed_pickups: Integer
- route_path: JSON  # GeoJSON or array of coordinates
- created_at: DateTime
```

**pickup_attempts**
```python
- id: Integer (PK)
- pickup_id: Integer FK(pickups.id)
- attempt_number: Integer
- attempted_at: DateTime
- status: String(50)  # successful, failed, customer_unavailable
- notes: Text
- created_by: String(255)
```

**drivers**
```python
- id: Integer (PK)
- driver_id: String(255) UNIQUE
- user_id: String(255) INDEX
- name: String(255)
- phone: String(50)
- vehicle_type: String(50)
- license_plate: String(50)
- active: Boolean
- created_at: DateTime
```

---

### 5. international-shipping (intl_shipping_db)

**Purpose:** International shipping rates, manifests, carriers

#### Tables

**rates** (Base pricing)
```python
- id: Integer (PK)
- name: String(255)
- operator_id: String  # DHL, FEDEX, UPS
- service_id: String  # EXPRESS, GROUND
- weight_min: Numeric(10, 2)
- weight_max: Numeric(10, 2)
- fixed_fee: Numeric(10, 2)
- percentage: Boolean
- created_at: DateTime
- updated_at: DateTime
- deleted_at: DateTime
```

**catalogs** (Rate groupings)
```python
- id: Integer (PK)
- catalog_id: String(255) UNIQUE
- name: String(255)
- description: Text
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
- deleted_at: DateTime
```

**catalog_rates** (M2M between catalogs and rates)
```python
- id: Integer (PK)
- catalog_id: Integer FK(catalogs.id)
- rate_id: Integer FK(rates.id)
- custom_fixed_fee: Numeric(10, 2)
- custom_percentage: Boolean
- created_at: DateTime
```

**client_ratebooks** (Customer-specific pricing)
```python
- id: Integer (PK)
- ratebook_id: String(255) UNIQUE
- client_id: String(255) INDEX
- warehouse_id: String(255) INDEX
- rate_id: Integer FK(rates.id) NULLABLE
- catalog_id: Integer FK(catalogs.id) NULLABLE
- operator_id: String INDEX
- service_id: String INDEX
- weight_min: Numeric(10, 2) INDEX
- weight_max: Numeric(10, 2) INDEX
- fixed_fee: Numeric(10, 2)
- percentage: Boolean
- dependent: Boolean  # If true, inherits from base rate
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
- deleted_at: DateTime

INDEX idx_client_rate_lookup (client_id, warehouse_id, operator_id, service_id, weight_min, weight_max)
```

**manifests** (International shipments)
```python
- id: Integer (PK)
- unique_id: String(255) UNIQUE
- manifest_id: String(255) UNIQUE
- status: String(50)  # draft, submitted, approved, shipped, in_transit, delivered
- total_weight: Float
- total_volume: Float
- total_value: Float
- currency: String(10)
- origin_country: String(100)
- destination_country: String(100)
- shipping_zone: String(50)
- carrier_id: Integer FK(shipping_carriers.id) NULLABLE
- carrier_service: String(100)
- tracking_number: String(255) UNIQUE INDEX
- estimated_delivery: DateTime
- company_id: String(255) INDEX
- created_by: String(255)
- created_at: DateTime
- updated_at: DateTime
- submitted_at: DateTime
- approved_at: DateTime
- shipped_at: DateTime
- delivered_at: DateTime
```

**manifest_items**
```python
- id: Integer (PK)
- manifest_id: Integer FK(manifests.id)
- description: Text
- quantity: Integer
- weight: Float
- volume: Float
- value: Float
- hs_code: String(50)  # Harmonized System Code
- country_of_origin: String(100)
- product_id: Integer NULLABLE
- created_at: DateTime
```

**shipping_carriers**
```python
- id: Integer (PK)
- name: String(255)
- code: String(50) UNIQUE  # DHL, FEDEX, UPS, etc.
- api_endpoint: String(500)
- api_key: String(500)  # ⚠️ Should be encrypted
- api_username: String(255)
- api_password: String(255)  # ⚠️ Should be encrypted
- active: Boolean
- supported_services: JSON
- supported_countries: JSON
- config: JSON
- created_at: DateTime
- updated_at: DateTime
- deleted_at: DateTime
```

**countries**
```python
- id: Integer (PK)
- country_code: String(3) UNIQUE  # ISO 3166
- name: String(255)
- shipping_zone: String(50)
- active: Boolean
```

**document_types**
```python
- id: Integer (PK)
- code: String(50) UNIQUE  # invoice, packing_list, letter_of_responsibility
- name: String(255)
- description: Text
- required_fields: JSON
```

**documents**
```python
- id: Integer (PK)
- document_type_id: Integer FK(document_types.id)
- envio_id: String(255) INDEX  # Reference to manifest.unique_id
- client_id: String(255) INDEX
- storage_url: String(1024)
- file_name: String(255)
- created_at: DateTime
- created_by: String(255)
```

**signatures** (Digital signatures for documents)
```python
- id: Integer (PK)
- client_id: String(255) INDEX
- image_url: String(1024)
- created_at: DateTime
```

---

### 6. microcredit (microcredit_db)

**Purpose:** Microcredit applications, accounts, and payment management

#### Tables

**credit_applications**
```python
- id: Integer (PK)
- application_id: String(255) UNIQUE
- customer_id: String(255) INDEX
- requested_amount: Numeric(12, 2)
- requested_term_months: Integer
- status: String(50)  # pending, approved, rejected, cancelled
- decision_date: DateTime
- decision_by: String(255)
- rejection_reason: Text
- created_at: DateTime
- updated_at: DateTime
```

**credit_accounts**
```python
- id: Integer (PK)
- account_id: String(255) UNIQUE
- application_id: String(255) INDEX
- customer_id: String(255) INDEX
- approved_amount: Numeric(12, 2)
- disbursed_amount: Numeric(12, 2)
- outstanding_balance: Numeric(12, 2)
- interest_rate: Numeric(5, 2)  # Percentage
- term_months: Integer
- status: String(50)  # active, completed, defaulted, written_off
- disbursement_date: Date
- maturity_date: Date
- created_at: DateTime
```

**payments**
```python
- id: Integer (PK)
- payment_id: String(255) UNIQUE
- account_id: String(255) INDEX
- amount: Numeric(12, 2)
- payment_date: Date
- payment_method: String(50)
- principal_amount: Numeric(12, 2)
- interest_amount: Numeric(12, 2)
- fees_amount: Numeric(12, 2)
- status: String(50)  # completed, pending, failed, reversed
- transaction_reference: String(255)
- created_at: DateTime
```

**payment_schedules**
```python
- id: Integer (PK)
- account_id: String(255) INDEX
- due_date: Date
- amount_due: Numeric(12, 2)
- amount_paid: Numeric(12, 2)
- status: String(50)  # upcoming, paid, overdue, waived
- paid_date: Date
```

**credit_scores**
```python
- id: Integer (PK)
- customer_id: String(255) INDEX
- score: Integer  # 300-850
- payment_history_score: Integer
- debt_ratio_score: Integer
- credit_utilization_score: Integer
- calculated_at: DateTime
```

**risk_assessments**
```python
- id: Integer (PK)
- application_id: String(255) INDEX
- risk_level: String(20)  # low, medium, high
- risk_factors: JSON
- recommended_amount: Numeric(12, 2)
- recommended_term: Integer
- assessed_by: String(50)  # system, manual
- assessed_at: DateTime
```

---

### 7. analytics (analytics_db)

**Purpose:** Business metrics, dashboards, and reporting

#### Tables

**metrics**
```python
- id: Integer (PK)
- metric_id: String(255) UNIQUE
- metric_type: String(100)  # orders_total, revenue_daily, shipments_count
- value: Float
- dimensions: JSON  # {\"country\": \"CO\", \"carrier\": \"DHL\"}
- timestamp: DateTime INDEX
- source_service: String(50)
- source_entity_id: String(255)
- tags: JSON  # For custom filtering
- created_at: DateTime
```

**dashboards**
```python
- id: Integer (PK)
- dashboard_id: String(255) UNIQUE
- name: String(255)
- description: Text
- owner_id: String(255) INDEX
- config: JSON  # Dashboard layout and widgets
- is_public: Boolean
- created_at: DateTime
- updated_at: DateTime
```

**reports**
```python
- id: Integer (PK)
- report_id: String(255) UNIQUE
- name: String(255)
- report_type: String(50)  # sales, operations, financial
- parameters: JSON
- status: String(50)  # queued, processing, completed, failed
- result_url: String(1024)
- requested_by: String(255)
- requested_at: DateTime
- completed_at: DateTime
```

---

### 8. reverse-logistics (reverse_logistics_db)

**Purpose:** Returns, exchanges, and product inspections

#### Tables

**returns**
```python
- id: Integer (PK)
- return_id: String(255) UNIQUE
- order_id: String(255) INDEX
- customer_id: String(255) INDEX
- reason: String(255)
- reason_details: Text
- status: String(50)  # requested, approved, rejected, picked_up, inspected, completed
- return_type: String(50)  # refund, exchange, repair
- requested_at: DateTime
- approved_at: DateTime
- completed_at: DateTime
```

**return_items**
```python
- id: Integer (PK)
- return_id: Integer FK(returns.id)
- product_id: String(255)
- quantity: Integer
- condition: String(50)  # unopened, opened, damaged, defective
- refund_amount: Numeric(10, 2)
```

**inspections**
```python
- id: Integer (PK)
- inspection_id: String(255) UNIQUE
- return_id: Integer FK(returns.id)
- inspector_id: String(255)
- inspection_date: DateTime
- condition_assessment: String(50)
- notes: Text
- photos: JSON  # Array of photo URLs
- approved_for_resale: Boolean
```

**return_pickups**
```python
- id: Integer (PK)
- return_id: Integer FK(returns.id)
- pickup_date: Date
- pickup_address: Text
- tracking_number: String(255)
- carrier: String(100)
- status: String(50)
```

**refunds**
```python
- id: Integer (PK)
- refund_id: String(255) UNIQUE
- return_id: Integer FK(returns.id)
- amount: Numeric(10, 2)
- refund_method: String(50)
- status: String(50)  # pending, processed, failed
- processed_at: DateTime
- transaction_reference: String(255)
```

---

### 9. franchise (franchise_db)

**Purpose:** Franchise management, territories, and performance tracking

#### Tables

**franchises**
```python
- id: Integer (PK)
- franchise_id: String(255) UNIQUE
- name: String(255)
- owner_user_id: String(255) INDEX
- territory_code: String(50)
- address: Text
- city: String(100)
- state: String(100)
- country: String(100)
- phone: String(50)
- email: String(255)
- status: String(50)  # active, inactive, suspended
- contract_start_date: Date
- contract_end_date: Date
- created_at: DateTime
- updated_at: DateTime
```

**territories**
```python
- id: Integer (PK)
- territory_code: String(50) UNIQUE
- name: String(255)
- description: Text
- coverage_area: JSON  # GeoJSON polygon
- population: Integer
- active: Boolean
```

**franchise_performance**
```python
- id: Integer (PK)
- franchise_id: String(255) INDEX
- metric_type: String(50)  # revenue, orders_count, customer_satisfaction
- metric_value: Float
- period_start: Date
- period_end: Date
- calculated_at: DateTime
```

**franchise_fees**
```python
- id: Integer (PK)
- franchise_id: String(255) INDEX
- fee_type: String(50)  # initial, monthly, royalty, marketing
- amount: Numeric(12, 2)
- due_date: Date
- paid_date: Date
- status: String(50)  # pending, paid, overdue
```

---

## Integration Services

### 10. carrier-integration (carrier_db)

**Purpose:** Multi-carrier logistics integration (DHL, FedEx, UPS, etc.)

#### Tables

**carrier_credentials** (Encrypted carrier API credentials)
```python
- id: Integer (PK)
- carrier_name: String(100) INDEX  # DHL, FEDEX, UPS
- encrypted_credentials: LargeBinary  # AES-256 encrypted JSON
- encryption_key_id: String(255)
- is_active: Boolean
- environment: String(20)  # sandbox, production
- created_at: DateTime
- updated_at: DateTime
```

**shipments**
```python
- id: Integer (PK)
- shipment_id: String(255) UNIQUE
- carrier: String(50) INDEX
- service_type: String(100)
- tracking_number: String(255) UNIQUE INDEX
- status: String(50)
- origin: JSON
- destination: JSON
- weight_kg: Float
- dimensions: JSON
- declared_value: Numeric(10, 2)
- label_url: String(1024)
- created_at: DateTime
- shipped_at: DateTime
```

**quotes** (Rate quotes from carriers)
```python
- id: Integer (PK)
- quote_id: String(255) UNIQUE
- carrier: String(50)
- service_type: String(100)
- origin_country: String(100)
- destination_country: String(100)
- weight_kg: Float
- quoted_price: Numeric(10, 2)
- currency: String(10)
- transit_days: Integer
- valid_until: DateTime
- created_at: DateTime
```

**exchange_rates** (Currency conversion rates from Banco República)
```python
- id: Integer (PK)
- currency_pair: String(10)  # USD-COP
- rate: Numeric(12, 6)
- source: String(100)  # banco_republica
- fetched_at: DateTime INDEX
```

**international_mailboxes** (Pasarex, Aeropost mailboxes)
```python
- id: Integer (PK)
- provider: String(50)  # pasarex, aeropost
- mailbox_number: String(100) UNIQUE
- customer_id: String(255) INDEX
- customer_name: String(255)
- address_line1: String(500)
- address_line2: String(500)
- city: String(100)
- state: String(100)
- country: String(100)
- postal_code: String(20)
- status: String(50)  # active, inactive, suspended
- created_at: DateTime
```

**pickit_points** (Pickit pickup point locations)
```python
- id: Integer (PK)
- point_id: String(100) UNIQUE
- name: String(255)
- address: Text
- city: String(100)
- coordinates: JSON  # {lat, lng}
- operating_hours: JSON
- is_active: Boolean
```

**tracking_events** (Tracking history)
```python
- id: Integer (PK)
- tracking_number: String(255) INDEX
- carrier: String(50)
- event_type: String(50)  # pickup, in_transit, delivered, exception
- event_description: Text
- event_timestamp: DateTime
- location: String(255)
- created_at: DateTime
```

**webhook_logs** (Carrier webhook processing)
```python
- id: Integer (PK)
- carrier: String(50)
- event_type: String(50)
- payload: JSON
- processed: Boolean
- processing_result: Text
- received_at: DateTime
- processed_at: DateTime
```

---

### 11. shopify-integration (shopify_db)

**Purpose:** Shopify marketplace integration

#### Tables

**shopify_stores**
```python
- id: Integer (PK)
- store_id: String(255) UNIQUE
- shop_domain: String(255) UNIQUE  # mystore.myshopify.com
- access_token: Text  # Encrypted
- scope: String(500)  # Read/write permissions
- is_active: Boolean
- installed_at: DateTime
- created_at: DateTime
```

**shopify_orders**
```python
- id: Integer (PK)
- store_id: String(255) INDEX
- shopify_order_id: BigInteger UNIQUE
- order_number: String(255)
- quenty_order_id: String(255) INDEX  # Reference to order.orders
- customer_email: String(255)
- total_price: Numeric(10, 2)
- currency: String(10)
- fulfillment_status: String(50)
- financial_status: String(50)
- synced_at: DateTime
- created_at: DateTime
```

**shopify_products**
```python
- id: Integer (PK)
- store_id: String(255) INDEX
- shopify_product_id: BigInteger UNIQUE
- quenty_product_id: String(255) INDEX
- title: String(500)
- sku: String(100)
- price: Numeric(10, 2)
- inventory_quantity: Integer
- synced_at: DateTime
```

**shopify_customers**
```python
- id: Integer (PK)
- store_id: String(255) INDEX
- shopify_customer_id: BigInteger UNIQUE
- quenty_customer_id: String(255) INDEX
- email: String(255)
- first_name: String(100)
- last_name: String(100)
- synced_at: DateTime
```

**shopify_webhooks**
```python
- id: Integer (PK)
- store_id: String(255) INDEX
- topic: String(100)  # orders/create, products/update
- webhook_id: BigInteger
- address: String(1024)
- created_at: DateTime
```

**sync_logs**
```python
- id: Integer (PK)
- store_id: String(255) INDEX
- sync_type: String(50)  # orders, products, customers
- status: String(50)  # success, failed, partial
- records_synced: Integer
- errors: JSON
- started_at: DateTime
- completed_at: DateTime
```

---

### 12. mercadolibre-integration (meli_db)

**Purpose:** MercadoLibre marketplace integration

#### Tables

**meli_accounts**
```python
- id: Integer (PK)
- account_id: String(255) UNIQUE
- user_id: BigInteger  # MercadoLibre user ID
- access_token: Text  # Encrypted
- refresh_token: Text  # Encrypted
- expires_at: DateTime
- site_id: String(10)  # MLA (Argentina), MLM (Mexico), etc.
- is_active: Boolean
- created_at: DateTime
```

**meli_orders**
```python
- id: Integer (PK)
- account_id: String(255) INDEX
- meli_order_id: BigInteger UNIQUE
- quenty_order_id: String(255) INDEX
- status: String(50)  # confirmed, paid, shipped, delivered
- total_amount: Numeric(10, 2)
- currency: String(10)
- buyer_id: BigInteger
- synced_at: DateTime
- created_at: DateTime
```

**meli_products**
```python
- id: Integer (PK)
- account_id: String(255) INDEX
- meli_listing_id: String(50) UNIQUE  # MLB123456789
- quenty_product_id: String(255) INDEX
- title: String(500)
- price: Numeric(10, 2)
- available_quantity: Integer
- listing_type: String(50)  # gold_special, gold_pro, free
- status: String(50)  # active, paused, closed
- synced_at: DateTime
```

**meli_questions**
```python
- id: Integer (PK)
- account_id: String(255) INDEX
- question_id: BigInteger UNIQUE
- item_id: String(50) INDEX
- text: Text
- answer: Text
- status: String(50)  # unanswered, answered
- from_user_id: BigInteger
- asked_at: DateTime
- answered_at: DateTime
```

**meli_notifications**
```python
- id: Integer (PK)
- account_id: String(255) INDEX
- notification_id: BigInteger UNIQUE
- topic: String(100)  # orders, questions, items
- resource: String(500)
- processed: Boolean
- received_at: DateTime
- processed_at: DateTime
```

---

### 13. rag-service (rag_db)

**Purpose:** RAG (Retrieval-Augmented Generation) for AI chat and search

#### Tables

**documents**
```python
- id: Integer (PK)
- document_id: String(255) UNIQUE
- title: String(500)
- content: Text
- source: String(255)
- source_type: String(50)  # faq, policy, product_manual
- embedding: Vector(1536)  # pgvector for similarity search
- metadata: JSON
- created_at: DateTime
- updated_at: DateTime
```

**conversations**
```python
- id: Integer (PK)
- conversation_id: String(255) UNIQUE
- user_id: String(255) INDEX
- context: JSON  # Conversation history
- created_at: DateTime
- updated_at: DateTime
```

**chat_messages**
```python
- id: Integer (PK)
- conversation_id: String(255) INDEX
- role: String(20)  # user, assistant, system
- content: Text
- retrieved_docs: JSON  # Array of document IDs used
- timestamp: DateTime
```

---

### 14. woocommerce-integration (woocommerce_db)

**Purpose:** WooCommerce store integration

#### Tables

**stores**
```python
- id: String(50) (PK)
- name: String(255)
- url: String(500) UNIQUE
- consumer_key: String(255)
- consumer_secret: Text  # Encrypted
- webhook_secret: String(255)
- active: Boolean
- version: String(10)  # wc/v3
- created_at: DateTime
```

**orders**
```python
- id: Integer (PK)
- store_id: String(50) FK(stores.id)
- wc_order_id: Integer
- order_number: String(255)
- quenty_order_id: String(255) INDEX
- status: Enum(OrderStatus)
- total: Numeric(10, 2)
- currency: String(10)
- customer_email: String(255)
- synced_at: DateTime
- created_at: DateTime
```

**order_items**
```python
- id: Integer (PK)
- order_id: Integer FK(orders.id)
- wc_item_id: Integer
- product_id: Integer
- name: String(500)
- quantity: Integer
- price: Numeric(10, 2)
- total: Numeric(10, 2)
```

**products**
```python
- id: Integer (PK)
- store_id: String(50) FK(stores.id)
- wc_product_id: Integer
- quenty_product_id: String(255) INDEX
- name: String(500)
- sku: String(100)
- type: Enum(ProductType)
- price: Numeric(10, 2)
- stock_quantity: Integer
- synced_at: DateTime
```

**product_variations**
```python
- id: Integer (PK)
- product_id: Integer FK(products.id)
- wc_variation_id: Integer
- sku: String(100)
- price: Numeric(10, 2)
- stock_quantity: Integer
- attributes: JSON
```

**customers**
```python
- id: Integer (PK)
- store_id: String(50) FK(stores.id)
- wc_customer_id: Integer
- quenty_customer_id: String(255) INDEX
- email: String(255) UNIQUE
- first_name: String(100)
- last_name: String(100)
- phone: String(20)
- synced_at: DateTime
```

**shipping_requests**
```python
- id: Integer (PK)
- order_id: Integer FK(orders.id)
- quenty_shipment_id: String(255)
- carrier: String(50)
- tracking_number: String(255)
- status: String(50)
- requested_at: DateTime
- fulfilled_at: DateTime
```

**webhook_events**
```python
- id: Integer (PK)
- store_id: String(50) FK(stores.id)
- event_type: String(100)
- resource_id: Integer
- payload: JSON
- processed: Boolean
- received_at: DateTime
- processed_at: DateTime
```

**sync_logs**
```python
- id: Integer (PK)
- store_id: String(50) FK(stores.id)
- sync_type: String(50)
- status: String(50)
- records_count: Integer
- errors: JSON
- started_at: DateTime
- completed_at: DateTime
```

**notifications**
```python
- id: Integer (PK)
- store_id: String(50) FK(stores.id)
- notification_type: String(50)
- title: String(255)
- message: Text
- is_read: Boolean
- created_at: DateTime
```

---

## Entity Relationship Summary

### Cross-Service References (String IDs)

Since we use Database-per-Service pattern, cross-service relationships are maintained via String IDs:

```
auth.users.unique_id
  ↓ (String reference)
├── customer.customers.user_id
├── order.orders.customer_id
├── pickup.pickups.customer_id
├── microcredit.credit_applications.customer_id
└── franchise.franchises.owner_user_id

order.orders.order_number
  ↓ (String reference)
├── pickup.pickups.order_id
├── pickup.pickup_packages.order_id
└── reverse-logistics.returns.order_id

pickup.pickup_packages.tracking_number
  ↓ (String reference)
└── carrier-integration.tracking_events.tracking_number
```

### Service Communication Patterns

1. **Synchronous**: Via API Gateway (REST)
2. **Asynchronous**: Via RabbitMQ message broker
3. **Data Sync**: Polling + webhook events

---

## Migration Status

### ✅ Complete (With Migrations)
- carrier-integration (1 migration)

### ⚠️ Needs Initial Migration Generation
- auth-service
- customer
- order
- pickup
- international-shipping
- microcredit
- shopify-integration
- mercadolibre-integration
- rag-service

### ⚠️ Needs Alembic Initialization
- analytics
- franchise
- reverse-logistics
- woocommerce-integration

### Recommended Actions

```bash
# For services needing Alembic init
cd microservices/{service-name}
alembic init alembic

# For services with alembic but no migrations
cd microservices/{service-name}
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## Security Considerations

### Encryption Requirements

**Fields that MUST be encrypted:**
- `auth.oauth_tokens.access_token`
- `auth.oauth_tokens.refresh_token`
- `carrier-integration.carrier_credentials.encrypted_credentials`
- `international-shipping.shipping_carriers.api_key`
- `international-shipping.shipping_carriers.api_password`
- `shopify-integration.shopify_stores.access_token`
- `mercadolibre-integration.meli_accounts.access_token`
- `mercadolibre-integration.meli_accounts.refresh_token`
- `woocommerce-integration.stores.consumer_secret`

**Encryption Method:** AES-256-GCM
**Key Storage:** Environment variable `ENCRYPTION_KEY`

### Soft Delete Pattern

Most tables use `deleted_at` timestamp for soft deletion:
- Allows data recovery
- Maintains referential integrity
- Enables audit trails
- Query performance consideration: Always filter `WHERE deleted_at IS NULL`

---

## Database Performance Considerations

### Key Indexes

All services have indexes on:
- Primary keys (automatic)
- Unique constraint columns
- Foreign key columns
- Frequently queried fields (status, created_at, customer_id, etc.)
- Composite indexes for complex queries

### Recommended Additional Indexes

```sql
-- international-shipping
CREATE INDEX idx_manifests_company_status_date
ON manifests(company_id, status, created_at DESC);

-- pickup
CREATE INDEX idx_pickups_driver_date_status
ON pickups(assigned_driver_id, pickup_date, status);

-- analytics
CREATE INDEX idx_metrics_timestamp_type
ON metrics(timestamp DESC, metric_type);
```

### Connection Pooling

All services use SQLAlchemy async with connection pooling:
- Default pool size: 5
- Max overflow: 10
- Pool timeout: 30s
- Pool recycle: 3600s

---

## Backup and Recovery

### Backup Strategy

1. **PostgreSQL Logical Backups**: Daily full backup via `pg_dump`
2. **Point-in-Time Recovery**: WAL archiving enabled
3. **Retention**: 30 days for daily backups, 1 year for monthly
4. **Replication**: Streaming replication to standby server

### Database Size Estimates

- auth_db: ~100 MB (10K users)
- order_db: ~5 GB (1M orders)
- international-shipping: ~2 GB (500K manifests)
- analytics_db: ~10 GB (time series data)
- Total: ~20-25 GB for moderate scale

---

## Monitoring

### Database Health Metrics

- Connection pool usage
- Query performance (slow query log)
- Table sizes and growth rates
- Index usage statistics
- Replication lag
- Transaction throughput

### Tools

- **Prometheus**: Database metrics exporter
- **Grafana**: Dashboards for visualization
- **pgAdmin**: Database administration
- **pg_stat_statements**: Query performance analysis

---

**Document Version:** 2.0
**Last Updated:** 2025-10-01
**Maintained By:** Quenty Platform Team
