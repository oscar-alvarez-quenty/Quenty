# Main Terraform configuration for Quenty Logistics Platform
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration (uncomment and configure for remote state)
  # backend "s3" {
  #   bucket = "quenty-terraform-state"
  #   key    = "quenty/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Quenty"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix = local.name_prefix
  cidr_block  = var.vpc_cidr
  azs         = data.aws_availability_zones.available.names
  
  tags = local.common_tags
}

# IAM Module
module "iam" {
  source = "./modules/iam"
  
  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# ECR Module
module "ecr" {
  source = "./modules/ecr"
  
  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# RDS Module
module "rds" {
  source = "./modules/rds"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  db_instance_class = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_username       = var.db_username
  db_password       = var.db_password
  
  tags = local.common_tags
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  node_type     = var.redis_node_type
  num_cache_nodes = var.redis_num_nodes
  
  tags = local.common_tags
}

# Application Load Balancer Module
module "alb" {
  source = "./modules/alb"
  
  name_prefix       = local.name_prefix
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  
  certificate_arn = var.ssl_certificate_arn
  
  tags = local.common_tags
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  # Dependencies
  target_group_arn = module.alb.target_group_arn
  task_role_arn    = module.iam.ecs_task_role_arn
  execution_role_arn = module.iam.ecs_execution_role_arn
  alb_security_group_id = module.alb.security_group_id
  
  # ECR
  app_image_uri = module.ecr.app_repository_url
  
  # Database
  database_url = module.rds.database_url
  
  # Redis
  redis_url = module.elasticache.redis_url
  
  # Application settings
  app_cpu    = var.app_cpu
  app_memory = var.app_memory
  app_count  = var.app_count
  
  tags = local.common_tags
}

# CloudWatch Module
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  name_prefix = local.name_prefix
  
  # ECS cluster name for monitoring
  ecs_cluster_name = module.ecs.cluster_name
  alb_name = "${local.name_prefix}-alb"
  
  tags = local.common_tags
}