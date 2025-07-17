# Quenty Terraform Infrastructure

Scripts de Terraform para desplegar la infraestructura de la plataforma logística Quenty en AWS.

## 🏗️ Arquitectura

La infraestructura incluye:

- **VPC** con subnets públicas/privadas en múltiples AZs
- **ECS Fargate** para aplicaciones containerizadas
- **Application Load Balancer** para distribución de tráfico
- **RDS PostgreSQL** para base de datos
- **ElastiCache Redis** para caché y sesiones
- **ECR** para repositorios de imágenes Docker
- **CloudWatch** para monitoreo y logging
- **IAM** roles y políticas de seguridad

## 📁 Estructura

```
terraform/
├── main.tf                    # Configuración principal
├── variables.tf               # Variables de entrada
├── outputs.tf                 # Valores de salida
├── modules/                   # Módulos reutilizables
│   ├── vpc/                   # Red y subnets
│   ├── ecs/                   # Cluster y servicios ECS
│   ├── rds/                   # Base de datos PostgreSQL
│   ├── elasticache/           # Cluster Redis
│   ├── alb/                   # Load Balancer
│   ├── ecr/                   # Repositorios Docker
│   ├── cloudwatch/            # Monitoreo
│   └── iam/                   # Roles y políticas
├── environments/              # Configuraciones por ambiente
│   ├── dev/                   # Desarrollo
│   ├── staging/               # Staging
│   └── prod/                  # Producción
└── scripts/                   # Scripts de despliegue
    ├── deploy.sh              # Despliegue de infraestructura
    └── build-and-deploy.sh    # Build y deploy de aplicación
```

## 🚀 Inicio Rápido

### 1. Prerrequisitos

```bash
# Instalar herramientas
brew install terraform awscli docker

# Configurar AWS CLI
aws configure
```

### 2. Despliegue de Desarrollo

```bash
# Clonar repositorio
git clone <repository-url>
cd Quenty/DDD/terraform

# Configurar variables
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con tus valores

# Desplegar infraestructura
../scripts/deploy.sh dev init
../scripts/deploy.sh dev apply
```

### 3. Despliegue de Aplicación

```bash
# Build y deploy de la aplicación
./scripts/build-and-deploy.sh dev latest
```

## ⚙️ Configuración

### Variables de Ambiente

**Desarrollo** (`environments/dev/terraform.tfvars`):
```hcl
db_password = "dev_password_123"
```

**Producción** (`environments/prod/terraform.tfvars`):
```hcl
db_password = "super_secure_prod_password"
ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
domain_name = "api.quenty.com"
```

### Scripts de Despliegue

**Infraestructura:**
```bash
# Planificar cambios
./scripts/deploy.sh dev plan

# Aplicar cambios
./scripts/deploy.sh dev apply

# Destruir recursos
./scripts/deploy.sh dev destroy
```

**Aplicación:**
```bash
# Build y deploy completo
./scripts/build-and-deploy.sh prod v1.0.0

# Solo para desarrollo
./scripts/build-and-deploy.sh dev latest
```

## 📊 Monitoreo

### CloudWatch Dashboard
- Métricas de ECS (CPU, memoria)
- Métricas de ALB (requests, latencia)
- Métricas de RDS (conexiones, CPU)
- Métricas de Redis (conexiones, hits/misses)

### Alarmas Configuradas
- CPU alto en ECS (>80%)
- Memoria alta en ECS (>85%)
- Tiempo de respuesta alto en ALB (>2s)
- Errores 5XX en ALB (>10)
- CPU alto en RDS (>80%)

### Logs Centralizados
- `/ecs/quenty-{env}/app` - Logs de aplicación
- `/aws/rds/instance/quenty-{env}-postgres/postgresql` - Logs de DB

## 🔒 Seguridad

### Red
- Subnets privadas para aplicación y DB
- Security groups con acceso mínimo requerido
- VPC endpoints para servicios AWS

### Datos
- Encriptación en RDS y ElastiCache
- Encriptación en S3 para logs
- Terminación SSL/TLS en ALB

### Acceso
- Roles IAM con privilegios mínimos
- Políticas de repositorio ECR
- Sin credenciales hardcodeadas

## 📈 Escalamiento

### Auto Scaling ECS
- CPU utilization (objetivo: 70%)
- Memory utilization (objetivo: 80%)

### Escalamiento Manual
```bash
# Escalar servicio ECS
aws ecs update-service \
  --cluster quenty-prod-cluster \
  --service quenty-prod-app \
  --desired-count 5
```

## 💰 Optimización de Costos

### Desarrollo
- Instancias más pequeñas
- Single AZ para recursos no críticos
- Retención de logs más corta

### Producción
- Multi-AZ para alta disponibilidad
- Reserved instances para cargas predecibles
- Políticas de lifecycle para logs

## 🔧 Troubleshooting

### Problemas Comunes

1. **Error al hacer pull de ECR**
   ```bash
   aws ecr get-login-password --region us-east-1
   ```

2. **Servicio ECS no inicia**
   ```bash
   aws ecs describe-services --cluster quenty-dev-cluster --services quenty-dev-app
   aws logs describe-log-streams --log-group-name /ecs/quenty-dev/app
   ```

3. **Problemas de conectividad a DB**
   ```bash
   # Verificar security groups y VPC
   aws ec2 describe-security-groups --group-ids sg-xxx
   ```

### Comandos Útiles

```bash
# Ver outputs de Terraform
terraform output

# Estado del servicio ECS
aws ecs describe-services --cluster quenty-dev-cluster --services quenty-dev-app

# Logs de aplicación
aws logs tail /ecs/quenty-dev/app --follow

# Métricas de CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=quenty-dev-app \
  --start-time 2023-01-01T00:00:00Z \
  --end-time 2023-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average
```

## 🧹 Limpieza

```bash
# Destruir ambiente completo
./scripts/deploy.sh dev destroy

# ADVERTENCIA: Esto eliminará todos los datos
# Asegúrate de tener backups antes de destruir producción
```

## 📞 Soporte

Para problemas relacionados con:
- **Infraestructura**: Revisar logs de CloudWatch y consola AWS
- **Aplicación**: Revisar logs de tareas ECS y health checks
- **Base de datos**: Monitorear métricas de performance de RDS
- **Red**: Verificar security groups y configuración VPC

## 🤝 Contribución

Al modificar la infraestructura:

1. Probar cambios en desarrollo primero
2. Usar `terraform plan` para revisar cambios
3. Documentar nuevas variables u outputs
4. Actualizar este README para cambios significativos