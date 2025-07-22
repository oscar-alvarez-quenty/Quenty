# Entity Relationship Models

## Overview

This document provides comprehensive entity relationship diagrams for the Quenty microservices platform, showing the data models and relationships within each service and across service boundaries.

## General System Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUENTY PLATFORM - COMPLETE ERD                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐     │
│  │ CUSTOMER SERVICE│      │  ORDER SERVICE  │      │ SHIPPING SERVICE│     │
│  │                 │      │                 │      │                 │     │
│  │ ┌─────────────┐ │      │ ┌─────────────┐ │      │ ┌─────────────┐ │     │
│  │ │   Users     │ │      │ │  Products   │ │      │ │ Manifests   │ │     │
│  │ │             │ │      │ │             │ │      │ │             │ │     │
│  │ │ id (PK)     │ │  ┌───┼─┤ id (PK)     │ │  ┌───┼─┤ id (PK)     │ │     │
│  │ │ unique_id   │ │  │   │ │ sku         │ │  │   │ │ unique_id   │ │     │
│  │ │ username    │ │  │   │ │ name        │ │  │   │ │ status      │ │     │
│  │ │ email       │ │  │   │ │ price       │ │  │   │ │ company_id  │ │     │
│  │ │ company_id  │◄─┼──┼───┼─┤ company_id  │ │  │   │ │ created_by  │ │     │
│  │ └─────────────┘ │  │   │ └─────────────┘ │  │   │ └─────────────┘ │     │
│  │       │         │  │   │       │         │  │   │       │         │     │
│  │       │         │  │   │       │         │  │   │       │         │     │
│  │ ┌─────▼───────┐ │  │   │ ┌─────▼───────┐ │  │   │ ┌─────▼───────┐ │     │
│  │ │ Companies   │ │  │   │ │ Inventory   │ │  │   │ │ManifestItems│ │     │
│  │ │             │ │  │   │ │   Items     │ │  │   │ │             │ │     │
│  │ │ id (PK)     │ │  │   │ │             │ │  │   │ │ id (PK)     │ │     │
│  │ │ company_id  │ │  │   │ │ id (PK)     │ │  │   │ │ manifest_id │ │     │
│  │ │ name        │ │  │   │ │ product_id  │◄─┼───┼──┤ product_id  │ │     │
│  │ │ business_n  │ │  │   │ │ quantity    │ │  │   │ │ description │ │     │
│  │ └─────────────┘ │  │   │ └─────────────┘ │  │   │ └─────────────┘ │     │
│  │                 │  │   │                 │  │   │                 │     │
│  │ ┌─────────────┐ │  │   │ ┌─────────────┐ │  │   │ ┌─────────────┐ │     │
│  │ │DocumentTypes│ │  │   │ │   Orders    │ │  │   │ │ShippingRates│ │     │
│  │ │             │ │  │   │ │             │ │  │   │ │             │ │     │
│  │ │ id (PK)     │ │  │   │ │ id (PK)     │ │  │   │ │ id (PK)     │ │     │
│  │ │ name        │ │  │   │ │ order_number│ │  │   │ │ manifest_id │ │     │
│  │ │ code        │ │  │   │ │ customer_id │◄─┼───┼──┤ carrier_name│ │     │
│  │ └─────────────┘ │  │   │ │ company_id  │ │  │   │ │ total_cost  │ │     │
│  └─────────────────┘  │   │ └─────────────┘ │  │   │ └─────────────┘ │     │
│                       │   │       │         │  │   │                 │     │
│                       │   │       │         │  │   │ ┌─────────────┐ │     │
│                       │   │ ┌─────▼───────┐ │  │   │ │  Countries  │ │     │
│                       │   │ │ OrderItems  │ │  │   │ │             │ │     │
│                       │   │ │             │ │  │   │ │ id (PK)     │ │     │
│                       │   │ │ id (PK)     │ │  │   │ │ name        │ │     │
│                       │   │ │ order_id    │ │  │   │ │ iso_code    │ │     │
│                       └───┼─┤ product_id  │ │  │   │ │ zone        │ │     │
│                           │ │ quantity    │ │  │   │ └─────────────┘ │     │
│                           │ └─────────────┘ │  │   │                 │     │
│                           │                 │  │   │ ┌─────────────┐ │     │
│                           │ ┌─────────────┐ │  │   │ │  Carriers   │ │     │
│                           │ │StockMovement│ │  │   │ │             │ │     │
│                           │ │             │ │  │   │ │ id (PK)     │ │     │
│                           │ │ id (PK)     │ │  │   │ │ name        │ │     │
│                           │ │ product_id  │ │  │   │ │ code        │ │     │
│                           │ │ movement_ty │ │  │   │ │ api_endpoint│ │     │
│                           │ │ quantity    │ │  │   │ └─────────────┘ │     │
│                           │ └─────────────┘ │  │   │                 │     │
│                           └─────────────────┘  │   └─────────────────┘     │
│                                                │                           │
│  Cross-Service Relationships:                  │                           │
│  - Users.company_id → Products.company_id      │                           │
│  - Orders.customer_id → Users.unique_id        │                           │
│  - ManifestItems.product_id → Products.id      │                           │
│  - Manifests.company_id → Companies.company_id │                           │
│  - Manifests.created_by → Users.unique_id      │                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Customer Service ERD

