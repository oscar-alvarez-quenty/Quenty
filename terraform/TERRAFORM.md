# Terraform Infrastructure for Quenty Logistics Platform

This directory contains Terraform configurations to deploy the Quenty application infrastructure on AWS.

## Architecture Overview

The infrastructure includes:

- **VPC** with public/private subnets across multiple AZs
- **ECS Fargate** cluster for containerized applications
- **Application Load Balancer** for traffic distribution
- **RDS PostgreSQL** for database
- **ElastiCache Redis** for caching and session storage
- **ECR** repositories for container images
- **CloudWatch** for monitoring and logging
- **IAM** roles and policies for security

## Directory Structure

```
terraform/
├── main.tf                    # Root module configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── modules/                   # Reusable modules
│   ├── vpc/                   # VPC and networking
│   ├── ecs/                   # ECS cluster and services
│   ├── rds/                   # PostgreSQL database
│   ├── elasticache/           # Redis cluster
│   ├── alb/                   # Application Load Balancer
│   ├── ecr/                   # Container registries
│   ├── cloudwatch/            # Monitoring and alarms
│   └── iam/                   # IAM roles and policies
└── environments/              # Environment-specific configurations
    ├── dev/                   # Development environment
    ├── staging/               # Staging environment
    └── prod/                  # Production environment
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** 1.0+ installed
3. **Docker** for building and pushing images
4. **AWS permissions** for creating infrastructure resources

### Required AWS Permissions

The deploying user/role needs permissions for:
- EC2 (VPC, subnets, security groups)
- ECS (clusters, services, tasks)
- RDS (instances, subnet groups)
- ElastiCache (clusters, subnet groups)
- ELB (load balancers, target groups)
- ECR (repositories)
- IAM (roles, policies)
- CloudWatch (logs, dashboards, alarms)
- S3 (for Terraform state and ALB logs)

## Quick Start

### 1. Clone and Initialize

```bash
git clone <repository-url>
cd Quenty/DDD/terraform
```

### 2. Development Environment

```bash
cd environments/dev

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
db_password = "your-secure-dev-password"
EOF

# Plan deployment
terraform plan

# Apply changes
terraform apply
```

### 3. Production Environment

```bash
cd environments/prod

# Create S3 bucket for state (one-time setup)
aws s3 mb s3://quenty-terraform-state-prod

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
db_password = "your-very-secure-prod-password"
ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
domain_name = "api.quenty.com"
EOF

# Plan deployment
terraform plan

# Apply changes
terraform apply
```

## Configuration

### Environment Variables

Create a `terraform.tfvars` file for each environment:

**Development:**
```hcl
db_password = "dev_password_123"
```

**Production:**
```hcl
db_password = "super_secure_prod_password_456"
ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
domain_name = "api.quenty.com"
```

### Key Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS region for deployment | `us-east-1` | No |
| `environment` | Environment name | `dev` | No |
| `db_password` | Database password | - | Yes |
| `ssl_certificate_arn` | SSL certificate ARN | `""` | Prod only |
| `domain_name` | Application domain | `""` | No |

## Modules

### VPC Module (`modules/vpc/`)

Creates:
- VPC with configurable CIDR
- Public subnets for ALB
- Private subnets for ECS tasks
- Database subnets for RDS
- NAT gateways for outbound traffic
- VPC endpoints for AWS services

### ECS Module (`modules/ecs/`)

Creates:
- ECS Fargate cluster
- Task definitions
- ECS services with auto-scaling
- Security groups
- CloudWatch log groups

### RDS Module (`modules/rds/`)

Creates:
- PostgreSQL RDS instance
- DB subnet group
- Parameter group
- Security group
- Automated backups
- Performance Insights

### ElastiCache Module (`modules/elasticache/`)

Creates:
- Redis cluster
- Cache subnet group
- Parameter group
- Security group

### ALB Module (`modules/alb/`)

Creates:
- Application Load Balancer
- Target groups
- HTTP/HTTPS listeners
- S3 bucket for access logs
- Security groups

### ECR Module (`modules/ecr/`)

Creates:
- ECR repositories for app and nginx
- Lifecycle policies
- Repository policies

### IAM Module (`modules/iam/`)

Creates:
- ECS task execution role
- ECS task role
- Auto-scaling roles
- Policies for AWS service access

### CloudWatch Module (`modules/cloudwatch/`)

Creates:
- CloudWatch dashboards
- Metric alarms
- Log groups
- Log insights queries

## Deployment Process

### 1. Infrastructure Deployment

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan
```

