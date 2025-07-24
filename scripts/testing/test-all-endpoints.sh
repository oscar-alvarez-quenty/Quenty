#!/bin/bash

# =============================================================================
# Quenty Microservices Comprehensive Endpoint Testing Script
# =============================================================================
# Tests all microservice endpoints and generates a detailed report
# Usage: ./test-all-endpoints.sh [--verbose] [--json] [--auth-token TOKEN]
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$RESULTS_DIR/endpoint_test_report_$TIMESTAMP.txt"
JSON_REPORT="$RESULTS_DIR/endpoint_test_report_$TIMESTAMP.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
VERBOSE=false
JSON_OUTPUT=false
AUTH_TOKEN=""

# Service definitions
declare -A SERVICES=(
    ["api-gateway"]="8000"
    ["customer-service"]="8001"
    ["order-service"]="8002"
    ["pickup-service"]="8003"
    ["international-shipping"]="8004"
    ["microcredit-service"]="8005"
    ["analytics-service"]="8006"
    ["reverse-logistics"]="8007"
    ["franchise-service"]="8008"
    ["auth-service"]="8009"
)

# Test results
declare -A TEST_RESULTS
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --auth-token)
            AUTH_TOKEN="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--verbose] [--json] [--auth-token TOKEN]"
            echo "  --verbose     Show detailed output"
            echo "  --json        Generate JSON report"
            echo "  --auth-token  JWT token for authenticated endpoints"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
log() {
    echo -e "${1}" | tee -a "$REPORT_FILE"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${1}" | tee -a "$REPORT_FILE"
    fi
}

test_endpoint() {
    local service_name="$1"
    local port="$2"
    local endpoint="$3"
    local method="${4:-GET}"
    local expected_status="${5:-200}"
    local description="$6"
    local auth_required="${7:-false}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    local url="http://localhost:$port$endpoint"
    local auth_header=""
    
    if [ "$auth_required" = true ] && [ -n "$AUTH_TOKEN" ]; then
        auth_header="-H \"Authorization: Bearer $AUTH_TOKEN\""
    fi
    
    log_verbose "Testing: $method $url"
    
    if [ "$method" = "GET" ]; then
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" $auth_header "$url" 2>/dev/null)
    elif [ "$method" = "POST" ]; then
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $auth_header "$url" 2>/dev/null)
    elif [ "$method" = "PUT" ]; then
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X PUT $auth_header "$url" 2>/dev/null)
    elif [ "$method" = "DELETE" ]; then
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X DELETE $auth_header "$url" 2>/dev/null)
    fi
    
    local body=$(echo "$response" | sed 's/HTTPSTATUS\:.*//g')
    local status=$(echo "$response" | tr -d '\n' | sed 's/.*HTTPSTATUS://')
    
    local result_key="${service_name}_${endpoint//\//_}"
    
    if [ "$status" = "$expected_status" ]; then
        log "✅ PASS: $service_name $endpoint ($status)"
        TEST_RESULTS["$result_key"]="PASS:$status:$description"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        log "❌ FAIL: $service_name $endpoint (Expected: $expected_status, Got: $status)"
        TEST_RESULTS["$result_key"]="FAIL:$status:$description"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    log_verbose "Response Body: $(echo "$body" | cut -c1-100)..."
    log_verbose ""
}

# Create results directory
mkdir -p "$RESULTS_DIR"

# Initialize report
log "======================================================================="
log "🚀 QUENTY MICROSERVICES ENDPOINT TEST REPORT"
log "======================================================================="
log "Timestamp: $(date)"
log "Test Environment: $(uname -s) $(uname -r)"
log "Docker Status: $(docker --version)"
log ""

# Check if services are running
log "🔍 Checking service availability..."
for service in "${!SERVICES[@]}"; do
    port="${SERVICES[$service]}"
    if curl -s --max-time 5 "http://localhost:$port/health" > /dev/null; then
        log "✅ $service:$port - Running"
    else
        log "❌ $service:$port - Not responding"
    fi
done
log ""

# =============================================================================
# HEALTH ENDPOINTS TESTING
# =============================================================================
log "🏥 TESTING HEALTH ENDPOINTS"
log "======================================================================="

for service in "${!SERVICES[@]}"; do
    port="${SERVICES[$service]}"
    test_endpoint "$service" "$port" "/health" "GET" "200" "Health check endpoint"
done
log ""

