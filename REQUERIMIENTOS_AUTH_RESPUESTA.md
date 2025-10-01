# Respuesta a Requerimientos de Autenticación - Sistema Quenty

**Fecha:** 2025-10-01
**Solicitado por:** Equipo Frontend
**Respondido por:** Equipo Backend / Arquitectura

---

## 📋 Resumen Ejecutivo

Hemos revisado completamente el servicio de autenticación (`auth-service`) del sistema Quenty y evaluado cada uno de los 4 requerimientos solicitados. A continuación se detalla el estado actual, los desarrollos necesarios y la documentación Swagger.

### Estado General

| # | Requerimiento | Estado Actual | Tiempo Implementación |
|---|---------------|---------------|----------------------|
| 1 | Swagger de registro | ⚠️ Parcial (existe endpoint admin) | 2 horas |
| 2 | API recuperar contraseña | ⚠️ Modelos existen, faltan endpoints | 4 horas |
| 3 | Términos y políticas | ❌ No existe | 3 horas |
| 4 | Diferenciación empresa/natural | ⚠️ Modelo Company existe, falta integración | 6 horas |

**Tiempo Total Estimado:** 15 horas (2 días de desarrollo)

---

## 1️⃣ Swagger del Endpoint de Registro de Usuario

### Estado Actual: ⚠️ PARCIAL

**Encontrado:** Endpoint `/api/v1/users` (POST) que permite crear usuarios, pero:
- ❌ Requiere autenticación (JWT token)
- ❌ Requiere permisos `users:create` (solo administradores)
- ❌ No es un endpoint de registro público

### Swagger Actual (Endpoint Administrativo)

```yaml
POST /api/v1/users
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request Body:
{
  "username": "string (3-50 chars, alphanumeric + _)",
  "email": "user@example.com",
  "password": "string (min 8 chars)",
  "password_confirm": "string (must match password)",
  "first_name": "string (optional)",
  "last_name": "string (optional)",
  "phone": "string (optional)",
  "role_id": "integer (optional)"
}

Response 201 Created:
{
  "id": 123,
  "unique_id": "USER-ABC12345",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+57-123-4567890",
  "is_active": true,
  "is_verified": false,
  "email_verified": false,
  "created_at": "2025-10-01T10:30:00Z",
  "role": {
    "id": 2,
    "name": "customer",
    "permissions": ["orders:read:own", "profile:*:own"]
  }
}

Error Responses:
- 400: Validation error (passwords don't match, invalid email, etc.)
- 401: Unauthorized (missing or invalid token)
- 403: Forbidden (insufficient permissions)
- 409: Conflict (username or email already exists)
```

### Swagger NUEVO - Endpoint de Registro Público

**Endpoint que CREAREMOS:**

```yaml
POST /api/v1/auth/register
Content-Type: application/json
# NO requiere autenticación

Request Body:
{
  "user_type": "natural" | "juridica",  # NUEVO: Tipo de persona
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",

  # Datos personales
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+57-300-1234567",

  # NUEVO: Identificación
  "document_type_code": "cedula" | "nit" | "passport",
  "document_number": "1234567890",  # Sin dígito de verificación para NIT

  # NUEVO: Términos y políticas (OBLIGATORIO)
  "terms_accepted": true,
  "privacy_policy_accepted": true,
  "marketing_consent": false,  # Opcional

  # Solo si user_type = "juridica"
  "company_data": {
    "name": "Mi Empresa S.A.S",
    "business_name": "Mi Empresa Sociedad por Acciones Simplificada",
    "nit": "9001234567",  # Sin dígito de verificación
    "industry": "Tecnología",
    "company_size": "small"  # startup, small, medium, large, enterprise
  }
}

Response 201 Created:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800,  # 30 minutos
  "user": {
    "id": 123,
    "unique_id": "USER-ABC12345",
    "username": "johndoe",
    "email": "john@example.com",
    "user_type": "natural",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+57-300-1234567",
    "document_type": "cedula",
    "document_number": "1234567890",
    "is_active": true,
    "is_verified": false,
    "email_verified": false,
    "company": null,  # o datos de empresa si es jurídica
    "role": {
      "id": 2,
      "name": "customer",
      "permissions": ["orders:read:own", "profile:*:own"]
    },
    "created_at": "2025-10-01T10:30:00Z"
  }
}

Error Responses:
400 Bad Request:
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "password",
      "message": "Password must contain at least 8 characters"
    },
    {
      "field": "terms_accepted",
      "message": "Must accept terms and conditions"
    }
  ]
}

409 Conflict:
{
  "detail": "Username or email already exists"
}

422 Unprocessable Entity:
{
  "detail": "Invalid document type for user type",
  "errors": [
    {
      "field": "document_type_code",
      "message": "NIT is only valid for juridica user type"
    }
  ]
}
```

