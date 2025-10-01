# 📊 ANÁLISIS COMPLETO: ORM Y PERSISTENCIA DE DATOS - SISTEMA QUENTY

**Fecha:** 2025-10-01
**Rama Analizada:** release/v0.1
**Enfoque:** Almacenamiento de cotizaciones, envíos, carriers y tracking

---

## 📑 ÍNDICE

1. [Arquitectura ORM General](#1-arquitectura-orm-general)
2. [Persistencia de Cotizaciones](#2-persistencia-de-cotizaciones)
3. [Persistencia de Envíos](#3-persistencia-de-envíos)
4. [Persistencia de Carriers](#4-persistencia-de-carriers)
5. [Tracking y Seguimiento](#5-tracking-y-seguimiento)
6. [Relaciones Entre Entidades](#6-relaciones-entre-entidades)
7. [Repositorios y Servicios](#7-repositorios-y-servicios)
8. [Migraciones de Base de Datos](#8-migraciones-de-base-de-datos)
9. [Análisis de Gaps y Recomendaciones](#9-análisis-de-gaps-y-recomendaciones)

---

## 1. ARQUITECTURA ORM GENERAL

### 1.1 Stack Tecnológico

**ORM:** SQLAlchemy 2.x con soporte **Async/Await**

```python
# Configuración estándar en todos los servicios
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=5,
    max_overflow=10
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()
```

**Driver:** AsyncPG (PostgreSQL asíncrono)

**Patrón de Acceso:**
```python
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 1.2 Arquitectura de Microservicios

Cada servicio tiene su **propia base de datos independiente**:

| Servicio | Base de Datos | Puerto | Propósito |
|----------|---------------|--------|-----------|
| auth-service | auth_db | 5441 | Usuarios, autenticación |
| customer | customer_db | 5433 | Perfiles de clientes |
| order | order_db | 5434 | Órdenes, productos, inventario |
| pickup | pickup_db | 5435 | Recolecciones |
| international-shipping | intl_shipping_db | 5436 | **Cotizaciones, envíos, carriers** |
| microcredit | microcredit_db | 5437 | Créditos |
| analytics | analytics_db | 5438 | Métricas |
| reverse-logistics | reverse_logistics_db | 5439 | Devoluciones |
| franchise | franchise_db | 5440 | Franquicias |

**Patrón:** Database per Service (DDD)

---

## 2. PERSISTENCIA DE COTIZACIONES

### 2.1 Modelo de Datos de Tarifas

El sistema de cotizaciones se basa en **3 niveles jerárquicos**:

#### NIVEL 1: Rate (Tarifas Base)

**Archivo:** `/microservices/international-shipping/src/models/models.py`

```python
class Rate(Base):
    """
    Tarifa base configurada por el administrador del sistema.
    Define precios por carrier, servicio y rango de peso.
    """
    __tablename__ = "rates"

    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    # Carrier y servicio
    operator_id = Column(String, nullable=False)     # 'DHL', 'FEDEX', 'UPS'
    service_id = Column(String, nullable=False)      # 'EXPRESS', 'GROUND'

    # Rango de peso aplicable
    weight_min = Column(Numeric(10, 2), nullable=False)  # Ej: 0.00
    weight_max = Column(Numeric(10, 2), nullable=False)  # Ej: 5.00

    # Precio
    fixed_fee = Column(Numeric(10, 2), nullable=False)   # Ej: 25.00 USD
    percentage = Column(Boolean, default=False)          # Si es % del valor

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)         # Soft delete

    # Relaciones
    catalog_rates = relationship("CatalogRate", back_populates="rate")
    client_ratebooks = relationship("ClientRatebook", foreign_keys="ClientRatebook.rate_id")
```

**Ejemplo de datos:**
```sql
INSERT INTO rates (operator_id, service_id, weight_min, weight_max, fixed_fee, percentage)
VALUES
    ('DHL', 'EXPRESS', 0.00, 1.00, 15.00, false),
    ('DHL', 'EXPRESS', 1.00, 5.00, 25.00, false),
    ('DHL', 'EXPRESS', 5.00, 10.00, 45.00, false),
    ('FEDEX', 'PRIORITY', 0.00, 1.00, 18.00, false);
```

#### NIVEL 2: Catalog (Catálogos de Tarifas)

```python
class Catalog(Base):
    """
    Agrupación de tarifas en catálogos.
    Permite versionar y activar/desactivar grupos de tarifas.
    """
    __tablename__ = "catalogs"

    id = Column(Integer, primary_key=True)
    catalog_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relaciones M2M con Rates
    catalog_rates = relationship("CatalogRate", back_populates="catalog")
```

#### NIVEL 3: CatalogRate (Tabla M2M)

```python
class CatalogRate(Base):
    """
    Relación Many-to-Many entre Catalogs y Rates.
    Permite que una tarifa pertenezca a múltiples catálogos.
    """
    __tablename__ = "catalog_rates"

    id = Column(Integer, primary_key=True)
    catalog_id = Column(Integer, ForeignKey("catalogs.id"), nullable=False)
    rate_id = Column(Integer, ForeignKey("rates.id"), nullable=False)

    # Permite override de precio en el catálogo
    custom_fixed_fee = Column(Numeric(10, 2))
    custom_percentage = Column(Boolean)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relaciones
    catalog = relationship("Catalog", back_populates="catalog_rates")
    rate = relationship("Rate", back_populates="catalog_rates")
```

#### NIVEL 4: ClientRatebook (Tarifas Personalizadas)

```python
class ClientRatebook(Base):
    """
    Tarifas específicas por cliente y almacén.
    Permite pricing personalizado que puede:
    1. Heredar de una Rate base (dependent=True)
    2. Ser completamente independiente (dependent=False)
    3. Pertenecer a un Catalog
    """
    __tablename__ = "client_ratebooks"

    id = Column(Integer, primary_key=True)
    ratebook_id = Column(String(255), unique=True, nullable=False)

    # Cliente y ubicación
    client_id = Column(String(255), nullable=False, index=True)
    warehouse_id = Column(String(255), nullable=False, index=True)

    # Relación con Rate/Catalog base
    rate_id = Column(Integer, ForeignKey("rates.id"), nullable=True)
    catalog_id = Column(Integer, ForeignKey("catalogs.id"), nullable=True)

    # Carrier y servicio (desnormalizado para performance)
    operator_id = Column(String, nullable=False, index=True)
    service_id = Column(String, nullable=False, index=True)
    name = Column(String(255))

    # Rango de peso
    weight_min = Column(Numeric(10, 2), nullable=False, index=True)
    weight_max = Column(Numeric(10, 2), nullable=False, index=True)

    # Precio
    fixed_fee = Column(Numeric(10, 2), nullable=False)
    percentage = Column(Boolean, default=False)

    # Comportamiento
    dependent = Column(Boolean, default=True)  # Si hereda cambios del Rate base
    is_active = Column(Boolean, default=True)

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Índice compuesto para búsqueda rápida de tarifas
    __table_args__ = (
        Index('idx_client_rate_lookup',
              'client_id', 'warehouse_id', 'operator_id', 'service_id',
              'weight_min', 'weight_max'),
        Index('idx_client_warehouse', 'client_id', 'warehouse_id'),
    )
```

### 2.2 Flujo de Cotización

#### Paso 1: Usuario solicita cotización

```python
# Request
quote_request = {
    "client_id": "CLIENT-001",
    "warehouse_id": "WH-MX-001",
    "origin": "Bogotá, CO",
    "destination": "Miami, FL, US",
    "weight_kg": 3.5,
    "dimensions": {"length": 40, "width": 30, "height": 10},
    "value_usd": 500.00,
    "carrier": "DHL",      # opcional, si no se especifica busca el mejor
    "service": "EXPRESS"   # opcional
}
```

#### Paso 2: Sistema busca tarifa aplicable

```python
from src.services.client_ratebook_service import ClientRatebookService

async def get_quote(request: QuoteRequest, db: AsyncSession):
    service = ClientRatebookService(db)

    # Busca tarifa personalizada del cliente
    rate = await service.find_matching_rate(
        client_id=request.client_id,
        warehouse_id=request.warehouse_id,
        operator_id=request.carrier,
        service_id=request.service,
        weight=request.weight_kg
    )

    if not rate:
        # Fallback a tarifa por defecto
        rate = await service.get_default_rate(
            operator_id=request.carrier,
            service_id=request.service,
            weight=request.weight_kg
        )

    # Calcula precio
    if rate.percentage:
        price = request.value_usd * (rate.fixed_fee / 100)
    else:
        price = rate.fixed_fee

    return QuoteResponse(
        carrier=request.carrier,
        service=request.service,
        price=price,
        currency="USD",
        rate_id=rate.id,
        quoted_at=datetime.utcnow()
    )
```

#### Paso 3: Query SQL ejecutada

```sql
SELECT * FROM client_ratebooks
WHERE client_id = 'CLIENT-001'
  AND warehouse_id = 'WH-MX-001'
  AND operator_id = 'DHL'
  AND service_id = 'EXPRESS'
  AND weight_min <= 3.5
  AND weight_max > 3.5
  AND deleted_at IS NULL
  AND is_active = TRUE
LIMIT 1;
```

#### Paso 4: Propagación de cambios (Dependent Rates)

**Escenario:** Admin actualiza Rate base, debe propagarse a ClientRatebooks dependientes

```python
class RateService:
    async def update_rate(self, rate_id: int, data: RateUpdate):
        rate = await self.get_by_id(rate_id)

        # Actualizar campos del Rate
        for field, value in data.dict(exclude_unset=True).items():
            setattr(rate, field, value)

        rate.updated_at = datetime.utcnow()
        await self.db.commit()

        # PROPAGACIÓN AUTOMÁTICA a ClientRatebooks dependientes
        await self.propagate_rate_update(rate)

    async def propagate_rate_update(self, rate: Rate):
        """
        Actualiza automáticamente todos los ClientRatebooks que:
        1. Referencian este Rate (rate_id = X)
        2. Tienen dependent = True
        """
        stmt = (
            update(ClientRatebook)
            .where(
                ClientRatebook.rate_id == rate.id,
                ClientRatebook.dependent == True,
                ClientRatebook.deleted_at.is_(None)
            )
            .values(
                operator_id=rate.operator_id,
                service_id=rate.service_id,
                name=rate.name,
                weight_min=rate.weight_min,
                weight_max=rate.weight_max,
                fixed_fee=rate.fixed_fee,
                percentage=rate.percentage,
                updated_at=datetime.utcnow()
            )
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount  # Número de ClientRatebooks actualizados
```

### 2.3 ❌ Gap Identificado: NO HAY TABLA DE QUOTES

**Problema:** Las cotizaciones se calculan on-demand pero **NO se persisten**.

**Consecuencias:**
- ❌ No hay historial de cotizaciones
- ❌ No se puede auditar cuántas cotizaciones se hicieron vs. cuántas se aceptaron
- ❌ No se puede analizar por qué los clientes rechazan cotizaciones
- ❌ No se puede comparar precio cotizado vs. precio final

**Recomendación:** Crear tabla de quotes históricas

```python
class RateQuote(Base):
    """
    Registro histórico de cotizaciones generadas.
    Permite auditoría y análisis de conversión.
    """
    __tablename__ = "rate_quotes"

    id = Column(Integer, primary_key=True)
    quote_id = Column(String(255), unique=True, nullable=False)

    # Cliente y contexto
    client_id = Column(String(255), nullable=False, index=True)
    warehouse_id = Column(String(255), nullable=False)
    user_id = Column(String(255))  # Quien solicitó la cotización

    # Detalles del envío cotizado
    operator_id = Column(String, nullable=False)
    service_id = Column(String, nullable=False)
    origin_country = Column(String(100))
    destination_country = Column(String(100))
    weight_kg = Column(Numeric(10, 2), nullable=False)
    value_usd = Column(Numeric(10, 2))

    # Precio cotizado
    quoted_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")

    # Fuente de la tarifa
    rate_source = Column(String(50))  # 'client_ratebook', 'catalog', 'default'
    rate_id = Column(Integer, ForeignKey("rates.id"), nullable=True)
    client_ratebook_id = Column(Integer, ForeignKey("client_ratebooks.id"), nullable=True)

    # Estado de la cotización
    status = Column(String(50), default="pending")  # pending, accepted, rejected, expired
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text)

    # Si se aceptó, referencia a la orden creada
    order_id = Column(String(255), nullable=True, index=True)

    # TTL de la cotización
    expires_at = Column(DateTime, nullable=False)  # Ej: 24 horas después de creada

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))

    __table_args__ = (
        Index('idx_quote_client_date', 'client_id', 'created_at'),
        Index('idx_quote_status', 'status', 'created_at'),
    )
```

---

## 3. PERSISTENCIA DE ENVÍOS

### 3.1 Envíos Internacionales: Manifest

**Archivo:** `/microservices/international-shipping/src/models/models.py`

```python
class Manifest(Base):
    """
    Manifiesto de envío internacional.
    Agrupa múltiples items que se envían juntos.
    """
    __tablename__ = "manifests"

    # Identificación
    id = Column(Integer, primary_key=True)
    unique_id = Column(String(255), unique=True, nullable=False)  # MAN-20250101123456
    manifest_id = Column(String(255), unique=True)                # Alias

    # Estado del workflow
    status = Column(String(50), nullable=False, default="draft")
    # Estados: draft → submitted → approved → shipped → in_transit → delivered

    # Información agregada del envío
    total_weight = Column(Float, default=0.0)
    total_volume = Column(Float, default=0.0)
    total_value = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")

    # Origen y destino
    origin_country = Column(String(100), nullable=False)
    destination_country = Column(String(100), nullable=False)
    shipping_zone = Column(String(50))  # Zone_1, Zone_2, etc.

    # Carrier asignado
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id"), nullable=True)
    carrier_service = Column(String(100))  # EXPRESS, GROUND, etc.

    # Tracking
    tracking_number = Column(String(255), unique=True, index=True)
    estimated_delivery = Column(DateTime, nullable=True)

    # Timestamps de workflow
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    # Referencias a otros servicios (Strings, no FK)
    company_id = Column(String(255), nullable=False, index=True)
    created_by = Column(String(255), nullable=False)  # user_id del Auth service

    # Relaciones
    manifest_items = relationship("ManifestItem", back_populates="manifest", cascade="all, delete-orphan")
    carrier = relationship("ShippingCarrier", foreign_keys=[carrier_id])

    __table_args__ = (
        Index('idx_manifest_company_status', 'company_id', 'status'),
        Index('idx_manifest_tracking', 'tracking_number'),
    )
```

### 3.2 Items del Manifiesto

```python
class ManifestItem(Base):
    """
    Item individual dentro de un manifiesto.
    Puede referenciar un producto del Order service.
    """
    __tablename__ = "manifest_items"

    id = Column(Integer, primary_key=True)
    manifest_id = Column(Integer, ForeignKey("manifests.id"), nullable=False, index=True)

    # Descripción del item
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    # Dimensiones y peso
    weight = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    value = Column(Float, nullable=False)

    # Información aduanera
    hs_code = Column(String(50), nullable=True)  # Harmonized System Code
    country_of_origin = Column(String(100), nullable=True)

    # Referencias externas (Strings, no FK)
    product_id = Column(Integer, nullable=True)  # Ref a Order.Product (mismo servicio? o externo?)

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación
    manifest = relationship("Manifest", back_populates="manifest_items")
```

### 3.3 Envíos Nacionales: Pickup

**Archivo:** `/microservices/pickup/src/models.py`

```python
class Pickup(Base):
    """
    Solicitud de recolección de paquetes.
    Puede ser una recolección única o recurrente.
    """
    __tablename__ = "pickups"

    # Identificación
    id = Column(Integer, primary_key=True)
    pickup_id = Column(String(255), unique=True, nullable=False)  # PCK-20250101123456

    # Cliente
    customer_id = Column(String(255), nullable=False, index=True)  # Ref a Auth.User

    # Tipo y estado
    pickup_type = Column(String(50), nullable=False)  # on_demand, scheduled, recurring, express
    status = Column(String(50), nullable=False, default="scheduled")
    # Estados: scheduled → assigned → in_progress → completed → cancelled → failed

    # Programación
    pickup_date = Column(Date, nullable=False)
    time_window_start = Column(Time, nullable=True)
    time_window_end = Column(Time, nullable=True)
    actual_pickup_time = Column(DateTime, nullable=True)

    # Ubicación
    pickup_address = Column(Text, nullable=False)
    pickup_latitude = Column(Float, nullable=True)
    pickup_longitude = Column(Float, nullable=True)
    postal_code = Column(String(20))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default="MX")

    # Contacto
    contact_name = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(255), nullable=True)

    # Información de paquetes
    package_count = Column(Integer, nullable=False)
    estimated_weight_kg = Column(Float, nullable=False)
    actual_weight_kg = Column(Float, nullable=True)  # Llenado después del pickup
    special_instructions = Column(Text)

    # Asignación logística
    assigned_driver_id = Column(String(255), nullable=True, index=True)
    assigned_route_id = Column(Integer, ForeignKey("pickup_routes.id"), nullable=True)

    # Financiero
    pickup_cost = Column(Float, nullable=True)
    currency = Column(String(10), default="MXN")

    # Referencias externas
    order_id = Column(String(255), nullable=True, index=True)  # Ref a Order.Order

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    route = relationship("PickupRoute", back_populates="pickups")
    packages = relationship("PickupPackage", back_populates="pickup", cascade="all, delete-orphan")
    attempts = relationship("PickupAttempt", back_populates="pickup")

    __table_args__ = (
        Index('idx_pickup_date_status', 'pickup_date', 'status'),
        Index('idx_pickup_customer', 'customer_id', 'created_at'),
    )
```

### 3.4 Paquetes de Recolección

```python
class PickupPackage(Base):
    """
    Paquete individual a recolectar.
    Genera tracking number después de la recolección exitosa.
    """
    __tablename__ = "pickup_packages"

    id = Column(Integer, primary_key=True)
    package_id = Column(String(255), unique=True, nullable=False)
    pickup_id = Column(Integer, ForeignKey("pickups.id"), nullable=False, index=True)

    # Descripción del paquete
    description = Column(String(500), nullable=False)
    category = Column(String(100))  # electronics, clothing, food, etc.

    # Dimensiones
    weight_kg = Column(Float, nullable=False)
    length_cm = Column(Float)
    width_cm = Column(Float)
    height_cm = Column(Float)

    # Características especiales
    is_fragile = Column(Boolean, default=False)
    requires_signature = Column(Boolean, default=False)
    insurance_value = Column(Float, nullable=True)

    # Tracking (generado DESPUÉS del pickup)
    tracking_number = Column(String(255), unique=True, nullable=True, index=True)

    # Destino final
    destination_address = Column(Text, nullable=True)
    destination_city = Column(String(100))
    destination_state = Column(String(100))
    destination_postal_code = Column(String(20))
    destination_country = Column(String(100), default="MX")
    destination_contact_name = Column(String(255))
    destination_contact_phone = Column(String(50))

    # Referencias externas
    order_id = Column(String(255), nullable=True, index=True)  # Ref a Order.Order

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación
    pickup = relationship("Pickup", back_populates="packages")
```

### 3.5 Flujo de Creación de Envío

```python
# 1. Cliente crea una orden
order = Order(
    order_number="ORD-20250101123456",
    customer_id="CUST-001",
    total_amount=500.00,
    status="pending"
)

# 2. Sistema crea un manifiesto para envío internacional
manifest = Manifest(
    unique_id="MAN-20250101123456",
    origin_country="MX",
    destination_country="US",
    total_value=500.00,
    company_id="COMP-001",
    created_by="USER-001",
    status="draft"
)

# 3. Agregar items al manifiesto
manifest_item = ManifestItem(
    manifest_id=manifest.id,
    description="Electronics - Laptop",
    quantity=1,
    weight=3.5,
    value=500.00,
    hs_code="8471.30.01"
)
manifest.manifest_items.append(manifest_item)

# 4. Usuario solicita recolección
pickup = Pickup(
    pickup_id="PCK-20250101123456",
    customer_id="CUST-001",
    pickup_type="scheduled",
    pickup_date=date(2025, 1, 2),
    pickup_address="Calle 123, Bogotá",
    contact_name="Juan Pérez",
    contact_phone="+573001234567",
    package_count=1,
    estimated_weight_kg=3.5,
    order_id="ORD-20250101123456"  # Referencia a la orden
)

# 5. Crear paquete vinculado al pickup
package = PickupPackage(
    package_id="PKG-001",
    pickup_id=pickup.id,
    description="Laptop Dell XPS 15",
    weight_kg=3.5,
    is_fragile=True,
    order_id="ORD-20250101123456"
)

# 6. Después del pickup exitoso, se genera tracking
package.tracking_number = "QTYTRK-20250102001"
manifest.tracking_number = "QTYTRK-20250102001"  # Mismo tracking
manifest.status = "shipped"

await db.commit()
```

---

## 4. PERSISTENCIA DE CARRIERS

### 4.1 Modelo ShippingCarrier

```python
class ShippingCarrier(Base):
    """
    Transportista/Carrier configurado en el sistema.
    Almacena información básica y configuración de API.
    """
    __tablename__ = "shipping_carriers"

    id = Column(Integer, primary_key=True)

    # Identificación
    name = Column(String(255), nullable=False)  # "DHL Express"
    code = Column(String(50), unique=True, nullable=False)  # "DHL"

    # Configuración API
    api_endpoint = Column(String(500), nullable=True)  # Base URL
    api_key = Column(String(500), nullable=True)       # ⚠️ PLAINTEXT - RIESGO DE SEGURIDAD
    api_username = Column(String(255), nullable=True)
    api_password = Column(String(255), nullable=True)  # ⚠️ PLAINTEXT - RIESGO DE SEGURIDAD

    # Capacidades
    active = Column(Boolean, default=True)
    supported_services = Column(JSON, default=list)
    # Ejemplo: ["EXPRESS_WORLDWIDE", "EXPRESS_12:00", "GROUND"]

    supported_countries = Column(JSON, default=list)
    # Ejemplo: ["US", "MX", "CO", "CA"]

    # Configuración adicional
    config = Column(JSON, default=dict)
    # Ejemplo: {"sandbox": true, "account_number": "123456", "timeout": 30}

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
```

**Ejemplo de datos:**
```sql
INSERT INTO shipping_carriers (name, code, api_endpoint, api_key, supported_services, active)
VALUES
    ('DHL Express', 'DHL', 'https://api.dhl.com/v1', 'xxx_api_key_xxx',
     '["EXPRESS_WORLDWIDE", "EXPRESS_12:00", "EXPRESS_9:00"]', true),

    ('FedEx International', 'FEDEX', 'https://api.fedex.com/v1', 'yyy_api_key_yyy',
     '["INTERNATIONAL_PRIORITY", "INTERNATIONAL_ECONOMY", "INTERNATIONAL_FIRST"]', true),

    ('UPS Worldwide', 'UPS', 'https://api.ups.com/v1', 'zzz_api_key_zzz',
     '["EXPRESS_PLUS", "EXPRESS', 'EXPRESS_SAVER"]', true),

    ('Servientrega', 'SERVIENTREGA', 'https://api.servientrega.com.co', null,
     '["NACIONAL_ESTANDAR", "NACIONAL_EXPRESS"]', true);
```

### 4.2 ⚠️ PROBLEMA CRÍTICO: Credenciales en Texto Plano

**Riesgo de Seguridad:**
- Las credenciales de API están almacenadas en **texto plano** en la columna `api_key`
- Cualquier persona con acceso a la base de datos puede ver las credenciales
- Backup de BD expone credenciales

**Recomendación: Implementar Encriptación**

```python
from cryptography.fernet import Fernet
import base64

class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"

    # ... otros campos ...

    # Cambiar a LargeBinary para almacenar datos encriptados
    api_key_encrypted = Column(LargeBinary, nullable=True)
    api_password_encrypted = Column(LargeBinary, nullable=True)

    # Métodos helper para encriptar/desencriptar
    def set_api_key(self, plaintext_key: str, encryption_key: bytes):
        """Encripta y almacena el API key"""
        f = Fernet(encryption_key)
        self.api_key_encrypted = f.encrypt(plaintext_key.encode())

    def get_api_key(self, encryption_key: bytes) -> str:
        """Desencripta y retorna el API key"""
        f = Fernet(encryption_key)
        return f.decrypt(self.api_key_encrypted).decode()
```

**Uso:**
```python
# Generar encryption key (una sola vez, almacenar en variable de entorno)
encryption_key = Fernet.generate_key()
# ENCRYPTION_KEY=b'SVZkwOLRWLSm6XJbDCyIVbHe-d5rX6cp2LBKPT4EavI='

# Almacenar credenciales
carrier = ShippingCarrier(name="DHL Express", code="DHL")
carrier.set_api_key("secret_api_key_123", encryption_key)
await db.commit()

# Recuperar credenciales
api_key = carrier.get_api_key(encryption_key)
```

---

## 5. TRACKING Y SEGUIMIENTO

### 5.1 ❌ Gap: NO HAY TABLA DE TRACKING EVENTS

**Estado actual:**
- `Manifest.tracking_number` existe (String)
- `PickupPackage.tracking_number` existe (String)
- El tracking actual se consulta de APIs externas (DHL, FedEx, etc.)
- **NO se persisten los eventos de tracking en la base de datos**

**Consecuencias:**
- ❌ No hay historial de tracking cuando el carrier elimina datos antiguos
- ❌ No se puede hacer analytics de tiempos de tránsito
- ❌ No se puede identificar patrones de retrasos por carrier/ruta
- ❌ Dependencia total de APIs externas

**Recomendación: Crear tabla de TrackingEvent**

```python
class TrackingEvent(Base):
    """
    Evento de tracking de un envío.
    Persiste todos los cambios de estado reportados por el carrier.
    """
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(255), unique=True, nullable=False)

    # Identificación del envío
    tracking_number = Column(String(255), nullable=False, index=True)
    carrier_code = Column(String(50), nullable=False)  # DHL, FEDEX, UPS

    # Evento
    event_type = Column(String(50), nullable=False)
    # pickup, in_transit, out_for_delivery, delivered, exception, returned

    event_description = Column(Text, nullable=False)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)

    # Ubicación
    location_city = Column(String(100))
    location_state = Column(String(100))
    location_country = Column(String(100))
    location_latitude = Column(Float)
    location_longitude = Column(Float)
    facility_name = Column(String(255))

    # Detalles adicionales
    signature_required = Column(Boolean, default=False)
    signed_by = Column(String(255))
    photo_url = Column(String(1024))  # Proof of delivery

    # Metadata del carrier
    carrier_event_code = Column(String(50))  # Código interno del carrier
    raw_payload = Column(JSON)  # Respuesta completa del carrier para debugging

    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    received_via = Column(String(50))  # 'webhook', 'polling', 'manual'

    __table_args__ = (
        Index('idx_tracking_events_number', 'tracking_number', 'event_timestamp'),
        Index('idx_tracking_events_type', 'event_type', 'created_at'),
        Index('idx_tracking_carrier', 'carrier_code', 'event_timestamp'),
    )
```

**Uso:**
```python
# Webhook recibe evento de DHL
webhook_data = {
    "tracking_number": "DHL987654321",
    "status": "in_transit",
    "location": "Miami Hub",
    "timestamp": "2025-01-02T15:30:00Z"
}

# Persistir evento
event = TrackingEvent(
    event_id=f"EVT-{uuid.uuid4()}",
    tracking_number=webhook_data["tracking_number"],
    carrier_code="DHL",
    event_type="in_transit",
    event_description="Shipment arrived at Miami Hub",
    event_timestamp=webhook_data["timestamp"],
    location_city="Miami",
    location_state="FL",
    location_country="US",
    facility_name="DHL Miami Hub",
    raw_payload=webhook_data,
    received_via="webhook"
)

await db.add(event)
await db.commit()

# Actualizar estado en Manifest
manifest = await db.get(Manifest, manifest_id)
manifest.status = "in_transit"
manifest.updated_at = datetime.utcnow()
await db.commit()
```

---

## 6. RELACIONES ENTRE ENTIDADES

### 6.1 Diagrama Entidad-Relación (International Shipping)

```
┌────────────────────┐
│ ShippingCarrier    │
│  - id (PK)         │
│  - code (UNIQUE)   │
│  - api_endpoint    │
│  - api_key         │
└──────┬─────────────┘
       │ (referenced by operator_id STRING)
       ↓
┌────────────────────┐
│      Rate          │
│  - id (PK)         │
│  - operator_id ────┼──→ ShippingCarrier.code (no FK real)
│  - service_id      │
│  - weight_min      │
│  - weight_max      │
│  - fixed_fee       │
└──────┬─────────────┘
       │
       │ M:N via CatalogRate
       ↓
┌────────────────────┐      ┌────────────────────┐
│   CatalogRate      │──────│     Catalog        │
│  - catalog_id (FK) │      │  - id (PK)         │
│  - rate_id (FK)    │      │  - name            │
└────────────────────┘      │  - is_active       │
                            └────────────────────┘
       ↓
┌────────────────────┐
│  ClientRatebook    │
│  - id (PK)         │
│  - client_id       │ (String, no FK a Customer service)
│  - warehouse_id    │ (String, no FK)
│  - rate_id (FK)    │──→ Rate.id (OPCIONAL)
│  - catalog_id (FK) │──→ Catalog.id (OPCIONAL)
│  - operator_id     │ (desnormalizado para performance)
│  - service_id      │ (desnormalizado)
│  - weight_min/max  │ (desnormalizado)
│  - fixed_fee       │ (puede override Rate base)
│  - dependent       │ (si hereda cambios del Rate)
└────────────────────┘
       ↓ (usado para cotizar, NO hay FK)
┌────────────────────┐
│  [Order Service]   │
│  Order             │
│  - quoted_price    │ (valor calculado, NO relación directa)
└────────────────────┘
       ↓ (String reference)
┌────────────────────┐      ┌────────────────────┐
│    Manifest        │──1:M─│   ManifestItem     │
│  - id (PK)         │      │  - id (PK)         │
│  - unique_id       │      │  - manifest_id(FK) │
│  - tracking_number │      │  - description     │
│  - carrier_id (FK) │──────┼──→ ShippingCarrier.id
│  - status          │      │  - weight          │
│  - company_id      │      │  - hs_code         │
│  - created_by      │      │  - product_id      │ (INT, pero ¿FK a dónde?)
└────────────────────┘      └────────────────────┘
       ↓ (referenced by envio_id STRING)
┌────────────────────┐      ┌────────────────────┐
│   DocumentType     │──1:M─│     Document       │
│  - id (PK)         │      │  - id (PK)         │
│  - code (UNIQUE)   │      │  - document_type_id│
│  - name            │      │  - envio_id        │ (String, ref a Manifest.unique_id)
└────────────────────┘      │  - client_id       │ (String, ref a otro servicio)
                            │  - storage_url     │
                            └────────────────────┘

[Tracking Events - NO EXISTE actualmente]
┌────────────────────┐
│  TrackingEvent     │ ⚠️ RECOMENDADO
│  - tracking_number │──→ Manifest.tracking_number (no FK)
│  - event_type      │
│  - event_timestamp │
│  - location        │
└────────────────────┘
```

### 6.2 Relaciones Cross-Service (Referencias String)

```
┌─────────────────────────────────────────────────┐
│            AUTH SERVICE (auth_db)               │
│  ┌──────────────┐       ┌──────────────┐       │
│  │    User      │       │   Company    │       │
│  │  - id        │       │  - company_id│       │
│  │  - unique_id │       └──────────────┘       │
│  └──────────────┘                               │
└───────┬─────────────────────┬───────────────────┘
        │ (String ref)        │ (String ref)
        ↓                     ↓
┌─────────────────────┐ ┌─────────────────────┐
│ CUSTOMER SERVICE    │ │  INT. SHIPPING SVC  │
│ CustomerProfile     │ │  Manifest           │
│  - user_id (str)    │ │  - company_id (str) │
│                     │ │  - created_by (str) │
└─────────────────────┘ └─────────────────────┘
        ↓ (String ref)        ↓ (String ref)
┌─────────────────────┐ ┌─────────────────────┐
│   ORDER SERVICE     │ │   PICKUP SERVICE    │
│  Order              │ │  Pickup             │
│  - customer_id(str) │ │  - customer_id(str) │
│  - order_number     │ │  - order_id (str)   │
└─────────────────────┘ └─────────┬───────────┘
        ↓ (String ref)            ↓ (String ref)
┌─────────────────────┐ ┌─────────────────────┐
│  PICKUP SERVICE     │ │  ANALYTICS SERVICE  │
│  PickupPackage      │ │  Metric             │
│  - order_id (str)   │ │  - source_entity_id │
│  - tracking_number  │ │  - tags (JSON)      │
└─────────────────────┘ └─────────────────────┘
```

**Características:**
- ✅ Cada servicio es independiente
- ✅ No hay Foreign Keys entre bases de datos de diferentes servicios
- ✅ Las relaciones se mantienen mediante IDs de tipo String
- ⚠️ No hay integridad referencial automática
- ⚠️ La consistencia debe manejarse a nivel de aplicación
- ⚠️ No se pueden hacer JOINs SQL entre servicios

---

## 7. REPOSITORIOS Y SERVICIOS

### 7.1 Patrón Base Service

Todos los servicios siguen un patrón similar:

```python
# Archivo: /microservices/international-shipping/src/services/base_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete as sql_delete
from datetime import datetime

class BaseService:
    """
    Servicio base con operaciones CRUD comunes.
    Todos los servicios heredan de esta clase.
    """

    def __init__(self, db: AsyncSession, model):
        self.db = db
        self.model = model

    async def get_by_id(self, id: int):
        """Obtiene un registro por ID (filtra soft deletes)"""
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None)  # Excluye registros eliminados
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0):
        """Obtiene todos los registros activos (paginados)"""
        stmt = (
            select(self.model)
            .where(self.model.deleted_at.is_(None))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs):
        """Crea un nuevo registro"""
        new_record = self.model(**kwargs)
        self.db.add(new_record)
        await self.db.commit()
        await self.db.refresh(new_record)
        return new_record

    async def update(self, id: int, **kwargs):
        """Actualiza un registro existente"""
        record = await self.get_by_id(id)
        if not record:
            raise ValueError(f"{self.model.__name__} with id {id} not found")

        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)

        record.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def soft_delete(self, id: int):
        """Elimina lógicamente un registro (soft delete)"""
        record = await self.get_by_id(id)
        if not record:
            raise ValueError(f"{self.model.__name__} with id {id} not found")

        record.deleted_at = datetime.utcnow()
        await self.db.commit()
        return record

    async def hard_delete(self, id: int):
        """Elimina físicamente un registro de la BD"""
        stmt = sql_delete(self.model).where(self.model.id == id)
        await self.db.execute(stmt)
        await self.db.commit()