# =============================================================================
# API GATEWAY TESTING
# =============================================================================
log "🌐 TESTING API GATEWAY ENDPOINTS"
log "======================================================================="

test_endpoint "api-gateway" "8000" "/docs" "GET" "200" "API documentation"
test_endpoint "api-gateway" "8000" "/openapi.json" "GET" "200" "OpenAPI specification"
test_endpoint "api-gateway" "8000" "/api/v1/status" "GET" "200" "API status endpoint"
log ""

# =============================================================================
# AUTH SERVICE TESTING
# =============================================================================
log "🔐 TESTING AUTH SERVICE ENDPOINTS"
log "======================================================================="

test_endpoint "auth-service" "8009" "/docs" "GET" "200" "Auth service documentation"
test_endpoint "auth-service" "8009" "/api/v1/register" "POST" "422" "Registration endpoint (no data)"
test_endpoint "auth-service" "8009" "/api/v1/login" "POST" "422" "Login endpoint (no data)"
test_endpoint "auth-service" "8009" "/api/v1/users" "GET" "403" "Users list (no auth)"
log ""

# =============================================================================
# CUSTOMER SERVICE TESTING
# =============================================================================
log "👥 TESTING CUSTOMER SERVICE ENDPOINTS"
log "======================================================================="

test_endpoint "customer-service" "8001" "/docs" "GET" "200" "Customer service documentation"
test_endpoint "customer-service" "8001" "/api/v1/customers" "GET" "403" "Customers list (no auth)"
test_endpoint "customer-service" "8001" "/api/v1/customers/search" "GET" "403" "Customer search (no auth)"
log ""

# =============================================================================
# ORDER SERVICE TESTING
# =============================================================================
log "📦 TESTING ORDER SERVICE ENDPOINTS"
log "======================================================================="

test_endpoint "order-service" "8002" "/docs" "GET" "200" "Order service documentation"
test_endpoint "order-service" "8002" "/api/v1/orders" "GET" "403" "Orders list (no auth)"
test_endpoint "order-service" "8002" "/api/v1/orders/stats" "GET" "403" "Order statistics (no auth)"
log ""

# =============================================================================
# PICKUP SERVICE TESTING
# =============================================================================
log "🚚 TESTING PICKUP SERVICE ENDPOINTS"
log "======================================================================="

test_endpoint "pickup-service" "8003" "/docs" "GET" "200" "Pickup service documentation"
test_endpoint "pickup-service" "8003" "/api/v1/pickups" "GET" "403" "Pickups list (no auth)"
test_endpoint "pickup-service" "8003" "/api/v1/routes" "GET" "403" "Routes list (no auth)"
log ""

# =============================================================================
# INTERNATIONAL SHIPPING TESTING
# =============================================================================
log "🌍 TESTING INTERNATIONAL SHIPPING ENDPOINTS"
log "======================================================================="

test_endpoint "international-shipping" "8004" "/docs" "GET" "200" "International shipping documentation"
test_endpoint "international-shipping" "8004" "/api/v1/manifests" "GET" "403" "Manifests list (no auth)"
test_endpoint "international-shipping" "8004" "/api/v1/countries" "GET" "403" "Countries list (no auth)"
test_endpoint "international-shipping" "8004" "/api/v1/carriers" "GET" "403" "Carriers list (no auth)"
log ""

# =============================================================================
# MICROCREDIT SERVICE TESTING
# =============================================================================
log "💳 TESTING MICROCREDIT SERVICE ENDPOINTS"
log "======================================================================="

test_endpoint "microcredit-service" "8005" "/docs" "GET" "200" "Microcredit service documentation"
test_endpoint "microcredit-service" "8005" "/api/v1/applications" "GET" "403" "Credit applications (no auth)"
test_endpoint "microcredit-service" "8005" "/api/v1/accounts" "GET" "403" "Credit accounts (no auth)"
log ""

# =============================================================================
# ANALYTICS SERVICE TESTING
# =============================================================================
log "📊 TESTING ANALYTICS SERVICE ENDPOINTS"
log "======================================================================="

test_endpoint "analytics-service" "8006" "/docs" "GET" "200" "Analytics service documentation"
test_endpoint "analytics-service" "8006" "/api/v1/analytics/dashboard" "GET" "403" "Analytics dashboard (no auth)"
test_endpoint "analytics-service" "8006" "/api/v1/analytics/trends" "GET" "403" "Business trends (no auth)"
log ""

