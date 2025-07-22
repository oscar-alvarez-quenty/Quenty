# Entity Relationship Models

## Overview

This document provides comprehensive entity relationship diagrams for the Quenty microservices platform, showing the data models and relationships within each of the 9 specialized services and across service boundaries.

## Complete System Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    QUENTY PLATFORM - COMPLETE ERD                                              │
│                                      9 Microservices Architecture                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                          │
│  │   AUTH SERVICE  │  │CUSTOMER SERVICE │  │ ORDER SERVICE   │  │ SHIPPING SERVICE│                          │
│  │   Port: 8009    │  │   Port: 8001    │  │   Port: 8002    │  │   Port: 8004    │                          │
│  │                 │  │                 │  │                 │  │                 │                          │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │                          │
│  │ │   Users     │ │  │ │   Users     │ │  │ │  Products   │ │  │ │ Manifests   │ │                          │
│  │ │             │◄┼──┼─┤             │ │  │ │             │ │  │ │             │ │                          │
│  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │                          │
│  │ │ user_id     │ │  │ │ unique_id   │ │  │ │ sku         │ │  │ │ unique_id   │ │                          │
│  │ │ email       │ │  │ │ username    │ │  │ │ name        │ │  │ │ status      │ │                          │
│  │ │ is_active   │ │  │ │ company_id  │◄─┼──┼─┤ company_id  │ │  │ │ company_id◄─┼─┐                        │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │ │                        │
│  │       │         │  │       │         │  │       │         │  │       │         │ │                        │
│  │ ┌─────▼───────┐ │  │ ┌─────▼───────┐ │  │ ┌─────▼───────┐ │  │ ┌─────▼───────┐ │ │                        │
│  │ │   Roles     │ │  │ │ Companies   │ │  │ │ Inventory   │ │  │ │ManifestItems│ │ │                        │
│  │ │             │ │  │ │             │ │  │ │   Items     │ │  │ │             │ │ │                        │
│  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │ │                        │
│  │ │ name        │ │  │ │ company_id  │ │  │ │ product_id  │◄─┼──┼─┤ product_id  │ │ │                        │
│  │ └─────────────┘ │  │ │ name        │ │  │ │ quantity    │ │  │ │ description │ │ │                        │
│  │       │         │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │ │                        │
│  │ ┌─────▼───────┐ │  │                 │  │                 │  │                 │ │                        │
│  │ │Permissions  │ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │ │                        │
│  │ │             │ │  │ │DocumentTypes│ │  │ │   Orders    │ │  │ │ShippingRates│ │ │                        │
│  │ │ id (PK)     │ │  │ │             │ │  │ │             │ │  │ │             │ │ │                        │
│  │ │ name        │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │ │                        │
│  │ │ resource    │ │  │ │ name        │ │  │ │ order_number│ │  │ │ manifest_id │ │ │                        │
│  │ │ action      │ │  │ │ code        │ │  │ │ customer_id │◄─┼──┼─┤ carrier_name│ │ │                        │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ │ company_id  │ │  │ │ total_cost  │ │ │                        │
│  └─────────────────┘  └─────────────────┘  │ └─────────────┘ │  │ └─────────────┘ │ │                        │
│                                             │       │         │  │                 │ │                        │
│                                             │ ┌─────▼───────┐ │  │ ┌─────────────┐ │ │                        │
│                                             │ │ OrderItems  │ │  │ │  Countries  │ │ │                        │
│                                             │ │             │ │  │ │             │ │ │                        │
│                                             │ │ id (PK)     │ │  │ │ id (PK)     │ │ │                        │
│                                             │ │ order_id    │ │  │ │ name        │ │ │                        │
│                                             │ │ product_id  │ │  │ │ iso_code    │ │ │                        │
│                                             │ │ quantity    │ │  │ │ zone        │ │ │                        │
│                                             │ └─────────────┘ │  │ └─────────────┘ │ │                        │
│                                             └─────────────────┘  └─────────────────┘ │                        │
│                                                                                       │                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │                        │
│  │ PICKUP SERVICE  │  │ANALYTICS SERVICE│  │REV. LOGISTICS   │  │FRANCHISE SERVICE│ │                        │
│  │   Port: 8005    │  │   Port: 8006    │  │   Port: 8007    │  │   Port: 8008    │ │                        │
│  │                 │  │                 │  │                 │  │                 │ │                        │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │ │                        │
│  │ │   Pickups   │ │  │ │  Metrics    │ │  │ │  Returns    │ │  │ │ Franchises  │ │ │                        │
│  │ │             │ │  │ │             │ │  │ │             │ │  │ │             │ │ │                        │
│  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │ │                        │
│  │ │ pickup_id   │ │  │ │ metric_id   │ │  │ │ return_id   │ │  │ │ franchise_id│ │ │                        │
│  │ │ customer_id │◄─┼──┼─┤ metric_type │ │  │ │ order_id    │◄─┼──┼─┤ franchisee  │ │ │                        │
│  │ │ pickup_type │ │  │ │ value       │ │  │ │ customer_id │ │  │ │ territory_cd│◄┼─┼────────────────┐       │
│  │ └─────────────┘ │  │ │ tags        │ │  │ │ status      │ │  │ └─────────────┘ │ │                │       │
│  │       │         │  │ └─────────────┘ │  │ └─────────────┘ │  │       │         │ │                │       │
│  │ ┌─────▼───────┐ │  │       │         │  │       │         │  │ ┌─────▼───────┐ │ │                │       │
│  │ │PickupRoutes │ │  │ ┌─────▼───────┐ │  │ ┌─────▼───────┐ │  │ │Territories  │ │ │◄───────────────┘       │
│  │ │             │ │  │ │Dashboards   │ │  │ │ReturnItems  │ │  │ │             │ │ │                        │
│  │ │ id (PK)     │ │  │ │             │ │  │ │             │ │  │ │ id (PK)     │ │ │                        │
│  │ │ route_id    │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │territory_cd │ │ │                        │
│  │ │ driver_id   │ │  │ │dashboard_id │ │  │ │return_id    │ │  │ │ name        │ │ │                        │
│  │ └─────────────┘ │  │ │ widgets     │ │  │ │ item_id     │ │  │ │ status      │ │ │                        │
│  │       │         │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │ │                        │
│  │ ┌─────▼───────┐ │  │       │         │  │       │         │  │       │         │ │                        │
│  │ │PickupPkgs   │ │  │ ┌─────▼───────┐ │  │ ┌─────▼───────┐ │  │ ┌─────▼───────┐ │ │                        │
│  │ │             │ │  │ │  Reports    │ │  │ │Inspections  │ │  │ │Performance  │ │ │                        │
│  │ │ id (PK)     │ │  │ │             │ │  │ │             │ │  │ │             │ │ │                        │
│  │ │ pickup_id   │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │  │ │ id (PK)     │ │ │                        │
│  │ │ tracking_no │ │  │ │ report_id   │ │  │ │inspection_id│ │  │ │performance_d│ │ │                        │
│  │ └─────────────┘ │  │ │ status      │ │  │ │ return_id   │ │  │ │ revenue     │ │ │                        │
│  └─────────────────┘  │ └─────────────┘ │  │ │ condition   │ │  │ │ score       │ │ │                        │
│                       └─────────────────┘  │ └─────────────┘ │  │ └─────────────┘ │ │                        │
│                                            └─────────────────┘  └─────────────────┘ │                        │
│                                                                                      │                        │
│  ┌─────────────────┐                                                                 │                        │
│  │MICROCREDIT SVC  │                                                                 │                        │
│  │   Port: 8005*   │                                                                 │                        │
│  │                 │                                                                 │                        │
│  │ ┌─────────────┐ │                                                                 │                        │
│  │ │CreditApps   │ │                                                                 │                        │
│  │ │             │ │                                                                 │                        │
│  │ │ id (PK)     │ │                                                                 │                        │
│  │ │app_id       │ │                                                                 │                        │
│  │ │customer_id  │◄┼─────────────────────────────────────────────────────────────────┘                        │
│  │ │status       │ │                                                                                          │
│  │ └─────────────┘ │                                                                                          │
│  │       │         │                                                                                          │
│  │ ┌─────▼───────┐ │                                                                                          │
│  │ │   Loans     │ │                                                                                          │
│  │ │             │ │                                                                                          │
│  │ │ id (PK)     │ │                                                                                          │
│  │ │ loan_id     │ │                                                                                          │
│  │ │ customer_id │ │                                                                                          │
│  │ │ amount      │ │                                                                                          │
│  │ └─────────────┘ │                                                                                          │
│  │       │         │                                                                                          │
│  │ ┌─────▼───────┐ │                                                                                          │
│  │ │CreditScores │ │                                                                                          │
│  │ │             │ │                                                                                          │
│  │ │ id (PK)     │ │                                                                                          │
│  │ │ score_id    │ │                                                                                          │
│  │ │ customer_id │ │                                                                                          │
│  │ │ score       │ │                                                                                          │
│  │ └─────────────┘ │                                                                                          │
│  └─────────────────┘                                                                                          │
│                                                                                                                │
│  Cross-Service Relationships (Logical References):                                                            │
│  - Auth.users.user_id ←→ Customer.users.unique_id (Authentication)                                           │
│  - Customer.users.unique_id → Orders.customer_id                                                             │
│  - Customer.companies.company_id → Products.company_id                                                       │
│  - Orders.order_number → Returns.original_order_id                                                           │
│  - Products.id → ManifestItems.product_id                                                                    │
│  - Customer.users.unique_id → Pickups.customer_id                                                            │
│  - Customer.users.unique_id → Returns.customer_id                                                            │
│  - Customer.users.unique_id → CreditApps.customer_id                                                         │
│  - All Services → Analytics.metrics (Performance Data)                                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Auth Service ERD

