# Historias de Usuario y Especificaciones DDD para Plataforma Quenty

## Entidades del Dominio

### Core Logístico
- **Cliente**: Comerciante que contrata servicios
- **Orden**: Solicitud de envío desde canal de venta
- **Envío**: Proceso físico de transporte
- **Guía**: Identificador único del envío
- **Operador Logístico**: Tercero encargado del transporte
- **Novedad**: Incidencia durante el envío
- **Reintento de Entrega**: Reprogramación tras novedad
- **Carta de Responsabilidad**: Documento legal para envíos internacionales

### Red Logística
- **Franquiciado**: Opera zona logística bajo licencia
- **Aliado Logístico**: Comercio local como punto de servicio
- **Punto Logístico**: Ubicación física de operaciones
- **Zona Logística**: División territorial

### Finanzas
- **Comisión**: Ingreso por operación logística
- **Token de Ciudad**: Activo digital de participación
- **Micronegocio/Wallet**: Cuenta financiera interna
- **Microcrédito**: Línea de crédito basada en historial
- **Pago Contra Entrega**: Cobro en destino
- **Campaña Comercial**: Promoción temporal

### Tecnología
- **Suscripción SaaS**: Acceso a funcionalidades premium
- **Integración**: Conexión con sistemas externos
- **Canal de Venta**: Plataforma origen de órdenes
- **Webhook/Evento API**: Punto de conexión
- **Tracking**: Registro de eventos del envío
- **Plantilla de Comunicación**: Configuración de notificaciones

### Control
- **Política Comercial**: Reglas por zona/cliente
- **Tarifa**: Precio por servicio
- **Catálogo de Servicios**: Funcionalidades disponibles
- **Reporte/Métrica**: KPIs y dashboards

## Historias de Usuario

### Epic 1: Gestión de Clientes

#### HU-001: Registro de Cliente
**Como** comerciante  
**Quiero** registrarme en la plataforma Quenty  
**Para** acceder a servicios logísticos y financieros  

**Criterios de Aceptación:**
- El sistema debe validar KYC obligatorio para envíos internacionales
- Debe permitir seleccionar tipo de cliente (pequeño, mediano, grande)
- Debe asignar un ID único de cliente
- Debe crear un micronegocio/wallet automáticamente
- Debe enviar email de confirmación de registro

#### HU-002: Configuración de Perfil de Cliente
**Como** cliente registrado  
**Quiero** configurar mi perfil comercial  
**Para** personalizar los servicios según mi negocio  

**Criterios de Aceptación:**
- Debe permitir cargar documentos de identificación
- Debe configurar dirección de origen por defecto
- Debe seleccionar categorías de productos
- Debe permitir configurar métodos de pago preferidos
- Debe validar información fiscal obligatoria

### Epic 2: Gestión de Órdenes y Envíos

#### HU-003: Creación de Orden Manual
**Como** cliente  
**Quiero** crear una orden de envío manualmente  
**Para** solicitar el transporte de mis productos  

**Criterios de Aceptación:**
- Debe permitir ingresar datos de destinatario
- Debe calcular dimensiones y peso del paquete
- Debe permitir declarar valor del producto
- Debe seleccionar tipo de servicio (nacional/internacional)
- Debe mostrar cotización antes de confirmar
- Debe generar orden con estado "Pendiente"

#### HU-004: Integración con Canal de Venta
**Como** cliente con tienda online  
**Quiero** integrar mi canal de venta con Quenty  
**Para** automatizar la creación de órdenes de envío  

**Criterios de Aceptación:**
- Debe soportar integraciones con Shopify, WooCommerce, MercadoLibre
- Debe sincronizar órdenes automáticamente
- Debe mapear campos de la orden correctamente
- Debe manejar webhooks para actualizaciones en tiempo real
- Debe permitir configurar reglas de filtrado de órdenes

#### HU-005: Cotización de Envío
**Como** cliente  
**Quiero** cotizar el costo de un envío  
**Para** conocer el precio antes de confirmar  