### Database Schema: customer_db

```
┌─────────────────────────────────────────────────┐
│                CUSTOMER SERVICE ERD             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────┐         ┌─────────────────┐│
│  │    Companies    │         │      Users      ││
│  │                 │         │                 ││
│  │ id (PK)         │◄────────┤ id (PK)         ││
│  │ company_id (UK) │    │    │ unique_id (UK)  ││
│  │ name            │    │    │ username (UK)   ││
│  │ business_name   │    └────┤ email (UK)      ││
│  │ document_type   │         │ password_hash   ││
│  │ document_number │         │ first_name      ││
│  │ active          │         │ last_name       ││
│  │ created_at      │         │ phone           ││
│  │ updated_at      │         │ role            ││
│  └─────────────────┘         │ active          ││
│                              │ last_login      ││
│                              │ company_id (FK) ││
│  ┌─────────────────┐         │ created_at      ││
│  │  DocumentTypes  │         │ updated_at      ││
│  │                 │         └─────────────────┘│
│  │ id (PK)         │                            │
│  │ name            │                            │
│  │ code (UK)       │                            │
│  │ description     │                            │
│  │ active          │                            │
│  │ created_at      │                            │
│  └─────────────────┘                            │
│                                                 │
│  Relationships:                                 │
│  - Companies (1) → Users (M)                    │
│  - Users.company_id references Companies.id     │
│                                                 │
│  Indexes:                                       │
│  - users.unique_id (unique)                     │
│  - users.username (unique)                      │
│  - users.email (unique)                         │
│  - companies.company_id (unique)                │
│  - companies.document_number (unique)           │
│  - document_types.code (unique)                 │
└─────────────────────────────────────────────────┘
```

## Order Service ERD

### Database Schema: order_db

