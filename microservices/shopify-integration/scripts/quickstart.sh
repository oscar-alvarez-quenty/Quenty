#!/bin/bash

# Shopify Integration Quick Start Script
# This script sets up the Shopify integration service quickly

set -e

echo "🚀 Shopify Integration Quick Start"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose detected${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file with your Shopify credentials${NC}"
fi

# Build containers
echo -e "${YELLOW}Building Docker containers...${NC}"
docker-compose build

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 10

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose exec -T shopify-integration alembic upgrade head

# Check service health
echo -e "${YELLOW}Checking service health...${NC}"
sleep 5

HEALTH_STATUS=$(curl -s http://localhost:8010/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ Service is healthy${NC}"
else
    echo -e "${RED}⚠️  Service health check failed${NC}"
fi

# Display service URLs
echo ""
echo -e "${GREEN}🎉 Shopify Integration Service is ready!${NC}"
echo ""
echo "Service URLs:"
echo "  API:        http://localhost:8010"
echo "  Docs:       http://localhost:8010/docs"
echo "  Health:     http://localhost:8010/health"
echo "  Metrics:    http://localhost:8010/metrics"
echo "  Flower:     http://localhost:5556"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f shopify-integration"
echo "  Stop services:    docker-compose down"
echo "  Reset database:   docker-compose exec shopify-integration alembic downgrade base"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your Shopify credentials"
echo "2. Register your store using the API"
echo "3. Configure webhooks"
echo "4. Start syncing data"
echo ""
echo "For detailed instructions, see INTEGRATION_GUIDE.md"