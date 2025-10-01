# 📋 ANÁLISIS COMPLETO DEL SISTEMA QUENTY

**Fecha de Análisis:** 2025-10-01
**Versión del Sistema:** v0.1 (release/v0.1)
**Analista:** Claude Code

---

## 📑 ÍNDICE

1. [Inicialización de Carriers](#1-inicialización-de-carriers)
2. [Estado del README](#2-estado-del-readme)
3. [Persistencia de Datos](#3-persistencia-de-datos)
4. [Flujo de Envío End-to-End](#4-flujo-de-envío-end-to-end)
5. [Versionado de Entornos](#5-versionado-de-entornos)
6. [Gestión de Variables de Entorno](#6-gestión-de-variables-de-entorno)
7. [Limpieza de Código](#7-limpieza-de-código)
8. [Diagramas de Base de Datos](#8-diagramas-de-base-de-datos)
9. [Recomendaciones Críticas](#9-recomendaciones-críticas)

---

## 1. INICIALIZACIÓN DE CARRIERS

### ❌ ESTADO ACTUAL: NO IMPLEMENTADO

**Hallazgo Principal:** Aunque el sistema tiene configuración completa de carriers en `.env.carriers`, **NO EXISTE INTEGRACIÓN REAL con las APIs de los transportistas**.

### 1.1 Carriers Configurados

#### ✅ Carriers con Credenciales Parciales:
- **DHL Express** - Sandbox configurado
  - Usuario: `quentysasCO`
  - Cuenta: `683146118`
  - Ambiente: `sandbox`

#### ⚠️ Carriers con Variables Definidas (sin credenciales reales):
- **FedEx International**
- **UPS Worldwide**
- **Servientrega** (Colombia)
- **InterRapidisimo** (Colombia)
- **Pasarex** (Casillero internacional)
- **Aeropost** (Casillero internacional)

### 1.2 Arquitectura Actual vs. Esperada

**LO QUE EXISTE:**
```
Usuario → API → Genera PDF con template → Retorna etiqueta mockeada
```

**LO QUE DEBERÍA EXISTIR:**
```
Usuario → API → CarrierFactory → DHLClient.create_shipment()
                                → API Real de DHL
                                → Tracking real + Etiqueta oficial
```

### 1.3 Archivos Relevantes

**Configuración:**
- `/home/jhunter/devel/QUENTY/Quenty/.env.carriers` (76 líneas de configuración)

**Templates de Etiquetas (NO son integraciones reales):**
- `microservices/international-shipping/src/utils/Operators/dhl.py`
- `microservices/international-shipping/src/utils/Operators/fedex.py`
- `microservices/international-shipping/src/utils/Operators/servientrega.py`
- `microservices/international-shipping/src/utils/Operators/pasarex.py`
- `microservices/international-shipping/src/utils/Operators/deprisa.py`

**Servicios Mock:**
- `microservices/international-shipping/src/utils/guia_provider.py` (retorna datos simulados)
- `microservices/international-shipping/src/utils/pdf_generator.py` (genera PDFs de templates)

### 1.4 ¿Dónde se "Inicializan"?

**Respuesta corta:** NO se inicializan.

El sistema actualmente:
1. ✅ Lee datos del request del usuario
2. ✅ Selecciona un template HTML según el carrier
3. ✅ Genera un PDF con datos mockeados
4. ❌ **NO se conecta a ninguna API real**
5. ❌ **NO usa las credenciales de `.env.carriers`**
6. ❌ **NO genera tracking numbers reales**

### 1.5 Qué Falta Implementar

#### 🔴 CRÍTICO - Core Missing:
1. **Clases de Cliente para cada Carrier**
   ```python
   class DHLClient:
       def __init__(self, username, password, account):
           self.auth_token = self.authenticate()

       def create_shipment(self, shipment_data):
           # Llamada real a DHL API
           pass

       def track_shipment(self, tracking_number):
           # Tracking real
           pass
   ```

2. **Factory Pattern**
   ```python
   class CarrierFactory:
       @staticmethod
       def get_carrier(carrier_code: str) -> BaseCarrier:
           if carrier_code == "DHL":
               return DHLClient(
                   os.getenv("DHL_USERNAME"),
                   os.getenv("DHL_PASSWORD"),
                   os.getenv("DHL_ACCOUNT_NUMBER")
               )
           # ...
   ```

3. **Capa de Integración**
   - Crear `/src/services/carrier_integration/`
   - Implementar `base_carrier.py` (interfaz)
   - Implementar integraciones específicas por carrier

#### 🟡 IMPORTANTE - Business Logic:
4. **Rate Shopping** - Comparar tarifas en tiempo real
5. **Shipment Creation** - Crear envíos reales con tracking
6. **Webhook Integration** - Recibir actualizaciones de estado
7. **Credential Management** - Cargar y encriptar credenciales

#### 🟢 MEJORAS - Optimization:
8. **Caching** - Redis para cotizaciones (TTL: 15min)
9. **Retry Logic** - Reintentos con backoff exponencial
10. **Monitoring** - Métricas por carrier (latencia, tasa de éxito)

### 1.6 Esfuerzo Estimado

- **Fase 1 - Foundation:** 1-2 semanas
- **Fase 2 - DHL Integration:** 2-3 semanas
- **Fase 3 - Otros Carriers:** 4-6 semanas
- **Fase 4 - Features Avanzadas:** 2-3 semanas

**TOTAL:** 9-14 semanas para integración completa

---

## 2. ESTADO DEL README

### ✅ README PRINCIPAL - BIEN DOCUMENTADO

**Ubicación:** `/home/jhunter/devel/QUENTY/Quenty/README.md`

**Estado:** ✅ **ACTUALIZADO Y COMPLETO** (501 líneas)

**Contenido:**
- ✅ Arquitectura DDD bien explicada
- ✅ 10 Bounded Contexts documentados
- ✅ Estructura del proyecto clara
- ✅ Funcionalidades implementadas listadas
- ✅ Suite de pruebas descrita
- ✅ Documentación comprensiva
- ✅ Guías de instalación y ejecución
- ✅ API Endpoints documentados

**Bounded Contexts Documentados:**
1. ✅ Gestión de Clientes
2. ✅ Gestión de Órdenes
3. ✅ Gestión de Recolecciones
4. ✅ Envíos Internacionales
5. ✅ Sistema de Microcréditos
6. ✅ Analytics y Reportes
7. ✅ Logística Inversa
8. ✅ Red Logística (Franquicias)
9. ✅ Gestión Financiera
10. ✅ Sistema de Tokenización

### ⚠️ README DE MICROSERVICIOS - DESACTUALIZADO

**Ubicación:** `/home/jhunter/devel/QUENTY/Quenty/microservices/README.md`

**Estado:** ⚠️ **PARCIALMENTE DESACTUALIZADO**

#### Lo que está BIEN:
- ✅ Arquitectura de autenticación documentada
- ✅ Roles y permisos RBAC bien explicados
- ✅ Security best practices listadas
- ✅ Guías de deployment

#### Lo que está DESACTUALIZADO:

1. **Puertos Incorrectos:**
   - Dice: Auth Service (Port 8003)
   - Real: Auth Service (Port 8009) según docker-compose.microservices.yml

2. **Servicios Marcados como "Legacy" que están Activos:**
   - Pickup Service - ✅ Tiene autenticación implementada
   - Microcredit Service - ✅ Tiene autenticación implementada
   - Analytics Service - ✅ Tiene autenticación implementada
   - Reverse Logistics - ✅ Tiene autenticación implementada
   - Franchise Service - ✅ Tiene autenticación implementada

3. **Servicios Faltantes:**
   - ❌ API Gateway no documentado en detalle
   - ❌ Integraciones (MercadoLibre, Shopify, WooCommerce) no mencionadas
   - ❌ RAG Service no documentado

### 📊 Servicios Reales vs. Documentados

| Servicio | Puerto Real | Puerto Docs | Estado |
|----------|-------------|-------------|---------|
| API Gateway | 8000 | 8000 | ✅ |
| Customer | 8001 | 8001 | ✅ |
| Order | 8002 | 8002 | ✅ |
| Pickup | 8003 | 8005 | ❌ |
| International Shipping | 8004 | 8004 | ✅ |
| Microcredit | 8005 | 8006 | ❌ |
| Analytics | 8006 | 8007 | ❌ |
| Reverse Logistics | 8007 | 8008 | ❌ |
| Franchise | 8008 | 8009 | ❌ |
| Auth Service | 8009 | 8003 | ❌ |

### 🔧 Acción Requerida:

**ACTUALIZAR** `/microservices/README.md` con:
1. Puertos correctos de todos los servicios
2. Remover etiqueta "Legacy" de servicios activos
3. Documentar servicios de integración (ML, Shopify, WooCommerce)
4. Agregar RAG Service
5. Actualizar mapa de arquitectura

---

## 3. PERSISTENCIA DE DATOS

### 🗄️ Arquitectura de Base de Datos

**Patrón:** Database per Service (una BD por microservicio)

**Stack:** PostgreSQL 15 + SQLAlchemy async + asyncpg

### 3.1 Mapa Completo de Bases de Datos

| Servicio | Base de Datos | Usuario | Puerto | Propósito |
|----------|---------------|---------|--------|-----------|
| **auth-service** | auth_db | auth / auth_pass | 5441 | Usuarios, autenticación, empresas, roles |
| **customer** | customer_db | customer / customer_pass | 5433 | Perfiles de clientes, soporte |
| **order** | order_db | order / order_pass | 5434 | Órdenes, productos, inventario |
| **pickup** | pickup_db | pickup / pickup_pass | 5435 | Recolecciones, rutas, conductores |
| **international-shipping** | intl_shipping_db | intlship / intlship_pass | 5436 | Manifiestos, cotizaciones, carriers |
| **microcredit** | microcredit_db | credit / credit_pass | 5437 | Créditos, scoring, pagos |
| **analytics** | analytics_db | analytics / analytics_pass | 5438 | Métricas, dashboards, reportes |
| **reverse-logistics** | reverse_logistics_db | reverse / reverse_pass | 5439 | Devoluciones, inspecciones |
| **franchise** | franchise_db | franchise / franchise_pass | 5440 | Franquicias, territorios, pagos |

### 3.2 ¿Dónde se Almacenan las Cotizaciones?

**Servicio:** international-shipping
**Base de Datos:** `intl_shipping_db`

**Tablas:**
```sql
-- Tarifas base por operador
rates (
    id, operator_id, service_id, zone_id,
    weight_min, weight_max, fixed_fee, percentage,
    created_at, updated_at
)

-- Catálogos de tarifas
catalogs (
    id, catalog_id, name, description,
    is_active, created_at
)

-- Relación catálogo-tarifas
catalog_rates (
    id, catalog_id, rate_id,
    custom_fixed_fee, custom_percentage
)

-- Tarifas personalizadas por cliente
client_ratebooks (
    id, ratebook_id, client_id, warehouse_id,
    catalog_id, is_active
)
```

**Flujo de Cotización:**
1. Cliente solicita cotización
2. Sistema busca en `client_ratebooks` si hay tarifa personalizada
3. Si no existe, usa `catalogs` + `catalog_rates` → `rates`
4. Calcula precio según peso y zona
5. Retorna cotización (actualmente mockeado)

### 3.3 ¿Dónde se Almacenan los Envíos?

**Distribuido entre 2 servicios:**

#### A) **Envíos Internacionales:**
**Servicio:** international-shipping
**Tablas:**
```sql
-- Manifiestos de envío internacional
manifests (
    id, unique_id, tracking_number, status,
    origin_country, destination_country,
    total_weight, total_volume, total_value,
    shipping_zone, carrier_id,
    estimated_delivery, created_at, shipped_at
)

-- Items del envío
manifest_items (
    id, manifest_id, product_id,
    description, quantity, weight, value,
    hs_code, country_of_origin
)

-- Documentos aduaneros
documents (
    id, document_id, manifest_id,
    document_type_id, file_url, uploaded_at
)
```

#### B) **Recolección de Paquetes:**
**Servicio:** pickup
**Tablas:**
```sql
-- Solicitudes de recolección
pickups (
    id, pickup_id, customer_id, order_id,
    pickup_type, status, address,
    scheduled_date, completed_at
)

-- Paquetes individuales
pickup_packages (
    id, package_id, pickup_id,
    tracking_number, weight, dimensions,
    order_id, notes
)

-- Rutas de recolección
pickup_routes (
    id, route_id, driver_id, date,
    status, total_stops, total_distance
)
```

### 3.4 ¿Dónde se Almacenan Órdenes y Otros Datos?

#### **Órdenes de Clientes:**
**Servicio:** order
**Tablas:** `orders`, `order_items`, `products`, `inventory_items`, `stock_movements`

#### **Créditos:**
**Servicio:** microcredit
**Tablas:** `credit_applications`, `credit_accounts`, `credit_payments`, `credit_scores`

#### **Devoluciones:**
**Servicio:** reverse-logistics
**Tablas:** `returns`, `return_items`, `inspection_reports`, `disposal_records`

#### **Franquicias:**
**Servicio:** franchise
**Tablas:** `franchises`, `franchise_contracts`, `territories`, `franchise_payments`

#### **Soporte al Cliente:**
**Servicio:** customer
**Tablas:** `customer_profiles`, `support_tickets`, `ticket_messages`

#### **Métricas y Analytics:**
**Servicio:** analytics
**Tablas:** `metrics`, `dashboards`, `reports`, `alerts`

### 3.5 Relaciones Entre Servicios

**No hay Foreign Keys físicas entre servicios**, pero existen referencias lógicas:

```
auth-service (user_id, company_id)
    ↓ referenciado por ↓
├── customer (customer_id = user_id)
├── order (customer_id, company_id)
├── pickup (customer_id)
├── microcredit (customer_id)
└── reverse-logistics (customer_id)

order (order_id, product_id)
    ↓ referenciado por ↓
├── pickup (order_id en pickup_packages)
├── international-shipping (product_id en manifest_items)
└── reverse-logistics (original_order_id en returns)
```

**Integridad Referencial:** Manejada a nivel de aplicación, no de BD

---

## 4. FLUJO DE ENVÍO END-TO-END

### 🚀 Flujo Completo: Desde Login hasta Recolección

#### **FASE 1: AUTENTICACIÓN** 🔐

```
1. Usuario → POST /api/v1/auth/login
   ├─ Servicio: auth-service (Puerto 8009)
   ├─ Request: { username, password }
   ├─ Proceso:
   │   ├─ Valida credenciales en auth_db.users
   │   ├─ Genera JWT access_token (exp: 30min)
   │   ├─ Genera refresh_token (exp: 7 días)
   │   ├─ Crea sesión en auth_db.user_sessions
   │   └─ Registra en auth_db.audit_logs
   └─ Response: {
       access_token,
       refresh_token,
       user: { id, username, roles, permissions }
     }

2. Cliente almacena tokens
   └─ Todas las requests subsecuentes incluyen:
      Header: "Authorization: Bearer {access_token}"
```

#### **FASE 2: CREACIÓN DE ORDEN** 📦

```
3. Usuario → POST /api/v1/orders
   ├─ Via: API Gateway (8000) → Order Service (8002)
   ├─ Auth Middleware:
   │   └─ Verifica token con auth-service
   ├─ Request: {
   │   customer_id,
   │   items: [
   │     { product_id, quantity, weight, dimensions, value }
   │   ],
   │   delivery_address: { ... },
   │   delivery_method: "home_delivery"
   │ }
   ├─ Proceso en order-service:
   │   ├─ Valida permisos: "orders:create"
   │   ├─ Verifica inventario en order_db.inventory_items
   │   ├─ Calcula totales (peso, volumen, valor)
   │   ├─ Crea orden en order_db.orders
   │   ├─ Crea items en order_db.order_items
   │   ├─ Genera order_number único
   │   └─ Actualiza inventario (stock reservado)
   └─ Response: {
       order_id: "ORD-20250101123456",
       tracking_number: "QTYORD-20250101123456",
       status: "pending",
       total_amount: 15252.50
     }
```

#### **FASE 3: COTIZACIÓN DE ENVÍO** 💰

```
4. Sistema (automático) o Usuario → POST /api/v1/shipping/quote
   ├─ Via: API Gateway → International Shipping (8004)
   ├─ Request: {
   │   origin_country: "MX",
   │   destination_country: "US",
   │   weight_kg: 3.5,
   │   dimensions: { length, width, height },
   │   value: 15000.00,
   │   service_type: "express"
   │ }
   ├─ Proceso en international-shipping:
   │   ├─ Determina shipping_zone según países
   │   ├─ Busca tarifas en:
   │   │   ├─ client_ratebooks (tarifa personalizada)
   │   │   ├─ catalog_rates (catálogo activo)
   │   │   └─ rates (tarifas base)
   │   ├─ Calcula por carrier disponible:
   │   │   ├─ DHL: fixed_fee + (percentage * value)
   │   │   ├─ FedEx: ...
   │   │   └─ UPS: ...
   │   └─ [FUTURO] Consulta APIs reales de carriers
   └─ Response: {
       quotes: [
         {
           carrier: "DHL Express",
           service: "Express Worldwide",
           price: 102.50,
           estimated_days: 2,
           tracking_available: true
         },
         { carrier: "FedEx", ... },
         { carrier: "UPS", ... }
       ],
       recommended: "DHL Express"
     }
```

#### **FASE 4: CONFIRMACIÓN Y MANIFIESTO** 📋

```
5. Usuario → POST /api/v1/manifests
   ├─ Via: API Gateway → International Shipping (8004)
   ├─ Request: {
   │   order_id: "ORD-20250101123456",
   │   selected_carrier: "DHL",
   │   selected_service: "Express Worldwide",
   │   origin_country: "MX",
   │   destination_country: "US",
   │   items: [ ... ],
   │   customs_info: { hs_codes, values, ... }
   │ }
   ├─ Proceso:
   │   ├─ Valida permisos: "shipping:create"
   │   ├─ Crea manifest en intl_shipping_db.manifests
   │   ├─ Crea items en manifest_items
   │   ├─ Genera unique_id: "MAN-20250101123456"
   │   ├─ Calcula aranceles (si aplica)
   │   ├─ [FUTURO] Crea shipment real con API de carrier
   │   └─ Actualiza estado orden en order-service
   └─ Response: {
       manifest_id: 16,
       unique_id: "MAN-20250101123456",
       tracking_number: "DHL123456789",
       status: "draft",
       estimated_delivery: "2025-01-03T18:00:00Z"
     }
```

#### **FASE 5: SOLICITUD DE RECOLECCIÓN** 🚚

```
6. Usuario → POST /api/v1/pickups
   ├─ Via: API Gateway → Pickup Service (8003)
   ├─ Request: {
   │   order_id: "ORD-20250101123456",
   │   manifest_id: 16,
   │   pickup_type: "scheduled",
   │   pickup_address: { ... },
   │   preferred_date: "2025-01-02",
   │   preferred_time_slot: "09:00-12:00",
   │   contact_person: "Juan Pérez",
   │   contact_phone: "+52123456789",
   │   packages: [
   │     { weight: 3.5, dimensions: {...}, tracking: "DHL123456789" }
   │   ]
   │ }
   ├─ Proceso en pickup-service:
   │   ├─ Valida permisos: "pickups:create"
   │   ├─ Verifica capacidad en pickup_zones
   │   ├─ Crea pickup en pickup_db.pickups
   │   ├─ Crea packages en pickup_packages
   │   ├─ Genera pickup_id: "PCK-20250101123456"
   │   ├─ Asigna a route si existe
   │   └─ Envía notificación al cliente (email/SMS)
   └─ Response: {
       pickup_id: "PCK-20250101123456",
       status: "scheduled",
       scheduled_date: "2025-01-02",
       time_slot: "09:00-12:00",
       confirmation_code: "ABC123"
     }
```

#### **FASE 6: OPTIMIZACIÓN DE RUTAS** 🗺️

```
7. Sistema (automático - cron job) → Optimizador de Rutas
   ├─ Servicio: pickup-service (proceso interno)
   ├─ Trigger: Diariamente a las 18:00 para el día siguiente
   ├─ Proceso:
   │   ├─ Obtiene todos pickups con status="scheduled" para mañana
   │   ├─ Agrupa por zona geográfica (postal_code)
   │   ├─ Calcula rutas óptimas (algoritmo TSP)
   │   ├─ Asigna conductores disponibles de pickup_db.drivers
   │   ├─ Crea pickup_routes con waypoints
   │   ├─ Actualiza pickups con route_id y sequence
   │   └─ Notifica a conductores (app móvil)
   └─ Resultado: {
       routes_created: 5,
       total_pickups: 32,
       drivers_assigned: 5,
       average_stops_per_route: 6.4
     }
```

#### **FASE 7: EJECUCIÓN DE RECOLECCIÓN** 📱

```
8. Conductor → App Móvil → Confirma llegada
   ├─ PUT /api/v1/pickups/{pickup_id}/status
   ├─ Request: { status: "in_progress", arrival_time: "..." }
   ├─ Actualiza pickup_db.pickups.status
   └─ Cliente recibe notificación

9. Conductor → Completa recolección
   ├─ POST /api/v1/pickups/{pickup_id}/complete
   ├─ Request: {
   │   status: "completed",
   │   completion_time: "2025-01-02T10:45:00",
   │   packages_collected: [
   │     { package_id, condition: "good", photo_url }
   │   ],
   │   signature: "base64_encoded_signature",
   │   notes: "Todo OK"
   │ }
   ├─ Proceso:
   │   ├─ Actualiza pickup_db.pickups.status = "completed"
   │   ├─ Registra en pickup_attempts (exitoso)
   │   ├─ Actualiza manifest en international-shipping
   │   │   └─ manifests.status = "ready_to_ship"
   │   ├─ Actualiza orden en order-service
   │   │   └─ orders.status = "picked_up"
   │   ├─ Notifica al cliente
   │   └─ Genera evento "pickup_completed" (RabbitMQ)
   └─ Response: {
       pickup_id: "PCK-20250101123456",
       status: "completed",
       packages_confirmed: 1,
       next_step: "in_transit_to_warehouse"
     }
```

#### **FASE 8: TRACKING Y ACTUALIZACIONES** 📍

```
10. Cliente o Sistema → GET /api/v1/tracking/{tracking_number}
    ├─ Via: API Gateway → International Shipping (8004)
    ├─ Request: tracking_number = "DHL123456789"
    ├─ Proceso:
    │   ├─ Busca en manifests por tracking_number
    │   ├─ Obtiene historial de estados
    │   ├─ [FUTURO] Consulta carrier API para tracking real
    │   └─ Consolida información
    └─ Response: {
        tracking_number: "DHL123456789",
        status: "in_transit",
        current_location: "Mexico City Airport",
        estimated_delivery: "2025-01-03T18:00:00Z",
        events: [
          {
            timestamp: "2025-01-02T10:45:00",
            status: "picked_up",
            location: "Warehouse A",
            description: "Package picked up by courier"
          },
          {
            timestamp: "2025-01-02T14:30:00",
            status: "in_transit",
            location: "Mexico City Sorting Center",
            description: "Departed from origin facility"
          },
          ...
        ]
      }
```

### 🔄 Flujo de Comunicación entre Microservicios

```
┌─────────────┐
│   CLIENTE   │
└──────┬──────┘
       │ HTTP Request (con JWT)
       ↓
┌─────────────────┐
│  API GATEWAY    │ (Puerto 8000)
│  (FastAPI)      │
└────────┬────────┘
         │
         ├──→ auth-service (8009) ──→ Valida JWT
         │                              ↓
         │                         auth_db.user_sessions
         │                              ↓
         │                         Retorna user + permissions
         │
         ├──→ order-service (8002) ──→ Crea orden
         │         ↓                     ↓
         │    Valida permisos      order_db.orders
         │         ↓                     ↓
         │    Retorna order_id     Actualiza inventory
         │
         ├──→ international-shipping (8004) ──→ Cotiza/Crea manifest
         │         ↓                              ↓
         │    Calcula tarifas              intl_shipping_db.manifests
         │         ↓                              ↓
         │    Retorna quote               Genera tracking_number
         │
         └──→ pickup-service (8003) ──→ Programa recolección
                   ↓                       ↓
              Verifica capacidad     pickup_db.pickups
                   ↓                       ↓
              Crea ruta             pickup_db.pickup_routes
                   ↓                       ↓
              Notifica conductor    Envía evento a RabbitMQ
```

### 📊 Almacenamiento de Información por Paso

| Paso | Servicio | Base de Datos | Tablas Afectadas |
|------|----------|---------------|------------------|
| 1. Login | auth-service | auth_db | users, user_sessions, audit_logs |
| 2. Crear Orden | order-service | order_db | orders, order_items, inventory_items |
| 3. Cotizar Envío | international-shipping | intl_shipping_db | rates, catalogs, client_ratebooks |
| 4. Crear Manifiesto | international-shipping | intl_shipping_db | manifests, manifest_items, documents |
| 5. Solicitar Recolección | pickup-service | pickup_db | pickups, pickup_packages |
| 6. Optimizar Rutas | pickup-service | pickup_db | pickup_routes, drivers |
| 7. Ejecutar Recolección | pickup-service | pickup_db | pickups, pickup_attempts |
| 8. Tracking | international-shipping | intl_shipping_db | manifests |

### 🔔 Eventos Generados (RabbitMQ)

```
order.created → Notifica a analytics, inventory
manifest.created → Notifica a pickup, order
pickup.scheduled → Notifica a customer, driver
pickup.completed → Notifica a customer, manifest, analytics
shipment.in_transit → Notifica a customer, analytics
shipment.delivered → Notifica a customer, order, analytics
```

---

## 5. VERSIONADO DE ENTORNOS

### 📦 Archivos de Configuración por Ambiente

#### **DESARROLLO**
```yaml
Archivo: docker-compose.yml
Servicios:
  - app (monolito DDD) - Puerto 8000
  - PostgreSQL (quenty_db) - Puerto 5432
  - Redis - Puerto 6379
  - pgAdmin - Puerto 5050
  - Nginx - Puertos 80, 443
  - Prometheus - Puerto 9090
  - Grafana - Puerto 3000
  - Jaeger - Puertos 16686, 14268

Características:
  - ✅ Hot reload activado (volumes montados)
  - ✅ Logs en modo DEBUG
  - ✅ Una sola réplica por servicio
  - ✅ Contraseñas simples (quenty123)
  - ✅ pgAdmin para administración de BD
  - ✅ Todas las herramientas de debugging

Dockerfile: Dockerfile.dev
  - Base: python:3.11-slim
  - Instala dependencias de dev
  - No optimizado para tamaño
```

#### **MICROSERVICIOS (Desarrollo Distribuido)**
```yaml
Archivo: docker-compose.microservices.yml
Servicios (10 microservicios):
  - api-gateway (8000)
  - auth-service (8009) + auth-db (5441)
  - customer-service (8001) + customer-db (5433)
  - order-service (8002) + order-db (5434)
  - pickup-service (8003) + pickup-db (5435)
  - international-shipping (8004) + intl-shipping-db (5436)
  - microcredit-service (8005) + microcredit-db (5437)
  - analytics-service (8006) + analytics-db (5438)
  - reverse-logistics (8007) + reverse-logistics-db (5439)
  - franchise-service (8008) + franchise-db (5440)

Infraestructura compartida:
  - Redis (6379)
  - RabbitMQ (5672, 15672)
  - Consul (8500)
  - Prometheus (9090)
  - Grafana (3000)
  - Jaeger (16686)
  - Loki (3100)
  - Promtail
  - Nginx (80, 443)

Características:
  - ✅ Cada servicio con su BD independiente
  - ✅ Service discovery con Consul
  - ✅ Message queue con RabbitMQ
  - ✅ Observabilidad completa (Prometheus + Grafana + Jaeger + Loki)
  - ✅ Load balancing con Nginx
  - ⚠️ Contraseñas aún simples (no para producción)

Dockerfiles: microservices/[servicio]/Dockerfile
  - Multistage builds
  - Usuario no-root
  - Optimización de capas
```

#### **PRODUCCIÓN**
```yaml
Archivo: docker-compose.prod.yml
Servicios:
  - app (con deployment.replicas: 3)
  - PostgreSQL con configuración optimizada
  - Redis Cluster
  - Nginx con SSL
  - Prometheus (retención 30 días)
  - Grafana
  - ELK Stack (Elasticsearch + Logstash + Kibana)

Características:
  - ✅ Múltiples réplicas (app: 3)
  - ✅ Resource limits (CPU/Memory)
  - ✅ Health checks configurados
  - ✅ SSL/TLS habilitado
  - ✅ Logs centralizados (ELK)
  - ✅ Métricas con retención de 30 días
  - ✅ Subnet customizada (172.20.0.0/16)
  - ⚠️ Contraseñas usando variables de entorno
  - ⚠️ Configuraciones externas (archivos en /docker/)

Dockerfile: Dockerfile (producción)
  - Multistage build
  - Imagen mínima
  - Security hardening
  - Usuario no-root
  - Health checks
```

### 🔐 Versiones de Credenciales

#### Desarrollo:
- DB Password: `quenty123`
- Redis Password: `quenty123`
- Admin Passwords: `admin123`

#### Producción:
- ⚠️ Usa variables de entorno: `${POSTGRES_PASSWORD}`, `${SECRET_KEY}`, etc.
- ❌ **PROBLEMA:** No hay archivo `.env.prod` de ejemplo
- ❌ **PROBLEMA:** Variables no documentadas completamente

### ⚠️ PROBLEMAS IDENTIFICADOS

1. **Falta `.env.prod.example`**
   - No hay template de variables de entorno para producción

2. **Contraseñas hardcodeadas en microservicios**
   - `docker-compose.microservices.yml` tiene contraseñas en texto plano

3. **Configuraciones externas no versionadas**
   - Archivos en `/docker/nginx/`, `/docker/prometheus/`, etc.
   - Algunos existen, otros se referencian pero no están

4. **JWT Secret hardcodeado**
   - `JWT_SECRET_KEY=your-secret-key-change-this-in-production`

5. **Falta archivo de migraciones versionado**
   - Cada servicio tiene `alembic/`, pero no hay script de migración inicial documentado

### ✅ RECOMENDACIONES

1. **Crear `.env.example` por ambiente:**
   ```
   .env.development.example
   .env.microservices.example
   .env.production.example
   ```

2. **Usar Secrets Management en producción:**
   - Docker Swarm Secrets
   - Kubernetes Secrets
   - HashiCorp Vault
   - AWS Secrets Manager

3. **Versionado de configuraciones:**
   ```
   /docker/
   ├── nginx/
   │   ├── nginx.dev.conf
   │   ├── nginx.microservices.conf
   │   └── nginx.prod.conf
   ├── prometheus/
   │   ├── prometheus.dev.yml
   │   └── prometheus.prod.yml
   └── ...
   ```

4. **Script de setup por ambiente:**
   ```bash
   scripts/setup-dev.sh
   scripts/setup-microservices.sh
   scripts/setup-production.sh
   ```

---

## 6. GESTIÓN DE VARIABLES DE ENTORNO

### 📝 Estrategia Actual

**Patrón:** Mixto - Archivo centralizado + Variables por servicio

### 6.1 Archivos de Entorno Existentes

| Archivo | Propósito | Líneas | Estado |
|---------|-----------|--------|--------|
| `.env.microservices` | Config de microservicios | 64 | ✅ Activo |
| `.env.carriers` | Credenciales de carriers | 76 | ✅ Activo (no usado) |

### 6.2 Variables en `.env.microservices`

```bash
# Puertos de servicios (9 servicios)
API_GATEWAY_PORT=8000
CUSTOMER_SERVICE_PORT=8001
ORDER_SERVICE_PORT=8002
# ...

# Credenciales de BD por servicio (9 bases de datos)
CUSTOMER_DB_USER=customer
CUSTOMER_DB_PASSWORD=customer_pass
CUSTOMER_DB_NAME=customer_db
# ...

# Servicios compartidos
REDIS_PASSWORD=
RABBITMQ_USER=quenty
RABBITMQ_PASSWORD=quenty_pass

# Monitoreo
GRAFANA_ADMIN_PASSWORD=admin
PROMETHEUS_RETENTION=15d

# Seguridad
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### 6.3 Variables en `.env.carriers`

```bash
# Encryption
ENCRYPTION_KEY=SVZkwOLRWLSm6XJbDCyIVbHe-d5rX6cp2LBKPT4EavI=

# DHL (ACTIVO)
DHL_USERNAME=quentysasCO
DHL_PASSWORD=M#6bM^7wW!7dV^1n
DHL_ACCOUNT_NUMBER=683146118
DHL_ENVIRONMENT=sandbox

# FedEx, UPS, Servientrega, InterRapidisimo, Pasarex, Aeropost
# (CONFIGURADOS PERO SIN CREDENCIALES REALES)

# Database para carriers (separada)
CARRIER_DATABASE_URL=postgresql://postgres:quenty123@db:5432/carrier_db

# Cache y Queue
CARRIER_REDIS_URL=redis://:quenty123@redis:6379/1
CARRIER_RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//
```

### 6.4 Variables en docker-compose Files

**docker-compose.microservices.yml** define variables inline:

```yaml
auth-service:
  environment:
    - SERVICE_NAME=auth-service
    - DATABASE_URL=postgresql+asyncpg://auth:auth_pass@auth-db:5432/auth_db
    - REDIS_URL=redis://redis:6379/0
    - LOG_LEVEL=DEBUG
    - JWT_SECRET_KEY=your-secret-key-change-this-in-production
    - JWT_ALGORITHM=HS256
    - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
    # ... más variables
```

### 6.5 ¿Centralizado o Distribuido?

**RESPUESTA:** **Híbrido ineficiente**

#### Problemas identificados:

1. **Duplicación de Variables:**
   - Puertos definidos en `.env.microservices` Y en `docker-compose.microservices.yml`
   - Credenciales de BD repetidas en múltiples lugares

2. **Variables Hardcodeadas:**
   - JWT secrets en texto plano en docker-compose
   - Passwords de BD no usan variables de entorno

3. **Archivo `.env.carriers` No Se Usa:**
   - Tiene configuración completa
   - Ningún servicio lo carga
   - No está referenciado en docker-compose

4. **Falta Validación:**
   - No hay schema de validación (ej: Pydantic Settings)
   - No hay valores por defecto documentados

5. **Sin Separación por Ambiente:**
   - Mismas variables para dev y prod
   - No hay `.env.production`, `.env.staging`

### 6.6 Estrategia Recomendada

#### ✅ OPCIÓN 1: Archivo Centralizado por Ambiente (RECOMENDADO)

```
.env.development       # Para docker-compose.yml
.env.microservices     # Para docker-compose.microservices.yml
.env.production        # Para docker-compose.prod.yml
.env.carriers          # Para integraciones de carriers

.env.development.example
.env.microservices.example
.env.production.example
.env.carriers.example
```

**docker-compose.microservices.yml:**
```yaml
auth-service:
  env_file:
    - .env.microservices
  environment:
    - SERVICE_NAME=auth-service
    # Solo variables específicas del servicio
```

#### ✅ OPCIÓN 2: Archivo por Servicio

```
microservices/
  auth-service/
    .env.auth
  customer/
    .env.customer
  order/
    .env.order
  ...
```

**Pros:** Aislamiento total
**Contras:** Duplicación de variables compartidas (Redis, RabbitMQ)

#### ✅ OPCIÓN 3: Híbrido Estructurado (MEJOR PRÁCTICA)

```
.env.shared          # Redis, RabbitMQ, Consul, JWT secrets
.env.auth            # Auth service specific
.env.customer        # Customer service specific
.env.order           # Order service specific
...
.env.carriers        # Carrier integrations
```

**docker-compose.microservices.yml:**
```yaml
auth-service:
  env_file:
    - .env.shared
    - .env.auth
```

### 6.7 Config Management con Pydantic

Cada servicio debería tener:

```python
# microservices/auth-service/src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service
    service_name: str = "auth-service"
    service_port: int = 8009

    # Database
    database_url: str

    # Redis
    redis_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Consul
    consul_host: str = "consul"
    consul_port: int = 8500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 6.8 Implementación Requerida

#### 🔴 CRÍTICO:
1. **Separar variables por ambiente**
2. **Remover hardcoded secrets**
3. **Usar env_file en docker-compose**
4. **Crear .env.example files**

#### 🟡 IMPORTANTE:
5. **Implementar validación con Pydantic**
6. **Cargar `.env.carriers` en international-shipping**
7. **Documentar todas las variables disponibles**

#### 🟢 MEJORA:
8. **Usar Vault en producción**
9. **Implementar rotación de secrets**
10. **Agregar health checks para config**

---

## 7. LIMPIEZA DE CÓDIGO

### 🧹 Análisis de Archivos en Desuso

#### 7.1 Archivos de Cache (1780 archivos)

```bash
# Python cache
**/__pycache__/  → 1780 archivos
*.pyc
*.pyo
*.pyd

# Virtual environment
.venv/  → No debe estar en repo

# IDE
.idea/  → Debería estar en .gitignore
```

**Acción:** Agregar a `.gitignore` y eliminar del repositorio

#### 7.2 Archivos Temporales

```bash
# No se encontraron archivos .bak, .old, .tmp
# ✅ Buena práctica
```

#### 7.3 Archivos de Configuración Obsoletos

**Problema identificado en git status:**
```
?? .env.carriers  → No trackeado (BIEN, tiene secrets)
?? .idea/         → No debería estar (IDE settings)
```

#### 7.4 Código Duplicado

**PROBLEMA GRAVE:** Código DDD duplicado

```
/src/                          # Código DDD original (monolito)
  ├── domain/
  ├── infrastructure/
  └── api/

/microservices/                # Código de microservicios
  ├── customer/
  ├── order/
  └── ...
```

**Análisis:**
- Funcionalidad de dominio existe en AMBOS lugares
- README principal documenta el monolito DDD
- Microservicios tienen su propia implementación
- **NO ESTÁN SINCRONIZADOS**

**Ejemplo:**
- `/src/domain/entities/customer.py` (Entidad DDD completa)
- `/microservices/customer/src/models.py` (Modelo SQLAlchemy)
- Son implementaciones DIFERENTES de lo mismo

#### 7.5 Tests Desorganizados

```
/tests/                        # Tests del monolito DDD
  ├── domain/
  ├── infrastructure/
  └── api/

# Microservicios NO tienen tests en sus directorios
# Tests están solo en el proyecto raíz
```

#### 7.6 Documentación Obsoleta

**Documentos encontrados:**
```
/docs/microservices/
  ├── auth-service.md
  ├── customer-service.md
  ├── order-service.md
  ├── pickup-service.md
  ├── international-shipping-service.md
  ├── microcredit-service.md
  ├── analytics-service.md
  ├── reverse-logistics-service.md
  └── franchise-service.md

/docs/deployment/
  ├── PORT_MAPPING.md
  ├── GRAFANA_SETUP_COMPLETE.md
  ├── GRAFANA_MONITORING_GUIDE.md
  └── production-deployment.md
```

**Estado:** Necesita revisión de vigencia

#### 7.7 Configuraciones Docker No Usadas

**Archivos referenciados pero no existentes:**
```yaml
# En docker-compose.yml
./docker/postgres/init.sql          → ¿Existe?
./docker/nginx/nginx.conf           → ¿Existe?
./docker/nginx/default.conf         → ¿Existe?
./docker/prometheus/prometheus.yml  → ¿Existe?
./docker/grafana/dashboards         → ¿Existe?
./docker/grafana/datasources        → ¿Existe?

# En docker-compose.prod.yml
./docker/postgres/postgresql.conf   → ¿Existe?
./docker/postgres/pg_hba.conf       → ¿Existe?
./docker/redis/redis.conf           → ¿Existe?
./docker/nginx/nginx.prod.conf      → ¿Existe?
./docker/logstash/pipeline          → ¿Existe?
```

**Acción requerida:** Verificar existencia o crear archivos

### 🎯 Plan de Limpieza Recomendado

#### FASE 1: Limpieza Inmediata (1 día)

```bash
# 1. Actualizar .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".idea/" >> .gitignore
echo ".venv/" >> .gitignore
echo ".env" >> .gitignore
echo "*.log" >> .gitignore

# 2. Remover archivos trackeados que no deberían estarlo
git rm -r --cached .venv/
git rm -r --cached **/__pycache__/
git rm -r --cached .idea/

# 3. Limpiar cache local
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

#### FASE 2: Reestructuración (1 semana)

1. **Decisión Arquitectural:**
   - ¿Mantener monolito DDD (`/src/`) o migrar completamente a microservicios?
   - Si microservicios: Marcar `/src/` como deprecated
   - Si mantener ambos: Separar en repositorios diferentes

2. **Consolidar Tests:**
   ```
   /tests/ → Solo para monolito
   /microservices/[servicio]/tests/ → Tests del servicio
   ```

3. **Organizar Configuraciones:**
   ```
   /docker/
   ├── development/
   ├── microservices/
   └── production/
   ```

4. **Actualizar Documentación:**
   - Revisar y actualizar cada .md en `/docs/`
   - Agregar fecha de última actualización
   - Marcar documentos obsoletos

#### FASE 3: Limpieza Profunda (2 semanas)

1. **Eliminar Código Muerto:**
   - Usar herramientas: `vulture`, `dead`
   - Analizar imports no usados
   - Remover funciones/clases sin referencias

2. **Consolidar Dependencias:**
   - Revisar `requirements.txt`
   - Separar:
     - `requirements-base.txt`
     - `requirements-dev.txt`
     - `requirements-test.txt`
     - `requirements-prod.txt`

3. **Normalizar Estructura:**
   - Todos los microservicios con misma estructura:
     ```
     microservices/[servicio]/
     ├── src/
     ├── tests/
     ├── alembic/
     ├── Dockerfile
     ├── requirements.txt
     └── README.md
     ```

### 📊 Impacto Estimado de Limpieza

**Archivos a eliminar:**
- Cache Python: ~1780 archivos
- Virtual env (si está): ~10,000 archivos
- Duplicados: TBD (requiere análisis manual)

**Espacio a liberar:**
- Cache: ~50-100 MB
- .venv: ~500 MB - 1 GB
- Logs antiguos: TBD

**Mejoras esperadas:**
- ✅ Repo más limpio
- ✅ Clones más rápidos
- ✅ CI/CD más eficiente
- ✅ Búsquedas más rápidas

---

## 8. DIAGRAMAS DE BASE DE DATOS

### 🗄️ Esquema Visual por Microservicio

#### 8.1 AUTH-SERVICE

```
┌─────────────────────────────────────────────────────────┐
│                      AUTH_DB                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │    users     │────────<│ user_sessions    │        │
│  ├──────────────┤         ├──────────────────┤        │
│  │ id (PK)      │         │ id (PK)          │        │
│  │ unique_id    │         │ user_id (FK)     │        │
│  │ username     │         │ access_token     │        │
│  │ email        │         │ refresh_token    │        │
│  │ password_hash│         │ expires_at       │        │
│  │ company_id   │────┐    │ device_info      │        │
│  │ role_id      │──┐ │    └──────────────────┘        │
│  │ is_active    │  │ │                                 │
│  │ created_at   │  │ │    ┌──────────────────┐        │
│  └──────────────┘  │ │    │ oauth_accounts   │        │
│                     │ │    ├──────────────────┤        │
│  ┌──────────────┐  │ │    │ id (PK)          │        │
│  │  companies   │<─┘ │    │ user_id (FK)     │        │
│  ├──────────────┤    │    │ provider         │        │
│  │ id (PK)      │    │    │ provider_user_id │        │
│  │ company_id   │    │    │ access_token     │        │
│  │ name         │    │    │ refresh_token    │        │
│  │ document_num │    │    └──────────────────┘        │
│  │ legal_name   │    │                                 │
│  └──────────────┘    │    ┌──────────────────┐        │
│                      │    │   audit_logs     │        │
│  ┌──────────────┐    │    ├──────────────────┤        │
│  │    roles     │<───┘    │ id (PK)          │        │
│  ├──────────────┤         │ user_id          │        │
│  │ id (PK)      │         │ action           │        │
│  │ name         │         │ resource         │        │
│  │ description  │         │ ip_address       │        │
│  │ permissions  │         │ timestamp        │        │
│  └──────────────┘         └──────────────────┘        │
│                                                         │
│  ┌──────────────────────┐                             │
│  │ password_reset_tokens│                             │
│  ├──────────────────────┤                             │
│  │ id (PK)              │                             │
│  │ user_id (FK)         │                             │
│  │ token                │                             │
│  │ expires_at           │                             │
│  └──────────────────────┘                             │
└─────────────────────────────────────────────────────────┘

RESPONSABILIDAD:
- Autenticación (login, logout, JWT)
- Gestión de usuarios y empresas
- Roles y permisos (RBAC)
- OAuth (Google, Azure)
- Auditoría de accesos
```

#### 8.2 INTERNATIONAL-SHIPPING

```
┌──────────────────────────────────────────────────────────────┐
│                  INTL_SHIPPING_DB                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐         ┌──────────────────┐          │
│  │   manifests     │────────<│ manifest_items   │          │
│  ├─────────────────┤         ├──────────────────┤          │
│  │ id (PK)         │         │ id (PK)          │          │
│  │ unique_id       │         │ manifest_id (FK) │          │
│  │ tracking_number │         │ product_id       │          │
│  │ status          │         │ description      │          │
│  │ origin_country  │         │ quantity         │          │
│  │ dest_country    │         │ weight           │          │
│  │ total_weight    │         │ value            │          │
│  │ total_value     │         │ hs_code          │          │
│  │ carrier_id      │─┐       │ country_of_origin│          │
│  │ shipping_zone   │ │       └──────────────────┘          │
│  │ company_id      │ │                                      │
│  │ created_by      │ │       ┌──────────────────┐          │
│  │ created_at      │ │       │   documents      │          │
│  │ shipped_at      │ │       ├──────────────────┤          │
│  └─────────────────┘ │       │ id (PK)          │          │
│                      │       │ document_id      │          │
│  ┌─────────────────┐ │       │ manifest_id (FK) │          │
│  │shipping_carriers│<┘       │ document_type_id │          │
│  ├─────────────────┤         │ file_url         │          │
│  │ id (PK)         │         │ uploaded_at      │          │
│  │ name            │         └──────────────────┘          │
│  │ code            │                                        │
│  │ api_endpoint    │         ┌──────────────────┐          │
│  │ api_key         │         │ document_types   │          │
│  │ active          │         ├──────────────────┤          │
│  │ supported_svcs  │         │ id (PK)          │          │
│  └─────────────────┘         │ name             │          │
│                              │ required_for     │          │
│  ┌─────────────────┐         │ template_url     │          │
│  │   countries     │         └──────────────────┘          │
│  ├─────────────────┤                                        │
│  │ id (PK)         │                                        │
│  │ name            │         ┌──────────────────┐          │
│  │ iso_code        │         │ client_signatures│          │
│  │ zone            │         ├──────────────────┤          │
│  │ active          │         │ id (PK)          │          │
│  └─────────────────┘         │ client_id        │          │
│                              │ manifest_id (FK) │          │
│  ┌─────────────────┐         │ signature_data   │          │
│  │     rates       │         │ signed_at        │          │
│  ├─────────────────┤         └──────────────────┘          │
│  │ id (PK)         │                                        │
│  │ operator_id     │                                        │
│  │ service_id      │         ┌──────────────────┐          │
│  │ zone_id         │         │    catalogs      │          │
│  │ weight_min      │         ├──────────────────┤          │
│  │ weight_max      │         │ id (PK)          │          │
│  │ fixed_fee       │         │ catalog_id       │          │
│  │ percentage      │         │ name             │          │
│  └─────────────────┘         │ is_active        │          │
│         ↑                    └──────────────────┘          │
│         │                             ↑                     │
│         │                             │                     │
│  ┌─────────────────┐         ┌──────────────────┐          │
│  │ catalog_rates   │────────>│client_ratebooks  │          │
│  ├─────────────────┤         ├──────────────────┤          │
│  │ id (PK)         │         │ id (PK)          │          │
│  │ catalog_id (FK) │         │ ratebook_id      │          │
│  │ rate_id (FK)    │         │ client_id        │          │
│  │ custom_fixed_fee│         │ warehouse_id     │          │
│  │ custom_percent  │         │ catalog_id (FK)  │          │
│  └─────────────────┘         │ is_active        │          │
│                              └──────────────────┘          │
└──────────────────────────────────────────────────────────────┘

RESPONSABILIDAD:
- Manifiestos de envío internacional
- Cotizaciones y tarifas (rates, catalogs)
- Integración con carriers (DHL, FedEx, UPS)
- Documentación aduanera
- Tracking internacional
```

#### 8.3 ORDER

```
┌─────────────────────────────────────────────────────────┐
│                      ORDER_DB                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────────┐        │
│  │   orders     │────────<│   order_items    │        │
│  ├──────────────┤         ├──────────────────┤        │
│  │ id (PK)      │         │ id (PK)          │        │
│  │ order_number │         │ order_id (FK)    │        │
│  │ customer_id  │         │ product_id (FK)  │        │
│  │ company_id   │         │ quantity         │        │
│  │ status       │         │ unit_price       │        │
│  │ total_amount │         │ total_price      │        │
│  │ currency     │         │ weight           │        │
│  │ created_at   │         └──────────────────┘        │
│  │ updated_at   │                ↓                     │
│  └──────────────┘         ┌──────────────────┐        │
│                           │    products      │        │
│  ┌──────────────┐         ├──────────────────┤        │
│  │inventory_items│────────>│ id (PK)          │        │
│  ├──────────────┤         │ unique_id        │        │
│  │ id (PK)      │         │ code (SKU)       │        │
│  │ product_id   │<────────│ name             │        │
│  │ quantity     │         │ description      │        │
│  │ reserved_qty │         │ unit_measure     │        │
│  │ min_stock    │         │ weight_kg        │        │
│  │ max_stock    │         │ dimensions       │        │
│  │ location     │         │ price            │        │
│  │ batch_number │         │ company_id       │        │
│  │ expiry_date  │         │ category_id      │        │
│  └──────────────┘         │ status           │        │
│         ↑                 └──────────────────┘        │
│         │                                              │
│  ┌──────────────────┐                                 │
│  │ stock_movements  │                                 │
│  ├──────────────────┤                                 │
│  │ id (PK)          │                                 │
│  │ product_id (FK)  │                                 │
│  │ movement_type    │ (IN/OUT/ADJUSTMENT/TRANSFER)   │
│  │ quantity         │                                 │
│  │ reference_number │                                 │
│  │ notes            │                                 │
│  │ created_by       │                                 │
│  │ created_at       │                                 │
│  └──────────────────┘                                 │
└─────────────────────────────────────────────────────────┘

RESPONSABILIDAD:
- Órdenes de clientes
- Catálogo de productos
- Gestión de inventario
- Control de stock
- Movimientos de mercancía
```

#### 8.4 PICKUP

```
┌──────────────────────────────────────────────────────────┐
│                      PICKUP_DB                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────────┐         │
│  │   pickups    │────────<│ pickup_packages  │         │
│  ├──────────────┤         ├──────────────────┤         │
│  │ id (PK)      │         │ id (PK)          │         │
│  │ pickup_id    │         │ package_id       │         │
│  │ customer_id  │         │ pickup_id (FK)   │         │
│  │ order_id     │         │ tracking_number  │         │
│  │ pickup_type  │         │ weight           │         │
│  │ status       │         │ dimensions       │         │
│  │ address      │         │ order_id         │         │
│  │ scheduled_dt │         │ special_handling │         │
│  │ completed_dt │         └──────────────────┘         │
│  │ route_id     │──┐                                    │
│  └──────────────┘  │      ┌──────────────────┐         │
│                    │      │ pickup_attempts  │         │
│  ┌──────────────┐  │      ├──────────────────┤         │
│  │pickup_routes │<─┘      │ id (PK)          │         │
│  ├──────────────┤         │ pickup_id (FK)   │         │
│  │ id (PK)      │         │ attempt_number   │         │
│  │ route_id     │         │ attempted_at     │         │
│  │ driver_id    │──┐      │ status           │         │
│  │ date         │  │      │ failure_reason   │         │
│  │ status       │  │      │ notes            │         │
│  │ total_stops  │  │      └──────────────────┘         │
│  │ total_dist   │  │                                    │
│  │ waypoints    │  │      ┌──────────────────┐         │
│  └──────────────┘  │      │  pickup_zones    │         │
│                    │      ├──────────────────┤         │
│  ┌──────────────┐  │      │ id (PK)          │         │
│  │   drivers    │<─┘      │ zone_id          │         │
│  ├──────────────┤         │ name             │         │
│  │ id (PK)      │         │ postal_codes     │         │
│  │ driver_id    │         │ max_capacity     │         │
│  │ name         │         │ service_hours    │         │
│  │ phone        │         │ base_fee         │         │
│  │ license_num  │         └──────────────────┘         │
│  │ vehicle_type │                                       │
│  │ vehicle_plate│         ┌──────────────────┐         │
│  │ status       │         │pickup_capacity   │         │
│  │ rating       │         ├──────────────────┤         │
│  └──────────────┘         │ id (PK)          │         │
│                           │ zone_id (FK)     │         │
│                           │ date             │         │
│                           │ available_slots  │         │
│                           │ reserved_slots   │         │
│                           └──────────────────┘         │
└──────────────────────────────────────────────────────────┘

RESPONSABILIDAD:
- Programación de recolecciones
- Optimización de rutas
- Gestión de conductores
- Capacidad por zona
- Intentos y reagendamientos
```

#### 8.5 MICROCREDIT

```
┌────────────────────────────────────────────────────────┐
│                   MICROCREDIT_DB                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────────────┐    ┌────────────────────┐  │
│  │credit_applications   │───>│  credit_accounts   │  │
│  ├──────────────────────┤    ├────────────────────┤  │
│  │ id (PK)              │    │ id (PK)            │  │
│  │ application_id       │    │ account_id         │  │
│  │ customer_id          │    │ application_id (FK)│  │
│  │ credit_type          │    │ customer_id        │  │
│  │ requested_amount     │    │ principal          │  │
│  │ approved_amount      │    │ interest_rate      │  │
│  │ status               │    │ term_months        │  │
│  │ risk_score           │    │ current_balance    │  │
│  │ approved_by          │    │ payments_made      │  │
│  │ created_at           │    │ status             │  │
│  └──────────────────────┘    │ disbursed_at       │  │
│                              │ due_date           │  │
│  ┌──────────────────────┐    └────────────────────┘  │
│  │  credit_documents    │              ↓              │
│  ├──────────────────────┤    ┌────────────────────┐  │
│  │ id (PK)              │    │  credit_payments   │  │
│  │ application_id (FK)  │    ├────────────────────┤  │
│  │ document_type        │    │ id (PK)            │  │
│  │ file_url             │    │ payment_id         │  │
│  │ uploaded_at          │    │ account_id (FK)    │  │
│  └──────────────────────┘    │ amount             │  │
│                              │ principal_paid     │  │
│  ┌──────────────────────┐    │ interest_paid      │  │
│  │   credit_scores      │    │ fees_paid          │  │
│  ├──────────────────────┤    │ payment_date       │  │
│  │ id (PK)              │    │ status             │  │
│  │ customer_id          │    │ payment_method     │  │
│  │ score_value          │    └────────────────────┘  │
│  │ risk_category        │                            │
│  │ factors              │    ┌────────────────────┐  │
│  │ calculated_at        │    │credit_disbursements│  │
│  └──────────────────────┘    ├────────────────────┤  │
│                              │ id (PK)            │  │
│  ┌──────────────────────┐    │ account_id (FK)    │  │
│  │  credit_policies     │    │ amount             │  │
│  ├──────────────────────┤    │ method             │  │
│  │ id (PK)              │    │ destination        │  │
│  │ policy_id            │    │ disbursed_at       │  │
│  │ credit_type          │    │ status             │  │
│  │ min_score            │    └────────────────────┘  │
│  │ max_amount           │                            │
│  │ interest_rate        │    ┌────────────────────┐  │
│  │ max_term_months      │    │  credit_limits     │  │
│  │ is_active            │    ├────────────────────┤  │
│  └──────────────────────┘    │ id (PK)            │  │
│                              │ customer_id        │  │
│                              │ credit_type        │  │
│                              │ total_limit        │  │
│                              │ used_amount        │  │
│                              │ available_amount   │  │
│                              └────────────────────┘  │
└────────────────────────────────────────────────────────┘

RESPONSABILIDAD:
- Solicitudes de crédito
- Evaluación crediticia y scoring
- Cuentas de crédito activas
- Pagos y desembolsos
- Políticas y límites
```

### 8.6 Diagrama de Relaciones Entre Servicios

```
┌────────────────────────────────────────────────────────────┐
│           RELACIONES LÓGICAS ENTRE MICROSERVICIOS          │
└────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │  AUTH-SERVICE   │
    │   (auth_db)     │
    └────────┬────────┘
             │
             │ user_id, company_id (referencias lógicas)
             ├─────────────────────────────────────────┐
             │                                          │
             ↓                                          ↓
    ┌────────────────┐                        ┌────────────────┐
    │    CUSTOMER    │                        │     ORDER      │
    │ (customer_db)  │                        │  (order_db)    │
    │                │                        │                │
    │ customer_id    │                        │ customer_id    │
    │   = user_id    │                        │ order_id       │
    └────────────────┘                        └───────┬────────┘
                                                      │
                                                      │ order_id, product_id
                                          ┌───────────┼───────────┐
                                          ↓           ↓           ↓
                                  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                                  │   PICKUP    │ │INTL-SHIPPING│ │   REVERSE   │
                                  │ (pickup_db) │ │(intl_ship_db)│ │LOGISTICS    │
                                  │             │ │             │ │(reverse_db) │
                                  │ pickup_id   │ │ manifest_id │ │ return_id   │
                                  │ order_id    │ │ product_id  │ │original_order│
                                  └─────────────┘ └─────────────┘ └─────────────┘

    ┌─────────────────┐
    │  MICROCREDIT    │
    │ (microcredit_db)│
    │                 │
    │ customer_id     │
    │  (= user_id)    │
    └─────────────────┘

    ┌─────────────────┐
    │   FRANCHISE     │
    │ (franchise_db)  │
    │                 │
    │ franchisee_id   │
    │  (= user_id)    │
    └─────────────────┘

    ┌─────────────────┐
    │   ANALYTICS     │
    │ (analytics_db)  │
    │                 │
    │ Agrega datos de │
    │ TODOS servicios │
    │ (read-only)     │
    └─────────────────┘

NOTAS:
- NO hay Foreign Keys físicas entre bases de datos
- Las relaciones se mantienen mediante IDs de referencia (strings/ints)
- Integridad referencial: nivel de aplicación
- Comunicación: REST APIs + RabbitMQ events
```

### 8.7 Diagrama de Flujo de Datos

```
┌────────────────────────────────────────────────────────────┐
│              FLUJO DE DATOS: ORDEN → ENVÍO                 │
└────────────────────────────────────────────────────────────┘

1. CREAR ORDEN
   Usuario
     ↓
   ORDER-SERVICE
     ├─ Crea: orders (order_id)
     ├─ Crea: order_items (product_id, qty)
     └─ Actualiza: inventory_items (reserved_qty)

2. COTIZAR ENVÍO
   Usuario/Sistema
     ↓
   INTL-SHIPPING-SERVICE
     ├─ Lee: rates (tarifas base)
     ├─ Lee: client_ratebooks (tarifas personalizadas)
     └─ Retorna: cotización calculada

3. CREAR MANIFIESTO
   Usuario
     ↓
   INTL-SHIPPING-SERVICE
     ├─ Crea: manifests (manifest_id, tracking_number)
     ├─ Crea: manifest_items (referencia product_id de ORDER)
     ├─ Crea: documents (documentación aduanera)
     └─ Emite evento: "manifest.created"

4. SOLICITAR RECOLECCIÓN
   Usuario
     ↓
   PICKUP-SERVICE
     ├─ Crea: pickups (pickup_id, order_id)
     ├─ Crea: pickup_packages (tracking_number del manifest)
     ├─ Actualiza: pickup_capacity
     └─ Emite evento: "pickup.scheduled"

5. OPTIMIZAR RUTAS
   Sistema (cron)
     ↓
   PICKUP-SERVICE
     ├─ Crea: pickup_routes (route_id)
     ├─ Actualiza: pickups.route_id
     ├─ Lee: drivers (asignación)
     └─ Emite evento: "route.created"

6. EJECUTAR RECOLECCIÓN
   Conductor
     ↓
   PICKUP-SERVICE
     ├─ Actualiza: pickups.status = "completed"
     ├─ Crea: pickup_attempts (registro exitoso)
     └─ Emite evento: "pickup.completed"
          ↓
   INTL-SHIPPING-SERVICE (listener)
     ├─ Actualiza: manifests.status = "in_transit"
     └─ Emite evento: "shipment.in_transit"
          ↓
   ORDER-SERVICE (listener)
     └─ Actualiza: orders.status = "shipped"

7. TRACKING
   Usuario
     ↓
   INTL-SHIPPING-SERVICE
     ├─ Lee: manifests (por tracking_number)
     ├─ [FUTURO] Consulta: API del carrier
     └─ Retorna: historial de estados

8. ANALYTICS
   Sistema (eventos)
     ↓
   ANALYTICS-SERVICE (listener de todos los eventos)
     └─ Escribe: metrics (para cada evento de negocio)

EVENTOS RABBITMQ:
- order.created
- manifest.created
- pickup.scheduled
- pickup.completed
- shipment.in_transit
- shipment.delivered
```

---

## 9. RECOMENDACIONES CRÍTICAS

### 🔴 CRÍTICO - Acción Inmediata Requerida

#### 1. **IMPLEMENTAR INTEGRACIÓN REAL DE CARRIERS** (Prioridad: ALTA)

**Problema:**
Sistema funciona con datos mockeados. No hay conexión real con DHL, FedEx, UPS.

**Impacto:**
- ❌ Tracking numbers no son reales
- ❌ Tarifas no son exactas
- ❌ No se pueden crear envíos reales
- ❌ Sistema no es funcional para producción

**Acción:**
1. Implementar `CarrierFactory` y `BaseCarrier`
2. Crear `DHLClient` con integración real
3. Cargar credenciales de `.env.carriers`
4. Implementar rate shopping en tiempo real
5. **Esfuerzo:** 2-3 semanas para DHL

#### 2. **SEPARAR VARIABLES DE ENTORNO POR AMBIENTE** (Prioridad: ALTA)

**Problema:**
Mismas variables para dev y prod. Secrets hardcodeados.

**Impacto:**
- ⚠️ Riesgo de seguridad
- ⚠️ Dificulta deployment
- ⚠️ Secrets en repositorio

**Acción:**
1. Crear `.env.development.example`, `.env.production.example`
2. Remover secrets hardcodeados de docker-compose
3. Usar `env_file` en docker-compose
4. Implementar validación con Pydantic Settings
5. **Esfuerzo:** 1-2 días

#### 3. **ACTUALIZAR README DE MICROSERVICIOS** (Prioridad: MEDIA)

**Problema:**
Puertos incorrectos. Servicios marcados como "legacy" están activos.

**Impacto:**
- ⚠️ Confusión para nuevos desarrolladores
- ⚠️ Documentación no refleja realidad

**Acción:**
1. Corregir tabla de puertos
2. Remover etiqueta "Legacy/Awaiting auth"
3. Documentar servicios de integración (ML, Shopify)
4. Actualizar diagrama de arquitectura
5. **Esfuerzo:** 2-3 horas

#### 4. **DECIDIR ARQUITECTURA: MONOLITO vs MICROSERVICIOS** (Prioridad: ALTA)

**Problema:**
Código DDD duplicado en `/src/` y `/microservices/`. No están sincronizados.

**Impacto:**
- ❌ Mantenimiento duplicado
- ❌ Riesgo de inconsistencias
- ❌ Confusión arquitectural

**Acción:**
**Opción A:** Migrar completamente a microservicios
- Marcar `/src/` como deprecated
- Mover tests a cada microservicio
- Actualizar README principal

**Opción B:** Mantener ambos (no recomendado)
- Separar en repositorios diferentes
- Definir casos de uso claros

**Opción C:** Volver al monolito (no recomendado)
- Eliminar microservicios
- Consolidar todo en `/src/`

**Recomendación:** Opción A (microservicios)
**Esfuerzo:** 1-2 semanas

### 🟡 IMPORTANTE - Corto Plazo

#### 5. **LIMPIAR REPOSITORIO** (Prioridad: MEDIA)

**Acción:**
- Agregar/actualizar `.gitignore`
- Remover 1780 archivos de cache
- Eliminar `.venv/` del repo
- Quitar `.idea/`
- **Esfuerzo:** 1 día

#### 6. **NORMALIZAR ESTRUCTURA DE TESTS** (Prioridad: MEDIA)

**Acción:**
- Mover tests a `/microservices/[servicio]/tests/`
- Crear `conftest.py` compartido
- Agregar tests de integración
- **Esfuerzo:** 3-5 días

#### 7. **VERIFICAR ARCHIVOS DE CONFIGURACIÓN DOCKER** (Prioridad: MEDIA)

**Acción:**
- Verificar existencia de archivos en `/docker/`
- Crear templates faltantes
- Documentar configuraciones
- **Esfuerzo:** 1-2 días

### 🟢 MEJORAS - Mediano Plazo

#### 8. **IMPLEMENTAR SECRETS MANAGEMENT** (Prioridad: BAJA)

**Acción:**
- Evaluar HashiCorp Vault / AWS Secrets Manager
- Migrar secrets sensibles
- Implementar rotación automática
- **Esfuerzo:** 1 semana

#### 9. **CREAR DIAGRAMAS ACTUALIZADOS** (Prioridad: BAJA)

**Acción:**
- Diagrama de arquitectura (con herramienta tipo Draw.io)
- Diagrama de flujos de negocio
- Diagramas ERD por servicio
- **Esfuerzo:** 2-3 días

#### 10. **IMPLEMENTAR CI/CD** (Prioridad: BAJA)

**Acción:**
- GitHub Actions / GitLab CI
- Tests automáticos en PRs
- Deployment automatizado
- **Esfuerzo:** 1 semana

---

## 📊 RESUMEN EJECUTIVO

### Estado General del Sistema

| Aspecto | Estado | Nivel de Riesgo |
|---------|--------|-----------------|
| **Carriers Integration** | ❌ No funcional | 🔴 CRÍTICO |
| **Database Architecture** | ✅ Bien diseñado | 🟢 BAJO |
| **Documentation (Main)** | ✅ Completo | 🟢 BAJO |
| **Documentation (Microservices)** | ⚠️ Desactualizado | 🟡 MEDIO |
| **Environment Variables** | ⚠️ Desorganizado | 🟡 MEDIO |
| **Code Duplication** | ❌ Duplicado | 🔴 CRÍTICO |
| **Security** | ⚠️ Secrets expuestos | 🟡 MEDIO |
| **Testing** | ⚠️ Desorganizado | 🟡 MEDIO |
| **Deployment** | ✅ Docker ready | 🟢 BAJO |

### Hallazgos Principales

#### ✅ FORTALEZAS:
1. Arquitectura de microservicios bien diseñada
2. Database per service implementado correctamente
3. Autenticación centralizada con RBAC
4. Documentación DDD completa
5. Infraestructura de observabilidad (Prometheus, Grafana, Jaeger)
6. Docker/docker-compose bien configurado

#### ❌ DEBILIDADES CRÍTICAS:
1. **Carriers NO funcionan** - Todo es mockeado
2. Código duplicado (monolito DDD vs microservicios)
3. Variables de entorno desorganizadas
4. Secrets hardcodeados
5. README de microservicios desactualizado
6. 1780 archivos de cache en repo

#### ⚠️ RIESGOS:
1. Sistema NO es funcional para producción (carriers mockeados)
2. Confusión arquitectural (dos códigos bases)
3. Seguridad comprometida (secrets expuestos)
4. Mantenimiento difícil (código duplicado)

### Esfuerzo de Corrección Estimado

| Prioridad | Tareas | Esfuerzo Total |
|-----------|--------|----------------|
| 🔴 CRÍTICO | 4 tareas | 4-6 semanas |
| 🟡 IMPORTANTE | 3 tareas | 1-2 semanas |
| 🟢 MEJORAS | 3 tareas | 2-3 semanas |
| **TOTAL** | **10 tareas** | **7-11 semanas** |

### Roadmap Recomendado

#### **Sprint 1-2 (2 semanas):**
- Limpieza de repositorio
- Separar variables de entorno
- Actualizar README
- Decidir arquitectura (mono vs micro)

#### **Sprint 3-6 (4 semanas):**
- Implementar DHL integration
- Normalizar estructura de tests
- Migrar a microservicios (si aplica)

#### **Sprint 7-9 (3 semanas):**
- Implementar otros carriers (FedEx, UPS)
- Secrets management
- CI/CD

#### **Sprint 10-11 (2 semanas):**
- Documentación final
- Diagramas actualizados
- Preparación para producción

---

## 📞 PRÓXIMOS PASOS

### Acciones Inmediatas (Esta Semana):

1. **Revisar este documento con el equipo**
2. **Decidir prioridades** según roadmap de negocio
3. **Asignar recursos** para tareas críticas
4. **Crear branches** para cada área de trabajo

### Preguntas para Discusión:

1. ¿Cuál es la fecha objetivo para tener carriers funcionando?
2. ¿Mantenemos monolito DDD o migramos todo a microservicios?
3. ¿Qué ambiente queremos deployar primero (dev/staging/prod)?
4. ¿Hay presupuesto para herramientas de secrets management?
5. ¿Quién será responsable de cada área de corrección?

---

**FIN DEL ANÁLISIS**

Documento generado automáticamente por Claude Code
Fecha: 2025-10-01
Versión: 1.0