### Database Schema: auth_db

```
┌─────────────────────────────────────────────────┐
│                AUTH SERVICE ERD                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────┐         ┌─────────────────┐│
│  │     Users       │         │     Roles       ││
│  │                 │         │                 ││
│  │ id (PK)         │         │ id (PK)         ││
│  │ user_id (UK)    │         │ role_id (UK)    ││
│  │ username (UK)   │         │ name (UK)       ││
│  │ email (UK)      │         │ description     ││
│  │ password_hash   │         │ is_active       ││
│  │ first_name      │         │ is_system_role  ││
│  │ last_name       │         │ created_at      ││
│  │ phone           │         │ updated_at      ││
│  │ is_active       │         └─────────────────┘│
│  │ is_verified     │                  │          │
│  │ created_at      │                  │          │
│  │ updated_at      │                  │          │
│  │ last_login      │                  │          │
│  └─────────┬───────┘                  │          │
│            │                          │          │
│            │         ┌────────────────▼──────────┐│
│            │         │        UserRoles          ││
│            │         │                           ││
│            │         │ id (PK)                   ││
│            └─────────┤ user_id (FK)              ││
│                      │ role_id (FK)              ││
│                      │ assigned_at               ││
│                      │ assigned_by               ││
│                      └───────────┬───────────────┘│
│                                  │                │
│  ┌─────────────────┐             │                │
│  │  RefreshTokens  │             │                │
│  │                 │             │                │
│  │ id (PK)         │             │                │
│  │ user_id (FK)    │◄────────────┘                │
│  │ token_hash      │                              │
│  │ expires_at      │              ┌───────────────┐│
│  │ is_revoked      │              │ Permissions   ││
│  │ created_at      │              │               ││
│  └─────────────────┘              │ id (PK)       ││
│                                   │ permission_id ││
│                                   │ name (UK)     ││
│  ┌─────────────────┐              │ resource      ││
│  │ RolePermissions │              │ action        ││
│  │                 │              │ description   ││
│  │ id (PK)         │              │ is_active     ││
│  │ role_id (FK)    │              │ created_at    ││
│  │ permission_id◄──┼──────────────┤               ││
│  │ assigned_at     │              └───────────────┘│
│  └─────────────────┘                              │
│                                                   │
│  Relationships:                                   │
│  - Users (1) → UserRoles (M) ← Roles (1)          │
│  - Users (1) → RefreshTokens (M)                  │
│  - Roles (1) → RolePermissions (M) ← Permissions  │
│  - RBAC: Users inherit permissions through roles  │
│                                                   │
│  Indexes:                                         │
│  - users.user_id, username, email (unique)       │
│  - roles.role_id, name (unique)                   │
│  - permissions.permission_id, name (unique)       │
│  - user_roles(user_id, role_id) composite         │
└─────────────────────────────────────────────────┘
```

