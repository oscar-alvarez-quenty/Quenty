#!/bin/bash

# Complete build and deploy script for Quenty application
# This script builds Docker images, pushes to ECR, and updates ECS service
# Usage: ./build-and-deploy.sh [environment] [image-tag]
# Example: ./build-and-deploy.sh dev latest
# Example: ./build-and-deploy.sh prod v1.0.0

set -e

ENVIRONMENT=${1:-dev}
IMAGE_TAG=${2:-latest}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/../.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment. Must be one of: dev, staging, prod"
    exit 1
fi

print_status "Building and deploying Quenty application"
print_status "Environment: $ENVIRONMENT"
print_status "Image tag: $IMAGE_TAG"

# Get AWS region and account ID
AWS_REGION=$(aws configure get region || echo "us-east-1")
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    print_error "Unable to get AWS account ID. Please check your AWS credentials."
    exit 1
fi

# Get ECR repository URLs from Terraform outputs
cd "${SCRIPT_DIR}/../environments/${ENVIRONMENT}"

if [ ! -f "terraform.tfstate" ]; then
    print_error "Terraform state not found. Please run 'terraform apply' first."
    exit 1
fi

ECR_APP_REPO=$(terraform output -raw ecr_app_repository_url 2>/dev/null || echo "")
ECR_NGINX_REPO=$(terraform output -raw ecr_nginx_repository_url 2>/dev/null || echo "")

if [ -z "$ECR_APP_REPO" ]; then
    print_error "Unable to get ECR repository URL from Terraform outputs."
    exit 1
fi

print_status "ECR App Repository: $ECR_APP_REPO"
print_status "ECR Nginx Repository: $ECR_NGINX_REPO"

# Login to ECR
print_status "Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_APP_REPO

# Build and push application image
print_status "Building application Docker image..."
cd "$PROJECT_ROOT"

docker build -f Dockerfile -t ${ECR_APP_REPO}:${IMAGE_TAG} .
docker tag ${ECR_APP_REPO}:${IMAGE_TAG} ${ECR_APP_REPO}:latest

print_status "Pushing application image to ECR..."
docker push ${ECR_APP_REPO}:${IMAGE_TAG}
docker push ${ECR_APP_REPO}:latest

# Build and push nginx image if repository exists
if [ -n "$ECR_NGINX_REPO" ]; then
    print_status "Building nginx Docker image..."
    docker build -f docker/nginx/Dockerfile.prod -t ${ECR_NGINX_REPO}:${IMAGE_TAG} docker/nginx/
    docker tag ${ECR_NGINX_REPO}:${IMAGE_TAG} ${ECR_NGINX_REPO}:latest
    
    print_status "Pushing nginx image to ECR..."
    docker push ${ECR_NGINX_REPO}:${IMAGE_TAG}
    docker push ${ECR_NGINX_REPO}:latest
fi

# Get ECS cluster and service names
ECS_CLUSTER=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "quenty-${ENVIRONMENT}-cluster")
ECS_SERVICE=$(terraform output -raw service_name 2>/dev/null || echo "quenty-${ENVIRONMENT}-app")

print_status "ECS Cluster: $ECS_CLUSTER"
print_status "ECS Service: $ECS_SERVICE"

# Update ECS service to use new image
print_status "Updating ECS service with new image..."
aws ecs update-service \
    --cluster $ECS_CLUSTER \
    --service $ECS_SERVICE \
    --force-new-deployment \
    --region $AWS_REGION

print_status "Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster $ECS_CLUSTER \
    --services $ECS_SERVICE \
    --region $AWS_REGION

# Get ALB DNS name for access
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "")
if [ -n "$ALB_DNS" ]; then
    print_status "Application deployed successfully!"
    print_status "Access your application at: http://$ALB_DNS"
    print_status "API Documentation: http://$ALB_DNS/docs"
    print_status "Health Check: http://$ALB_DNS/health"
else
    print_status "Application deployed successfully!"
    print_warning "Unable to get ALB DNS name from outputs."
fi

print_status "Deployment completed!"

# Show service status
print_status "Current service status:"
aws ecs describe-services \
    --cluster $ECS_CLUSTER \
    --services $ECS_SERVICE \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
    --output table \
    --region $AWS_REGION