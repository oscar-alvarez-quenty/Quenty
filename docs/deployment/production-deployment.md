# Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Quenty microservices platform to production environments, including cloud platforms, container orchestration, security configurations, and operational procedures.

## Production Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐     │
│  │  Load Balancer  │      │      CDN        │      │   API Gateway   │     │
│  │   (AWS ALB/     │      │  (CloudFlare/   │      │   (Kong/Nginx)  │     │
│  │    GCP LB)      │      │   CloudFront)   │      │                 │     │
│  └─────────┬───────┘      └─────────┬───────┘      └─────────┬───────┘     │
│            │                        │                        │             │
│            └────────────────────────┼────────────────────────┘             │
│                                     │                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    KUBERNETES CLUSTER                                  │ │
│  │                                                                         │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │ │
│  │  │ Customer Service│  │  Order Service  │  │ Shipping Service│       │ │
│  │  │   (3 replicas)  │  │   (3 replicas)  │  │   (2 replicas)  │       │ │
│  │  └─────────┬───────┘  └─────────┬───────┘  └─────────┬───────┘       │ │
│  │            │                    │                    │               │ │
│  │  ┌─────────▼───────┐  ┌─────────▼───────┐  ┌─────────▼───────┐       │ │
│  │  │ Customer DB     │  │   Order DB     │  │  Shipping DB    │       │ │
│  │  │ (Primary +      │  │ (Primary +     │  │ (Primary +      │       │ │
│  │  │  Read Replica)  │  │  Read Replica) │  │  Read Replica)  │       │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                   SHARED SERVICES                              │   │ │
│  │  │                                                                 │   │ │
│  │  │ Redis Cluster    RabbitMQ Cluster    Consul Cluster           │   │ │
│  │  │ (3 nodes)        (3 nodes)           (3 nodes)                │   │ │
│  │  │                                                                 │   │ │
│  │  │ Elasticsearch    Prometheus HA       Grafana HA               │   │ │
│  │  │ (3 nodes)        (2 instances)       (2 instances)            │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                       EXTERNAL SERVICES                                │ │
│  │                                                                         │ │
│  │  S3/GCS (File Storage)    CloudWatch/Stackdriver (Monitoring)          │ │
│  │  Route53/Cloud DNS        Certificate Manager                          │ │
│  │  Secrets Manager          CI/CD Pipeline                               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-managed)
- kubectl configured
- Helm 3.x installed
- Docker registry (ECR, GCR, DockerHub)

### Namespace Configuration

```yaml
# k8s/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: quenty-prod
  labels:
    name: quenty-prod
    environment: production
---
apiVersion: v1
kind: Namespace
metadata:
  name: quenty-monitoring
  labels:
    name: quenty-monitoring
    environment: production
```

### ConfigMaps and Secrets

#### Application ConfigMap
```yaml
# k8s/configmaps/app-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: quenty-config
  namespace: quenty-prod
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  CONSUL_HOST: "consul-service"
  CONSUL_PORT: "8500"
  REDIS_HOST: "redis-cluster"
  REDIS_PORT: "6379"
  RABBITMQ_HOST: "rabbitmq-cluster"
  RABBITMQ_PORT: "5672"
  PROMETHEUS_HOST: "prometheus-service"
  JAEGER_HOST: "jaeger-collector"
```

#### Database Configuration
```yaml
# k8s/configmaps/db-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: database-config
  namespace: quenty-prod
data:
  CUSTOMER_DB_HOST: "customer-db-primary"
  CUSTOMER_DB_PORT: "5432"
  CUSTOMER_DB_NAME: "customer_db"
  ORDER_DB_HOST: "order-db-primary"
  ORDER_DB_PORT: "5432"  
  ORDER_DB_NAME: "order_db"
  SHIPPING_DB_HOST: "shipping-db-primary"
  SHIPPING_DB_PORT: "5432"
  SHIPPING_DB_NAME: "intl_shipping_db"
```

#### Secrets
```yaml
# k8s/secrets/app-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: quenty-secrets
  namespace: quenty-prod
type: Opaque
stringData:
  JWT_SECRET_KEY: "your-super-secret-jwt-key"
  DATABASE_CUSTOMER_PASSWORD: "secure-customer-password"
  DATABASE_ORDER_PASSWORD: "secure-order-password"
  DATABASE_SHIPPING_PASSWORD: "secure-shipping-password"
  REDIS_PASSWORD: "secure-redis-password"
  RABBITMQ_USER: "quenty"
  RABBITMQ_PASSWORD: "secure-rabbitmq-password"
  DHL_API_KEY: "your-dhl-api-key"
  FEDEX_API_KEY: "your-fedex-api-key"
  UPS_API_KEY: "your-ups-api-key"
```