## Customer Service ERD

### Database Schema: customer_db

```
┌─────────────────────────────────────────────────┐
│               CUSTOMER SERVICE ERD              │
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
│  External References (Cross-Service):           │
│  - Users.unique_id → Auth Service users         │
│  - Companies.company_id → All business services │
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
│  │ company_id ─────┼────┼────┤ updated_at      │                       │
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
│                      │ customer_id ────┼──────► Customer Service      │
│                      │ company_id ─────┼──────► Customer Service      │
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
│  - Products.id → Shipping Service (ManifestItems.product_id)           │
│  - Orders.order_number → Reverse Logistics (Returns.original_order_id) │
│                                                                        │
│  Business Rules:                                                       │
│  - Products must belong to a company                                   │
│  - Orders must have valid customer and company                         │
│  - Inventory is decremented on order confirmation                      │
│  - Stock movements track all inventory changes                         │
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
│  │ shipping_zone   │    │    │ product_id ─────┼──────► Order Service       │
│  │ estimated_deliv │    │    │ created_at      │                            │
│  │ tracking_number │    │    └─────────────────┘                            │
│  │ company_id ─────┼────┼────────────────────────────► Customer Service     │
│  │ created_by ─────┼────┼────────────────────────────► Customer Service     │
│  │ created_at      │    │                                                   │
│  │ updated_at      │    │    ┌─────────────────┐                            │
│  └─────────┬───────┘    │    │ ShippingRates   │                            │
│            │            │    │                 │                            │
│            │            └────┤ id (PK)         │                            │
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
│  - Countries provide zone configuration                                     │
│  - Carriers provide shipping services                                       │
│                                                                             │
│  Cross-Service References:                                                  │
│  - Manifests.company_id → Customer Service (Companies.company_id)           │
│  - Manifests.created_by → Customer Service (Users.unique_id)                │
│  - ManifestItems.product_id → Order Service (Products.id)                  │
│                                                                             │
│  Business Rules:                                                            │
│  - Manifests aggregate multiple items for shipping                          │
│  - Shipping rates calculated based on weight, volume, and destination       │
│  - Country zones determine shipping availability and pricing                │
│  - Carriers provide real-time rate and tracking integration                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Pickup Service ERD

### Database Schema: pickup_db

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PICKUP SERVICE ERD                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐                            │
│  │   Pickups       │         │ PickupPackages  │                            │
│  │                 │         │                 │                            │
│  │ id (PK)         │◄────────┤ id (PK)         │                            │
│  │ pickup_id (UK)  │    │    │ pickup_id (FK)  │                            │
│  │ customer_id ────┼────┼────┤ package_ref     │                            │
│  │ pickup_type     │    │    │ description     │                            │
│  │ status          │    │    │ category        │                            │
│  │ pickup_date     │    │    │ weight_kg       │                            │
│  │ time_window_st  │    │    │ dimensions      │                            │
│  │ time_window_end │    │    │ is_fragile      │                            │
│  │ pickup_address  │    │    │ tracking_number │                            │
│  │ contact_name    │    │    │ order_id ───────┼──────► Order Service       │
│  │ contact_phone   │    │    │ created_at      │                            │
│  │ package_count   │    │    └─────────────────┘                            │
│  │ estimated_wt_kg │    │                                                   │
│  │ actual_weight   │    │    ┌─────────────────┐                            │
│  │ assigned_driver │    │    │ PickupAttempts  │                            │
│  │ pickup_cost     │    │    │                 │                            │
│  │ created_at      │    └────┤ id (PK)         │                            │
│  └─────────┬───────┘         │ pickup_id (FK)  │                            │
│            │                 │ attempt_number  │                            │
│            │                 │ attempted_at    │                            │
│            │                 │ driver_id       │                            │
│            │                 │ attempt_status  │                            │
│  ┌─────────▼───────┐         │ failure_reason  │                            │
│  │ PickupRoutes    │         │ reschedule_date │                            │
│  │                 │         │ driver_notes    │                            │
│  │ id (PK)         │         │ attempt_photos  │                            │
│  │ route_id (UK)   │         │ gps_coordinates │                            │
│  │ driver_id       │         │ created_at      │                            │
│  │ route_name      │         └─────────────────┘                            │
│  │ route_date      │                                                        │
│  │ status          │         ┌─────────────────┐                            │
│  │ vehicle_type    │         │ PickupCapacity  │                            │
│  │ total_distance  │         │                 │                            │
│  │ total_pickups   │         │ id (PK)         │                            │
│  │ completed_pckps │         │ postal_code     │                            │
│  │ optimized_wpts  │         │ pickup_date     │                            │
│  │ route_start_tm  │         │ time_slot_start │                            │
│  │ route_end_time  │         │ time_slot_end   │                            │
│  │ created_at      │         │ max_capacity    │                            │
│  └─────────────────┘         │ current_booking │                            │
│                              │ special_event   │                            │
│                              │ created_at      │                            │
│  ┌─────────────────┐         └─────────────────┘                            │
│  │   Drivers       │                                                        │
│  │                 │         ┌─────────────────┐                            │
│  │ id (PK)         │         │  PickupZones    │                            │
│  │ driver_id (UK)  │         │                 │                            │
│  │ user_id ────────┼─────────┤ id (PK)         │                            │
│  │ license_number  │         │ zone_id (UK)    │                            │
│  │ license_expiry  │         │ zone_name       │                            │
│  │ vehicle_type    │         │ postal_codes    │                            │
│  │ vehicle_plate   │         │ boundaries      │                            │
│  │ is_active       │         │ service_avail   │                            │
│  │ current_zone    │         │ pickup_fee      │                            │
│  │ total_pickups   │         │ express_fee     │                            │
│  │ success_rate    │         │ service_hours   │                            │
│  │ avg_rating      │         │ slot_duration   │                            │
│  │ created_at      │         │ created_at      │                            │
│  └─────────────────┘         └─────────────────┘                            │
│                                                                             │
│  Relationships:                                                             │
│  - Pickups (1) → PickupPackages (M)                                         │
│  - Pickups (1) → PickupAttempts (M)                                         │
│  - Pickups (M) → PickupRoutes (1)                                           │
│  - Drivers manage routes and perform pickups                                │
│  - Zones define service areas and capacity                                  │
│                                                                             │
│  Cross-Service References:                                                  │
│  - Pickups.customer_id → Customer Service (Users.unique_id)                 │
│  - PickupPackages.order_id → Order Service (Orders.order_number)           │
│  - Drivers.user_id → Auth Service (Users.user_id)                           │
│                                                                             │
│  Business Rules:                                                            │
│  - Pickups must be scheduled within service zone hours                      │
│  - Routes optimize multiple pickups for efficiency                          │
│  - Capacity management prevents overbooking                                 │
│  - Failed attempts trigger rescheduling workflow                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Analytics Service ERD

### Database Schema: analytics_db

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ANALYTICS SERVICE ERD                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐                            │
│  │    Metrics      │         │   Dashboards    │                            │
│  │                 │         │                 │                            │
│  │ id (PK)         │         │ id (PK)         │                            │
│  │ metric_id (UK)  │         │ dashboard_id(UK)│                            │
│  │ metric_type     │         │ name            │                            │
│  │ name            │         │ description     │                            │
│  │ description     │         │ dashboard_type  │                            │
│  │ value           │         │ widgets         │                            │
│  │ unit            │         │ layout          │                            │
│  │ tags (JSONB)    │         │ filters         │                            │
│  │ timestamp       │         │ refresh_interval│                            │
│  │ period          │         │ owner_id ───────┼──────► Auth Service        │
│  │ source_service  │         │ is_public       │                            │
│  │ source_entity   │         │ allowed_users   │                            │
│  │ entity_type     │         │ allowed_roles   │                            │
│  │ created_at      │         │ is_active       │                            │
│  └─────────────────┘         │ created_at      │                            │
│           │                  │ updated_at      │                            │
│           │                  └─────────────────┘                            │
│           │                                                                 │
│           │                  ┌─────────────────┐                            │
│           │                  │    Reports      │                            │
│           │                  │                 │                            │
│           │                  │ id (PK)         │                            │
│           │                  │ report_id (UK)  │                            │
│           │                  │ name            │                            │
│           │                  │ description     │                            │
│           │                  │ report_type     │                            │
│           │                  │ format          │                            │
│           │                  │ parameters      │                            │
│           │                  │ filters         │                            │
│           │                  │ date_range      │                            │
│           │                  │ status          │                            │
│           │                  │ progress_pct    │                            │
│           │                  │ file_url        │                            │
│           │                  │ file_size       │                            │
│           │                  │ is_scheduled    │                            │
│           │                  │ schedule_expr   │                            │
│           │                  │ next_run        │                            │
│           │                  │ requested_by ───┼──────► Auth Service        │
│           │                  │ created_at      │                            │
│           │                  │ completed_at    │                            │
│           │                  │ expires_at      │                            │
│           │                  └─────────────────┘                            │
│           │                                                                 │
│           │                  ┌─────────────────┐                            │
│           └──────────────────┤     Alerts      │                            │
│                              │                 │                            │
│                              │ id (PK)         │                            │
│                              │ alert_id (UK)   │                            │
│                              │ name            │                            │
│                              │ description     │                            │
│                              │ metric_type     │                            │
│                              │ condition_expr  │                            │
│                              │ threshold_value │                            │
│                              │ comparison_op   │                            │
│                              │ time_window     │                            │
│                              │ notification_ch │                            │
│                              │ recipients      │                            │
│                              │ is_active       │                            │
│                              │ last_triggered  │                            │
│                              │ trigger_count   │                            │
│                              │ created_by ─────┼──────► Auth Service        │
│                              │ created_at      │                            │
│                              │ updated_at      │                            │
│                              └─────────────────┘                            │
│                                                                             │
│  Data Flow:                                                                 │
│  - All services send metrics to Analytics Service                           │
│  - Metrics feed into dashboards, reports, and alerts                        │
│  - Dashboards provide real-time business intelligence                       │
│  - Reports generate scheduled/on-demand business reports                     │
│  - Alerts trigger notifications based on thresholds                         │
│                                                                             │
│  Time-Series Design:                                                        │
│  - Metrics table partitioned by created_at (monthly)                        │
│  - Tags stored as JSONB for flexible filtering                              │
│  - Composite indexes on (metric_type, timestamp)                            │
│  - GIN indexes on tags for complex queries                                  │
│                                                                             │
│  Cross-Service Integration:                                                 │
│  - Receives metrics from all 8 other services                              │
│  - User context from Auth Service for dashboards/reports                    │
│  - Provides business intelligence across entire platform                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Reverse Logistics Service ERD

### Database Schema: reverse_logistics_db

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REVERSE LOGISTICS SERVICE ERD                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐                            │
│  │    Returns      │         │  ReturnItems    │                            │
│  │                 │         │                 │                            │
│  │ id (PK)         │◄────────┤ id (PK)         │                            │
│  │ return_id (UK)  │    │    │ return_item_id  │                            │
│  │ original_order_id───┼────┤ return_id (FK)  │                            │
│  │ customer_id ────┼────┼────┤ item_id ────────┼──────► Order Service       │
│  │ return_type     │    │    │ item_name       │                            │
│  │ return_reason   │    │    │ sku             │                            │
│  │ status          │    │    │ quantity        │                            │
│  │ description     │    │    │ unit_price      │                            │
│  │ preferred_res   │    │    │ return_reason   │                            │
│  │ rma_number      │    │    │ reason_details  │                            │
│  │ order_value     │    │    │ condition_recv  │                            │
│  │ est_refund_amt  │    │    │ photos          │                            │
│  │ actual_refund   │    │    │ inspection_res  │                            │
│  │ shipping_cost   │    │    │ resale_value    │                            │
│  │ processing_fee  │    │    │ refund_eligible │                            │
│  │ pickup_address  │    │    │ refund_amount   │                            │
│  │ tracking_number │    │    │ exchange_item   │                            │
│  │ carrier         │    │    │ created_at      │                            │
│  │ pickup_dates    │    │    │ updated_at      │                            │
│  │ expires_at      │    │    └─────────────────┘                            │
│  │ approval_notes  │    │                                                   │
│  │ photos          │    │    ┌─────────────────┐                            │
│  │ created_by ─────┼────┼────┤InspectionReports│                            │
│  │ processed_by    │    │    │                 │                            │
│  │ created_at      │    └────┤ id (PK)         │                            │
│  │ updated_at      │         │ inspection_id   │                            │
│  └─────────────────┘         │ return_id (FK)  │                            │
│                              │ item_id         │                            │
│                              │ inspector_id ───┼──────► Auth Service        │
│  ┌─────────────────┐         │ inspector_name  │                            │
│  │ReturnStatusHist │         │ inspection_date │                            │
│  │                 │         │ overall_cond    │                            │
│  │ id (PK)         │         │ functional_stat │                            │
│  │ return_id (FK)  │         │ cosmetic_cond   │                            │
│  │ status          │         │ completeness    │                            │
│  │ status_date     │         │ defects_found   │                            │
│  │ changed_by      │         │ photos          │                            │
│  │ notes           │         │ notes           │                            │
│  │ created_at      │         │ original_value  │                            │
│  └─────────────────┘         │ market_value    │                            │
│                              │ resale_value    │                            │
│                              │ salvage_value   │                            │
│  ┌─────────────────┐         │ recommended_act │                            │
│  │DisposalRecords  │         │ disposition_rec │                            │
│  │                 │         │ repair_cost     │                            │
│  │ id (PK)         │         │ refurb_cost     │                            │
│  │ return_id (FK)  │         │ created_at      │                            │
│  │ item_id         │         │ updated_at      │                            │
│  │ disposition     │         └─────────────────┘                            │
│  │ disposal_method │                                                        │
│  │ recovery_value  │                                                        │
│  │ environmental   │         ┌─────────────────┐                            │
│  │ disposal_date   │         │ ReturnMetrics   │                            │
│  │ disposed_by     │         │                 │                            │
│  │ created_at      │         │ id (PK)         │                            │
│  └─────────────────┘         │ metric_date     │                            │
│                              │ total_returns   │                            │
│                              │ processed_ret   │                            │
│                              │ refund_rate     │                            │
│                              │ avg_proc_time   │                            │
│                              │ recovery_rate   │                            │
│                              │ customer_sat    │                            │
│                              │ created_at      │                            │
│                              └─────────────────┘                            │
│                                                                             │
│  Relationships:                                                             │
│  - Returns (1) → ReturnItems (M)                                            │
│  - Returns (1) → InspectionReports (M)                                      │
│  - Returns (1) → ReturnStatusHistory (M)                                    │
│  - Returns (1) → DisposalRecords (M)                                        │
│                                                                             │
│  Cross-Service References:                                                  │
│  - Returns.original_order_id → Order Service (Orders.order_number)          │
│  - Returns.customer_id → Customer Service (Users.unique_id)                 │
│  - ReturnItems.item_id → Order Service (Products.id)                       │
│  - InspectionReports.inspector_id → Auth Service (Users.user_id)            │
│                                                                             │
│  Business Rules:                                                            │
│  - Returns require valid original order                                     │
│  - Inspection determines refund eligibility and amount                      │
│  - Items can be refunded, exchanged, or disposed                           │
│  - Environmental tracking for sustainability compliance                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Franchise Service ERD

### Database Schema: franchise_db

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRANCHISE SERVICE ERD                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐                            │
│  │  Franchises     │         │  Territories    │                            │
│  │                 │         │                 │                            │
│  │ id (PK)         │         │ id (PK)         │                            │
│  │ franchise_id(UK)│         │ territory_code  │◄───────┐                   │
│  │ name            │         │ name            │        │                   │
│  │ franchisee_name │         │ description     │        │                   │
│  │ email           │         │ country         │        │                   │
│  │ phone           │         │ state           │        │                   │
│  │ address         │         │ region          │        │                   │
│  │ city            │         │ boundaries      │        │                   │
│  │ state           │         │ area_size       │        │                   │
│  │ country         │         │ population      │        │                   │
│  │ postal_code     │         │ market_potential│        │                   │
│  │ business_license│         │ competition_lev │        │                   │
│  │ tax_id          │         │ average_income  │        │                   │
│  │ territory_code──┼─────────┤ demographic_data│        │                   │
│  │ contract_dates  │         │ status          │        │                   │
│  │ contract_terms  │         │ reserved_until  │        │                   │
│  │ status          │         │ reserved_by     │        │                   │
│  │ opening_date    │         │ is_active       │        │                   │
│  │ operational_hrs │         │ created_at      │        │                   │
│  │ services_offered│         │ updated_at      │        │                   │
│  │ equipment_list  │         └─────────────────┘        │                   │
│  │ fees_structure  │                                    │                   │
│  │ is_active       │                                    │                   │
│  │ created_at      │                                    │                   │
│  │ updated_at      │                                    │                   │
│  └─────────┬───────┘                                    │                   │
│            │                                            │                   │
│            │         ┌─────────────────┐                │                   │
│            │         │FranchiseContract│                │                   │
│            │         │                 │                │                   │
│            │         │ id (PK)         │                │                   │
│            │         │ franchise_id(FK)│                │                   │
│            │         │ contract_type   │                │                   │
│            │         │ start_date      │                │                   │
│            │         │ end_date        │                │                   │
│            │         │ terms_conditions│                │                   │
│            │         │ renewal_terms   │                │                   │
│            │         │ fee_structure   │                │                   │
│            │         │ performance_req │                │                   │
│            │         │ signed_date     │                │                   │
│            │         │ status          │                │                   │
│            │         │ created_at      │                │                   │
│            │         └─────────────────┘                │                   │
│            │                                            │                   │
│            │         ┌─────────────────┐                │                   │
│            │         │FranchisePayments│                │                   │
│            │         │                 │                │                   │
│            │         │ id (PK)         │                │                   │
│            │         │ franchise_id(FK)│                │                   │
│            │         │ payment_type    │                │                   │
│            │         │ amount          │                │                   │
│            │         │ due_date        │                │                   │
│            │         │ paid_date       │                │                   │
│            │         │ payment_method  │                │                   │
│            │         │ transaction_id  │                │                   │
│            │         │ status          │                │                   │
│            │         │ created_at      │                │                   │
│            │         └─────────────────┘                │                   │
│            │                                            │                   │
│            │         ┌─────────────────┐                │                   │
│            └─────────┤FranchisePerform │                │                   │
│                      │                 │                │                   │
│                      │ id (PK)         │                │                   │
│                      │ performance_id  │                │                   │
│                      │ franchise_id(FK)│                │                   │
│                      │ period_type     │                │                   │
│                      │ period_start    │                │                   │
│                      │ period_end      │                │                   │
│                      │ revenue         │                │                   │
│                      │ costs           │                │                   │
│                      │ profit          │                │                   │
│                      │ royalties_paid  │                │                   │
│                      │ orders_count    │                │                   │
│                      │ customers_served│                │                   │
│                      │ avg_order_value │                │                   │
│                      │ cust_sat_score  │                │                   │
│                      │ performance_scr │                │                   │
│                      │ ranking         │                │                   │
│                      │ improvement_are │                │                   │
│                      │ calculated_at   │                │                   │
│                      │ created_at      │                │                   │
│                      └─────────────────┘                │                   │
│                                                         │                   │
│  ┌─────────────────┐                                    │                   │
│  │FranchiseAudit   │                                    │                   │
│  │                 │                                    │                   │
│  │ id (PK)         │                                    │                   │
│  │ franchise_id(FK)│───────────────────────────────────┘                   │
│  │ audit_type      │                                                        │
│  │ audit_date      │                                                        │
│  │ auditor_id ─────┼──────► Auth Service                                    │
│  │ findings        │                                                        │
│  │ compliance_score│                                                        │
│  │ action_items    │                                                        │
│  │ follow_up_date  │                                                        │
│  │ status          │                                                        │
│  │ created_at      │                                                        │
│  └─────────────────┘                                                        │
│                                                                             │
│  Relationships:                                                             │
│  - Franchises (1) → Territories (1)                                         │
│  - Franchises (1) → FranchiseContracts (M)                                  │
│  - Franchises (1) → FranchisePayments (M)                                   │
│  - Franchises (1) → FranchisePerformance (M)                                │
│  - Franchises (1) → FranchiseAudit (M)                                      │
│                                                                             │
│  Cross-Service References:                                                  │
│  - Territory assignment affects order routing                               │
│  - Performance metrics fed from Order and Analytics services                │
│  - Audit functions integrate with Auth service for auditor identity         │
│                                                                             │
│  Business Rules:                                                            │
│  - One franchise per territory (exclusive assignment)                       │
│  - Performance tracking drives fee structures and rankings                  │
│  - Contract lifecycle management with renewal processes                     │
│  - Territory availability managed through reservation system                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Microcredit Service ERD

### Database Schema: microcredit_db

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MICROCREDIT SERVICE ERD                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐                            │
│  │CreditApplications│        │     Loans       │                            │
│  │                 │         │                 │                            │
│  │ id (PK)         │◄────────┤ id (PK)         │                            │
│  │ application_id  │    │    │ loan_id (UK)    │                            │
│  │ customer_id ────┼────┼────┤ application_id  │                            │
│  │ customer_type   │    │    │ customer_id     │                            │
│  │ requested_amt   │    │    │ principal_amt   │                            │
│  │ requested_term  │    │    │ interest_rate   │                            │
│  │ purpose         │    │    │ term_months     │                            │
│  │ monthly_income  │    │    │ monthly_payment │                            │
│  │ employment_stat │    │    │ status          │                            │
│  │ employment_dur  │    │    │ disbursement_dt │                            │
│  │ existing_debts  │    │    │ maturity_date   │                            │
│  │ credit_score    │    │    │ total_amt_due   │                            │
│  │ risk_category   │    │    │ amount_paid     │                            │
│  │ approved_amount │    │    │ outstanding_bal │                            │
│  │ approved_term   │    │    │ next_payment_dt │                            │
│  │ interest_rate   │    │    │ payments_made   │                            │
│  │ status          │    │    │ days_past_due   │                            │
│  │ decision_reason │    │    │ collection_stat │                            │
│  │ processed_by    │    │    │ restructured    │                            │
│  │ decision_date   │    │    │ created_at      │                            │
│  │ documents_sub   │    │    │ updated_at      │                            │
│  │ verification    │    │    │ closed_at       │                            │
│  │ created_at      │    │    └─────────────────┘                            │
│  │ expires_at      │    │              │                                    │
│  └─────────────────┘    │              │                                    │
│            │            │              │                                    │
│            │            │              │                                    │
│  ┌─────────▼───────┐    │    ┌─────────▼───────┐                            │
│  │  CreditChecks   │    │    │  LoanPayments   │                            │
│  │                 │    │    │                 │                            │
│  │ id (PK)         │    │    │ id (PK)         │                            │
│  │ application_id  │    │    │ payment_id (UK) │                            │
│  │ check_type      │    │    │ loan_id (FK)    │                            │
│  │ check_date      │    │    │ payment_amount  │                            │
│  │ bureau_name     │    │    │ principal_amt   │                            │
│  │ credit_score    │    │    │ interest_amount │                            │
│  │ payment_history │    │    │ late_fee_amount │                            │
│  │ debt_to_income  │    │    │ payment_date    │                            │
│  │ employment_ver  │    │    │ payment_method  │                            │
│  │ income_ver      │    │    │ payment_ref     │                            │
│  │ risk_factors    │    │    │ payment_status  │                            │
│  │ recommendations │    │    │ remaining_bal   │                            │
│  │ created_at      │    │    │ created_at      │                            │
│  └─────────────────┘    │    └─────────────────┘                            │
│                         │                                                   │
│                         │    ┌─────────────────┐                            │
│                         │    │ PaymentSchedule │                            │
│                         │    │                 │                            │
│                         │    │ id (PK)         │                            │
│                         │    │ loan_id (FK)    │                            │
│                         │    │ payment_number  │                            │
│                         │    │ due_date        │                            │
│                         │    │ payment_amount  │                            │
│                         │    │ principal_amt   │                            │
│                         │    │ interest_amount │                            │
│                         │    │ remaining_bal   │                            │
│                         │    │ status          │                            │
│                         │    │ paid_date       │                            │
│                         │    │ created_at      │                            │
│                         │    └─────────────────┘                            │
│                         │                                                   │
│  ┌─────────────────┐    │                                                   │
│  │  CreditScores   │    │                                                   │
│  │                 │    │                                                   │
│  │ id (PK)         │    │                                                   │
│  │ score_id (UK)   │    │                                                   │
│  │ customer_id ────┼────┘                                                   │
│  │ score           │                                                        │
│  │ score_date      │                                                        │
│  │ score_version   │                                                        │
│  │ payment_hist_sc │         ┌─────────────────┐                            │
│  │ credit_util_sc  │         │  CollectionLog  │                            │
│  │ length_hist_sc  │         │                 │                            │
│  │ credit_mix_sc   │         │ id (PK)         │                            │
│  │ new_credit_sc   │         │ loan_id (FK)    │                            │
│  │ risk_category   │         │ collection_date │                            │
│  │ default_prob    │         │ collection_type │                            │
│  │ recommended_lmt │         │ contact_method  │                            │
│  │ positive_facts  │         │ outcome         │                            │
│  │ negative_facts  │         │ next_action     │                            │
│  │ improvement_sug │         │ notes           │                            │
│  │ previous_score  │         │ agent_id ───────┼──────► Auth Service        │
│  │ score_change    │         │ created_at      │                            │
│  │ calculated_by   │         └─────────────────┘                            │
│  │ created_at      │                                                        │
│  └─────────────────┘                                                        │
│                                                                             │
│  Relationships:                                                             │
│  - CreditApplications (1) → Loans (1)                                       │
│  - CreditApplications (1) → CreditChecks (M)                                │
│  - Loans (1) → LoanPayments (M)                                             │
│  - Loans (1) → PaymentSchedule (M)                                          │
│  - Loans (1) → CollectionLog (M)                                            │
│  - Customers (1) → CreditScores (M)                                         │
│                                                                             │
│  Cross-Service References:                                                  │
│  - CreditApplications.customer_id → Customer Service (Users.unique_id)      │
│  - CollectionLog.agent_id → Auth Service (Users.user_id)                    │
│  - Credit decisions influence customer creditworthiness                     │
│                                                                             │
│  Business Rules:                                                            │
│  - Credit applications require thorough underwriting                        │
│  - Loan disbursement only after approval and agreement signing              │
│  - Payment schedules auto-generated based on loan terms                     │
│  - Credit scores updated with payment history and external data             │
│  - Collection activities logged for regulatory compliance                   │
│                                                                             │
│  Financial Calculations:                                                    │
│  - Interest calculations based on reducing balance method                   │
│  - Late fees applied based on days past due                                │
│  - Credit scoring algorithm considers multiple factors                      │
│  - Risk-based pricing for interest rates                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Cross-Service Data Flow and Integration Patterns

### Service Communication Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CROSS-SERVICE DATA RELATIONSHIPS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Data Flow Patterns:                                                        │
│                                                                             │
│  1. Authentication Flow (Auth → All Services):                             │
│     Auth.users.user_id ←→ All Services (JWT token validation)              │
│                                                                             │
│  2. Customer/Company References:                                            │
│     Customer.users.unique_id → Orders, Pickups, Returns, Microcredit       │
│     Customer.companies.company_id → Orders, Shipping, Franchises           │
│                                                                             │
│  3. Order-Related Flow:                                                     │
│     Orders.order_number → Returns.original_order_id                        │
│     Orders.products.id → Shipping.manifest_items.product_id                │
│     Orders.order_number → Pickups.packages.order_id                        │
│                                                                             │
│  4. Analytics Integration (All → Analytics):                               │
│     All Services → Analytics.metrics (Performance data)                    │
│     All Services → Analytics.alerts (Threshold monitoring)                 │
│                                                                             │
│  5. Franchise Operations:                                                   │
│     Franchises.territory_code → Order routing logic                        │
│     Franchises.performance ← Order/Analytics data                          │
│                                                                             │
│  Event-Driven Consistency Patterns:                                        │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │ Customer Events │    │  Order Events   │    │Analytics Events │          │
│  │                 │    │                 │    │                 │          │
│  │ • user.created  │───→│ • validate_user │───→│ • user_metrics  │          │
│  │ • user.updated  │───→│ • update_cache  │───→│ • update_dashbd │          │
│  │ • company.deact │───→│ • block_orders  │───→│ • alert_trigger │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
│                                  │                                         │
│  ┌─────────────────┐             │              ┌─────────────────┐          │
│  │Shipping Events  │             │              │ Pickup Events   │          │
│  │                 │             │              │                 │          │
│  │ • manifest.sub  │◄────────────┤              │ • pickup.done   │          │
│  │ • shipment.del  │             └─────────────→│ • update_order  │          │
│  └─────────────────┘                            └─────────────────┘          │
│                                                                             │
│  Data Consistency Strategies:                                              │
│                                                                             │
│  1. Eventually Consistent:                                                  │
│     - User profile updates across services                                 │
│     - Company information synchronization                                  │
│     - Product catalog updates                                              │
│     - Performance metrics aggregation                                      │
│                                                                             │
│  2. Strong Consistency:                                                     │
│     - Financial transactions (payments, refunds)                           │
│     - Inventory deductions                                                 │
│     - Credit decisions and loan disbursement                               │
│     - Order state transitions                                              │
│                                                                             │
│  3. Saga Pattern:                                                          │
│     - Order creation with inventory reservation                            │
│     - Return processing with refund coordination                           │
│     - Loan approval with credit limit updates                              │
│     - Franchise assignment with territory reservation                      │
│                                                                             │
│  Database Design Principles:                                               │
│                                                                             │
│  • Database-per-Service: Each service owns its data                        │
│  • Logical References: Cross-service FKs managed by application            │
│  • Event Sourcing: Critical events stored for audit trails                │
│  • CQRS: Read/write separation for complex aggregations                    │
│  • Time-series Partitioning: For metrics and historical data              │
│  • JSONB Usage: For flexible, schema-less attributes                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Performance Optimization and Indexing Strategy

### Database Performance Patterns

```sql
-- Cross-service query optimization patterns

