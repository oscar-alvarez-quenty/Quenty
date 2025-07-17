#!/bin/bash

# Deployment script for Quenty Terraform infrastructure
# Usage: ./deploy.sh [environment] [action]
# Example: ./deploy.sh dev plan
# Example: ./deploy.sh prod apply

set -e

ENVIRONMENT=${1:-dev}
ACTION=${2:-plan}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../environments/${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate inputs
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment. Must be one of: dev, staging, prod"
    exit 1
fi

if [[ ! "$ACTION" =~ ^(init|plan|apply|destroy|output)$ ]]; then
    print_error "Invalid action. Must be one of: init, plan, apply, destroy, output"
    exit 1
fi

# Check if terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    print_error "Terraform directory not found: $TERRAFORM_DIR"
    exit 1
fi

# Check if terraform.tfvars exists
if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ] && [[ "$ACTION" != "init" ]]; then
    print_warning "terraform.tfvars not found in $TERRAFORM_DIR"
    print_warning "Copy terraform.tfvars.example to terraform.tfvars and update values"
    if [ -f "$TERRAFORM_DIR/terraform.tfvars.example" ]; then
        print_status "Example file available: $TERRAFORM_DIR/terraform.tfvars.example"
    fi
    exit 1
fi

print_status "Deploying to environment: $ENVIRONMENT"
print_status "Action: $ACTION"
print_status "Working directory: $TERRAFORM_DIR"

cd "$TERRAFORM_DIR"

case $ACTION in
    init)
        print_status "Initializing Terraform..."
        terraform init
        ;;
    plan)
        print_status "Planning Terraform changes..."
        terraform plan -out=tfplan
        ;;
    apply)
        print_status "Applying Terraform changes..."
        if [ -f "tfplan" ]; then
            terraform apply tfplan
            rm -f tfplan
        else
            print_warning "No plan file found. Running plan and apply..."
            terraform plan -out=tfplan
            terraform apply tfplan
            rm -f tfplan
        fi
        ;;
    destroy)
        print_warning "This will destroy all resources in the $ENVIRONMENT environment!"
        read -p "Are you sure? Type 'yes' to continue: " -r
        if [[ $REPLY == "yes" ]]; then
            terraform destroy
        else
            print_status "Destroy cancelled."
        fi
        ;;
    output)
        print_status "Showing Terraform outputs..."
        terraform output
        ;;
esac

print_status "Operation completed successfully!"