```
┌────────────────────────────────────────────────────────────────────────┐
│                           ORDER SERVICE ERD                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────┐         ┌─────────────────┐                       │
│  │    Products     │         │ InventoryItems  │                       │
│  │                 │         │                 │                       │
│  │ id (PK)         │◄────────┤ id (PK)         │                       │
│  │ name            │    │    │ product_id (FK) │                       │
│  │ description     │    │    │ quantity        │                       │
│  │ sku (UK)        │    │    │ reserved_qty    │                       │
│  │ category        │    │    │ min_stock_level │                       │
│  │ price           │    │    │ max_stock_level │                       │
│  │ cost            │    │    │ location        │                       │
│  │ weight          │    │    │ batch_number    │                       │
│  │ dimensions      │    │    │ expiry_date     │                       │
│  │ active          │    │    │ created_at      │                       │
│  │ company_id      │    │    │ updated_at      │                       │
│  │ created_at      │    │    └─────────────────┘                       │
│  │ updated_at      │    │                                              │
│  └─────────┬───────┘    │    ┌─────────────────┐                       │
│            │            │    │ StockMovements  │                       │
│            │            │    │                 │                       │
│            │            └────┤ id (PK)         │                       │
│            │                 │ product_id (FK) │                       │
│            │                 │ movement_type   │                       │
│            │                 │ quantity        │                       │
│            │                 │ reference_number│                       │
│            │                 │ notes           │                       │
│            │                 │ created_at      │                       │
│            │                 │ created_by      │                       │
│            │                 └─────────────────┘                       │
│            │                                                           │
│            │         ┌─────────────────┐                               │
│            │         │   OrderItems    │                               │
│            │         │                 │                               │
│            └─────────┤ id (PK)         │                               │
│                      │ order_id (FK)   │                               │
│                      │ product_id (FK) │                               │
│                      │ quantity        │                               │
│                      │ unit_price      │                               │
│                      │ total_price     │                               │
│                      │ created_at      │                               │
│                      └─────────┬───────┘                               │
│                                │                                       │
│                      ┌─────────▼───────┐                               │
│                      │     Orders      │                               │
│                      │                 │                               │
│                      │ id (PK)         │                               │
│                      │ order_number(UK)│                               │
│                      │ status          │                               │
│                      │ total_amount    │                               │
│                      │ currency        │                               │
│                      │ customer_id     │ ──────► References User       │
│                      │ company_id      │ ──────► References Company    │
│                      │ created_at      │                               │
│                      │ updated_at      │                               │
│                      └─────────────────┘                               │
│                                                                        │
│  Relationships:                                                        │
│  - Products (1) → InventoryItems (M)                                   │
│  - Products (1) → StockMovements (M)                                   │
│  - Products (1) → OrderItems (M)                                       │
│  - Orders (1) → OrderItems (M)                                         │
│                                                                        │
│  Cross-Service References:                                             │
│  - Orders.customer_id → Customer Service (Users.unique_id)             │
│  - Orders.company_id → Customer Service (Companies.company_id)         │
│                                                                        │
│  Indexes:                                                              │
│  - products.sku (unique)                                               │
│  - products.company_id (index)                                         │
│  - orders.order_number (unique)                                        │
│  - orders.customer_id (index)                                          │
│  - stock_movements.product_id (index)                                  │
│  - stock_movements.created_at (index)                                  │
└────────────────────────────────────────────────────────────────────────┘
```

## International Shipping Service ERD

### Database Schema: intl_shipping_db

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTERNATIONAL SHIPPING SERVICE ERD                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐                            │
│  │   Manifests     │         │ ManifestItems   │                            │
│  │                 │         │                 │                            │
│  │ id (PK)         │◄────────┤ id (PK)         │                            │
│  │ unique_id (UK)  │    │    │ manifest_id (FK)│                            │
│  │ status          │    │    │ description     │                            │
│  │ total_weight    │    │    │ quantity        │                            │
│  │ total_volume    │    │    │ weight          │                            │
│  │ total_value     │    │    │ volume          │                            │
│  │ currency        │    │    │ value           │                            │
│  │ origin_country  │    │    │ hs_code         │                            │
│  │ destination_cty │    │    │ country_origin  │                            │
│  │ shipping_zone   │    │    │ product_id      │ ──────► References Product │
│  │ estimated_deliv │    │    │ created_at      │                            │
│  │ tracking_number │    │    └─────────────────┘                            │
│  │ company_id      │    │                                                   │
│  │ created_by      │    │    ┌─────────────────┐                            │
│  │ created_at      │    │    │ ShippingRates   │                            │
│  │ updated_at      │    │    │                 │                            │
│  └─────────┬───────┘    └────┤ id (PK)         │                            │
│            │                 │ manifest_id (FK)│                            │
│            │                 │ carrier_name    │                            │
│            │                 │ service_type    │                            │
│            │                 │ base_rate       │                            │
│            │                 │ weight_rate     │                            │
│            │                 │ volume_rate     │                            │
│            │                 │ fuel_surcharge  │                            │
│            │                 │ insurance_rate  │                            │
│            │                 │ total_cost      │                            │
│            │                 │ currency        │                            │
│            │                 │ transit_days    │                            │
│            │                 │ valid_until     │                            │
│            │                 │ created_at      │                            │
│            │                 └─────────────────┘                            │
│            │                                                                │
│  ┌─────────▼───────┐         ┌─────────────────┐                            │
│  │   Countries     │         │ ShippingCarriers│                            │
│  │                 │         │                 │                            │
│  │ id (PK)         │         │ id (PK)         │                            │
│  │ name            │         │ name            │                            │
│  │ iso_code (UK)   │         │ code (UK)       │                            │
│  │ zone            │         │ api_endpoint    │                            │
│  │ active          │         │ api_key         │                            │
│  │ created_at      │         │ active          │                            │
│  └─────────────────┘         │ supported_svcs  │                            │
│                              │ created_at      │                            │
│                              └─────────────────┘                            │
│                                                                             │
│  Relationships:                                                             │
│  - Manifests (1) → ManifestItems (M)                                        │
│  - Manifests (1) → ShippingRates (M)                                        │
│                                                                             │
│  Cross-Service References:                                                  │
│  - Manifests.company_id → Customer Service (Companies.company_id)           │
│  - Manifests.created_by → Customer Service (Users.unique_id)                │
│  - ManifestItems.product_id → Order Service (Products.id)                  │
│                                                                             │
│  Indexes:                                                                   │
│  - manifests.unique_id (unique)                                             │
│  - manifests.tracking_number (unique)                                       │
│  - manifests.company_id (index)                                             │
│  - manifest_items.manifest_id (index)                                       │
│  - countries.iso_code (unique)                                              │
│  - shipping_carriers.code (unique)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Cross-Service Data Relationships