**Criterios de Aceptación:**
- Debe mostrar opciones de operadores disponibles
- Debe calcular precio según peso, dimensiones y destino
- Debe mostrar tiempo estimado de entrega
- Debe aplicar descuentos o promociones vigentes
- Debe responder en menos de 500ms
- Debe permitir comparar múltiples operadores

#### HU-006: Generación de Guía
**Como** cliente  
**Quiero** generar la guía de mi envío  
**Para** iniciar el proceso logístico  

**Criterios de Aceptación:**
- Debe generar ID único de guía
- Debe validar que el cliente no tenga cartera vencida
- Debe verificar límite de crédito si aplica
- Debe generar código de barras/QR
- Debe enviar guía por email al cliente
- Debe cambiar estado de orden a "Con Guía"

### Epic 3: Gestión de Recolección

#### HU-007: Recolección en Punto Logístico
**Como** cliente pequeño  
**Quiero** entregar mi paquete en un punto logístico  
**Para** iniciar el envío sin recolección directa  

**Criterios de Aceptación:**
- Debe mostrar puntos logísticos cercanos
- Debe mostrar horarios de atención
- Debe permitir seleccionar punto preferido
- Debe generar código de entrega
- Debe notificar al punto logístico sobre el paquete esperado

#### HU-008: Recolección Directa
**Como** cliente mediano/grande  
**Quiero** que recojan mi paquete en mi dirección  
**Para** optimizar mi operación logística  

**Criterios de Aceptación:**
- Debe estar disponible solo para clientes medianos/grandes
- Debe permitir agendar recolección
- Debe asignar operador autorizado
- Debe enviar notificación de ventana de recolección
- Debe permitir reprogramar hasta 2 veces

#### HU-009: Seguimiento de Recolección
**Como** cliente  
**Quiero** hacer seguimiento de la recolección  
**Para** conocer el estado de mi paquete  

**Criterios de Aceptación:**
- Debe actualizar estado en tiempo real
- Debe mostrar ubicación del mensajero (si aplica)
- Debe notificar cuando el paquete sea recolectado
- Debe permitir contactar al mensajero
- Debe registrar eventos en el tracking

### Epic 4: Gestión de Tracking y Entregas

#### HU-010: Seguimiento de Envío
**Como** cliente  
**Quiero** hacer seguimiento de mi envío  
**Para** conocer su ubicación y estado actual  

**Criterios de Aceptación:**
- Debe mostrar todos los eventos del tracking
- Debe mostrar fecha y hora de cada evento
- Debe mostrar ubicación actual del paquete
- Debe mostrar tiempo estimado de entrega
- Debe permitir compartir tracking con destinatario

#### HU-011: Notificaciones de Estado
**Como** cliente  
**Quiero** recibir notificaciones sobre mi envío  
**Para** estar informado del progreso  

**Criterios de Aceptación:**
- Debe enviar notificaciones por email, SMS o WhatsApp
- Debe usar plantillas configurables por evento
- Debe permitir al cliente elegir canales de notificación
- Debe incluir link de tracking en notificaciones
- Debe respetar horarios de envío configurados

#### HU-012: Gestión de Novedades
**Como** operador logístico  
**Quiero** reportar novedades en entregas  
**Para** informar problemas durante el envío  

**Criterios de Aceptación:**
- Debe permitir seleccionar tipo de novedad
- Debe requerir comentario explicativo
- Debe permitir adjuntar evidencia fotográfica
- Debe notificar automáticamente al cliente
- Debe generar reintento automático según políticas

### Epic 5: Gestión de Envíos Internacionales

#### HU-013: Validación KYC para Envíos Internacionales
**Como** sistema  
**Quiero** validar el KYC del cliente  
**Para** cumplir requisitos legales de envíos internacionales  