### Validaciones Implementadas

**Persona Natural (`user_type = "natural"`):**
- ✅ Email válido y único
- ✅ Username único (3-50 caracteres, alfanumérico + guión bajo)
- ✅ Contraseña mínimo 8 caracteres (1 mayúscula, 1 minúscula, 1 número, 1 especial)
- ✅ Contraseña y confirmación deben coincidir
- ✅ `terms_accepted` y `privacy_policy_accepted` deben ser `true`
- ✅ `document_type_code` válido: "cedula", "passport", "drivers_license"
- ✅ `document_number` requerido
- ❌ `company_data` no debe enviarse (será ignorado)

**Persona Jurídica (`user_type = "juridica"`):**
- ✅ Todas las validaciones de persona natural
- ✅ `document_type_code` debe ser "nit"
- ✅ `document_number` (NIT sin dígito de verificación) único
- ✅ `company_data` requerido con:
  - `name` requerido (mínimo 3 caracteres)
  - `nit` requerido (mínimo 9 dígitos, sin dígito de verificación)
  - `nit` único en la base de datos (nadie más puede registrarse con ese NIT)

**Regla de Negocio Importante:**
> Una vez registrada una empresa con un NIT, **solo el administrador maestro** de esa empresa puede crear usuarios adicionales asociados a ese NIT. Ningún otro usuario puede registrarse públicamente con el mismo NIT.

---

## 2️⃣ API para Recuperar Contraseña

### Estado Actual: ⚠️ MODELOS EXISTEN, FALTAN ENDPOINTS

**Buenas noticias:** El modelo de datos ya está implementado:
- ✅ Tabla `password_reset_tokens` existe
- ✅ Funciones `create_password_reset_token()` y `verify_password_reset_token()` implementadas
- ✅ Schemas `PasswordResetRequest` y `PasswordResetConfirm` definidos

**Necesitamos:** Crear los endpoints HTTP que expongan esta funcionalidad.

### Swagger - Flujo Completo de Recuperación

#### Paso 1: Solicitar Recuperación de Contraseña

```yaml
POST /api/v1/auth/password-reset/request
Content-Type: application/json
# NO requiere autenticación

Request Body:
{
  "email": "user@example.com"
}

Response 200 OK:
{
  "message": "Si el correo existe, se ha enviado un enlace de recuperación"
}

# Nota: Por seguridad, siempre retorna 200 aunque el email no exista
# Esto previene enumeración de usuarios
```

**Email enviado al usuario:**

```
Asunto: Recuperación de Contraseña - Quenty Platform

Hola [Nombre],

Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.

Para crear una nueva contraseña, haz clic en el siguiente enlace:

https://app.quenty.com/reset-password?token=eyJhbGciOiJIUzI1NiIsInR5cCI...

Este enlace expirará en 1 hora.

Si no solicitaste este cambio, ignora este mensaje.

Equipo Quenty
```