### 2. Application Deployment

After infrastructure is ready:

```bash
# Get ECR repository URL
ECR_REPO=$(terraform output -raw ecr_app_repository_url)

# Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO

docker build -t $ECR_REPO:latest .
docker push $ECR_REPO:latest

# Update ECS service to use new image
aws ecs update-service --cluster quenty-dev-cluster --service quenty-dev-app --force-new-deployment
```

### 3. Database Migration

```bash
# Get RDS endpoint
DB_ENDPOINT=$(terraform output -raw database_endpoint)

# Run migrations (from local machine or ECS task)
docker run --rm \
  -e DATABASE_URL="postgresql://quenty_user:password@$DB_ENDPOINT:5432/quenty_db" \
  $ECR_REPO:latest \
  alembic upgrade head
```

## Monitoring

### CloudWatch Dashboard

Access the automatically created dashboard:
```bash
terraform output cloudwatch_dashboard_url
```

### Alarms

Configured alarms monitor:
- ECS CPU and memory utilization
- RDS CPU and connection count
- ALB response time and error rates

### Logs

Application logs are centralized in CloudWatch:
- `/ecs/quenty-{env}/app` - Application logs
- `/aws/rds/instance/quenty-{env}-postgres/postgresql` - Database logs

## Security Considerations

### Network Security

- Private subnets for application and database
- Security groups with minimal required access
- VPC endpoints to avoid internet routing

### Data Protection

- RDS encryption at rest
- ElastiCache encryption at rest
- S3 bucket encryption for logs
- SSL/TLS termination at ALB

### Access Control

- IAM roles with least privilege
- ECR repository policies
- No hardcoded credentials

## Scaling

### Auto Scaling

ECS services include auto-scaling based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)

### Manual Scaling

```bash
# Scale ECS service
aws ecs update-service \
  --cluster quenty-prod-cluster \
  --service quenty-prod-app \
  --desired-count 5
```

### Database Scaling

- RDS supports vertical scaling (instance type)
- Read replicas can be added for read scaling

## Cost Optimization

### Development Environment

- Uses smaller instance types
- Single AZ deployment for non-critical resources
- Shorter log retention periods

### Production Environment

- Multi-AZ for high availability
- Reserved instances for predictable workloads
- Lifecycle policies for log cleanup

## Backup and Disaster Recovery

### Automated Backups

- RDS automated backups (7-day retention)
- ElastiCache snapshots
- ALB access logs in S3

### Infrastructure Recovery

- Terraform state in S3 with versioning
- Infrastructure as Code for reproducibility
- Multi-AZ deployment for availability

## Troubleshooting

### Common Issues

1. **ECR Image Pull Errors**
   ```bash
   # Check ECR permissions
   aws ecr describe-repositories
   aws ecr get-login-password --region us-east-1
   ```

2. **ECS Service Not Starting**
   ```bash
   # Check ECS service events
   aws ecs describe-services --cluster quenty-dev-cluster --services quenty-dev-app
   
   # Check CloudWatch logs
   aws logs describe-log-streams --log-group-name /ecs/quenty-dev/app
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connectivity from ECS task
   aws ecs run-task --cluster quenty-dev-cluster --task-definition quenty-dev-app --overrides '{
     "containerOverrides": [{
       "name": "app",
       "command": ["python", "-c", "import psycopg2; print(\"OK\")"]
     }]
   }'
   ```

### Logs and Debugging

```bash
# View Terraform logs
export TF_LOG=DEBUG
terraform apply

# Check AWS CloudTrail for API calls
aws logs filter-log-events --log-group-name CloudTrail/QuentyAPILogs

# Monitor ECS service health
aws ecs describe-services --cluster quenty-dev-cluster --services quenty-dev-app
```

## Cleanup

### Destroy Environment

```bash
# Destroy development environment
cd environments/dev
terraform destroy

# Destroy production environment
cd environments/prod
terraform destroy
```

**Warning:** This will delete all data. Ensure backups are taken before destroying production environments.

## Support

For issues related to:
- Infrastructure: Check CloudWatch logs and AWS console
- Application: Review ECS task logs and service health
- Database: Monitor RDS performance metrics
- Networking: Verify security groups and VPC configuration

## Contributing

When modifying infrastructure:

1. Test changes in development environment first
2. Use `terraform plan` to review changes
3. Document any new variables or outputs
4. Update this README for significant changes