### Database Deployments

#### PostgreSQL with High Availability
```yaml
# k8s/databases/postgresql-ha.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: customer-db-cluster
  namespace: quenty-prod
spec:
  instances: 3
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      work_mem: "4MB"
      maintenance_work_mem: "64MB"
      
  bootstrap:
    initdb:
      database: customer_db
      owner: customer
      secret:
        name: customer-db-credentials
        
  storage:
    size: 100Gi
    storageClass: ssd-storage
    
  monitoring:
    enabled: true
    
  backup:
    retentionPolicy: "30d"
    barmanObjectStore:
      destinationPath: s3://quenty-backups/customer-db
      s3Credentials:
        accessKeyId:
          name: s3-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: s3-credentials
          key: SECRET_ACCESS_KEY
      wal:
        retention: "7d"
      data:
        retention: "30d"
```

### Service Deployments

#### Customer Service
```yaml
# k8s/services/customer-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customer-service
  namespace: quenty-prod
  labels:
    app: customer-service
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: customer-service
  template:
    metadata:
      labels:
        app: customer-service
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8001"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: customer-service
        image: your-registry/quenty-customer-service:v1.0.0
        ports:
        - containerPort: 8001
          name: http
        env:
        - name: SERVICE_NAME
          value: "customer-service"
        - name: DATABASE_URL
          value: "postgresql+asyncpg://customer:$(DATABASE_CUSTOMER_PASSWORD)@customer-db-primary:5432/customer_db"
        - name: DATABASE_CUSTOMER_PASSWORD
          valueFrom:
            secretKeyRef:
              name: quenty-secrets
              key: DATABASE_CUSTOMER_PASSWORD
        - name: REDIS_URL
          value: "redis://:$(REDIS_PASSWORD)@redis-cluster:6379/1"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: quenty-secrets
              key: REDIS_PASSWORD
        envFrom:
        - configMapRef:
            name: quenty-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL
---
apiVersion: v1
kind: Service
metadata:
  name: customer-service
  namespace: quenty-prod
  labels:
    app: customer-service
spec:
  selector:
    app: customer-service
  ports:
  - port: 8001
    targetPort: 8001
    name: http
  type: ClusterIP
```

#### Order Service
```yaml
# k8s/services/order-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: quenty-prod
  labels:
    app: order-service
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8002"
    spec:
      containers:
      - name: order-service
        image: your-registry/quenty-order-service:v1.0.0
        ports:
        - containerPort: 8002
        env:
        - name: SERVICE_NAME
          value: "order-service"
        - name: DATABASE_URL
          value: "postgresql+asyncpg://order:$(DATABASE_ORDER_PASSWORD)@order-db-primary:5432/order_db"
        - name: DATABASE_ORDER_PASSWORD
          valueFrom:
            secretKeyRef:
              name: quenty-secrets
              key: DATABASE_ORDER_PASSWORD
        - name: CUSTOMER_SERVICE_URL
          value: "http://customer-service:8001"
        envFrom:
        - configMapRef:
            name: quenty-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: quenty-prod
spec:
  selector:
    app: order-service
  ports:
  - port: 8002
    targetPort: 8002
  type: ClusterIP
```

### Ingress Configuration

```yaml
# k8s/ingress/api-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: quenty-api-ingress
  namespace: quenty-prod
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.quenty.com
    secretName: quenty-api-tls
  rules:
  - host: api.quenty.com
    http:
      paths:
      - path: /api/v1/(users|companies|auth).*
        pathType: Prefix
        backend:
          service:
            name: customer-service
            port:
              number: 8001
      - path: /api/v1/(products|orders|inventory).*
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 8002
      - path: /api/v1/(manifests|shipping|carriers).*
        pathType: Prefix
        backend:
          service:
            name: international-shipping-service
            port:
              number: 8004
```

## Infrastructure as Code

### Terraform Configuration

#### AWS EKS Cluster
```hcl
# terraform/aws/main.tf
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "quenty-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  
  tags = {
    Environment = "production"
    Project     = "quenty"
  }
}

module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "quenty-prod"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  node_groups = {
    main = {
      desired_capacity = 6
      max_capacity     = 10
      min_capacity     = 3
      
      instance_types = ["m5.large"]
      
      k8s_labels = {
        Environment = "production"
        Application = "quenty"
      }
    }
    
    monitoring = {
      desired_capacity = 2
      max_capacity     = 3
      min_capacity     = 1
      
      instance_types = ["m5.xlarge"]
      
      k8s_labels = {
        Environment = "production"
        NodeType    = "monitoring"
      }
      
      taints = {
        monitoring = {
          key    = "monitoring"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
}
```