#### Paso 2: Usuario hace clic en el enlace (Frontend muestra formulario)

**Frontend URL:** `https://app.quenty.com/reset-password?token=TOKEN_AQUI`

**Frontend muestra:**
- Campo "Nueva contraseña"
- Campo "Confirmar contraseña"
- Botón "Guardar"

#### Paso 3: Confirmar Nueva Contraseña

```yaml
POST /api/v1/auth/password-reset/confirm
Content-Type: application/json
# NO requiere autenticación (usa el token)

Request Body:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePass456!",
  "new_password_confirm": "NewSecurePass456!"
}

Response 200 OK:
{
  "message": "Contraseña restablecida exitosamente",
  "redirect_to": "/login"
}

Error Responses:
400 Bad Request - Token inválido o expirado:
{
  "detail": "Token de recuperación inválido o expirado"
}

400 Bad Request - Contraseñas no coinciden:
{
  "detail": "Las contraseñas no coinciden"
}

422 Unprocessable Entity - Contraseña débil:
{
  "detail": "La contraseña debe contener al menos 8 caracteres, incluyendo mayúsculas, minúsculas, números y símbolos"
}
```

### Flujo Completo (Diagrama)

```
┌──────────────┐
│   Cliente    │
│   (Frontend) │
└──────┬───────┘
       │
       │ 1. POST /api/v1/auth/password-reset/request
       │    Body: { email: "user@example.com" }
       ▼
┌──────────────┐
│    Backend   │──────► 2. Validar email existe
│   (Auth API) │        3. Generar token único
└──────┬───────┘        4. Guardar en DB con expiración (1 hora)
       │                5. Enviar email con enlace
       │
       │ 6. Response: { message: "Email enviado" }
       ▼
┌──────────────┐
│   Cliente    │
│  Lee email   │
└──────┬───────┘
       │
       │ 7. Click en enlace: https://app.quenty.com/reset-password?token=XYZ
       ▼
┌──────────────┐
│   Frontend   │
│  Muestra     │──────► 8. Usuario ingresa:
│  formulario  │           - Nueva contraseña
└──────┬───────┘           - Confirmar contraseña
       │
       │ 9. POST /api/v1/auth/password-reset/confirm
       │    Body: { token: "XYZ", new_password: "...", ... }
       ▼
┌──────────────┐
│    Backend   │──────► 10. Validar token no expirado
│   (Auth API) │        11. Validar token no usado
└──────┬───────┘        12. Hash nueva contraseña
       │                13. Actualizar user.password_hash
       │                14. Marcar token como usado
       │
       │ 15. Response: { message: "Éxito" }
       ▼
┌──────────────┐
│   Cliente    │
│  Redirige a  │──────► 16. Usuario puede iniciar sesión
│    /login    │            con nueva contraseña
└──────────────┘
```

### Configuración de Email Requerida

**Variables de entorno (`.env`):**

```bash
# SMTP Configuration (para envío de emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@quenty.com
SMTP_PASSWORD=your_app_password_here
SMTP_FROM=noreply@quenty.com
SMTP_FROM_NAME=Quenty Platform

# Frontend URLs
FRONTEND_URL=https://app.quenty.com
PASSWORD_RESET_URL=https://app.quenty.com/reset-password

# Token expiration (in seconds)
PASSWORD_RESET_TOKEN_EXPIRE=3600  # 1 hora
```

**Nota:** Si usan Gmail, deben crear una "App Password" en la configuración de seguridad de Google.

---

## 3️⃣ Aceptación de Términos y Política de Tratamiento de Datos

### Estado Actual: ❌ NO EXISTE

**Necesitamos agregar:**
1. Campos en el modelo de datos `User`
2. Validación obligatoria en el registro
3. Timestamps de aceptación (para auditoría legal)

### Swagger - Campos en Registro

