#!/bin/bash

# =============================================================================
# Quenty Endpoint Testing - Quick Start Script
# =============================================================================
# This script provides easy commands to run different types of endpoint tests
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_SCRIPT="$SCRIPT_DIR/test-all-endpoints.sh"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Quenty Microservices Endpoint Testing${NC}"
echo "=========================================="
echo ""

# Check if test script exists
if [ ! -f "$TEST_SCRIPT" ]; then
    echo "❌ Test script not found: $TEST_SCRIPT"
    exit 1
fi

# Make sure it's executable
chmod +x "$TEST_SCRIPT"

echo "Available test options:"
echo ""
echo "1. Basic endpoint test (quick)"
echo "2. Verbose endpoint test (detailed)"
echo "3. Generate JSON report"
echo "4. Check service health only"
echo "5. Monitor infrastructure"
echo "6. Run all tests and generate reports"
echo ""

read -p "Select option (1-6): " choice

case $choice in
    1)
        echo -e "${GREEN}Running basic endpoint tests...${NC}"
        "$TEST_SCRIPT"
        ;;
    2)
        echo -e "${GREEN}Running verbose endpoint tests...${NC}"
        "$TEST_SCRIPT" --verbose
        ;;
    3)
        echo -e "${GREEN}Generating JSON report...${NC}"
        "$TEST_SCRIPT" --json
        echo ""
        echo "📄 JSON report generated in test-results/"
        ls -la test-results/*.json | tail -1
        ;;
    4)
        echo -e "${GREEN}Checking service health...${NC}"
        echo ""
        services=(
            "api-gateway:8000"
            "customer-service:8001" 
            "order-service:8002"
            "pickup-service:8003"
            "international-shipping:8004"
            "microcredit-service:8005"
            "analytics-service:8006"
            "reverse-logistics:8007"
            "franchise-service:8008"
            "auth-service:8009"
        )
        
        for service in "${services[@]}"; do
            name=$(echo "$service" | cut -d: -f1)
            port=$(echo "$service" | cut -d: -f2)
            
            if curl -s --max-time 5 "http://localhost:$port/health" > /dev/null; then
                echo "✅ $name (port $port)"
            else
                echo "❌ $name (port $port)"
            fi
        done
        ;;
    5)
        echo -e "${GREEN}Checking infrastructure components...${NC}"
        echo ""
        
        components=(
            "Grafana:3000:/api/health"
            "Prometheus:9090:/-/healthy"
            "Loki:3100:/ready"
            "Jaeger:16686:/"
            "Consul:8500:/v1/status/leader"
        )
        
        for component in "${components[@]}"; do
            name=$(echo "$component" | cut -d: -f1)
            port=$(echo "$component" | cut -d: -f2)
            path=$(echo "$component" | cut -d: -f3)
            
            if curl -s --max-time 5 "http://localhost:$port$path" > /dev/null; then
                echo "✅ $name (http://localhost:$port)"
            else
                echo "❌ $name (http://localhost:$port)"
            fi
        done
        ;;
    6)
        echo -e "${GREEN}Running comprehensive tests with reports...${NC}"
        echo ""
        
        # Run verbose test with JSON output
        "$TEST_SCRIPT" --verbose --json
        
        echo ""
        echo -e "${YELLOW}📊 Test Summary:${NC}"
        
        # Get latest results
        latest_json=$(ls -t test-results/*.json 2>/dev/null | head -1)
        if [ -f "$latest_json" ]; then
            echo "📄 Latest JSON report: $latest_json"
            echo "📁 Latest text report: ${latest_json%.json}.txt"
            
            # Show summary if tools available
            if command -v python3 >/dev/null 2>&1; then
                echo ""
                echo "Quick Summary:"
                python3 -c "
import json
with open('$latest_json') as f:
    data = json.load(f)
    print(f\"✅ Passed: {data['passed_tests']}/{data['total_tests']}\")
    print(f\"❌ Failed: {data['failed_tests']}/{data['total_tests']}\")
    print(f\"📈 Success Rate: {data['success_rate']:.1f}%\")
"
            fi
        fi
        
        echo ""
        echo -e "${BLUE}📱 Access Points:${NC}"
        echo "🌐 Grafana Dashboard: http://localhost:3000"
        echo "📊 Prometheus: http://localhost:9090"  
        echo "🔍 Jaeger Tracing: http://localhost:16686"
        echo "🏛️ Consul UI: http://localhost:8500"
        echo ""
        echo "🔗 API Documentation:"
        echo "   • API Gateway: http://localhost:8000/docs"
        echo "   • Auth Service: http://localhost:8009/docs"
        echo "   • Customer Service: http://localhost:8001/docs"
        echo "   • Order Service: http://localhost:8002/docs"
        echo "   • And more... (check each service on its port/docs)"
        ;;
    *)
        echo "Invalid option. Please select 1-6."
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Test execution completed!${NC}"
echo ""
echo "💡 Tips:"
echo "   • View detailed logs: docker logs quenty-<service-name>"
echo "   • Restart services: docker compose -f docker-compose.microservices.yml restart"
echo "   • Monitor logs in Grafana: http://localhost:3000"
echo "   • Test specific endpoints manually via Swagger UI docs"
echo ""
echo "📚 For more information, see:"
echo "   • ENDPOINT_TESTING_DOCUMENTATION.md"
echo "   • GRAFANA_DASHBOARD_FILTERS.md"