```

### 7.2 RateService - Gestión de Tarifas

```python
# Archivo: /microservices/international-shipping/src/services/rate_service.py

from src.services.base_service import BaseService
from src.models.models import Rate, ClientRatebook
from sqlalchemy import select, update

class RateService(BaseService):
    """Servicio para gestión de tarifas base"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Rate)

    async def get_rates_by_operator(self, operator_id: str, service_id: str = None):
        """Obtiene todas las tarifas de un operador"""
        stmt = select(Rate).where(
            Rate.operator_id == operator_id,
            Rate.deleted_at.is_(None)
        )

        if service_id:
            stmt = stmt.where(Rate.service_id == service_id)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def find_rate_for_weight(
        self,
        operator_id: str,
        service_id: str,
        weight: float
    ) -> Rate:
        """
        Encuentra la tarifa que aplica para un peso específico.
        La tarifa debe cumplir: weight_min <= weight < weight_max
        """
        stmt = select(Rate).where(
            Rate.operator_id == operator_id,
            Rate.service_id == service_id,
            Rate.weight_min <= weight,
            Rate.weight_max > weight,
            Rate.deleted_at.is_(None)
        ).limit(1)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_rate(self, rate_id: int, data: dict):
        """
        Actualiza una tarifa Y propaga cambios a ClientRatebooks dependientes
        """
        # Actualizar el Rate
        rate = await self.update(rate_id, **data)

        # Propagar a ClientRatebooks que tienen dependent=True
        await self.propagate_rate_update(rate)

        return rate

    async def propagate_rate_update(self, rate: Rate):
        """
        Propaga cambios de un Rate a todos los ClientRatebooks que dependen de él.
        Solo actualiza ClientRatebooks con dependent=True.
        """
        stmt = (
            update(ClientRatebook)
            .where(
                ClientRatebook.rate_id == rate.id,
                ClientRatebook.dependent == True,
                ClientRatebook.deleted_at.is_(None)
            )
            .values(
                operator_id=rate.operator_id,
                service_id=rate.service_id,
                name=rate.name,
                weight_min=rate.weight_min,
                weight_max=rate.weight_max,
                fixed_fee=rate.fixed_fee,
                percentage=rate.percentage,
                updated_at=datetime.utcnow()
            )
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        rows_updated = result.rowcount
        print(f"Propagated rate update to {rows_updated} ClientRatebooks")

        return rows_updated
```

### 7.3 ClientRatebookService - Cotizaciones Personalizadas

```python
# Archivo: /microservices/international-shipping/src/services/client_ratebook_service.py

from src.services.base_service import BaseService
from src.models.models import ClientRatebook, Rate

class ClientRatebookService(BaseService):
    """Servicio para tarifas personalizadas por cliente"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, ClientRatebook)

    async def find_matching_rate(
        self,
        client_id: str,
        warehouse_id: str,
        operator_id: str,
        service_id: str,
        weight: float
    ) -> ClientRatebook:
        """
        Busca la tarifa personalizada que aplica para:
        - Cliente específico
        - Almacén específico
        - Operador/servicio específico
        - Peso específico
        """
        stmt = select(ClientRatebook).where(
            ClientRatebook.client_id == client_id,
            ClientRatebook.warehouse_id == warehouse_id,
            ClientRatebook.operator_id == operator_id,
            ClientRatebook.service_id == service_id,
            ClientRatebook.weight_min <= weight,
            ClientRatebook.weight_max > weight,
            ClientRatebook.is_active == True,
            ClientRatebook.deleted_at.is_(None)
        ).limit(1)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_client_rates(
        self,
        client_id: str,
        warehouse_id: str = None
    ):
        """Obtiene todas las tarifas de un cliente"""
        stmt = select(ClientRatebook).where(
            ClientRatebook.client_id == client_id,
            ClientRatebook.deleted_at.is_(None)
        )

        if warehouse_id:
            stmt = stmt.where(ClientRatebook.warehouse_id == warehouse_id)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def assign_rate_to_client(
        self,
        rate_id: int,
        client_id: str,
        warehouse_id: str,
        custom_fixed_fee: float = None,
        dependent: bool = True
    ):
        """
        Asigna una tarifa base a un cliente específico.

        Args:
            rate_id: ID del Rate base
            client_id: ID del cliente
            warehouse_id: ID del almacén
            custom_fixed_fee: Precio personalizado (opcional)
            dependent: Si hereda cambios del Rate base (default: True)
        """
        # Obtener el Rate base
        rate = await self.db.get(Rate, rate_id)
        if not rate:
            raise ValueError(f"Rate {rate_id} not found")

        # Crear ClientRatebook
        client_rate = ClientRatebook(
            ratebook_id=f"CRB-{client_id}-{warehouse_id}-{rate.id}",
            client_id=client_id,
            warehouse_id=warehouse_id,
            rate_id=rate.id,
            operator_id=rate.operator_id,
            service_id=rate.service_id,
            name=rate.name,
            weight_min=rate.weight_min,
            weight_max=rate.weight_max,
            fixed_fee=custom_fixed_fee or rate.fixed_fee,
            percentage=rate.percentage,
            dependent=dependent,
            is_active=True
        )

        self.db.add(client_rate)
        await self.db.commit()
        await self.db.refresh(client_rate)

        return client_rate

    async def make_independent(self, client_ratebook_id: int):
        """
        Hace que un ClientRatebook sea independiente (no hereda cambios).
        Útil cuando el cliente negocia una tarifa fija.
        """
        client_rate = await self.get_by_id(client_ratebook_id)
        client_rate.dependent = False
        client_rate.rate_id = None  # Rompe la relación con el Rate base
        await self.db.commit()

        return client_rate