### Service Communication and Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CROSS-SERVICE RELATIONSHIPS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Customer Service                Order Service              Shipping Service │
│  ┌─────────────────┐             ┌─────────────────┐        ┌─────────────────┐
│  │   Companies     │             │    Products     │        │   Manifests     │
│  │                 │             │                 │        │                 │
│  │ company_id ─────┼─────────────┼──→ company_id   │        │ company_id ◄────┤
│  │ name            │             │ name            │        │ unique_id       │
│  │ active          │             │ price           │        │ status          │
│  └─────────────────┘             │ active          │        │ created_by ◄────┤
│                                  └──────┬──────────┘        └─────────────────┘
│  ┌─────────────────┐                     │                          │         │
│  │     Users       │                     │                          │         │
│  │                 │                     │                  ┌───────▼───────┐ │
│  │ unique_id ──────┼─────────────────────┼──────────────────┤ManifestItems   │ │
│  │ username        │                     │                  │                │ │
│  │ email           │             ┌───────▼───────┐          │ product_id ◄───┤ │
│  │ company_id ─────┤             │   Orders      │          │ description    │ │
│  └─────────────────┘             │               │          │ quantity       │ │
│                                  │ customer_id ◄─┤          │ weight         │ │
│                                  │ company_id ◄──┤          │ value          │ │
│                                  │ order_number  │          └─────────────────┘ │
│                                  │ status        │                             │
│                                  └───────┬───────┘                             │
│                                          │                                     │
│                                  ┌───────▼───────┐                             │
│                                  │  OrderItems   │                             │
│                                  │               │                             │
│                                  │ product_id ◄──┤                             │
│                                  │ quantity      │                             │
│                                  │ unit_price    │                             │
│                                  └─────────────────┘                             │
│                                                                             │
│  Data Flow Patterns:                                                        │
│                                                                             │
│  1. User Registration Flow:                                                 │
│     Users → Companies (company validation)                                  │
│                                                                             │
│  2. Order Creation Flow:                                                    │
│     Customer Service (user/company) → Order Service (create order)          │
│     Order Service → Customer Service (validate customer)                    │
│                                                                             │
│  3. Shipping Manifest Flow:                                                 │
│     Order Service (products) → Shipping Service (manifest items)           │
│     Customer Service (company/user) → Shipping Service (manifest header)   │
│                                                                             │
│  4. Cross-Service Validation:                                               │
│     - All services validate company_id with Customer Service                │
│     - Shipping Service validates product details with Order Service        │
│     - Order Service validates customer_id with Customer Service            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Consistency Patterns