#### RDS Configuration
```hcl
# terraform/aws/rds.tf
resource "aws_rds_cluster" "customer_db" {
  cluster_identifier      = "quenty-customer-db"
  engine                 = "aurora-postgresql"
  engine_version         = "13.7"
  availability_zones     = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  database_name          = "customer_db"
  master_username        = "customer"
  master_password        = var.customer_db_password
  backup_retention_period = 30
  preferred_backup_window = "07:00-09:00"
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  storage_encrypted = true
  
  tags = {
    Name        = "quenty-customer-db"
    Environment = "production"
  }
}

resource "aws_rds_cluster_instance" "customer_db_instances" {
  count              = 2
  identifier         = "quenty-customer-db-${count.index}"
  cluster_identifier = aws_rds_cluster.customer_db.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.customer_db.engine
  engine_version     = aws_rds_cluster.customer_db.engine_version
}
```

### Helm Charts

#### Custom Helm Chart Structure
```
helm/quenty/
├── Chart.yaml
├── values.yaml
├── values-production.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   └── pdb.yaml
└── charts/
    ├── postgresql/
    ├── redis/
    └── rabbitmq/
```

#### Values Configuration
```yaml
# helm/quenty/values-production.yaml
global:
  environment: production
  imageRegistry: your-registry.com
  imageTag: "v1.0.0"
  
customerService:
  enabled: true
  replicaCount: 3
  image:
    repository: quenty-customer-service
    tag: "v1.0.0"
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80

orderService:
  enabled: true
  replicaCount: 3
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

postgresql:
  enabled: true
  auth:
    postgresPassword: "secure-postgres-password"
  primary:
    persistence:
      size: 100Gi
      storageClass: "ssd-storage"
  readReplicas:
    replicaCount: 2
    
redis:
  enabled: true
  architecture: replication
  auth:
    password: "secure-redis-password"
  master:
    persistence:
      size: 10Gi
  replica:
    replicaCount: 2
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/production-deploy.yml
name: Production Deployment

on:
  push:
    tags:
      - 'v*'

env:
  REGISTRY: your-registry.com
  CLUSTER_NAME: quenty-prod
  CLUSTER_REGION: us-east-1

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [customer, order, international-shipping]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd microservices/${{ matrix.service }}
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        cd microservices/${{ matrix.service }}
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Build Docker image
      run: |
        cd microservices/${{ matrix.service }}
        docker build -t $REGISTRY/quenty-${{ matrix.service }}-service:${{ github.ref_name }} .
    
    - name: Push Docker image
      run: |
        docker push $REGISTRY/quenty-${{ matrix.service }}-service:${{ github.ref_name }}

  deploy:
    needs: build-and-test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.CLUSTER_REGION }}
    
    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --region $CLUSTER_REGION --name $CLUSTER_NAME
    
    - name: Deploy with Helm
      run: |
        helm upgrade --install quenty ./helm/quenty \
          -f helm/quenty/values-production.yaml \
          --set global.imageTag=${{ github.ref_name }} \
          --namespace quenty-prod \
          --create-namespace \
          --wait
    
    - name: Verify deployment
      run: |
        kubectl rollout status deployment/customer-service -n quenty-prod
        kubectl rollout status deployment/order-service -n quenty-prod
        kubectl rollout status deployment/international-shipping-service -n quenty-prod
    
    - name: Run smoke tests
      run: |
        kubectl run smoke-test --rm -i --restart=Never --image=curlimages/curl -- \
          curl -f http://customer-service.quenty-prod.svc.cluster.local:8001/health
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# k8s/monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: quenty-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              - alertmanager:9093
    
    scrape_configs:
      - job_name: 'kubernetes-apiservers'
        kubernetes_sd_configs:
        - role: endpoints
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
        relabel_configs:
        - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
          action: keep
          regex: default;kubernetes;https
      
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
        - role: pod
        relabel_configs:
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
          action: keep
          regex: true
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
          action: replace
          target_label: __metrics_path__
          regex: (.+)
        - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
          action: replace
          regex: ([^:]+)(?::\d+)?;(\d+)
          replacement: $1:$2
          target_label: __address__
        - action: labelmap
          regex: __meta_kubernetes_pod_label_(.+)
        - source_labels: [__meta_kubernetes_namespace]
          action: replace
          target_label: kubernetes_namespace
        - source_labels: [__meta_kubernetes_pod_name]
          action: replace
          target_label: kubernetes_pod_name
      
      - job_name: 'quenty-services'
        static_configs:
        - targets: ['customer-service:8001', 'order-service:8002', 'international-shipping-service:8004']
        metrics_path: /metrics
```

### Alerting Rules

