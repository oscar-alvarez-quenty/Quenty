# Production Environment Configuration for Quenty

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for production
  backend "s3" {
    bucket = "quenty-terraform-state-prod"
    key    = "quenty/prod/terraform.tfstate"
    region = "us-east-1"
  }
}

module "quenty_prod" {
  source = "../../"

  # Environment configuration
  environment = "prod"
  aws_region  = "us-east-1"

  # Networking
  vpc_cidr = "10.0.0.0/16"

  # Database configuration (production)
  db_instance_class     = "db.t3.small"
  db_allocated_storage  = 100
  db_username          = "quenty_user"
  db_password          = var.db_password

  # Redis configuration (production)
  redis_node_type  = "cache.t3.small"
  redis_num_nodes  = 2

  # Application configuration (production)
  app_cpu    = 1024
  app_memory = 2048
  app_count  = 3

  # SSL Certificate (required for production)
  ssl_certificate_arn = var.ssl_certificate_arn

  # Domain
  domain_name = var.domain_name
}

# Variables
variable "db_password" {
  description = "Database password for production"
  type        = string
  sensitive   = true
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for production"
  type        = string
}

variable "domain_name" {
  description = "Domain name for production"
  type        = string
}

# Outputs
output "alb_dns_name" {
  description = "ALB DNS name for production"
  value       = module.quenty_prod.alb_dns_name
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.quenty_prod.cloudwatch_log_group
}