```yaml
POST /api/v1/auth/register
Request Body:
{
  # ... otros campos ...

  # NUEVO: Términos y políticas (OBLIGATORIO)
  "terms_accepted": true,  # REQUERIDO: debe ser true
  "privacy_policy_accepted": true,  # REQUERIDO: debe ser true
  "marketing_consent": false  # OPCIONAL: puede ser true/false
}
```

### Modelo de Datos (Nuevos Campos)

**Tabla `users` tendrá:**

```sql
-- Términos y condiciones
terms_accepted BOOLEAN NOT NULL DEFAULT FALSE,
terms_accepted_at TIMESTAMP NULL,
terms_version VARCHAR(20) NULL,  -- Ej: "v1.0"

-- Política de privacidad
privacy_policy_accepted BOOLEAN NOT NULL DEFAULT FALSE,
privacy_policy_accepted_at TIMESTAMP NULL,
privacy_policy_version VARCHAR(20) NULL,  -- Ej: "v1.0"

-- Consentimiento de marketing (opcional)
marketing_consent BOOLEAN NOT NULL DEFAULT FALSE,
marketing_consent_at TIMESTAMP NULL
```

### Validaciones

**En el endpoint de registro:**

```python
@validator('terms_accepted', 'privacy_policy_accepted')
def must_accept_required_policies(cls, v, field):
    if not v:
        raise ValueError(f'{field.name.replace("_", " ").title()} es obligatorio')
    return v
```

**Error Response si no acepta:**

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "terms_accepted",
      "message": "Debe aceptar los términos y condiciones para continuar"
    },
    {
      "field": "privacy_policy_accepted",
      "message": "Debe aceptar la política de privacidad para continuar"
    }
  ]
}
```

### Frontend - Componente de Registro

**Ejemplo de cómo debe verse:**

```html
<form>
  <!-- ... campos de email, password, etc. ... -->

  <!-- Checkbox de términos -->
  <div class="checkbox-group">
    <input
      type="checkbox"
      id="terms"
      name="terms_accepted"
      required
      value="true"
    />
    <label for="terms">
      Acepto los
      <a href="/terminos" target="_blank">términos y condiciones</a>
    </label>
  </div>

  <!-- Checkbox de privacidad -->
  <div class="checkbox-group">
    <input
      type="checkbox"
      id="privacy"
      name="privacy_policy_accepted"
      required
      value="true"
    />
    <label for="privacy">
      Acepto la
      <a href="/politica-privacidad" target="_blank">política de tratamiento de datos</a>
    </label>
  </div>

  <!-- Checkbox opcional de marketing -->
  <div class="checkbox-group">
    <input
      type="checkbox"
      id="marketing"
      name="marketing_consent"
      value="true"
    />
    <label for="marketing">
      Deseo recibir información promocional (opcional)
    </label>
  </div>

  <button type="submit">Registrarme</button>
</form>
```

### Auditoría Legal

**Cuando un usuario acepta, se guarda:**
- ✅ Timestamp exacto de aceptación
- ✅ Versión del documento aceptado
- ✅ IP address del usuario (en logs)
- ✅ User agent del navegador (en logs)

Esto es importante para cumplimiento legal (GDPR, CCPA, Ley 1581 de Colombia).

---

## 4️⃣ Registro Diferenciado: Empresa vs Persona Natural

### Estado Actual: ⚠️ MODELO COMPANY EXISTE, FALTA INTEGRACIÓN

**Lo que ya existe:**
- ✅ Tabla `companies` con campos completos
- ✅ Relación `User.company_id` → `Company.company_id`
- ✅ Tabla `document_types` con tipos de documento

**Lo que falta:**
- ❌ Campo `user_type` en `User` ("natural" vs "juridica")
- ❌ Campos de documento en `User` (tipo y número)
- ❌ Validación de NIT único para empresas
- ❌ Lógica condicional en registro según tipo

### Swagger - Registro Persona Natural

```yaml
POST /api/v1/auth/register
Content-Type: application/json