```

### 7.4 ManifestService - Gestión de Envíos

```python
# Archivo: /microservices/international-shipping/src/services/manifest_service.py

from src.services.base_service import BaseService
from src.models.models import Manifest, ManifestItem
from sqlalchemy import select
from sqlalchemy.orm import selectinload

class ManifestService(BaseService):
    """Servicio para gestión de manifiestos de envío"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Manifest)

    async def get_manifest_with_items(self, manifest_id: int):
        """Obtiene un manifiesto con todos sus items (eager loading)"""
        stmt = (
            select(Manifest)
            .where(Manifest.id == manifest_id)
            .options(selectinload(Manifest.manifest_items))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_manifest(
        self,
        company_id: str,
        created_by: str,
        origin_country: str,
        destination_country: str,
        items: list[dict]
    ):
        """
        Crea un manifiesto con sus items.

        Args:
            company_id: ID de la empresa
            created_by: ID del usuario que crea
            origin_country: País de origen
            destination_country: País de destino
            items: Lista de items [{"description": "...", "weight": 1.5, ...}]
        """
        # Generar unique_id
        unique_id = f"MAN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Calcular totales
        total_weight = sum(item.get("weight", 0) for item in items)
        total_volume = sum(item.get("volume", 0) for item in items)
        total_value = sum(item.get("value", 0) for item in items)

        # Crear manifiesto
        manifest = Manifest(
            unique_id=unique_id,
            status="draft",
            origin_country=origin_country,
            destination_country=destination_country,
            total_weight=total_weight,
            total_volume=total_volume,
            total_value=total_value,
            company_id=company_id,
            created_by=created_by
        )

        self.db.add(manifest)
        await self.db.flush()  # Para obtener el manifest.id

        # Crear items
        for item_data in items:
            item = ManifestItem(
                manifest_id=manifest.id,
                description=item_data["description"],
                quantity=item_data.get("quantity", 1),
                weight=item_data["weight"],
                volume=item_data.get("volume"),
                value=item_data["value"],
                hs_code=item_data.get("hs_code"),
                country_of_origin=item_data.get("country_of_origin"),
                product_id=item_data.get("product_id")
            )
            manifest.manifest_items.append(item)

        await self.db.commit()
        await self.db.refresh(manifest)

        return manifest

    async def update_manifest_status(
        self,
        manifest_id: int,
        new_status: str,
        tracking_number: str = None
    ):
        """
        Actualiza el estado de un manifiesto.
        Valida las transiciones de estado permitidas.
        """
        valid_transitions = {
            "draft": ["submitted", "cancelled"],
            "submitted": ["approved", "rejected"],
            "approved": ["shipped"],
            "shipped": ["in_transit"],
            "in_transit": ["delivered", "exception"],
            "exception": ["in_transit", "returned"]
        }

        manifest = await self.get_by_id(manifest_id)
        current_status = manifest.status

        # Validar transición
        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(
                f"Invalid status transition: {current_status} → {new_status}"
            )

        # Actualizar estado
        manifest.status = new_status

        # Actualizar timestamps según el estado
        if new_status == "submitted":
            manifest.submitted_at = datetime.utcnow()
        elif new_status == "approved":
            manifest.approved_at = datetime.utcnow()
        elif new_status == "shipped":
            manifest.shipped_at = datetime.utcnow()
            if tracking_number:
                manifest.tracking_number = tracking_number
        elif new_status == "delivered":
            manifest.delivered_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(manifest)

        return manifest

    async def get_manifests_by_company(
        self,
        company_id: str,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ):
        """Obtiene manifiestos de una empresa (paginados)"""
        stmt = select(Manifest).where(Manifest.company_id == company_id)

        if status:
            stmt = stmt.where(Manifest.status == status)

        stmt = stmt.order_by(Manifest.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return result.scalars().all()
```

---

## 8. MIGRACIONES DE BASE DE DATOS

### 8.1 Estado Actual de Migraciones

**Servicios con Alembic configurado:**
- ✅ auth-service
- ✅ customer
- ✅ international-shipping
- ✅ microcredit
- ✅ order
- ✅ pickup

**Problema:** Las carpetas `alembic/versions/` están **VACÍAS** o tienen muy pocas migraciones.

**Método actual:** Se usa `Base.metadata.create_all()` en el startup:

```python
# Archivo: /microservices/international-shipping/src/main.py

@app.on_event("startup")
async def startup_event():
    await create_tables()  # ⚠️ Crea tablas en runtime
    await register_with_consul()
    logger.info("International Shipping Service started")

# Archivo: /microservices/international-shipping/src/database.py

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # ⚠️ Anti-patrón para producción
```

### 8.2 ⚠️ Problemas de usar create_all()

1. **No hay control de versiones** del esquema de BD
2. **No se pueden hacer rollbacks** de cambios de esquema
3. **Dificulta deployments** en producción (¿qué cambios se aplicarán?)
4. **Puede causar pérdida de datos** si se remueven columnas
5. **No hay trazabilidad** de cambios en el esquema

### 8.3 ✅ Implementar Migraciones con Alembic

#### Paso 1: Generar migración inicial

```bash
cd /home/jhunter/devel/QUENTY/Quenty/microservices/international-shipping

# Generar migración automática
alembic revision --autogenerate -m "Initial schema: rates, catalogs, manifests"

# Esto crea: alembic/versions/20250101_1200_abcdef123456_initial_schema.py
```

#### Paso 2: Revisar y editar migración generada

```python
# Archivo: alembic/versions/20250101_1200_xxx_initial_schema.py

"""Initial schema: rates, catalogs, manifests

