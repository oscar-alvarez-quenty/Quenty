# Development Environment Configuration for Quenty

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

module "quenty_dev" {
  source = "../../"

  # Environment configuration
  environment = "dev"
  aws_region  = "us-east-1"

  # Networking
  vpc_cidr = "10.0.0.0/16"

  # Database configuration (development)
  db_instance_class     = "db.t3.micro"
  db_allocated_storage  = 20
  db_username          = "quenty_user"
  db_password          = var.db_password

  # Redis configuration (development)
  redis_node_type  = "cache.t3.micro"
  redis_num_nodes  = 1

  # Application configuration (development)
  app_cpu    = 256
  app_memory = 512
  app_count  = 1

  # SSL Certificate (optional for dev)
  ssl_certificate_arn = ""
}

# Variables
variable "db_password" {
  description = "Database password for development"
  type        = string
  sensitive   = true
}

# Outputs
output "alb_dns_name" {
  description = "ALB DNS name for development"
  value       = module.quenty_dev.alb_dns_name
}

output "ecr_app_repository_url" {
  description = "ECR repository URL for app"
  value       = module.quenty_dev.ecr_app_repository_url
}