**Criterios de Aceptación:**
- Debe validar KYC en el momento del registro
- Debe integrar con proveedor KYC (Truora)
- Debe bloquear envíos internacionales sin KYC aprobado
- Debe permitir reenvío de documentos si es rechazado
- Debe notificar resultado de validación

#### HU-014: Carga de Documentos Internacionales
**Como** cliente  
**Quiero** cargar los documentos requeridos  
**Para** realizar envíos internacionales  

**Criterios de Aceptación:**
- Debe permitir cargar factura del cliente
- Debe permitir cargar carta de responsabilidad
- Debe validar formato y completitud de documentos
- Debe generar versión en inglés si destino no es hispano
- Debe almacenar documentos de forma segura

#### HU-015: Cotización Internacional
**Como** cliente  
**Quiero** cotizar envíos internacionales  
**Para** conocer costos y tiempos de entrega  

**Criterios de Aceptación:**
- Debe mostrar operadores internacionales disponibles
- Debe incluir costos aduaneros estimados
- Debe mostrar restricciones por país destino
- Debe validar documentación requerida
- Debe calcular tiempo estimado incluyendo aduanas

### Epic 6: Gestión de Pagos

#### HU-016: Pago Contado
**Como** cliente contado  
**Quiero** pagar inmediatamente mi envío  
**Para** generar la guía sin demoras  

**Criterios de Aceptación:**
- Debe procesar pago antes de generar guía
- Debe soportar múltiples medios de pago (tarjeta, PSE, etc.)
- Debe integrar con pasarelas de pago (Epayco, dLocal)
- Debe generar comprobante de pago
- Debe reembolsar automáticamente si hay error en envío

#### HU-017: Pago a Crédito
**Como** cliente crédito  
**Quiero** generar envíos sin pago inmediato  
**Para** optimizar mi flujo de caja  

**Criterios de Aceptación:**
- Debe validar límite de crédito disponible
- Debe generar factura tras confirmación de "Recibido"
- Debe calcular fecha de vencimiento según términos
- Debe bloquear nuevos envíos si hay cartera vencida
- Debe enviar recordatorios de pago

#### HU-018: Pago Contra Entrega (PCE)
**Como** cliente  
**Quiero** ofrecer pago contra entrega  
**Para** facilitar ventas a mis clientes finales  

**Criterios de Aceptación:**
- Debe permitir configurar monto a cobrar
- Debe soportar pago en efectivo y digital (QR/link)
- Debe validar pago antes de entregar paquete
- Debe liquidar al cliente según políticas configuradas
- Debe manejar casos de no pago o pago parcial

### Epic 7: Gestión de Franquicias y Aliados

#### HU-019: Registro de Franquiciado
**Como** emprendedor  
**Quiero** registrarme como franquiciado  
**Para** operar un nodo logístico de Quenty  

**Criterios de Aceptación:**
- Debe validar requisitos mínimos de capital
- Debe asignar zona logística exclusiva
- Debe crear cuenta de micronegocio/wallet
- Debe configurar participación en tokens de ciudad
- Debe enviar kit de bienvenida digital

#### HU-020: Gestión de Punto Logístico
**Como** franquiciado  
**Quiero** gestionar mi punto logístico  
**Para** brindar servicio eficiente a los clientes  

**Criterios de Aceptación:**
- Debe permitir actualizar horarios de atención
- Debe mostrar paquetes pendientes de recolección
- Debe permitir registrar entrega de paquetes
- Debe generar reportes de operación diaria
- Debe notificar cuando hay paquetes por recoger

#### HU-021: Registro de Aliado Logístico
**Como** comerciante local  
**Quiero** ser aliado logístico de Quenty  
**Para** generar ingresos adicionales  

**Criterios de Aceptación:**
- Debe permitir registro simplificado
- Debe asignar código único de aliado
- Debe configurar comisiones por operación
- Debe proporcionar capacitación básica
- Debe crear acceso limitado al panel de gestión

### Epic 8: Gestión de Comisiones