Request Body (Persona Natural):
{
  "user_type": "natural",

  # Identificación personal
  "email": "juan.perez@email.com",
  "username": "juanperez",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",

  # Datos personales
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone": "+57-300-1234567",

  # Documento de identidad
  "document_type_code": "cedula",  # o "passport"
  "document_number": "1234567890",

  # Términos
  "terms_accepted": true,
  "privacy_policy_accepted": true

  # NO incluir company_data
}

Response 201:
{
  "access_token": "...",
  "user": {
    "id": 123,
    "unique_id": "USER-NAT12345",
    "user_type": "natural",
    "username": "juanperez",
    "email": "juan.perez@email.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "document_type": "cedula",
    "document_number": "1234567890",
    "company": null,  # Sin empresa
    "role": {
      "name": "customer",
      "permissions": ["orders:read:own", "profile:*:own"]
    }
  }
}
```

### Swagger - Registro Empresa

```yaml
POST /api/v1/auth/register
Content-Type: application/json

Request Body (Persona Jurídica):
{
  "user_type": "juridica",

  # Identificación del representante legal
  "email": "admin@miempresa.com",
  "username": "adminempresa",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",

  # Datos del representante legal
  "first_name": "Carlos",
  "last_name": "Rodríguez",
  "phone": "+57-300-9876543",

  # Documento del representante (cédula)
  "document_type_code": "cedula",
  "document_number": "9876543210",

  # NUEVO: Datos de la empresa (OBLIGATORIO para juridica)
  "company_data": {
    "name": "Tech Solutions S.A.S",
    "business_name": "Tech Solutions Sociedad por Acciones Simplificada",
    "nit": "9001234567",  # SIN dígito de verificación
    "legal_address": "Calle 123 #45-67, Bogotá",
    "industry": "Tecnología",
    "company_size": "small"  # startup | small | medium | large | enterprise
  },

  # Términos
  "terms_accepted": true,
  "privacy_policy_accepted": true
}

Response 201:
{
  "access_token": "...",
  "user": {
    "id": 124,
    "unique_id": "USER-JUR98765",
    "user_type": "juridica",
    "username": "adminempresa",
    "email": "admin@miempresa.com",
    "first_name": "Carlos",
    "last_name": "Rodríguez",
    "document_type": "cedula",
    "document_number": "9876543210",

    # Datos de la empresa asociada
    "company": {
      "company_id": "COMP-ABC12345",
      "name": "Tech Solutions S.A.S",
      "business_name": "Tech Solutions Sociedad por Acciones Simplificada",
      "nit": "9001234567",
      "industry": "Tecnología",
      "company_size": "small",
      "is_verified": false  # Admin debe verificar
    },

    "role": {
      "name": "company_admin",  # Rol especial para administrador de empresa
      "permissions": [
        "company:*:own",
        "users:create:company",  # Puede crear usuarios de su empresa
        "orders:*:company",
        "profile:*:own"
      ]
    }
  }
}
```

### Reglas de Negocio

#### 1. **Validación de NIT Único**

```yaml
POST /api/v1/auth/register
Body:
{
  "user_type": "juridica",
  "company_data": {
    "nit": "9001234567"  # NIT ya registrado
  }
}

Response 409 Conflict:
{
  "detail": "El NIT 9001234567 ya está registrado en el sistema",
  "code": "NIT_ALREADY_EXISTS",
  "suggestion": "Si perteneces a esta empresa, contacta al administrador para que te agregue como usuario"
}
```

#### 2. **Solo Admin de Empresa Puede Agregar Usuarios**

Una vez registrada una empresa, nadie más puede usar ese NIT en el registro público.

**Endpoint para que admin de empresa agregue usuarios:**

```yaml
POST /api/v1/company/users
Authorization: Bearer {jwt_token_of_company_admin}
Content-Type: application/json