### Event-Driven Consistency

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT-DRIVEN DATA CONSISTENCY                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Event Types and Data Propagation:                                         │
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │ Customer Events │                                                        │
│  │                 │                                                        │
│  │ • user.created  │ ──→ Order Service (cache user info)                   │
│  │ • user.updated  │ ──→ Shipping Service (update manifest owner)          │
│  │ • company.created│ ──→ All services (company validation cache)          │
│  │ • company.deact │ ──→ All services (disable company operations)         │
│  └─────────────────┘                                                        │
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │  Order Events   │                                                        │
│  │                 │                                                        │
│  │ • order.created │ ──→ Shipping Service (prepare manifest)               │
│  │ • order.shipped │ ──→ Customer Service (notify user)                    │
│  │ • inventory.low │ ──→ External systems (reorder alerts)                 │
│  │ • product.created│ ──→ Shipping Service (update available products)     │
│  └─────────────────┘                                                        │
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │ Shipping Events │                                                        │
│  │                 │                                                        │
│  │ • manifest.sub  │ ──→ Order Service (update order status)               │
│  │ • shipment.del  │ ──→ Order Service (complete order)                    │
│  │ • rate.updated  │ ──→ Order Service (update shipping costs)             │
│  └─────────────────┘                                                        │
│                                                                             │
│  Consistency Strategies:                                                    │
│                                                                             │
│  1. Eventually Consistent:                                                  │
│     - User profile updates across services                                 │
│     - Company information synchronization                                  │
│     - Product catalog updates                                              │
│                                                                             │
│  2. Strong Consistency:                                                     │
│     - Financial transactions                                               │
│     - Inventory deductions                                                 │
│     - Order state transitions                                              │
│                                                                             │
│  3. Saga Pattern:                                                          │
│     - Order creation with inventory reservation                            │
│     - Manifest creation with product validation                            │
│     - Payment processing with order confirmation                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Database Indexes and Performance

### Indexing Strategy

```sql
-- Customer Service Indexes
CREATE INDEX CONCURRENTLY idx_users_company_id ON users(company_id);
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email, active);
CREATE INDEX CONCURRENTLY idx_companies_active ON companies(active);

-- Order Service Indexes  
CREATE INDEX CONCURRENTLY idx_products_company_category ON products(company_id, category);
CREATE INDEX CONCURRENTLY idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX CONCURRENTLY idx_inventory_product_location ON inventory_items(product_id, location);
CREATE INDEX CONCURRENTLY idx_stock_movements_product_date ON stock_movements(product_id, created_at);

-- Shipping Service Indexes
CREATE INDEX CONCURRENTLY idx_manifests_company_status ON manifests(company_id, status);  
CREATE INDEX CONCURRENTLY idx_manifests_created_at ON manifests(created_at DESC);
CREATE INDEX CONCURRENTLY idx_manifest_items_manifest ON manifest_items(manifest_id);
CREATE INDEX CONCURRENTLY idx_shipping_rates_manifest_carrier ON shipping_rates(manifest_id, carrier_name);
```

## Data Migration Strategy

### Cross-Service Data Migration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA MIGRATION STRATEGY                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Migration Phases:                                                          │
│                                                                             │
│  Phase 1: Core Data Setup                                                   │
│  ┌─────────────────┐                                                        │
│  │ Customer Service│ ──→ Create companies and users                         │
│  │                 │     • Bootstrap admin users                           │
│  │                 │     • Create default document types                   │
│  │                 │     • Setup initial companies                         │
│  └─────────────────┘                                                        │
│                                                                             │
│  Phase 2: Product Catalog                                                   │
│  ┌─────────────────┐                                                        │
│  │  Order Service  │ ──→ Setup product catalog                             │
│  │                 │     • Import existing products                        │
│  │                 │     • Initialize inventory levels                     │
│  │                 │     • Create product categories                       │
│  └─────────────────┘                                                        │
│                                                                             │
│  Phase 3: Shipping Configuration                                            │
│  ┌─────────────────┐                                                        │
│  │ Shipping Service│ ──→ Configure shipping parameters                     │
│  │                 │     • Setup countries and zones                       │
│  │                 │     • Configure carriers                              │
│  │                 │     • Import rate tables                              │
│  └─────────────────┘                                                        │
│                                                                             │
│  Data Seeding Order:                                                        │
│  1. Document Types                                                          │
│  2. Companies                                                               │
│  3. Users (with company relationships)                                      │
│  4. Countries and Shipping Zones                                            │
│  5. Shipping Carriers                                                       │
│  6. Product Categories                                                       │
│  7. Products (with company ownership)                                       │
│  8. Initial Inventory Levels                                                │
│  9. Sample Orders (for testing)                                             │
│  10. Sample Manifests (for testing)                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```