#### HU-022: Cálculo de Comisiones
**Como** sistema  
**Quiero** calcular comisiones automáticamente  
**Para** distribuir ingresos según reglas configuradas  

**Criterios de Aceptación:**
- Debe calcular comisiones por cada envío exitoso
- Debe aplicar reglas por tipo de usuario (agente, franquicia, aliado)
- Debe considerar estructura piramidal para agentes
- Debe aplicar bonos por volumen según campañas
- Debe generar comisión solo si no hay cartera vencida en la línea

#### HU-023: Liquidación de Comisiones
**Como** franquiciado/agente  
**Quiero** recibir mis comisiones  
**Para** obtener los ingresos ganados  

**Criterios de Aceptación:**
- Debe liquidar comisiones según periodicidad configurada
- Debe descontar impuestos y retenciones aplicables
- Debe transferir a cuenta bancaria o wallet
- Debe generar comprobante de liquidación
- Debe permitir consultar histórico de comisiones

### Epic 9: Gestión de Microcréditos

#### HU-024: Evaluación de Microcrédito
**Como** cliente  
**Quiero** solicitar un microcrédito  
**Para** obtener capital de trabajo  

**Criterios de Aceptación:**
- Debe evaluar historial operativo del cliente
- Debe calcular scoring basado en envíos y pagos
- Debe definir monto máximo según rating
- Debe establecer términos y condiciones
- Debe requerir aprobación manual para montos altos

#### HU-025: Desembolso de Microcrédito
**Como** cliente aprobado  
**Quiero** recibir el desembolso  
**Para** usar el capital en mi negocio  

**Criterios de Aceptación:**
- Debe transferir a cuenta bancaria del cliente
- Debe crear plan de pagos automático
- Debe enviar contrato digital para firma
- Debe activar descuentos automáticos de pagos futuros
- Debe notificar fechas de pago

### Epic 10: Gestión de Tokenización

#### HU-026: Emisión de Tokens de Ciudad
**Como** sistema  
**Quiero** emitir tokens de ciudad  
**Para** permitir participación en utilidades locales  

**Criterios de Aceptación:**
- Debe emitir tokens solo para franquicias activas
- Debe calcular participación según facturación histórica
- Debe usar blockchain para transparencia
- Debe permitir transferencia entre holders
- Debe generar smart contract automáticamente

#### HU-027: Liquidación de Tokens
**Como** holder de tokens  
**Quiero** recibir mi participación en utilidades  
**Para** obtener rendimiento de mi inversión  

**Criterios de Aceptación:**
- Debe calcular utilidades mensuales por ciudad
- Debe distribuir proporcionalmente según tokens
- Debe descontar costos operativos de la franquicia
- Debe liquidar en criptomoneda o moneda local
- Debe generar reporte de rendimiento

### Epic 11: Gestión de Reportes y Analytics

#### HU-028: Dashboard Operativo
**Como** cliente  
**Quiero** ver mi dashboard operativo  
**Para** monitorear el rendimiento de mis envíos  

**Criterios de Aceptación:**
- Debe mostrar KPIs en tiempo real
- Debe incluir gráficos de tendencias
- Debe permitir filtros por período y zona
- Debe mostrar comparativas vs. período anterior
- Debe permitir exportar reportes en PDF/Excel

#### HU-029: Reportes Financieros
**Como** franquiciado  
**Quiero** acceder a reportes financieros  
**Para** evaluar la rentabilidad de mi operación  

**Criterios de Aceptación:**
- Debe mostrar ingresos y costos detallados
- Debe incluir proyecciones de comisiones
- Debe mostrar participación en tokens
- Debe calcular ROI y payback
- Debe permitir comparar con otras franquicias

### Epic 12: Gestión de Logística Inversa

#### HU-030: Solicitud de Devolución
**Como** cliente  
**Quiero** solicitar devolución de un envío  
**Para** gestionar la logística inversa  