Revision ID: abcdef123456
Revises:
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abcdef123456'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.create_table('rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('operator_id', sa.String(), nullable=False),
        sa.Column('service_id', sa.String(), nullable=False),
        sa.Column('weight_min', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('weight_max', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('fixed_fee', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('percentage', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rates_id'), 'rates', ['id'], unique=False)

    # ... más tablas ...
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic ###
    op.drop_index(op.f('ix_rates_id'), table_name='rates')
    op.drop_table('rates')
    # ... más tablas ...
    # ### end Alembic commands ###
```

#### Paso 3: Aplicar migración

```bash
# Aplicar migraciones pendientes
alembic upgrade head

# Ver historial de migraciones
alembic history

# Rollback una migración
alembic downgrade -1
```

#### Paso 4: Remover create_all() del startup

```python
# Archivo: /microservices/international-shipping/src/main.py

@app.on_event("startup")
async def startup_event():
    # await create_tables()  # ❌ REMOVER ESTO
    await register_with_consul()
    logger.info("International Shipping Service started")
```

### 8.4 Workflow de Migraciones en Equipo

```bash
# Developer 1: Agrega nueva columna a Rate
# 1. Editar modelo
class Rate(Base):
    # ... campos existentes ...
    discount_percentage = Column(Numeric(5, 2), default=0.0)  # NUEVO

# 2. Generar migración
alembic revision --autogenerate -m "Add discount_percentage to rates"

# 3. Commit cambios
git add alembic/versions/20250102_xxx_add_discount.py
git add src/models/models.py
git commit -m "feat: Add discount_percentage to rates"
git push

# Developer 2: Pull cambios
git pull

# 4. Aplicar migraciones
alembic upgrade head

# En producción:
docker exec quenty-international-shipping alembic upgrade head
```

---

## 9. ANÁLISIS DE GAPS Y RECOMENDACIONES

### 9.1 Gaps Críticos Identificados

#### 🔴 CRÍTICO

**1. NO HAY TABLA DE QUOTES (Cotizaciones Históricas)**
- **Problema:** Las cotizaciones se calculan on-demand y no se persisten
- **Impacto:** No hay auditoría, no se puede analizar conversión, no hay historial
- **Solución:** Implementar tabla `RateQuote` (ver sección 2.3)

**2. Credenciales de Carriers en Texto Plano**
- **Problema:** `ShippingCarrier.api_key` almacena credenciales sin encriptar
- **Impacto:** Riesgo de seguridad alto, exposición de credenciales en backups
- **Solución:** Implementar encriptación AES-256 (ver sección 4.2)

**3. NO HAY TABLA DE TRACKING EVENTS**
- **Problema:** No se persisten eventos de tracking, dependencia total de APIs externas
- **Impacto:** Pérdida de historial, no analytics, no detección de patrones
- **Solución:** Implementar tabla `TrackingEvent` (ver sección 5.1)

**4. Migraciones NO Implementadas**
- **Problema:** Se usa `create_all()` en startup en lugar de Alembic
- **Impacto:** No hay control de versiones, rollbacks difíciles, riesgo en producción
- **Solución:** Generar migraciones iniciales y workflow de Alembic (ver sección 8)

#### 🟡 IMPORTANTE

**5. Relaciones Cross-Service Débiles**
- **Problema:** Referencias String sin Foreign Keys entre servicios
- **Impacto:** No hay integridad referencial, posibles IDs huérfanos
- **Solución:** Implementar validación a nivel de aplicación, eventos de sincronización

**6. Soft Deletes Inconsistentes**
- **Problema:** International Shipping usa soft delete, Order/Pickup no
- **Impacto:** Inconsistencia en comportamiento, dificultad de auditoría
- **Solución:** Estandarizar soft delete en todos los servicios

**7. Falta Tabla de Audit Log**
- **Problema:** No hay registro de quién cambió qué y cuándo (excepto updated_at)
- **Impacto:** No hay trazabilidad completa de cambios
- **Solución:** Implementar tabla genérica de audit_log

**8. Índices Faltantes**
- **Problema:** Algunos queries comunes no tienen índices
- **Impacto:** Performance degradado en búsquedas de cotizaciones
- **Solución:** Agregar índices compuestos (ver sección 9.3)

#### 🟢 MEJORAS

**9. Sin Particionamiento de Tablas**
- **Problema:** Tablas grandes (Metrics, TrackingEvents) sin particionamiento
- **Impacto:** Queries lentas al crecer los datos
- **Solución:** Implementar particionamiento por fecha (PARTITION BY RANGE)

**10. Cache No Implementado**
- **Problema:** Cotizaciones frecuentes golpean siempre la BD
- **Impacto:** Performance subóptimo
- **Solución:** Implementar cache Redis para cotizaciones (TTL: 15 min)

### 9.2 Roadmap de Implementación

#### Sprint 1-2 (Crítico - 2 semanas)
1. ✅ Implementar tabla `RateQuote`
2. ✅ Encriptar credenciales de carriers
3. ✅ Generar migraciones iniciales con Alembic
4. ✅ Remover `create_all()` del startup

#### Sprint 3-4 (Importante - 2 semanas)
5. ✅ Implementar tabla `TrackingEvent`
6. ✅ Estandarizar soft deletes
7. ✅ Agregar índices faltantes
8. ✅ Implementar audit log genérico

#### Sprint 5-6 (Mejoras - 2 semanas)
9. ✅ Cache Redis para cotizaciones
10. ✅ Particionamiento de tablas grandes
11. ✅ Validación cross-service
12. ✅ Monitoreo de integridad referencial

### 9.3 Índices Recomendados

```sql
-- International Shipping

-- Búsqueda de tarifas por cliente
CREATE INDEX idx_client_rate_lookup ON client_ratebooks (
    client_id, warehouse_id, operator_id, service_id, weight_min, weight_max
);

-- Búsqueda de manifiestos por empresa y estado
CREATE INDEX idx_manifest_company_status ON manifests (company_id, status, created_at);

-- Tracking numbers
CREATE INDEX idx_manifest_tracking ON manifests (tracking_number) WHERE tracking_number IS NOT NULL;

-- Pickup

-- Búsqueda de pickups por fecha y estado
CREATE INDEX idx_pickup_date_status ON pickups (pickup_date, status);

-- Búsqueda por cliente
CREATE INDEX idx_pickup_customer ON pickups (customer_id, created_at);

-- Tracking numbers de paquetes
CREATE INDEX idx_package_tracking ON pickup_packages (tracking_number) WHERE tracking_number IS NOT NULL;

-- Analytics

-- Búsqueda de métricas por tipo y fecha
CREATE INDEX idx_metrics_type_timestamp ON metrics (metric_type, timestamp DESC);

-- Tags JSON (requiere PostgreSQL + GIN)
CREATE INDEX idx_metrics_tags ON metrics USING GIN (tags);

-- Tracking Events (nueva tabla)

-- Búsqueda por tracking number y fecha
CREATE INDEX idx_tracking_events_number ON tracking_events (tracking_number, event_timestamp DESC);

-- Búsqueda por tipo de evento
CREATE INDEX idx_tracking_events_type ON tracking_events (event_type, created_at);
```

### 9.4 Ejemplo de Audit Log Genérico

```python
class AuditLog(Base):
    """
    Registro genérico de auditoría para todos los cambios en el sistema.
    Captura quién, qué, cuándo y cómo cambió.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    audit_id = Column(String(255), unique=True, nullable=False)

    # Qué se cambió
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(255), nullable=False, index=True)

    # Tipo de operación
    operation = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE

    # Quién lo cambió
    user_id = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(50))
    user_agent = Column(Text)

    # Qué cambió
    changed_fields = Column(JSON)  # ["fixed_fee", "weight_max"]
    old_values = Column(JSON)      # {"fixed_fee": 25.00, "weight_max": 5.00}
    new_values = Column(JSON)      # {"fixed_fee": 30.00, "weight_max": 10.00}

    # Cuándo
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Metadata adicional
    request_id = Column(String(255))  # Correlation ID
    service_name = Column(String(100))  # "international-shipping"

    __table_args__ = (
        Index('idx_audit_table_record', 'table_name', 'record_id'),
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
    )
```

**Uso:**
```python
# Middleware de FastAPI que captura cambios
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    # Intercepta response
    response = await call_next(request)

    # Si fue un POST/PUT/DELETE, registrar en audit log
    if request.method in ["POST", "PUT", "DELETE"]:
        # Extraer datos del request/response
        audit_entry = AuditLog(
            audit_id=f"AUDIT-{uuid.uuid4()}",
            table_name="rates",
            record_id="123",
            operation="UPDATE",
            user_id=request.state.user_id,
            changed_fields=["fixed_fee"],
            old_values={"fixed_fee": 25.00},
            new_values={"fixed_fee": 30.00},
            service_name="international-shipping"
        )
        db.add(audit_entry)
        await db.commit()

    return response
```

---

## 10. RESUMEN EJECUTIVO

### 10.1 Arquitectura ORM

| Aspecto | Detalle |
|---------|---------|
| **ORM** | SQLAlchemy 2.x Async |
| **Driver** | AsyncPG (PostgreSQL) |
| **Patrón** | Database per Service (9 bases de datos independientes) |
| **Migraciones** | Alembic configurado, pero NO usado (⚠️ usar create_all) |
| **Soft Deletes** | Implementado en International Shipping, falta en otros |

### 10.2 Persistencia de Cotizaciones

**Modelo de 4 niveles:**
1. `Rate` - Tarifas base por carrier/servicio/peso
2. `Catalog` - Agrupaciones de tarifas versionadas
3. `CatalogRate` - Relación M:M entre Catalogs y Rates
4. `ClientRatebook` - Tarifas personalizadas por cliente/almacén

**Cálculo:** On-demand via `ClientRatebookService.find_matching_rate()`

**❌ Gap:** NO hay tabla de quotes históricas

### 10.3 Persistencia de Envíos

**Envíos Internacionales:**
- `Manifest` (cabecera) + `ManifestItem` (detalles)
- Estados: draft → submitted → approved → shipped → in_transit → delivered
- Tracking number generado por carrier

**Envíos Nacionales:**
- `Pickup` (solicitud) + `PickupPackage` (paquetes)
- Estados: scheduled → assigned → in_progress → completed
- Tracking number generado después del pickup

### 10.4 Persistencia de Carriers

**Tabla:** `ShippingCarrier`
- Almacena: name, code, api_endpoint, api_key, supported_services
- **⚠️ RIESGO:** Credenciales en texto plano
- **✅ Solución:** Implementar encriptación AES-256

### 10.5 Tracking

**❌ Gap:** NO hay tabla de `TrackingEvent`
- Tracking actual se consulta de APIs externas
- No hay persistencia de historial
- No analytics posible

**✅ Solución:** Implementar tabla de eventos de tracking

### 10.6 Gaps Críticos (Top 5)

1. 🔴 NO hay tabla de quotes históricas
2. 🔴 Credenciales de carriers sin encriptar
3. 🔴 NO hay tabla de tracking events
4. 🔴 Migraciones NO implementadas (usando create_all)
5. 🟡 Relaciones cross-service débiles (String IDs, no FK)

### 10.7 Esfuerzo de Corrección

| Prioridad | Items | Esfuerzo |
|-----------|-------|----------|
| 🔴 Crítico | 4 items | 2 semanas |
| 🟡 Importante | 4 items | 2 semanas |
| 🟢 Mejoras | 4 items | 2 semanas |
| **TOTAL** | **12 items** | **6 semanas** |

---

**FIN DEL ANÁLISIS ORM Y PERSISTENCIA**

*Documento generado el 2025-10-01*
*Versión: 1.0*