Request Body:
{
  "email": "empleado@miempresa.com",
  "username": "empleado01",
  "first_name": "María",
  "last_name": "González",
  "role": "employee",  # Rol dentro de la empresa
  "permissions": ["orders:read", "products:read"]
}

Response 201:
{
  "id": 125,
  "unique_id": "USER-EMP55555",
  "user_type": "juridica",
  "email": "empleado@miempresa.com",
  "company": {
    "company_id": "COMP-ABC12345",
    "name": "Tech Solutions S.A.S",
    "nit": "9001234567"
  },
  "role": {
    "name": "employee",
    "permissions": ["orders:read", "products:read"]
  }
}
```

#### 3. **Campos Obligatorios Diferenciados**

**Persona Natural - Campos Mínimos:**
- ✅ Email
- ✅ Username
- ✅ Password
- ✅ Nombre completo (first_name + last_name)
- ✅ Documento (tipo + número)
- ✅ Términos aceptados

**Persona Jurídica - Campos Adicionales:**
- ✅ Todo lo de persona natural (datos del representante)
- ✅ Datos de empresa (name, NIT, dirección, industria, tamaño)
- ✅ NIT sin dígito de verificación
- ✅ Razón social

### Diferenciación en Frontend

**Según el tipo de usuario registrado, el sistema debe mostrar:**

#### Persona Natural - Vista Simplificada
```
Dashboard:
├── Mis Pedidos
├── Cotizaciones
├── Tracking de envíos
├── Mi Perfil (datos personales)
└── Soporte

Datos requeridos para crear orden:
- Dirección de envío
- Productos
- Método de pago
```

#### Persona Jurídica - Vista Empresarial
```
Dashboard:
├── Órdenes de la Empresa
├── Usuarios de la Empresa (si es admin)
├── Cotizaciones Corporativas
├── Facturación
├── Reportes y Analytics
├── Perfil de la Empresa
└── Configuración Corporativa

Datos adicionales requeridos:
- Centro de costos
- Orden de compra
- Aprobadores
- Presupuestos
```

### Validación de Documento según Tipo

```python
# Backend validation logic

DOCUMENT_TYPES = {
    "natural": ["cedula", "passport", "drivers_license"],
    "juridica": ["nit"]  # Solo NIT para empresas
}

def validate_document_type(user_type: str, document_type_code: str):
    valid_types = DOCUMENT_TYPES.get(user_type, [])
    if document_type_code not in valid_types:
        raise ValueError(
            f"Document type '{document_type_code}' is not valid for user type '{user_type}'. "
            f"Valid types: {', '.join(valid_types)}"
        )
```

**Error si persona natural intenta usar NIT:**

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "document_type_code",
      "message": "NIT solo es válido para empresas. Para persona natural usa: cedula, passport o drivers_license"
    }
  ]
}
```

---

## 📊 Resumen de Endpoints Nuevos

### Endpoints a Crear

| Método | Endpoint | Autenticación | Descripción |
|--------|----------|---------------|-------------|
| POST | `/api/v1/auth/register` | ❌ Público | Registro de usuario (natural o jurídica) |
| POST | `/api/v1/auth/password-reset/request` | ❌ Público | Solicitar recuperación de contraseña |
| POST | `/api/v1/auth/password-reset/confirm` | ❌ Público | Confirmar nueva contraseña con token |
| POST | `/api/v1/company/users` | ✅ JWT (Company Admin) | Admin de empresa crea usuario |
| GET | `/api/v1/company/users` | ✅ JWT (Company Admin) | Listar usuarios de la empresa |

### Endpoints Existentes (No modificar)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Iniciar sesión |
| POST | `/api/v1/auth/refresh` | Renovar token de acceso |
| POST | `/api/v1/auth/logout` | Cerrar sesión |
| GET | `/api/v1/profile` | Obtener perfil del usuario actual |
| PUT | `/api/v1/profile` | Actualizar perfil |