**Criterios de Aceptación:**
- Debe permitir seleccionar motivo de devolución
- Debe validar política de devoluciones aplicable
- Debe generar guía de devolución
- Debe programar recolección en destino
- Debe notificar al cliente original sobre la devolución

#### HU-031: Seguimiento de Devolución
**Como** cliente  
**Quiero** hacer seguimiento de mi devolución  
**Para** conocer cuándo recibiré mi producto  

**Criterios de Aceptación:**
- Debe mostrar tracking específico de devolución
- Debe notificar eventos importantes
- Debe estimar tiempo de entrega en origen
- Debe permitir contactar mensajero de devolución
- Debe confirmar recepción del producto devuelto

### Epic 13: Administración del Sistema

#### HU-032: Configuración de Políticas Comerciales
**Como** administrador  
**Quiero** configurar políticas comerciales  
**Para** establecer reglas de negocio por zona/cliente  

**Criterios de Aceptación:**
- Debe permitir definir reglas por país, zona, cliente
- Debe configurar límites de peso, dimensiones, valor
- Debe establecer condiciones de servicio
- Debe definir penalidades por incumplimiento
- Debe versionear cambios en políticas

#### HU-033: Gestión de Tarifas
**Como** administrador  
**Quiero** gestionar tarifas  
**Para** mantener precios competitivos y rentables  

**Criterios de Aceptación:**
- Debe permitir configurar tarifas base por servicio
- Debe establecer excepciones por cliente o zona
- Debe aplicar incrementos por peso o dimensiones
- Debe configurar descuentos por volumen
- Debe activar/desactivar tarifas por período

### Epic 14: Integraciones con Operadores Logísticos Específicos

#### HU-034: Integración con DHL
**Como** administrador  
**Quiero** integrar el sistema con DHL  
**Para** ofrecer servicios de envío internacional premium  

**Criterios de Aceptación:**
- Debe integrar con DHL Express API para cotizaciones en tiempo real
- Debe soportar generación de guías DHL (AWB - Air Waybill)
- Debe sincronizar tracking events desde DHL cada 30 minutos
- Debe mapear servicios DHL (Express Worldwide, Express 12:00, Express 9:00)
- Debe validar restricciones de envío por país según normativa DHL
- Debe manejar documentación aduanera electrónica (PLT - Paperless Trade)
- Debe soportar pickup scheduling mediante API
- Debe manejar errores y reintentos con circuit breaker pattern

#### HU-035: Integración con FedEx
**Como** administrador  
**Quiero** integrar el sistema con FedEx  
**Para** ampliar opciones de envío internacional y nacional  

**Criterios de Aceptación:**
- Debe integrar con FedEx Web Services (Ship, Rate, Track)
- Debe obtener y renovar automáticamente tokens OAuth 2.0
- Debe generar etiquetas de envío FedEx con código de barras
- Debe soportar servicios FedEx (International Priority, International Economy, Ground)
- Debe calcular duties & taxes para envíos internacionales
- Debe permitir programación de recolección mediante FedEx Pickup API
- Debe sincronizar eventos de tracking mediante webhooks
- Debe manejar consolidación de envíos (MPS - Multi-Piece Shipments)
- Debe almacenar credenciales de forma segura (account number, meter number)

#### HU-036: Integración con UPS
**Como** administrador  
**Quiero** integrar el sistema con UPS  
**Para** ofrecer alternativas competitivas de envío  

**Criterios de Aceptación:**
- Debe integrar con UPS Developer Kit APIs
- Debe autenticar mediante OAuth 2.0 con client credentials flow
- Debe soportar UPS Rating API para cotizaciones
- Debe generar labels mediante UPS Shipping API
- Debe rastrear paquetes con UPS Tracking API
- Debe soportar servicios UPS (Worldwide Express, Expedited, Standard)
- Debe manejar UPS Paperless Invoice para documentación comercial
- Debe procesar notificaciones mediante UPS Webhooks (Quantum View)
- Debe validar direcciones con UPS Address Validation API
- Debe manejar tiempos de respuesta con timeout de 30 segundos