```yaml
# k8s/monitoring/alert-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: quenty-monitoring
data:
  quenty-alerts.yml: |
    groups:
    - name: quenty.rules
      rules:
      - alert: ServiceDown
        expr: up == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.job }} has been down for more than 5 minutes."
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }} on {{ $labels.job }}"
      
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time on {{ $labels.job }}"
          description: "95th percentile response time is {{ $value }}s on {{ $labels.job }}"
      
      - alert: DatabaseConnectionFailure
        expr: increase(database_connection_errors_total[5m]) > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failures on {{ $labels.job }}"
          description: "{{ $value }} database connection failures in the last 5 minutes"
```

## Security Configuration

### Network Policies

```yaml
# k8s/security/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quenty-network-policy
  namespace: quenty-prod
spec:
  podSelector:
    matchLabels:
      app: customer-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: order-service
    ports:
    - protocol: TCP
      port: 8001
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: customer-db
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Pod Security Policies

```yaml
# k8s/security/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: quenty-restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## Backup and Disaster Recovery

### Database Backup Strategy

```yaml
# k8s/backup/pg-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgresql-backup
  namespace: quenty-prod
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: pg-backup
            image: postgres:15-alpine
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: quenty-secrets
                  key: DATABASE_CUSTOMER_PASSWORD
            command:
            - /bin/bash
            - -c
            - |
              DATE=$(date +%Y%m%d_%H%M%S)
              pg_dump -h customer-db-primary -U customer -d customer_db | gzip > /backup/customer_db_${DATE}.sql.gz
              aws s3 cp /backup/customer_db_${DATE}.sql.gz s3://quenty-backups/customer-db/
              # Keep only last 30 days
              find /backup -name "customer_db_*.sql.gz" -mtime +30 -delete
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### Application State Backup

```bash
#!/bin/bash
# scripts/backup-application-state.sh

NAMESPACE="quenty-prod"
BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Kubernetes resources
kubectl get all -n $NAMESPACE -o yaml > $BACKUP_DIR/k8s-resources.yaml
kubectl get secrets -n $NAMESPACE -o yaml > $BACKUP_DIR/secrets.yaml
kubectl get configmaps -n $NAMESPACE -o yaml > $BACKUP_DIR/configmaps.yaml

# Backup persistent volumes
kubectl get pv -o yaml > $BACKUP_DIR/persistent-volumes.yaml

# Upload to S3
aws s3 sync $BACKUP_DIR s3://quenty-backups/k8s-state/$(basename $BACKUP_DIR)

echo "Backup completed: $BACKUP_DIR"
```

## Performance Optimization

### Resource Allocation

```yaml
# k8s/performance/resource-quotas.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quenty-quota
  namespace: quenty-prod
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "20"
    pods: "50"
    services: "20"
```

### Horizontal Pod Autoscaler

```yaml
# k8s/performance/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: customer-service-hpa
  namespace: quenty-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: customer-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
```

## Operational Procedures

### Deployment Checklist

1. **Pre-deployment:**
   - [ ] Run full test suite
   - [ ] Security scan completed
   - [ ] Database migration scripts reviewed
   - [ ] Backup completed
   - [ ] Rollback plan prepared

2. **Deployment:**
   - [ ] Deploy to staging environment
   - [ ] Run smoke tests
   - [ ] Performance tests passed
   - [ ] Deploy to production
   - [ ] Health checks passing

3. **Post-deployment:**
   - [ ] Monitor error rates
   - [ ] Check application metrics
   - [ ] Verify database connections
   - [ ] Confirm external integrations
   - [ ] Document deployment

### Troubleshooting Runbook

#### Service Not Starting
```bash
# Check pod status
kubectl get pods -n quenty-prod -l app=customer-service

# Check pod logs
kubectl logs -n quenty-prod -l app=customer-service --tail=100

# Check events
kubectl get events -n quenty-prod --sort-by=.metadata.creationTimestamp

# Check resources
kubectl describe pod -n quenty-prod <pod-name>
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl run --rm -i --tty debug --image=postgres:15-alpine --restart=Never -- \
  psql -h customer-db-primary -U customer -d customer_db

# Check database pod status
kubectl get pods -n quenty-prod -l app=customer-db

# Check database logs
kubectl logs -n quenty-prod -l app=customer-db
```

#### Performance Issues
```bash
# Check resource usage
kubectl top pods -n quenty-prod

# Check HPA status
kubectl get hpa -n quenty-prod

# Scale manually if needed
kubectl scale deployment customer-service --replicas=5 -n quenty-prod
```

This production deployment guide provides a comprehensive foundation for deploying the Quenty microservices platform to production environments with high availability, security, and operational excellence.