---

## 🔧 Cambios Técnicos Requeridos

### 1. Migraciones de Base de Datos

**Archivo:** `microservices/auth-service/alembic/versions/YYYYMMDD_add_user_type_and_policies.py`

```sql
ALTER TABLE users ADD COLUMN user_type VARCHAR(20);
ALTER TABLE users ADD COLUMN document_type_id INTEGER REFERENCES document_types(id);
ALTER TABLE users ADD COLUMN document_number VARCHAR(100);
ALTER TABLE users ADD COLUMN terms_accepted BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ADD COLUMN terms_accepted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN terms_version VARCHAR(20);
ALTER TABLE users ADD COLUMN privacy_policy_accepted BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ADD COLUMN privacy_policy_accepted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN privacy_policy_version VARCHAR(20);
ALTER TABLE users ADD COLUMN marketing_consent BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE users ADD COLUMN marketing_consent_at TIMESTAMP;

CREATE INDEX idx_users_document ON users(document_type_id, document_number);
CREATE INDEX idx_users_user_type ON users(user_type);
```

### 2. Archivos a Modificar

```
microservices/auth-service/
├── src/
│   ├── models.py               # Agregar campos a User
│   ├── schemas.py              # Actualizar UserCreate, agregar CompanyCreate
│   ├── main.py                 # Agregar 3 nuevos endpoints
│   └── email_service.py        # NUEVO: Envío de emails
├── alembic/
│   └── versions/
│       └── XXX_add_user_type_and_policies.py  # Nueva migración
└── tests/
    └── test_register.py        # NUEVO: Tests para registro
```

### 3. Variables de Entorno

**Agregar a `.env`:**

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@quenty.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@quenty.com

# Frontend URLs
FRONTEND_URL=https://app.quenty.com
PASSWORD_RESET_URL=https://app.quenty.com/reset-password
EMAIL_VERIFICATION_URL=https://app.quenty.com/verify-email

# Token Expiration
PASSWORD_RESET_TOKEN_EXPIRE=3600  # 1 hora
EMAIL_VERIFICATION_TOKEN_EXPIRE=86400  # 24 horas