#### HU-037: Integración con Servientrega
**Como** administrador  
**Quiero** integrar el sistema con Servientrega  
**Para** ofrecer cobertura nacional completa en Colombia  

**Criterios de Aceptación:**
- Debe integrar con Web Service SOAP de Servientrega
- Debe autenticar con usuario y contraseña del convenio empresarial
- Debe generar guías con numeración consecutiva de Servientrega
- Debe soportar servicios nacionales (Mercancía Premier, Documento Unitario)
- Debe consultar cobertura por código postal/municipio
- Debe sincronizar estados de envío cada hora
- Debe manejar servicios adicionales (entrega sábado, firma y sello)
- Debe generar manifiestos de despacho para consolidación
- Debe calcular flete según acuerdo comercial configurado
- Debe manejar reintentos con backoff exponencial

#### HU-038: Integración con Interrapidisimo
**Como** administrador  
**Quiero** integrar el sistema con Interrapidisimo  
**Para** complementar cobertura logística nacional  

**Criterios de Aceptación:**
- Debe integrar con API REST de Interrapidisimo
- Debe autenticar mediante API Key del cliente corporativo
- Debe generar remesas con estructura JSON requerida
- Debe soportar modalidades de servicio (Hoy, Normal, Grandes Superficies)
- Debe consultar tarifas según origen-destino y peso volumétrico
- Debe imprimir rótulos con código de barras I2of5
- Debe rastrear envíos mediante endpoint de consulta masiva
- Debe manejar novedades específicas de Interrapidisimo
- Debe generar relación de envíos para cierre de despacho
- Debe validar ciudades de cobertura antes de generar guía

### Epic 15: Integración con Servicios Financieros

#### HU-039: Integración con Banco de la República - TRM
**Como** sistema  
**Quiero** obtener la TRM oficial del Banco de la República  
**Para** calcular correctamente valores en envíos internacionales  

**Criterios de Aceptación:**
- Debe consumir el Web Service SOAP del Banco de la República
- Debe obtener TRM vigente del día actual cada mañana a las 6:00 AM
- Debe almacenar histórico de TRM con fecha de vigencia
- Debe usar TRM del día para todas las cotizaciones internacionales
- Debe manejar caché local con TTL de 24 horas
- Debe tener fallback a última TRM conocida si el servicio está caído
- Debe exponer endpoint interno `/api/v1/exchange-rates/cop-usd`
- Debe notificar al administrador si la TRM varía más del 5% día a día
- Debe aplicar TRM + spread configurable para cotizaciones a clientes
- Debe registrar en logs cada actualización de TRM

#### HU-040: Configuración de Credenciales de Operadores
**Como** administrador  
**Quiero** gestionar credenciales de operadores logísticos  
**Para** mantener las integraciones funcionando correctamente  

**Criterios de Aceptación:**
- Debe permitir configurar credenciales por operador (API keys, tokens, passwords)
- Debe encriptar credenciales en base de datos usando AES-256
- Debe validar conectividad al guardar nuevas credenciales
- Debe mantener múltiples ambientes (sandbox, producción)
- Debe rotar credenciales según política de cada operador
- Debe notificar antes de expiración de credenciales
- Debe mantener log de auditoría de cambios en credenciales
- Debe soportar múltiples cuentas por operador (multi-tenant)

#### HU-041: Monitoreo de Integraciones
**Como** administrador  
**Quiero** monitorear el estado de las integraciones  
**Para** garantizar disponibilidad del servicio  

**Criterios de Aceptación:**
- Debe ejecutar health checks cada 5 minutos por operador
- Debe medir latencia promedio de cada API
- Debe detectar degradación del servicio (latencia > 2x normal)
- Debe activar circuit breaker tras 5 fallos consecutivos
- Debe enviar alertas por email/SMS cuando un servicio está caído
- Debe mantener dashboard con uptime de últimos 30 días
- Debe registrar todas las llamadas a APIs externas con request/response
- Debe calcular tasa de error por operador y endpoint
- Debe generar reporte mensual de SLA por operador
- Debe permitir forzar reconexión manual desde panel admin