-- 1. Customer Service - Company user lookups
CREATE INDEX CONCURRENTLY idx_users_company_active ON users(company_id, active) WHERE active = true;

-- 2. Order Service - Customer order history
CREATE INDEX CONCURRENTLY idx_orders_customer_date ON orders(customer_id, created_at DESC);

-- 3. Analytics Service - Time-series metrics
CREATE INDEX CONCURRENTLY idx_metrics_type_timestamp ON metrics(metric_type, timestamp DESC);
CREATE INDEX CONCURRENTLY idx_metrics_service_timestamp ON metrics(source_service, timestamp DESC);

-- 4. Pickup Service - Driver route optimization  
CREATE INDEX CONCURRENTLY idx_pickups_date_zone ON pickups(pickup_date, postal_code);

-- 5. Reverse Logistics - Return processing pipeline
CREATE INDEX CONCURRENTLY idx_returns_status_date ON returns(status, created_at DESC);

-- 6. Franchise Service - Territory performance
CREATE INDEX CONCURRENTLY idx_performance_territory_period ON franchise_performance(franchise_id, period_start, period_end);

-- 7. Microcredit Service - Customer credit pipeline
CREATE INDEX CONCURRENTLY idx_loans_customer_status ON loans(customer_id, status);
CREATE INDEX CONCURRENTLY idx_credit_scores_customer_date ON credit_scores(customer_id, score_date DESC);

-- 8. Auth Service - Permission lookups
CREATE INDEX CONCURRENTLY idx_user_roles_permissions ON user_roles(user_id) INCLUDE (role_id);
```

This comprehensive Entity Relationship Models documentation covers all 9 microservices in the Quenty platform, showing detailed data models, relationships, cross-service integrations, and performance optimization strategies for the complete system architecture.