# Terms and Privacy
CURRENT_TERMS_VERSION=v1.0
CURRENT_PRIVACY_VERSION=v1.0
```

---

## 📅 Plan de Implementación

### Fase 1: Base de Datos (Día 1 - 3 horas)

1. ✅ Crear migración Alembic
2. ✅ Ejecutar migración en desarrollo
3. ✅ Verificar integridad de datos

**Entregables:**
- Migración Alembic aplicada
- Campos nuevos en tabla `users`

### Fase 2: Backend - Modelos y Schemas (Día 1 - 2 horas)

1. ✅ Actualizar `models.py` con nuevos campos
2. ✅ Actualizar schemas (UserCreate, CompanyCreate, etc.)
3. ✅ Agregar validadores Pydantic

**Entregables:**
- Modelos actualizados
- Schemas con validación completa

### Fase 3: Backend - Endpoints (Día 2 - 8 horas)

1. ✅ Implementar `/api/v1/auth/register`
2. ✅ Implementar `/api/v1/auth/password-reset/request`
3. ✅ Implementar `/api/v1/auth/password-reset/confirm`
4. ✅ Implementar `email_service.py`
5. ✅ Implementar `/api/v1/company/users` (opcional)

**Entregables:**
- 3-4 endpoints nuevos funcionando
- Servicio de email configurado
- Tests unitarios

### Fase 4: Documentación y Testing (Día 2 - 2 horas)

1. ✅ Generar Swagger automático (FastAPI)
2. ✅ Documentar ejemplos de uso
3. ✅ Crear Postman collection
4. ✅ Testing manual de flujos completos

**Entregables:**
- Swagger actualizado
- Postman collection
- Documentación de API

### Fase 5: Integración Frontend (Coordinación)

**Nota:** El equipo de frontend necesitará:
- URLs de endpoints
- Ejemplos de request/response
- Códigos de error posibles
- Flujo de usuario esperado

---

## ✅ Checklist de Implementación

### Backend
- [ ] Crear migración Alembic con nuevos campos
- [ ] Ejecutar migración en BD de desarrollo
- [ ] Actualizar `models.py` (User + campos nuevos)
- [ ] Actualizar `schemas.py` (UserCreate + validaciones)
- [ ] Crear `email_service.py`
- [ ] Implementar endpoint `/api/v1/auth/register`
- [ ] Implementar endpoint `/api/v1/auth/password-reset/request`
- [ ] Implementar endpoint `/api/v1/auth/password-reset/confirm`
- [ ] Configurar variables de entorno (SMTP)
- [ ] Crear tests unitarios
- [ ] Probar flujo completo de registro
- [ ] Probar flujo completo de recuperación de contraseña
- [ ] Generar Swagger documentation
- [ ] Crear Postman collection

### Frontend
- [ ] Actualizar formulario de registro con nuevos campos
- [ ] Agregar checkbox de términos y políticas
- [ ] Implementar selección de tipo de usuario (natural/juridica)
- [ ] Mostrar campos condicionales según tipo
- [ ] Validar formato de NIT (sin dígito verificación)
- [ ] Crear página de recuperación de contraseña
- [ ] Implementar formulario de nueva contraseña
- [ ] Integrar con nuevos endpoints
- [ ] Manejar errores de validación
- [ ] Probar flujos end-to-end

### Coordinación
- [ ] Reunión de alineación backend-frontend
- [ ] Compartir Swagger y ejemplos
- [ ] Definir códigos de error y mensajes
- [ ] Acordar formato de validaciones
- [ ] Testing integrado

---

## 🚀 ¿Cuándo Estará Listo?

**Estimación Realista:**
- **Backend:** 2 días completos de desarrollo
- **Testing Backend:** 0.5 días
- **Frontend:** 1.5 días (en paralelo con backend)
- **Testing Integración:** 0.5 días
- **Total:** **3-4 días hábiles**

**Si priorizamos:**
1. **Día 1:** Registro público + Términos y políticas
2. **Día 2:** Recuperación de contraseña
3. **Día 3:** Diferenciación empresa/natural
4. **Día 4:** Testing + Ajustes + Documentación

---

## 📞 Próximos Pasos

### Acción Inmediata

1. **Aprobación:** ¿Están de acuerdo con el enfoque propuesto?
2. **Priorización:** ¿En qué orden prefieren los requerimientos?
3. **Recursos:** ¿Quién del equipo backend trabajará en esto?
4. **Coordinación:** Agendar reunión con frontend para alinear

### Preguntas Pendientes

1. **Email Service:** ¿Tienen servidor SMTP configurado? (Gmail, SendGrid, AWS SES, etc.)
2. **Términos Legales:** ¿Ya existen los documentos de términos y privacidad?
3. **Validación NIT:** ¿Necesitamos validar el NIT con DIAN o solo formato?
4. **Roles de Empresa:** ¿Qué roles internos de empresa necesitan? (admin, employee, accountant, etc.)

---

## 📚 Referencias

### Documentación Actual
- **Arquitectura:** `/ARCHITECTURE.md`
- **Modelo de Datos:** `/DATA_MODEL.md`
- **Seguridad:** `/SECURITY.md`
- **Auth Service:** `/microservices/auth-service/`

### Recursos Externos
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Pydantic Validation:** https://docs.pydantic.dev/
- **JWT Best Practices:** https://datatracker.ietf.org/doc/html/rfc8725

---

**Documento Preparado Por:** Equipo de Arquitectura Backend
**Fecha:** 2025-10-01
**Versión:** 1.0
**Estado:** Listo para Aprobación e Implementación