#### HU-042: Gestión de Fallback entre Operadores
**Como** sistema  
**Quiero** usar operadores alternativos automáticamente  
**Para** garantizar continuidad del servicio  

**Criterios de Aceptación:**
- Debe configurar orden de prioridad por ruta (origen-destino)
- Debe cambiar automáticamente al siguiente operador si el principal falla
- Debe notificar al cliente si hay diferencia de precio > 10%
- Debe mantener las mismas características de servicio si es posible
- Debe registrar motivo de fallback en el tracking
- Debe intentar volver al operador principal cada hora
- Debe calcular estadísticas de uso de fallback
- Debe permitir configurar reglas de fallback por tipo de cliente

## Bounded Contexts

### 1. Gestión de Clientes y Usuarios
- Entidades: Cliente, Agente, Franquiciado, Aliado Logístico, Administrador
- Servicios: Registro, KYC, Perfiles, Autenticación

### 2. Gestión de Órdenes y Envíos
- Entidades: Orden, Envío, Guía, Tracking, Novedad, Reintento
- Servicios: Cotización, Creación de órdenes, Generación de guías

### 3. Gestión de Red Logística
- Entidades: Punto Logístico, Zona Logística, Operador Logístico
- Servicios: Recolección, Entrega, Gestión de puntos

### 4. Gestión Financiera
- Entidades: Factura, Pago, Comisión, Microcrédito, Wallet, TRM
- Servicios: Facturación, Pagos, Liquidaciones, Conversión de divisas

### 5. Gestión de Tokenización
- Entidades: Token de Ciudad, Smart Contract
- Servicios: Emisión, Distribución, Liquidación

### 6. Gestión de Integraciones
- Entidades: Canal de Venta, Integración, Webhook, Credencial de Operador
- Servicios: Sincronización, APIs, Notificaciones, Health Checks

### 7. Gestión de Configuración
- Entidades: Política Comercial, Tarifa, Catálogo de Servicios
- Servicios: Configuración, Versionado, Aplicación de reglas

### 8. Reporting y Analytics
- Entidades: Reporte, Métrica, Dashboard
- Servicios: Generación de reportes, KPIs, Business Intelligence

### 9. Gestión de Operadores Logísticos Externos
- Entidades: Operador Externo (DHL, FedEx, UPS, Servientrega, Interrapidisimo), Credencial, Estado de Integración
- Servicios: Cotización Multi-operador, Generación de Guías Externas, Tracking Unificado, Fallback Management

### 10. Gestión de Tipos de Cambio
- Entidades: TRM, Histórico de Tasas, Spread
- Servicios: Actualización TRM, Conversión de Moneda, Notificación de Variaciones

## Servicios de Dominio Principales

### OrderService
- `createOrder(orderData): Order`
- `calculateShipping(origin, destination, package): Quote`
- `generateGuide(orderId): Guide`
- `cancelOrder(orderId): void`

### ShippingService
- `schedulePickup(guideId, address): Pickup`
- `trackShipment(guideId): TrackingInfo`
- `reportIncident(guideId, incident): Incident`
- `processDelivery(guideId): Delivery`

### PaymentService
- `processPayment(paymentData): Payment`
- `generateInvoice(customerId, items): Invoice`
- `processCashOnDelivery(amount, method): CODPayment`
- `calculateCredit(customerId): CreditLimit`

### CommissionService
- `calculateCommission(shipmentId): Commission`
- `distributeCommissions(period): CommissionDistribution`
- `processLiquidation(agentId): Liquidation`

### TokenService
- `issueTokens(franchiseId): TokenIssuance`
- `distributeUtilities(cityId, amount): TokenDistribution`
- `transferTokens(fromId, toId, amount): Transfer`