# =============================================================================
# REVERSE LOGISTICS TESTING
# =============================================================================
log "↩️ TESTING REVERSE LOGISTICS ENDPOINTS"
log "======================================================================="

test_endpoint "reverse-logistics" "8007" "/docs" "GET" "200" "Reverse logistics documentation"
test_endpoint "reverse-logistics" "8007" "/api/v1/returns" "GET" "403" "Returns list (no auth)"
log ""

# =============================================================================
# FRANCHISE SERVICE TESTING
# =============================================================================
log "🏢 TESTING FRANCHISE SERVICE ENDPOINTS"
log "======================================================================="

test_endpoint "franchise-service" "8008" "/docs" "GET" "200" "Franchise service documentation"
test_endpoint "franchise-service" "8008" "/api/v1/franchises" "GET" "403" "Franchises list (no auth)"
test_endpoint "franchise-service" "8008" "/api/v1/territories" "GET" "403" "Territories list (no auth)"
log ""

# =============================================================================
# MONITORING AND INFRASTRUCTURE TESTING
# =============================================================================
log "🔍 TESTING MONITORING INFRASTRUCTURE"
log "======================================================================="

# Test Grafana
if curl -s --max-time 5 "http://localhost:3000/api/health" > /dev/null; then
    log "✅ Grafana - Available at http://localhost:3000"
else
    log "❌ Grafana - Not responding"
fi

# Test Prometheus
if curl -s --max-time 5 "http://localhost:9090/-/healthy" > /dev/null; then
    log "✅ Prometheus - Available at http://localhost:9090"
else
    log "❌ Prometheus - Not responding"
fi

# Test Loki
if curl -s --max-time 5 "http://localhost:3100/ready" > /dev/null; then
    log "✅ Loki - Available at http://localhost:3100"
else
    log "❌ Loki - Not responding"
fi

# Test Jaeger
if curl -s --max-time 5 "http://localhost:16686/" > /dev/null; then
    log "✅ Jaeger - Available at http://localhost:16686"
else
    log "❌ Jaeger - Not responding"
fi

# Test Consul
if curl -s --max-time 5 "http://localhost:8500/v1/status/leader" > /dev/null; then
    log "✅ Consul - Available at http://localhost:8500"
else
    log "❌ Consul - Not responding"
fi
log ""

# =============================================================================
# SUMMARY REPORT
# =============================================================================
log "📋 TEST SUMMARY"
log "======================================================================="
log "Total Tests: $TOTAL_TESTS"
log "Passed: $PASSED_TESTS"
log "Failed: $FAILED_TESTS"
log "Success Rate: $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)%"
log ""

if [ $FAILED_TESTS -eq 0 ]; then
    log "🎉 ALL TESTS PASSED! Quenty microservices are running correctly."
else
    log "⚠️  $FAILED_TESTS tests failed. Please check the detailed results above."
fi

log ""
log "📁 Report saved to: $REPORT_FILE"

# Generate JSON report if requested
if [ "$JSON_OUTPUT" = true ]; then
    log "📄 JSON report saved to: $JSON_REPORT"
    
    echo "{" > "$JSON_REPORT"
    echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$JSON_REPORT"
    echo "  \"total_tests\": $TOTAL_TESTS," >> "$JSON_REPORT"
    echo "  \"passed_tests\": $PASSED_TESTS," >> "$JSON_REPORT"
    echo "  \"failed_tests\": $FAILED_TESTS," >> "$JSON_REPORT"
    echo "  \"success_rate\": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)," >> "$JSON_REPORT"
    echo "  \"results\": {" >> "$JSON_REPORT"
    
    local first=true
    for key in "${!TEST_RESULTS[@]}"; do
        if [ "$first" = false ]; then
            echo "," >> "$JSON_REPORT"
        fi
        first=false
        local value="${TEST_RESULTS[$key]}"
        local status=$(echo "$value" | cut -d: -f1)
        local code=$(echo "$value" | cut -d: -f2)
        local desc=$(echo "$value" | cut -d: -f3-)
        echo -n "    \"$key\": {\"status\": \"$status\", \"code\": \"$code\", \"description\": \"$desc\"}" >> "$JSON_REPORT"
    done
    
    echo "" >> "$JSON_REPORT"
    echo "  }" >> "$JSON_REPORT"
    echo "}" >> "$JSON_REPORT"
fi

log "======================================================================="

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi