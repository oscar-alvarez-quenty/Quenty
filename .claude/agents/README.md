# Quenty Platform - Specialized Agents

Este directorio contiene perfiles de agentes especializados optimizados para desarrollar y mantener el proyecto Quenty.

## 📋 Índice de Agentes

### 🏗️ Architecture & Backend

#### [Backend Architect](./backend-architect.md)
**Rol:** Diseño y revisión de arquitectura de microservicios
**Responsabilidades:**
- Diseño de arquitectura de microservicios
- Modelado de datos y esquemas de base de datos
- Patrones de integración entre servicios
- Estrategias de escalabilidad y performance
- Arquitectura de seguridad

**Cuándo usar:**
- Diseñar nuevos microservicios
- Evaluar cambios arquitectónicos importantes
- Revisar patrones de comunicación entre servicios
- Diseñar esquemas de base de datos
- Planificar escalabilidad

---

#### [Backend Developer](./backend-developer.md)
**Rol:** Desarrollo de microservicios Python/FastAPI
**Responsabilidades:**
- Implementación de endpoints REST con FastAPI
- Desarrollo de modelos SQLAlchemy
- Creación de migraciones Alembic
- Implementación de lógica de negocio
- Pruebas unitarias e integración

**Cuándo usar:**
- Implementar nuevas funcionalidades
- Crear nuevos endpoints de API
- Modificar modelos de base de datos
- Escribir migraciones
- Implementar validaciones y business logic

---

#### [Database Specialist](./database-specialist.md)
**Rol:** Especialista en PostgreSQL y optimización de base de datos
**Responsabilidades:**
- Diseño de esquemas eficientes
- Creación y gestión de migraciones Alembic
- Optimización de queries
- Estrategias de indexación
- Monitoreo de performance

**Cuándo usar:**
- Diseñar esquemas de base de datos complejos
- Optimizar queries lentos
- Crear índices apropiados
- Planificar particionamiento de tablas
- Resolver problemas de performance en BD

---

### 🔧 DevOps & Infrastructure

#### [DevOps Engineer](./devops-engineer.md)
**Rol:** Infraestructura, despliegue y operaciones
**Responsabilidades:**
- Gestión de contenedores Docker
- Configuración de docker-compose
- Pipelines de CI/CD
- Monitoreo con Grafana/Prometheus
- Configuración de Nginx y balanceo de carga

**Cuándo usar:**
- Configurar nuevos servicios en Docker
- Optimizar Dockerfiles
- Configurar monitoreo y alertas
- Planificar estrategias de despliegue
- Gestionar backups y disaster recovery

---

### 🎨 Frontend

#### [Frontend Developer](./frontend-developer.md)
**Rol:** Desarrollo de interfaces de usuario
**Responsabilidades:**
- Desarrollo de componentes React/Vue
- Integración con APIs REST
- Gestión de estado (Redux/Zustand)
- Manejo de formularios y validación
- Implementación de autenticación JWT

**Cuándo usar:**
- Crear nuevas pantallas y componentes
- Integrar con endpoints de backend
- Implementar formularios complejos
- Gestionar autenticación en frontend
- Optimizar performance de UI

---

### 🔒 Security

#### [Security Specialist](./security-specialist.md)
**Rol:** Especialista en seguridad de aplicaciones
**Responsabilidades:**
- Implementación de JWT y OAuth
- Encriptación de datos (AES-256-GCM)
- Rate limiting y prevención de ataques
- Auditorías de seguridad
- Gestión de secrets y compliance

**Cuándo usar:**
- Implementar autenticación y autorización
- Revisar vulnerabilidades de seguridad
- Diseñar encriptación de datos sensibles
- Implementar rate limiting
- Auditar código para OWASP Top 10

---

### 📊 Business & Product

#### [Business Analyst](./business-analyst.md)
**Rol:** Análisis de negocio y requisitos
**Responsabilidades:**
- Recolección de requisitos de negocio
- Documentación de user stories
- Análisis de procesos y workflows
- Definición de reglas de negocio
- Análisis de KPIs y métricas

**Cuándo usar:**
- Analizar nuevos requisitos de negocio
- Documentar user stories y casos de uso
- Definir reglas de negocio complejas
- Analizar impacto de cambios
- Crear reportes de métricas de negocio

---

#### [Product Manager](./product-manager.md)
**Rol:** Gestión de producto y roadmap
**Responsabilidades:**
- Definición de visión de producto
- Priorización de features (RICE, MoSCoW)
- Gestión de roadmap
- Análisis de métricas y OKRs
- Comunicación con stakeholders

**Cuándo usar:**
- Definir prioridades de desarrollo
- Crear PRDs (Product Requirements Documents)
- Analizar métricas de adopción
- Tomar decisiones sobre features
- Planificar roadmap trimestral

---

### 🧪 Quality Assurance

#### [QA Tester](./qa-tester.md)
**Rol:** Testing y aseguramiento de calidad
**Responsabilidades:**
- Creación de planes y casos de prueba
- Testing funcional, integración y E2E
- Automatización de tests con pytest
- Testing de seguridad y performance
- Gestión de defectos

**Cuándo usar:**
- Crear estrategias de testing
- Escribir tests automatizados
- Validar nuevas funcionalidades
- Realizar pruebas de seguridad
- Documentar y reportar bugs

---

## 🎯 Guía de Uso

### Selección del Agente Apropiado

**Para Nuevas Funcionalidades:**
1. **Product Manager** → Define requisitos y prioridad
2. **Business Analyst** → Detalla user stories y reglas de negocio
3. **Backend Architect** → Diseña arquitectura y data model
4. **Backend Developer** → Implementa funcionalidad
5. **Frontend Developer** → Crea interfaz de usuario
6. **QA Tester** → Valida implementación
7. **DevOps Engineer** → Despliega a producción

**Para Bugs Críticos:**
1. **QA Tester** → Reproduce y documenta
2. **Backend Developer** o **Frontend Developer** → Investiga y corrige
3. **Security Specialist** → Si es vulnerabilidad de seguridad
4. **DevOps Engineer** → Despliega hotfix

**Para Mejoras de Performance:**
1. **Database Specialist** → Optimiza queries y esquemas
2. **Backend Architect** → Evalúa patrones de arquitectura
3. **DevOps Engineer** → Optimiza infraestructura
4. **Frontend Developer** → Optimiza UI si es necesario

**Para Revisiones de Seguridad:**
1. **Security Specialist** → Auditoría completa
2. **Backend Architect** → Valida diseño de seguridad
3. **DevOps Engineer** → Revisa infraestructura
4. **QA Tester** → Ejecuta pruebas de penetración

### Matriz de Responsabilidades (RACI)

| Actividad | Architect | Backend Dev | DB Specialist | DevOps | Frontend | Security | BA | PM | QA |
|-----------|-----------|-------------|---------------|--------|----------|----------|----|----|-----|
| Definir requisitos | C | C | C | C | C | C | R | A | C |
| Diseñar arquitectura | A | R | R | C | I | C | I | C | I |
| Implementar features | C | A | R | I | A | C | I | C | I |
| Crear migraciones DB | C | R | A | I | I | I | I | I | I |
| Configurar Docker | I | C | I | A | I | C | I | I | I |
| Testing | I | R | I | I | R | C | I | C | A |
| Deploy producción | I | C | I | A | I | C | I | C | R |
| Auditoría seguridad | C | R | R | R | R | A | I | C | R |

**Leyenda:**
- **R** = Responsible (Ejecuta)
- **A** = Accountable (Responsable final)
- **C** = Consulted (Consultado)
- **I** = Informed (Informado)

---

## 🛠️ Stack Tecnológico

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.x Async
- **Database:** PostgreSQL 15
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Authentication:** JWT + OAuth 2.0
- **Encryption:** AES-256-GCM, bcrypt

### Frontend (Recomendado)
- **Framework:** React 18+ o Vue 3+
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** Redux Toolkit / Zustand
- **Forms:** React Hook Form
- **HTTP:** Axios
- **Validation:** Zod / Yup

### DevOps
- **Containers:** Docker + docker-compose
- **Proxy:** Nginx
- **Monitoring:** Grafana + Prometheus + Loki
- **Cache:** Redis
- **Queue:** RabbitMQ
- **Service Discovery:** Consul
- **CI/CD:** GitHub Actions

### Database
- **Primary:** PostgreSQL 15
- **Vector DB:** pgvector (RAG service)
- **Total Instances:** 14 databases
- **Pattern:** Database-per-Service

---

## 📚 Documentación de Referencia

### Arquitectura
- [`/ARCHITECTURE.md`](../../ARCHITECTURE.md) - Arquitectura completa del sistema
- [`/DATA_MODEL.md`](../../DATA_MODEL.md) - Modelo de datos de todos los servicios
- [`/SECURITY.md`](../../SECURITY.md) - Guía de implementación de seguridad

### Implementación
- [`/IMPLEMENTATION_SUMMARY.md`](../../IMPLEMENTATION_SUMMARY.md) - Resumen de implementación
- [`/ENVIRONMENT_SETUP.md`](../../ENVIRONMENT_SETUP.md) - Configuración de entornos
- [`/DEVELOPER_INTEGRATION_GUIDE.md`](../../DEVELOPER_INTEGRATION_GUIDE.md) - Guía de integración

### Frontend
- [`/FRONTEND_INTEGRATION_EXAMPLES.md`](../../FRONTEND_INTEGRATION_EXAMPLES.md) - Ejemplos de integración frontend
- [`/REQUERIMIENTOS_AUTH_RESPUESTA.md`](../../REQUERIMIENTOS_AUTH_RESPUESTA.md) - Especificaciones de autenticación

### Testing
- [`/microservices/TESTING.md`](../../microservices/TESTING.md) - Guía de testing
- [`/docs/testing/ENDPOINT_TESTING_DOCUMENTATION.md`](../../docs/testing/ENDPOINT_TESTING_DOCUMENTATION.md) - Testing de endpoints

### Deployment
- [`/docs/deployment/STARTUP_STATUS.md`](../../docs/deployment/STARTUP_STATUS.md) - Estado de servicios
- [`/docs/deployment/PORT_MAPPING.md`](../../docs/deployment/PORT_MAPPING.md) - Mapeo de puertos
- [`/docs/DOCKER.md`](../../docs/DOCKER.md) - Guía de Docker

---

## 🔑 Principios de Desarrollo

### Arquitectura
1. **Microservices Pattern** - Servicios independientes y desacoplados
2. **Database-per-Service** - Cada servicio tiene su propia BD
3. **API Gateway** - Punto de entrada único para clientes externos
4. **Async Operations** - Operaciones I/O asíncronas con async/await
5. **Service Discovery** - Consul para descubrimiento de servicios

### Data Management
1. **Soft Deletes** - Usar `deleted_at` en lugar de DELETE físico
2. **Audit Trail** - `created_at`, `updated_at`, `created_by` en todas las tablas
3. **String References** - Referencias cross-service usan `unique_id` (String), no FKs
4. **Alembic Migrations** - Todo cambio de esquema requiere migración
5. **Proper Indexing** - Índices en PKs, FKs, y campos de búsqueda

### Security
1. **JWT Authentication** - Tokens con expiración (30 min access, 7 días refresh)
2. **RBAC** - Control de acceso basado en roles y permisos
3. **Input Validation** - Validar todo input con Pydantic
4. **SQL Injection Prevention** - Solo queries parametrizadas
5. **Encryption** - AES-256 para datos sensibles, bcrypt para passwords

### Code Quality
1. **Type Hints** - Usar type hints en todo Python code
2. **Pydantic Schemas** - Request/response validation
3. **Error Handling** - Capturar y manejar errores apropiadamente
4. **Structured Logging** - JSON logs para todas las operaciones
5. **Tests** - Unit tests (>80% coverage), integration tests

### API Design
1. **RESTful** - Seguir convenciones REST
2. **Versioning** - `/api/v1/...` para todos los endpoints
3. **HTTP Status Codes** - Usar códigos apropiados (200, 201, 400, 401, 404, 500)
4. **OpenAPI/Swagger** - Documentación automática con FastAPI
5. **Pagination** - Paginar listas largas (default: 10 items)

---

## 🚀 Workflows Comunes

### 1. Agregar Nueva Funcionalidad