### CarrierIntegrationService
- `getQuoteFromDHL(shipmentData): DHLQuote`
- `getQuoteFromFedEx(shipmentData): FedExQuote`
- `getQuoteFromUPS(shipmentData): UPSQuote`
- `getQuoteFromServientrega(shipmentData): ServientregaQuote`
- `getQuoteFromInterrapidisimo(shipmentData): InterrapidisimoQuote`
- `generateDHLLabel(orderData): DHLLabel`
- `generateFedExLabel(orderData): FedExLabel`
- `generateUPSLabel(orderData): UPSLabel`
- `generateServientregaGuide(orderData): ServientregaGuide`
- `generateInterrapidisimoRemesa(orderData): InterrapidisimoRemesa`
- `trackMultiCarrier(trackingNumber, carrier): TrackingInfo`
- `scheduleCarrierPickup(carrier, pickupData): PickupConfirmation`
- `validateCarrierCredentials(carrier, credentials): ValidationResult`
- `getCarrierHealthStatus(carrier): HealthStatus`

### ExchangeRateService
- `getCurrentTRM(): TRMRate`
- `updateTRMFromBanRep(): TRMUpdate`
- `convertCOPtoUSD(amount): ConvertedAmount`
- `convertUSDtoCOP(amount): ConvertedAmount`
- `getTRMHistory(startDate, endDate): TRMHistory[]`
- `applySpread(amount, spreadPercentage): AmountWithSpread`
- `notifyTRMVariation(threshold): Notification`

### CarrierFallbackService
- `selectPrimaryCarrier(route): Carrier`
- `selectFallbackCarrier(route, excludeCarriers): Carrier`
- `recordFallbackEvent(orderId, fromCarrier, toCarrier, reason): FallbackRecord`
- `attemptCarrierRecovery(carrier): RecoveryResult`
- `getCarrierPriority(route): CarrierPriority[]`

## Eventos de Dominio

### Order Events
- `OrderCreated`
- `OrderCancelled`
- `GuideGenerated`

### Shipping Events
- `PackagePickedUp`
- `PackageInTransit`
- `PackageDelivered`
- `IncidentReported`

### Payment Events
- `PaymentProcessed`
- `PaymentFailed`
- `InvoiceGenerated`
- `CreditLimitExceeded`

### Commission Events
- `CommissionCalculated`
- `CommissionLiquidated`
- `CommissionBlocked`

### Carrier Integration Events
- `CarrierQuoteReceived`
- `CarrierQuoteFailed`
- `CarrierLabelGenerated`
- `CarrierPickupScheduled`
- `CarrierServiceDegraded`
- `CarrierServiceRecovered`
- `CarrierFallbackActivated`
- `CarrierCredentialsExpiring`

### Exchange Rate Events
- `TRMUpdated`
- `TRMUpdateFailed`
- `TRMVariationDetected`
- `ExchangeRateApplied`

## Agregados Principales

1. **Customer Aggregate**: Cliente, Wallet, Microcrédito
2. **Order Aggregate**: Orden, Guía, Tracking, Novedades
3. **Shipping Aggregate**: Envío, Recolección, Entrega
4. **Payment Aggregate**: Factura, Pago, Comisión
5. **Franchise Aggregate**: Franquicia, Punto Logístico, Tokens
6. **Policy Aggregate**: Política Comercial, Tarifa, Catálogo
7. **Carrier Integration Aggregate**: Operador Externo, Credenciales, Estado de Servicio, Configuración de Fallback
8. **Exchange Rate Aggregate**: TRM, Histórico de Tasas, Configuración de Spread

Esta especificación proporciona una base sólida para implementar la plataforma Quenty siguiendo principios DDD, con historias de usuario claras y criterios de aceptación específicos que guiarán el desarrollo de cada funcionalidad, incluyendo las integraciones con operadores logísticos internacionales (DHL, FedEx, UPS) y nacionales colombianos (Servientrega, Interrapidisimo), así como la integración con el Banco de la República para obtener la TRM oficial.
