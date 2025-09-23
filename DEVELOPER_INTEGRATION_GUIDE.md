# 📚 QUENTY - GUÍA COMPLETA DE INTEGRACIÓN PARA DESARROLLADORES

## ÍNDICE

1. [CONFIGURACIÓN INICIAL](#1-configuración-inicial)
2. [ARQUITECTURA Y SERVICIOS](#2-arquitectura-y-servicios)
3. [AUTENTICACIÓN Y SEGURIDAD](#3-autenticación-y-seguridad)
4. [API ENDPOINTS COMPLETOS](#4-api-endpoints-completos)
5. [INTEGRACIONES DE CARRIERS](#5-integraciones-de-carriers)
6. [INTEGRACIONES E-COMMERCE](#6-integraciones-e-commerce)
7. [WEBHOOKS Y EVENTOS](#7-webhooks-y-eventos)
8. [GUÍA FRONTEND](#8-guía-frontend)
9. [GUÍA BACKEND](#9-guía-backend)
10. [TESTING Y DEBUGGING](#10-testing-y-debugging)
11. [EJEMPLOS DE CÓDIGO](#11-ejemplos-de-código)
12. [TROUBLESHOOTING](#12-troubleshooting)

---

## 1. CONFIGURACIÓN INICIAL

### 1.1 Setup Rápido (5 minutos)

```bash
# 1. Clonar repositorio
git clone https://github.com/quenty/quenty-platform.git
cd quenty-platform

# 2. Copiar TODOS los archivos de configuración
cp .env.example .env
cp .env.carriers.example .env.carriers

# 3. Configurar credenciales mínimas en .env
DATABASE_URL=postgresql://postgres:quenty123@localhost:5432/quenty_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=development-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production

# 4. Levantar servicios con Docker
docker-compose up -d

# 5. Verificar que todo esté corriendo
curl http://localhost:8000/health
```

### 1.2 Puertos de Servicios

| Servicio | Puerto | URL | Descripción |
|----------|--------|-----|-------------|
| API Gateway | 8000 | http://localhost:8000 | Punto de entrada principal |
| Auth Service | 8001 | http://localhost:8001 | Autenticación y usuarios |
| Customer Service | 8002 | http://localhost:8002 | Gestión de clientes |
| Order Service | 8003 | http://localhost:8003 | Órdenes y pedidos |
| Carrier Integration | 8009 | http://localhost:8009 | Integraciones de envío |
| PostgreSQL | 5432 | localhost:5432 | Base de datos principal |
| Redis | 6379 | localhost:6379 | Cache y sesiones |
| RabbitMQ | 15672 | http://localhost:15672 | Panel de mensajería |
| Flower | 5555 | http://localhost:5555 | Monitor de Celery |
| Grafana | 3000 | http://localhost:3000 | Dashboards (admin/admin123) |
| Prometheus | 9090 | http://localhost:9090 | Métricas |

### 1.3 Credenciales por Defecto (Desarrollo)

```yaml
# Base de Datos
PostgreSQL:
  usuario: postgres
  password: quenty123
  database: quenty_db

# Redis
Redis:
  password: quenty123

# RabbitMQ
RabbitMQ:
  usuario: guest
  password: guest

# Grafana
Grafana:
  usuario: admin
  password: admin123

# API Keys de Desarrollo
API_KEY: dev-api-key-12345
SECRET_KEY: dev-secret-key-change-in-production
```

---

## 2. ARQUITECTURA Y SERVICIOS

### 2.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│                   (React/Vue/Angular)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    NGINX (Puerto 80/443)                     │
│                    - Load Balancing                          │
│                    - SSL Termination                         │
│                    - Static Files                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                 API GATEWAY (Puerto 8000)                    │
│                 - Routing                                    │
│                 - Rate Limiting                              │
│                 - Authentication                             │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────┘
   │          │          │          │          │
   ↓          ↓          ↓          ↓          ↓
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Auth  │ │Order │ │Cust. │ │Ship. │ │Carrier   │
│:8001 │ │:8003 │ │:8002 │ │:8004 │ │:8009     │
└──────┘ └──────┘ └──────┘ └──────┘ └──────────┘
   │          │          │          │          │
   └──────────┴──────────┴──────────┴──────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
   ┌────────┐                        ┌──────────┐
   │PostgreSQL│                      │  Redis   │
   │  :5432   │                      │  :6379   │
   └──────────┘                      └──────────┘
```

### 2.2 Flujo de Requests

```mermaid
sequenceDiagram
    participant C as Cliente
    participant G as API Gateway
    participant A as Auth Service
    participant S as Service
    participant D as Database

    C->>G: Request + Token
    G->>A: Validate Token
    A->>G: Token Valid
    G->>S: Forward Request
    S->>D: Query Data
    D->>S: Return Data
    S->>G: Response
    G->>C: Final Response
```

---

## 3. AUTENTICACIÓN Y SEGURIDAD

### 3.1 Flujo de Autenticación

#### Login Endpoint
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "admin",
    "permissions": ["read", "write", "delete"]
  }
}
```

### 3.2 Usando el Token

```javascript
// Frontend - Axios
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Frontend - Fetch
fetch('http://localhost:8000/api/v1/orders', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### 3.3 Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3.4 Permisos y Roles

```python
# Backend - Decorador de permisos
@require_permissions(['admin', 'manager'])
def admin_endpoint():
    pass

# Roles disponibles
ROLES = {
  'super_admin': ['*'],
  'admin': ['read', 'write', 'delete'],
  'manager': ['read', 'write'],
  'user': ['read'],
  'guest': []
}
```

---

## 4. API ENDPOINTS COMPLETOS

### 4.1 AUTH SERVICE (Puerto 8001)

#### Registro de Usuario
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "nuevo@usuario.com",
  "password": "SecurePass123!",
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone": "+573001234567",
  "accept_terms": true
}

Response: 201 Created
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "nuevo@usuario.com",
  "status": "pending_verification",
  "verification_sent": true
}
```

#### Login
```http
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

Response: 200 OK
{
  "access_token": "eyJ0eXA...",
  "refresh_token": "eyJ0eXA...",
  "expires_in": 3600
}
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer {token}

Response: 200 OK
{
  "message": "Successfully logged out"
}
```

#### Verificar Email
```http
GET /api/v1/auth/verify-email?token={verification_token}

Response: 200 OK
{
  "message": "Email verified successfully",
  "redirect_url": "/login"
}
```

#### Reset Password
```http
POST /api/v1/auth/reset-password
{
  "email": "user@example.com"
}

Response: 200 OK
{
  "message": "Reset email sent"
}
```

#### Cambiar Password
```http
PUT /api/v1/auth/change-password
Authorization: Bearer {token}
{
  "current_password": "old_password",
  "new_password": "new_SecurePass123!"
}
```

### 4.2 CUSTOMER SERVICE (Puerto 8002)

#### Listar Clientes
```http
GET /api/v1/customers?page=1&limit=20&search=juan
Authorization: Bearer {token}

Response: 200 OK
{
  "customers": [
    {
      "id": "uuid",
      "email": "juan@example.com",
      "first_name": "Juan",
      "last_name": "Pérez",
      "phone": "+573001234567",
      "created_at": "2024-01-01T00:00:00Z",
      "loyalty_points": 1500,
      "tier": "gold",
      "total_orders": 25,
      "total_spent": 2500000
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "pages": 5
  }
}
```

#### Crear Cliente
```http
POST /api/v1/customers
Authorization: Bearer {token}
{
  "email": "nuevo@cliente.com",
  "first_name": "María",
  "last_name": "González",
  "phone": "+573009876543",
  "document_type": "CC",
  "document_number": "1234567890",
  "address": {
    "street": "Calle 100 #45-67",
    "city": "Bogotá",
    "state": "Cundinamarca",
    "postal_code": "110111",
    "country": "CO"
  },
  "preferences": {
    "newsletter": true,
    "sms_notifications": false,
    "language": "es"
  }
}
```

#### Actualizar Cliente
```http
PUT /api/v1/customers/{customer_id}
Authorization: Bearer {token}
{
  "phone": "+573001112222",
  "address": {
    "street": "Carrera 7 #123-45"
  }
}
```

#### Historial de Órdenes del Cliente
```http
GET /api/v1/customers/{customer_id}/orders
Authorization: Bearer {token}

Response: 200 OK
{
  "orders": [
    {
      "order_id": "ORD-2024-0001",
      "date": "2024-01-15T10:30:00Z",
      "status": "delivered",
      "total": 150000,
      "items": 3
    }
  ]
}
```

### 4.3 ORDER SERVICE (Puerto 8003)

#### Crear Orden
```http
POST /api/v1/orders
Authorization: Bearer {token}
{
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "product_id": "PROD-001",
      "quantity": 2,
      "price": 50000,
      "name": "Producto A"
    },
    {
      "product_id": "PROD-002",
      "quantity": 1,
      "price": 75000,
      "name": "Producto B"
    }
  ],
  "shipping_address": {
    "street": "Calle 100 #45-67",
    "city": "Bogotá",
    "state": "Cundinamarca",
    "postal_code": "110111",
    "country": "CO"
  },
  "payment_method": "credit_card",
  "shipping_method": "standard"
}

Response: 201 Created
{
  "order_id": "ORD-2024-0002",
  "status": "pending",
  "subtotal": 175000,
  "tax": 33250,
  "shipping": 10000,
  "total": 218250,
  "estimated_delivery": "2024-01-20",
  "tracking_number": null
}
```

#### Obtener Orden
```http
GET /api/v1/orders/{order_id}
Authorization: Bearer {token}

Response: 200 OK
{
  "order_id": "ORD-2024-0002",
  "customer": {
    "id": "uuid",
    "name": "Juan Pérez",
    "email": "juan@example.com"
  },
  "items": [...],
  "status": "processing",
  "payment_status": "paid",
  "shipping_status": "pending",
  "timeline": [
    {
      "status": "created",
      "timestamp": "2024-01-15T10:00:00Z",
      "note": "Order placed"
    },
    {
      "status": "paid",
      "timestamp": "2024-01-15T10:05:00Z",
      "note": "Payment confirmed"
    }
  ]
}
```

#### Actualizar Estado de Orden
```http
PATCH /api/v1/orders/{order_id}/status
Authorization: Bearer {token}
{
  "status": "shipped",
  "tracking_number": "TRK123456789",
  "carrier": "DHL",
  "notes": "Package shipped via DHL Express"
}
```

#### Cancelar Orden
```http
POST /api/v1/orders/{order_id}/cancel
Authorization: Bearer {token}
{
  "reason": "Customer request",
  "refund_amount": 218250,
  "refund_method": "original_payment"
}
```

### 4.4 CARRIER INTEGRATION (Puerto 8009)

#### Obtener Cotización de Envío
```http
POST /api/v1/carriers/quote
Authorization: Bearer {token}
{
  "carrier": "DHL",  // DHL, UPS, FEDEX, SERVIENTREGA, INTERRAPIDISIMO
  "origin": {
    "country": "CO",
    "city": "Bogotá",
    "postal_code": "110111",
    "street": "Calle 100 #10-20"
  },
  "destination": {
    "country": "US",
    "city": "Miami",
    "postal_code": "33101",
    "street": "123 Main St"
  },
  "packages": [
    {
      "weight_kg": 2.5,
      "length_cm": 30,
      "width_cm": 20,
      "height_cm": 15,
      "value": 100000,
      "currency": "COP"
    }
  ],
  "service_type": "express"  // standard, express, overnight
}

Response: 200 OK
{
  "quote_id": "QUOTE-DHL-2024-0001",
  "carrier": "DHL",
  "service": "DHL Express Worldwide",
  "amount": 125000,
  "currency": "COP",
  "estimated_days": 3,
  "valid_until": "2024-01-16T23:59:59Z",
  "breakdown": {
    "base_rate": 100000,
    "fuel_surcharge": 15000,
    "insurance": 10000
  }
}
```

#### Obtener Mejor Cotización (Múltiples Carriers)
```http
POST /api/v1/carriers/best-quote
Authorization: Bearer {token}
{
  "origin": {...},
  "destination": {...},
  "packages": [...],
  "preferences": {
    "max_days": 5,
    "max_price": 200000,
    "preferred_carriers": ["DHL", "FEDEX"]
  }
}

Response: 200 OK
{
  "quotes": [
    {
      "carrier": "SERVIENTREGA",
      "amount": 45000,
      "estimated_days": 2,
      "score": 95  // Basado en precio y tiempo
    },
    {
      "carrier": "DHL",
      "amount": 125000,
      "estimated_days": 3,
      "score": 85
    }
  ],
  "recommended": "SERVIENTREGA"
}
```

#### Generar Guía de Envío
```http
POST /api/v1/carriers/label
Authorization: Bearer {token}
{
  "carrier": "DHL",
  "quote_id": "QUOTE-DHL-2024-0001",  // Opcional si tienes quote previa
  "order_id": "ORD-2024-0002",
  "origin": {
    "contact_name": "Almacén Quenty",
    "contact_phone": "+573001234567",
    "contact_email": "almacen@quenty.com",
    "company": "Quenty SAS",
    "street": "Bodega 5, Zona Industrial",
    "city": "Bogotá",
    "state": "Cundinamarca",
    "postal_code": "110111",
    "country": "CO"
  },
  "destination": {
    "contact_name": "John Doe",
    "contact_phone": "+13051234567",
    "contact_email": "john@example.com",
    "street": "123 Main St, Apt 4B",
    "city": "Miami",
    "state": "FL",
    "postal_code": "33101",
    "country": "US"
  },
  "packages": [...],
  "customs_documents": {  // Solo para envíos internacionales
    "invoice_number": "INV-2024-0001",
    "description": "Electronic accessories",
    "terms_of_trade": "DAP"
  }
}

Response: 201 Created
{
  "tracking_number": "7798339175",
  "carrier": "DHL",
  "label_url": "https://api.quenty.com/labels/DHL-7798339175.pdf",
  "label_data": "base64_encoded_pdf_data...",
  "awb_number": "7798339175",
  "estimated_delivery": "2024-01-18T18:00:00Z",
  "cost": {
    "amount": 125000,
    "currency": "COP"
  },
  "pickup_required": true,
  "pickup_confirmation": "PKP-2024-0001"
}
```

#### Rastrear Envío
```http
GET /api/v1/carriers/track/{tracking_number}?carrier=DHL
Authorization: Bearer {token}

Response: 200 OK
{
  "tracking_number": "7798339175",
  "carrier": "DHL",
  "status": "in_transit",
  "current_location": "Miami International Airport",
  "estimated_delivery": "2024-01-18T18:00:00Z",
  "delivered": false,
  "events": [
    {
      "date": "2024-01-15T10:00:00Z",
      "status": "picked_up",
      "description": "Shipment picked up",
      "location": "Bogotá, CO"
    },
    {
      "date": "2024-01-15T14:00:00Z",
      "status": "in_transit",
      "description": "Departed from facility",
      "location": "Bogotá Airport, CO"
    },
    {
      "date": "2024-01-16T02:00:00Z",
      "status": "in_transit",
      "description": "Arrived at sort facility",
      "location": "Miami, FL, US"
    }
  ],
  "proof_of_delivery": null
}
```

#### Programar Recolección
```http
POST /api/v1/carriers/pickup
Authorization: Bearer {token}
{
  "carrier": "DHL",
  "pickup_date": "2024-01-16",
  "pickup_window_start": "09:00",
  "pickup_window_end": "18:00",
  "address": {
    "contact_name": "Juan Pérez",
    "contact_phone": "+573001234567",
    "company": "Quenty SAS",
    "street": "Bodega 5, Zona Industrial",
    "city": "Bogotá",
    "postal_code": "110111",
    "country": "CO"
  },
  "packages_count": 5,
  "total_weight_kg": 25,
  "special_instructions": "Llamar al llegar"
}

Response: 201 Created
{
  "confirmation_number": "PKP-DHL-2024-0002",
  "carrier": "DHL",
  "pickup_date": "2024-01-16",
  "pickup_window": "09:00-18:00",
  "status": "scheduled",
  "contact_phone": "+573001234567"
}
```

#### Estado de Carriers
```http
GET /api/v1/carriers/status
Authorization: Bearer {token}

Response: 200 OK
{
  "enabled_carriers": ["DHL", "UPS", "FEDEX", "SERVIENTREGA", "INTERRAPIDISIMO"],
  "total_carriers": 5,
  "carrier_status": {
    "DHL": {
      "active": true,
      "environment": "production",
      "last_request": "2024-01-15T10:00:00Z",
      "success_rate": 98.5,
      "average_response_time": 1250
    },
    "UPS": {
      "active": true,
      "environment": "sandbox",
      "last_request": "2024-01-15T09:30:00Z",
      "success_rate": 97.2,
      "average_response_time": 1500
    },
    "SERVIENTREGA": {
      "active": true,
      "environment": "production",
      "last_request": "2024-01-15T10:15:00Z",
      "success_rate": 95.0,
      "average_response_time": 2000
    }
  }
}
```

---

## 5. INTEGRACIONES DE CARRIERS

### 5.1 Configuración de Credenciales

#### Archivo: `.env.carriers`
```bash
# DHL Express
DHL_API_KEY=ABC123DEF456
DHL_API_SECRET=secret123
DHL_USERNAME=dhl_user
DHL_PASSWORD=dhl_pass123
DHL_ACCOUNT_NUMBER=960010000
DHL_ENVIRONMENT=production  # sandbox para pruebas

# UPS
UPS_CLIENT_ID=ups_client_id_123
UPS_CLIENT_SECRET=ups_secret_456
UPS_ACCOUNT_NUMBER=A1B2C3
UPS_ACCESS_LICENSE_NUMBER=LICENSE123
UPS_USERNAME=ups_user
UPS_PASSWORD=ups_pass123
UPS_ENVIRONMENT=sandbox

# FedEx
FEDEX_CLIENT_ID=fedex_client_789
FEDEX_CLIENT_SECRET=fedex_secret_012
FEDEX_ACCOUNT_NUMBER=510087020
FEDEX_METER_NUMBER=119238439
FEDEX_KEY=fedex_key_345
FEDEX_PASSWORD=fedex_pass678
FEDEX_ENVIRONMENT=sandbox

# Servientrega (Colombia)
SERVIENTREGA_USER=usuario_servientrega
SERVIENTREGA_PASSWORD=pass_servientrega
SERVIENTREGA_BILLING_CODE=SER001
SERVIENTREGA_ID_CLIENT=12345
SERVIENTREGA_NAME_PACK=PAQUETE_ESTANDAR
SERVIENTREGA_ENVIRONMENT=production

# InterRapidisimo (Colombia)
INTERRAPIDISIMO_API_KEY=inter_key_123
INTERRAPIDISIMO_CLIENT_CODE=INTER001
INTERRAPIDISIMO_USERNAME=inter_user
INTERRAPIDISIMO_PASSWORD=inter_pass
INTERRAPIDISIMO_CONTRACT_NUMBER=CTR001
INTERRAPIDISIMO_ENVIRONMENT=production
```

### 5.2 Mapeo de Servicios por Carrier

| Carrier | Servicios Disponibles | Código |
|---------|----------------------|---------|
| **DHL** | Express Worldwide | `P` |
| | Express 9:00 | `N` |
| | Express 12:00 | `I` |
| | Economy | `U` |
| **UPS** | Next Day Air | `01` |
| | 2nd Day Air | `02` |
| | Ground | `03` |
| | Express | `07` |
| **FedEx** | Priority Overnight | `PRIORITY_OVERNIGHT` |
| | Standard Overnight | `STANDARD_OVERNIGHT` |
| | 2 Day | `FEDEX_2_DAY` |
| | Express Saver | `FEDEX_EXPRESS_SAVER` |
| **Servientrega** | Mercancía Premier | `1` |
| | Documentos | `2` |
| | Mercancía Industrial | `3` |
| **InterRapidisimo** | Hoy | `HOY` |
| | Express | `EXPRESS` |
| | Estándar | `ESTANDAR` |

### 5.3 Ejemplos de Integración

#### Python - Backend
```python
import requests

class CarrierIntegration:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://localhost:8009/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_quote(self, carrier, origin, destination, packages):
        """Obtener cotización de envío"""
        payload = {
            "carrier": carrier,
            "origin": origin,
            "destination": destination,
            "packages": packages
        }

        response = requests.post(
            f"{self.base_url}/carriers/quote",
            json=payload,
            headers=self.headers
        )
        return response.json()

    def create_label(self, carrier, order_data):
        """Crear guía de envío"""
        response = requests.post(
            f"{self.base_url}/carriers/label",
            json=order_data,
            headers=self.headers
        )
        return response.json()

    def track_shipment(self, tracking_number, carrier):
        """Rastrear envío"""
        response = requests.get(
            f"{self.base_url}/carriers/track/{tracking_number}",
            params={"carrier": carrier},
            headers=self.headers
        )
        return response.json()

# Uso
carrier = CarrierIntegration(api_key="your-api-key")

# Cotización DHL
quote = carrier.get_quote(
    carrier="DHL",
    origin={
        "country": "CO",
        "city": "Bogotá",
        "postal_code": "110111"
    },
    destination={
        "country": "US",
        "city": "Miami",
        "postal_code": "33101"
    },
    packages=[{
        "weight_kg": 2.5,
        "length_cm": 30,
        "width_cm": 20,
        "height_cm": 15
    }]
)

print(f"Precio: ${quote['amount']} {quote['currency']}")
print(f"Tiempo estimado: {quote['estimated_days']} días")
```

#### JavaScript - Frontend
```javascript
class CarrierService {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'http://localhost:8009/api/v1';
  }

  async getQuote(carrier, origin, destination, packages) {
    const response = await fetch(`${this.baseUrl}/carriers/quote`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        carrier,
        origin,
        destination,
        packages
      })
    });

    return await response.json();
  }

  async trackShipment(trackingNumber, carrier) {
    const response = await fetch(
      `${this.baseUrl}/carriers/track/${trackingNumber}?carrier=${carrier}`,
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      }
    );

    return await response.json();
  }

  async getBestQuote(origin, destination, packages) {
    const response = await fetch(`${this.baseUrl}/carriers/best-quote`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        origin,
        destination,
        packages
      })
    });

    return await response.json();
  }
}

// Uso en React
const CarrierComponent = () => {
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);

  const carrierService = new CarrierService('your-api-key');

  const handleGetQuote = async () => {
    setLoading(true);
    try {
      const result = await carrierService.getBestQuote(
        { country: 'CO', city: 'Bogotá', postal_code: '110111' },
        { country: 'US', city: 'Miami', postal_code: '33101' },
        [{ weight_kg: 2, length_cm: 30, width_cm: 20, height_cm: 15 }]
      );
      setQuote(result);
    } catch (error) {
      console.error('Error getting quote:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleGetQuote} disabled={loading}>
        {loading ? 'Obteniendo cotización...' : 'Cotizar Envío'}
      </button>

      {quote && (
        <div>
          <h3>Mejor opción: {quote.recommended}</h3>
          {quote.quotes.map(q => (
            <div key={q.carrier}>
              <p>{q.carrier}: ${q.amount} - {q.estimated_days} días</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## 6. INTEGRACIONES E-COMMERCE

### 6.1 SHOPIFY

#### Configuración Inicial
```bash
# .env
SHOPIFY_SHOP_DOMAIN=tu-tienda.myshopify.com
SHOPIFY_API_KEY=shppa_123abc
SHOPIFY_API_SECRET=shpss_456def
SHOPIFY_ACCESS_TOKEN=shpat_789ghi
SHOPIFY_WEBHOOK_SECRET=whsec_jklmno
```

#### Endpoints Shopify
```http
# Sincronizar productos
POST /api/v1/shopify/sync/products
Authorization: Bearer {token}
{
  "shop_domain": "tu-tienda.myshopify.com",
  "sync_images": true,
  "sync_variants": true,
  "update_existing": true
}

# Importar órdenes
POST /api/v1/shopify/sync/orders
{
  "shop_domain": "tu-tienda.myshopify.com",
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "status": ["paid", "fulfilled"]
}

# Actualizar inventario
POST /api/v1/shopify/inventory/update
{
  "updates": [
    {
      "sku": "PROD-001",
      "quantity": 50,
      "location_id": "gid://shopify/Location/1"
    }
  ]
}

# Webhook receiver
POST /api/v1/shopify/webhook
X-Shopify-Topic: orders/create
X-Shopify-Hmac-Sha256: {signature}
{
  // Shopify order payload
}
```

#### Configurar Webhooks en Shopify
```javascript
// Script para registrar webhooks
const registerWebhooks = async () => {
  const webhooks = [
    { topic: 'orders/create', address: 'https://api.quenty.com/shopify/webhook' },
    { topic: 'orders/updated', address: 'https://api.quenty.com/shopify/webhook' },
    { topic: 'products/update', address: 'https://api.quenty.com/shopify/webhook' }
  ];

  for (const webhook of webhooks) {
    await fetch(`https://${SHOP_DOMAIN}/admin/api/2024-01/webhooks.json`, {
      method: 'POST',
      headers: {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ webhook })
    });
  }
};
```

### 6.2 WOOCOMMERCE

#### Configuración
```bash
# .env
WOOCOMMERCE_URL=https://tu-tienda.com
WOOCOMMERCE_CONSUMER_KEY=ck_abc123
WOOCOMMERCE_CONSUMER_SECRET=cs_def456
```

#### Endpoints WooCommerce
```http
# Sincronizar productos
POST /api/v1/woocommerce/sync/products
{
  "store_url": "https://tu-tienda.com",
  "sync_categories": true,
  "sync_attributes": true,
  "batch_size": 50
}

# Procesar orden
POST /api/v1/woocommerce/orders/process
{
  "order_id": "123",
  "action": "complete",
  "tracking_number": "TRK123456",
  "carrier": "DHL"
}
```

### 6.3 MERCADOLIBRE

#### Configuración OAuth
```bash
# .env
MELI_APP_ID=123456789
MELI_CLIENT_SECRET=abc123def456
MELI_REDIRECT_URI=https://api.quenty.com/meli/callback
```

#### Flujo de Autorización
```http
# 1. Redirigir usuario a MercadoLibre
GET https://auth.mercadolibre.com.co/authorization?response_type=code&client_id={APP_ID}&redirect_uri={REDIRECT_URI}

# 2. Callback recibe código
GET /api/v1/meli/callback?code={AUTH_CODE}

# 3. Exchange código por token
POST /api/v1/meli/token
{
  "code": "{AUTH_CODE}"
}

Response:
{
  "access_token": "APP_USR-123...",
  "refresh_token": "TG-123...",
  "user_id": 123456789
}
```

#### Endpoints MercadoLibre
```http
# Publicar producto
POST /api/v1/meli/items
{
  "title": "Producto Ejemplo",
  "category_id": "MCO1234",
  "price": 50000,
  "currency_id": "COP",
  "available_quantity": 10,
  "condition": "new",
  "listing_type_id": "gold_special",
  "pictures": [
    {"source": "http://imagen1.jpg"},
    {"source": "http://imagen2.jpg"}
  ],
  "attributes": [
    {"id": "BRAND", "value_name": "Samsung"},
    {"id": "MODEL", "value_name": "Galaxy"}
  ]
}

# Actualizar stock
PUT /api/v1/meli/items/{item_id}/stock
{
  "available_quantity": 25
}

# Responder pregunta
POST /api/v1/meli/questions/{question_id}/answer
{
  "text": "Sí, tenemos disponible en color negro."
}

# Obtener órdenes
GET /api/v1/meli/orders?status=paid&limit=50
```

---

## 7. WEBHOOKS Y EVENTOS

### 7.1 Configuración de Webhooks

#### Registrar Webhook
```http
POST /api/v1/webhooks
Authorization: Bearer {token}
{
  "url": "https://tu-servidor.com/webhook",
  "events": ["order.created", "order.shipped", "payment.completed"],
  "secret": "webhook_secret_key",
  "active": true
}

Response:
{
  "webhook_id": "webhook_123",
  "url": "https://tu-servidor.com/webhook",
  "secret": "webhook_secret_key",
  "status": "active"
}
```

### 7.2 Eventos Disponibles

| Evento | Descripción | Payload |
|--------|-------------|---------|
| `order.created` | Nueva orden creada | Order object |
| `order.updated` | Orden actualizada | Order object + changes |
| `order.shipped` | Orden enviada | Order + tracking |
| `order.delivered` | Orden entregada | Order + proof |
| `order.cancelled` | Orden cancelada | Order + reason |
| `payment.completed` | Pago completado | Payment object |
| `payment.failed` | Pago fallido | Payment + error |
| `customer.created` | Nuevo cliente | Customer object |
| `shipment.update` | Actualización de envío | Tracking object |

### 7.3 Verificación de Webhook

```python
# Python - Verificar firma
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

# Uso
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_data(as_text=True)

    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        return 'Unauthorized', 401

    # Procesar evento
    event = json.loads(payload)
    handle_event(event)

    return 'OK', 200
```

```javascript
// JavaScript - Verificar firma
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return signature === expected;
}

// Express handler
app.post('/webhook', (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  const payload = JSON.stringify(req.body);

  if (!verifyWebhook(payload, signature, WEBHOOK_SECRET)) {
    return res.status(401).send('Unauthorized');
  }

  // Procesar evento
  handleEvent(req.body);
  res.status(200).send('OK');
});
```

---

## 8. GUÍA FRONTEND

### 8.1 Configuración Inicial

#### Variables de Entorno Frontend
```javascript
// .env.local (React/Next.js)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_VERSION=v1
REACT_APP_GOOGLE_MAPS_KEY=your-google-maps-key
REACT_APP_STRIPE_PUBLIC_KEY=pk_test_123
REACT_APP_SENTRY_DSN=https://sentry.io/123
```

### 8.2 Servicio API Base

```javascript
// services/api.js
import axios from 'axios';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor para agregar token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor para manejar errores
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            const response = await this.refreshToken(refreshToken);

            localStorage.setItem('access_token', response.data.access_token);
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;

            return this.client(originalRequest);
          } catch (refreshError) {
            // Redirect to login
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  async refreshToken(refreshToken) {
    return axios.post(`${process.env.REACT_APP_API_URL}/auth/refresh`, {
      refresh_token: refreshToken
    });
  }

  // Auth methods
  async login(email, password) {
    const response = await this.client.post('/auth/login', { email, password });
    const { access_token, refresh_token, user } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));

    return response.data;
  }

  async logout() {
    await this.client.post('/auth/logout');
    localStorage.clear();
  }

  // Orders
  async getOrders(params = {}) {
    return this.client.get('/orders', { params });
  }

  async createOrder(orderData) {
    return this.client.post('/orders', orderData);
  }

  // Customers
  async getCustomers(params = {}) {
    return this.client.get('/customers', { params });
  }

  // Shipping
  async getShippingQuote(data) {
    return this.client.post('/carriers/quote', data);
  }

  async trackShipment(trackingNumber, carrier) {
    return this.client.get(`/carriers/track/${trackingNumber}`, {
      params: { carrier }
    });
  }
}

export default new ApiService();
```

### 8.3 Hooks Personalizados

```javascript
// hooks/useAuth.js
import { useState, useEffect, createContext, useContext } from 'react';
import ApiService from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const data = await ApiService.login(email, password);
    setUser(data.user);
    return data;
  };

  const logout = async () => {
    await ApiService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// hooks/useOrders.js
import { useState, useEffect } from 'react';
import ApiService from '../services/api';

export const useOrders = (params = {}) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOrders();
  }, [JSON.stringify(params)]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getOrders(params);
      setOrders(response.data.orders);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createOrder = async (orderData) => {
    const response = await ApiService.createOrder(orderData);
    await fetchOrders(); // Refresh list
    return response.data;
  };

  return { orders, loading, error, createOrder, refetch: fetchOrders };
};
```

### 8.4 Componentes de Ejemplo

```jsx
// components/ShippingCalculator.jsx
import React, { useState } from 'react';
import ApiService from '../services/api';

const ShippingCalculator = ({ origin, destination, packages }) => {
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCarrier, setSelectedCarrier] = useState(null);

  const calculateShipping = async () => {
    setLoading(true);
    try {
      const response = await ApiService.client.post('/carriers/best-quote', {
        origin,
        destination,
        packages
      });
      setQuotes(response.data.quotes);
    } catch (error) {
      console.error('Error calculating shipping:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectCarrier = async (carrier) => {
    setSelectedCarrier(carrier);
    // Generar label
    const response = await ApiService.client.post('/carriers/label', {
      carrier: carrier.carrier,
      quote_id: carrier.quote_id,
      origin,
      destination,
      packages
    });

    console.log('Label generated:', response.data);
  };

  return (
    <div className="shipping-calculator">
      <button onClick={calculateShipping} disabled={loading}>
        {loading ? 'Calculando...' : 'Calcular Envío'}
      </button>

      {quotes.length > 0 && (
        <div className="quotes">
          <h3>Opciones de Envío</h3>
          {quotes.map((quote) => (
            <div key={quote.carrier} className="quote-option">
              <h4>{quote.carrier}</h4>
              <p>Precio: ${quote.amount} {quote.currency}</p>
              <p>Tiempo: {quote.estimated_days} días</p>
              <button onClick={() => selectCarrier(quote)}>
                Seleccionar
              </button>
            </div>
          ))}
        </div>
      )}

      {selectedCarrier && (
        <div className="selected-carrier">
          <h3>Carrier Seleccionado: {selectedCarrier.carrier}</h3>
        </div>
      )}
    </div>
  );
};

// components/OrderTracking.jsx
import React, { useState, useEffect } from 'react';
import ApiService from '../services/api';

const OrderTracking = ({ trackingNumber, carrier }) => {
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (trackingNumber && carrier) {
      fetchTracking();
    }
  }, [trackingNumber, carrier]);

  const fetchTracking = async () => {
    try {
      const response = await ApiService.trackShipment(trackingNumber, carrier);
      setTracking(response.data);
    } catch (error) {
      console.error('Error fetching tracking:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Cargando información de rastreo...</div>;
  if (!tracking) return <div>No se encontró información de rastreo</div>;

  return (
    <div className="order-tracking">
      <h2>Rastreo de Envío</h2>
      <div className="tracking-header">
        <p>Número: {tracking.tracking_number}</p>
        <p>Carrier: {tracking.carrier}</p>
        <p>Estado: {tracking.status}</p>
        <p>Ubicación: {tracking.current_location}</p>
      </div>

      <div className="tracking-timeline">
        <h3>Historial</h3>
        {tracking.events.map((event, index) => (
          <div key={index} className="tracking-event">
            <span className="event-date">{new Date(event.date).toLocaleString()}</span>
            <span className="event-status">{event.status}</span>
            <span className="event-description">{event.description}</span>
            <span className="event-location">{event.location}</span>
          </div>
        ))}
      </div>

      {tracking.estimated_delivery && (
        <div className="delivery-estimate">
          <h3>Entrega Estimada</h3>
          <p>{new Date(tracking.estimated_delivery).toLocaleDateString()}</p>
        </div>
      )}
    </div>
  );
};
```

### 8.5 Estado Global (Redux Toolkit)

```javascript
// store/slices/ordersSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import ApiService from '../../services/api';

export const fetchOrders = createAsyncThunk(
  'orders/fetchOrders',
  async (params = {}) => {
    const response = await ApiService.getOrders(params);
    return response.data;
  }
);

export const createOrder = createAsyncThunk(
  'orders/createOrder',
  async (orderData) => {
    const response = await ApiService.createOrder(orderData);
    return response.data;
  }
);

const ordersSlice = createSlice({
  name: 'orders',
  initialState: {
    orders: [],
    currentOrder: null,
    loading: false,
    error: null
  },
  reducers: {
    setCurrentOrder: (state, action) => {
      state.currentOrder = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrders.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.loading = false;
        state.orders = action.payload.orders;
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(createOrder.fulfilled, (state, action) => {
        state.orders.push(action.payload);
        state.currentOrder = action.payload;
      });
  }
});

export const { setCurrentOrder } = ordersSlice.actions;
export default ordersSlice.reducer;
```

---

## 9. GUÍA BACKEND

### 9.1 Estructura del Proyecto

```
quenty/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── orders.py
│   │   │   │   ├── customers.py
│   │   │   │   └── carriers.py
│   │   │   └── router.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── order.py
│   │   └── customer.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── order.py
│   │   └── customer.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── order_service.py
│   │   └── carrier_service.py
│   └── main.py
├── tests/
├── alembic/
└── requirements.txt
```

### 9.2 Modelos de Base de Datos

```python
# models/order.py
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    order_number = Column(String, unique=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"))
    status = Column(String, default="pending")
    payment_status = Column(String, default="pending")
    shipping_status = Column(String, default="pending")

    # Amounts
    subtotal = Column(Float)
    tax = Column(Float)
    shipping_cost = Column(Float)
    total = Column(Float)

    # Shipping
    shipping_method = Column(String)
    carrier = Column(String)
    tracking_number = Column(String)
    estimated_delivery = Column(DateTime)

    # Addresses
    shipping_address = Column(JSON)
    billing_address = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("orders.id"))
    product_id = Column(String)
    product_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    total = Column(Float)

    # Relationship
    order = relationship("Order", back_populates="items")
```

### 9.3 Servicios

```python
# services/carrier_service.py
from typing import Dict, List, Optional
import httpx
from ..models import Order
from ..schemas import ShippingQuote, ShippingLabel

class CarrierService:
    def __init__(self):
        self.carriers = {
            'DHL': DHLClient(),
            'UPS': UPSClient(),
            'FEDEX': FedExClient(),
            'SERVIENTREGA': ServientregaClient(),
            'INTERRAPIDISIMO': InterrapidisimoClient()
        }

    async def get_quote(
        self,
        carrier: str,
        origin: Dict,
        destination: Dict,
        packages: List[Dict]
    ) -> ShippingQuote:
        """Get shipping quote from specific carrier"""
        client = self.carriers.get(carrier)
        if not client:
            raise ValueError(f"Carrier {carrier} not supported")

        quote = await client.get_quote(origin, destination, packages)
        return ShippingQuote(**quote)

    async def get_best_quote(
        self,
        origin: Dict,
        destination: Dict,
        packages: List[Dict]
    ) -> Dict:
        """Get quotes from all carriers and return best option"""
        quotes = []

        # Get quotes in parallel
        tasks = []
        for carrier_name, client in self.carriers.items():
            task = client.get_quote(origin, destination, packages)
            tasks.append((carrier_name, task))

        # Wait for all quotes
        for carrier_name, task in tasks:
            try:
                quote = await task
                quote['carrier'] = carrier_name
                quotes.append(quote)
            except Exception as e:
                print(f"Error getting quote from {carrier_name}: {e}")

        # Sort by price
        quotes.sort(key=lambda x: x['amount'])

        return {
            'quotes': quotes,
            'recommended': quotes[0]['carrier'] if quotes else None
        }

    async def create_label(
        self,
        carrier: str,
        order: Order,
        origin: Dict,
        destination: Dict
    ) -> ShippingLabel:
        """Create shipping label"""
        client = self.carriers.get(carrier)
        if not client:
            raise ValueError(f"Carrier {carrier} not supported")

        label_data = await client.create_label({
            'order_id': order.order_number,
            'origin': origin,
            'destination': destination,
            'packages': self._get_packages_from_order(order)
        })

        # Save tracking number to order
        order.tracking_number = label_data['tracking_number']
        order.carrier = carrier

        return ShippingLabel(**label_data)

    async def track_shipment(
        self,
        tracking_number: str,
        carrier: str
    ) -> Dict:
        """Track shipment"""
        client = self.carriers.get(carrier)
        if not client:
            raise ValueError(f"Carrier {carrier} not supported")

        tracking_data = await client.track(tracking_number)
        return tracking_data
```

### 9.4 Endpoints API

```python
# api/v1/endpoints/carriers.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ....services.carrier_service import CarrierService
from ....schemas import ShippingQuoteRequest, ShippingQuoteResponse

router = APIRouter(prefix="/carriers", tags=["carriers"])

@router.post("/quote", response_model=ShippingQuoteResponse)
async def get_quote(
    request: ShippingQuoteRequest,
    carrier_service: CarrierService = Depends(get_carrier_service)
):
    """Get shipping quote from specific carrier"""
    try:
        quote = await carrier_service.get_quote(
            carrier=request.carrier,
            origin=request.origin.dict(),
            destination=request.destination.dict(),
            packages=[p.dict() for p in request.packages]
        )
        return quote
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/best-quote")
async def get_best_quote(
    request: ShippingQuoteRequest,
    carrier_service: CarrierService = Depends(get_carrier_service)
):
    """Get best quote from all carriers"""
    try:
        result = await carrier_service.get_best_quote(
            origin=request.origin.dict(),
            destination=request.destination.dict(),
            packages=[p.dict() for p in request.packages]
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/track/{tracking_number}")
async def track_shipment(
    tracking_number: str,
    carrier: str,
    carrier_service: CarrierService = Depends(get_carrier_service)
):
    """Track shipment"""
    try:
        tracking = await carrier_service.track_shipment(
            tracking_number=tracking_number,
            carrier=carrier
        )
        return tracking
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 9.5 Middleware y Seguridad

```python
# core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str, requests_per_minute: int = 60):
        super().__init__(app)
        self.redis = redis.from_url(redis_url)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host

        # Create Redis key
        key = f"rate_limit:{client_ip}"

        # Check current count
        current = self.redis.get(key)

        if current is None:
            # First request
            self.redis.setex(key, 60, 1)
        elif int(current) < self.requests_per_minute:
            # Increment counter
            self.redis.incr(key)
        else:
            # Rate limit exceeded
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        response = await call_next(request)
        return response
```

---

## 10. TESTING Y DEBUGGING

### 10.1 Testing con Postman

#### Colección Postman
```json
{
  "info": {
    "name": "Quenty API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api/v1"
    },
    {
      "key": "access_token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "var jsonData = pm.response.json();",
                  "pm.environment.set('access_token', jsonData.access_token);",
                  "pm.environment.set('refresh_token', jsonData.refresh_token);"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"admin@quenty.com\",\n  \"password\": \"admin123\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/auth/login",
              "host": ["{{base_url}}"],
              "path": ["auth", "login"]
            }
          }
        }
      ]
    },
    {
      "name": "Carriers",
      "item": [
        {
          "name": "Get Quote",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"carrier\": \"DHL\",\n  \"origin\": {\n    \"country\": \"CO\",\n    \"city\": \"Bogotá\",\n    \"postal_code\": \"110111\"\n  },\n  \"destination\": {\n    \"country\": \"US\",\n    \"city\": \"Miami\",\n    \"postal_code\": \"33101\"\n  },\n  \"packages\": [\n    {\n      \"weight_kg\": 2,\n      \"length_cm\": 30,\n      \"width_cm\": 20,\n      \"height_cm\": 15\n    }\n  ]\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/carriers/quote",
              "host": ["{{base_url}}"],
              "path": ["carriers", "quote"]
            }
          }
        }
      ]
    }
  ]
}
```

### 10.2 Tests Automatizados

```python
# tests/test_carriers.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_quote():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "test123"}
        )
        token = login_response.json()["access_token"]

        # Get quote
        response = await client.post(
            "/api/v1/carriers/quote",
            json={
                "carrier": "DHL",
                "origin": {
                    "country": "CO",
                    "city": "Bogotá",
                    "postal_code": "110111"
                },
                "destination": {
                    "country": "US",
                    "city": "Miami",
                    "postal_code": "33101"
                },
                "packages": [
                    {
                        "weight_kg": 2,
                        "length_cm": 30,
                        "width_cm": 20,
                        "height_cm": 15
                    }
                ]
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "amount" in data
        assert "carrier" in data
        assert data["carrier"] == "DHL"

@pytest.mark.asyncio
async def test_track_shipment():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/carriers/track/7798339175?carrier=DHL",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "tracking_number" in data
        assert "status" in data
        assert "events" in data
```

### 10.3 Debugging

#### Logs Estructurados
```python
# logging_config.py
import structlog
import logging

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Uso
import structlog
logger = structlog.get_logger()

logger.info(
    "Quote requested",
    carrier="DHL",
    origin="Bogotá",
    destination="Miami",
    packages_count=2,
    total_weight=5.5
)
```

#### Debug con VS Code
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.main:app", "--reload", "--port", "8000"],
      "jinja": true,
      "env": {
        "DATABASE_URL": "postgresql://postgres:quenty123@localhost:5432/quenty_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "DEBUG": "true"
      }
    }
  ]
}
```

---

## 11. EJEMPLOS DE CÓDIGO

### 11.1 Integración Completa - Crear Orden con Envío

```python
# Python - Backend Service
async def process_order_with_shipping(order_data: dict):
    """
    Proceso completo: crear orden, obtener cotización, generar label
    """
    # 1. Crear orden
    order = await create_order(order_data)

    # 2. Obtener mejor cotización de envío
    shipping_quotes = await carrier_service.get_best_quote(
        origin=WAREHOUSE_ADDRESS,
        destination=order.shipping_address,
        packages=order.get_packages()
    )

    # 3. Seleccionar carrier recomendado
    selected_carrier = shipping_quotes['recommended']
    selected_quote = shipping_quotes['quotes'][0]

    # 4. Generar guía de envío
    label = await carrier_service.create_label(
        carrier=selected_carrier,
        order=order,
        origin=WAREHOUSE_ADDRESS,
        destination=order.shipping_address
    )

    # 5. Actualizar orden con información de envío
    order.tracking_number = label.tracking_number
    order.carrier = selected_carrier
    order.shipping_cost = selected_quote['amount']
    order.estimated_delivery = label.estimated_delivery
    await order.save()

    # 6. Enviar notificaciones
    await send_order_confirmation_email(order)
    await send_shipping_notification(order)

    # 7. Programar webhook para tracking updates
    await schedule_tracking_webhook(order.tracking_number, selected_carrier)

    return {
        'order': order,
        'shipping': {
            'tracking_number': label.tracking_number,
            'carrier': selected_carrier,
            'label_url': label.label_url,
            'estimated_delivery': label.estimated_delivery
        }
    }
```

```javascript
// JavaScript - Frontend Flow
class OrderService {
  async createOrderWithShipping(orderData) {
    try {
      // 1. Validar datos
      this.validateOrderData(orderData);

      // 2. Obtener cotización de envío
      const shippingQuote = await this.getShippingQuote({
        destination: orderData.shipping_address,
        packages: orderData.items.map(item => ({
          weight_kg: item.weight,
          length_cm: item.dimensions.length,
          width_cm: item.dimensions.width,
          height_cm: item.dimensions.height
        }))
      });

      // 3. Mostrar opciones al usuario
      const selectedCarrier = await this.showShippingOptions(shippingQuote.quotes);

      // 4. Crear orden con carrier seleccionado
      const order = await this.api.post('/orders', {
        ...orderData,
        shipping_method: selectedCarrier.carrier,
        shipping_cost: selectedCarrier.amount
      });

      // 5. Generar label de envío
      const label = await this.api.post('/carriers/label', {
        carrier: selectedCarrier.carrier,
        order_id: order.id,
        quote_id: selectedCarrier.quote_id
      });

      // 6. Mostrar confirmación
      this.showOrderConfirmation({
        order,
        shipping: {
          tracking_number: label.tracking_number,
          carrier: selectedCarrier.carrier,
          estimated_delivery: label.estimated_delivery
        }
      });

      return order;

    } catch (error) {
      this.handleError(error);
    }
  }

  async trackOrder(trackingNumber, carrier) {
    const tracking = await this.api.get(
      `/carriers/track/${trackingNumber}?carrier=${carrier}`
    );

    // Actualizar UI con información de tracking
    this.updateTrackingUI(tracking);

    // Setup polling para actualizaciones
    this.pollTracking(trackingNumber, carrier);
  }

  pollTracking(trackingNumber, carrier) {
    this.trackingInterval = setInterval(async () => {
      const tracking = await this.trackOrder(trackingNumber, carrier);

      if (tracking.delivered) {
        clearInterval(this.trackingInterval);
        this.showDeliveryNotification(tracking);
      }
    }, 60000); // Check every minute
  }
}
```

### 11.2 Webhook Handler

```python
# webhook_handler.py
from fastapi import Request, HTTPException
import hmac
import hashlib

async def handle_carrier_webhook(request: Request):
    """
    Handler para webhooks de carriers (DHL, UPS, etc.)
    """
    # Verificar firma
    signature = request.headers.get('X-Webhook-Signature')
    payload = await request.body()

    if not verify_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse evento
    event = json.loads(payload)
    event_type = event.get('type')

    # Procesar según tipo de evento
    if event_type == 'shipment.delivered':
        await handle_delivery(event['data'])
    elif event_type == 'shipment.exception':
        await handle_shipping_exception(event['data'])
    elif event_type == 'shipment.update':
        await handle_tracking_update(event['data'])

    return {"status": "processed"}

async def handle_delivery(data):
    """Procesar entrega completada"""
    tracking_number = data['tracking_number']

    # Buscar orden
    order = await Order.get_by_tracking(tracking_number)
    if not order:
        return

    # Actualizar estado
    order.shipping_status = 'delivered'
    order.delivered_at = data['delivered_at']
    order.proof_of_delivery = data.get('signature')
    await order.save()

    # Notificar cliente
    await send_delivery_notification(order)

    # Trigger post-delivery workflows
    await trigger_feedback_request(order)
    await update_loyalty_points(order)
```

---

## 12. TROUBLESHOOTING

### 12.1 Problemas Comunes y Soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| **401 Unauthorized** | Token expirado o inválido | Refresh token o re-login |
| **429 Rate Limit** | Demasiadas requests | Implementar retry con backoff |
| **500 Server Error** | Error en backend | Revisar logs del servidor |
| **CORS Error** | Origen no permitido | Agregar origen a CORS_ORIGINS |
| **Connection Refused** | Servicio caído | Verificar Docker containers |
| **Timeout** | Request muy lenta | Aumentar timeout o optimizar |

### 12.2 Comandos de Debugging

```bash
# Ver logs de servicios
docker-compose logs -f api-gateway
docker-compose logs -f carrier-integration

# Verificar servicios corriendo
docker-compose ps

# Reiniciar servicio específico
docker-compose restart carrier-integration

# Ejecutar comando en container
docker-compose exec api-gateway sh

# Ver base de datos
docker-compose exec postgres psql -U postgres -d quenty_db

# Monitor de Celery
open http://localhost:5555

# Ver RabbitMQ
open http://localhost:15672  # guest/guest

# Redis CLI
docker-compose exec redis redis-cli

# Verificar health de servicios
curl http://localhost:8000/health
curl http://localhost:8009/health
```

### 12.3 Logs y Monitoreo

```python
# Ver logs en tiempo real
import structlog
logger = structlog.get_logger()

# Diferentes niveles de log
logger.debug("Debug info", variable=value)
logger.info("Operation completed", order_id=order.id)
logger.warning("Rate limit approaching", current=85, limit=100)
logger.error("Operation failed", error=str(e), traceback=True)

# Métricas con Prometheus
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@request_duration.time()
def process_request():
    request_count.inc()
    # Process...
```

### 12.4 Testing de Integración

```bash
# Test de carriers
curl -X POST http://localhost:8009/api/v1/carriers/quote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "carrier": "DHL",
    "origin": {"country": "CO", "city": "Bogotá", "postal_code": "110111"},
    "destination": {"country": "US", "city": "Miami", "postal_code": "33101"},
    "packages": [{"weight_kg": 2, "length_cm": 30, "width_cm": 20, "height_cm": 15}]
  }'

# Test de tracking
curl http://localhost:8009/api/v1/carriers/track/7798339175?carrier=DHL \
  -H "Authorization: Bearer YOUR_TOKEN"

# Health check
curl http://localhost:8009/health

# Métricas
curl http://localhost:8009/metrics
```

---

## RESUMEN DE CONFIGURACIÓN RÁPIDA

```bash
# 1. Setup inicial (3 minutos)
git clone repo && cd quenty
cp .env.example .env
cp .env.carriers.example .env.carriers
docker-compose up -d

# 2. Verificar servicios (30 segundos)
curl http://localhost:8000/health
curl http://localhost:8009/api/v1/carriers/status

# 3. Obtener token (30 segundos)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@quenty.com","password":"admin123"}' \
  | jq -r '.access_token')

# 4. Test rápido (30 segundos)
curl http://localhost:8009/api/v1/carriers/quote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "carrier": "DHL",
    "origin": {"country": "CO", "city": "Bogotá", "postal_code": "110111"},
    "destination": {"country": "US", "city": "Miami", "postal_code": "33101"},
    "packages": [{"weight_kg": 2, "length_cm": 30, "width_cm": 20, "height_cm": 15}]
  }'
```

## CONTACTO Y SOPORTE

**NO** me preguntes sobre:
- ✅ Cómo configurar credenciales (está todo aquí)
- ✅ Qué endpoints usar (están todos documentados)
- ✅ Cómo autenticar (ejemplos incluidos)
- ✅ Errores comunes (troubleshooting incluido)

**SÍ** pregúntame sobre:
- ❓ Nuevas features
- ❓ Optimizaciones de arquitectura
- ❓ Decisiones de negocio

---

Documentación generada el 2024. Versión 1.0.0