```bash
# 1. Product Manager define requisitos
→ Crear PRD con user stories y métricas de éxito

# 2. Business Analyst detalla requisitos
→ Documentar user stories, reglas de negocio, flujos

# 3. Backend Architect diseña solución
→ Diseñar esquema de BD, endpoints de API, integraciones

# 4. Backend Developer implementa
→ Crear migraciones Alembic
→ Implementar modelos SQLAlchemy
→ Crear endpoints FastAPI
→ Escribir tests

# 5. Frontend Developer crea UI
→ Crear componentes React/Vue
→ Integrar con API
→ Implementar validaciones

# 6. QA Tester valida
→ Ejecutar tests funcionales
→ Pruebas de integración
→ Validar reglas de negocio

# 7. Security Specialist revisa
→ Auditoría de seguridad
→ Validar autenticación/autorización
→ Revisar exposición de datos

# 8. DevOps Engineer despliega
→ Configurar en docker-compose
→ Desplegar a staging
→ Validar en producción
→ Configurar monitoreo
```

### 2. Resolver Bug Crítico

```bash
# 1. QA Tester reproduce y documenta
→ Crear bug report detallado
→ Pasos para reproducir
→ Logs y screenshots

# 2. Backend/Frontend Developer investiga
→ Reproducir localmente
→ Identificar causa raíz
→ Implementar fix
→ Agregar tests de regresión

# 3. QA Tester valida fix
→ Verificar bug está resuelto
→ Validar no hay regresiones
→ Aprobar para deploy

# 4. DevOps Engineer despliega hotfix
→ Deploy urgente a producción
→ Monitorear métricas
→ Confirmar resolución
```

### 3. Optimizar Performance

```bash
# 1. DevOps identifica problema
→ Monitorear dashboards de Grafana
→ Identificar servicio lento
→ Recolectar métricas

# 2. Database Specialist analiza queries
→ Revisar slow query logs
→ Analizar execution plans
→ Crear índices necesarios

# 3. Backend Architect evalúa arquitectura
→ Identificar cuellos de botella
→ Proponer mejoras arquitectónicas
→ Planificar caching

# 4. Backend Developer implementa
→ Optimizar queries
→ Implementar caching (Redis)
→ Refactorizar código ineficiente

# 5. QA Tester valida mejoras
→ Ejecutar tests de performance
→ Validar tiempos de respuesta
→ Confirmar mejoras
```

---

## 📞 Contacto y Soporte

### Para Consultas Técnicas
- **Backend:** Consultar con Backend Architect o Backend Developer agent
- **Frontend:** Consultar con Frontend Developer agent
- **Database:** Consultar con Database Specialist agent
- **DevOps:** Consultar con DevOps Engineer agent

### Para Consultas de Negocio
- **Requisitos:** Business Analyst agent
- **Priorización:** Product Manager agent
- **Testing:** QA Tester agent

### Para Consultas de Seguridad
- **Siempre:** Security Specialist agent

---

## 🔄 Actualización de Agentes

Estos perfiles de agentes se actualizan basándose en:
- Evolución del proyecto y stack tecnológico
- Lecciones aprendidas en sprints
- Nuevas mejores prácticas
- Feedback del equipo
- Cambios en arquitectura

**Última actualización:** 2025-10-01
**Versión:** 1.0.0

---

## 📝 Contribuir

Para mejorar los perfiles de agentes:
1. Identificar gaps o información desactualizada
2. Proponer mejoras específicas
3. Documentar nuevos patrones y best practices
4. Actualizar ejemplos de código
5. Agregar referencias a documentación

---

## 📖 Glosario

**Microservicio:** Servicio independiente con responsabilidad única
**API Gateway:** Punto de entrada centralizado para todos los clientes
**JWT:** JSON Web Token para autenticación stateless
**RBAC:** Role-Based Access Control
**ORM:** Object-Relational Mapping (SQLAlchemy)
**CI/CD:** Continuous Integration / Continuous Deployment
**RICE:** Reach, Impact, Confidence, Effort (framework de priorización)
**PRD:** Product Requirements Document
**OKR:** Objectives and Key Results
**NPS:** Net Promoter Score

---

**¡Bienvenido al equipo de desarrollo de Quenty!** 🚀
