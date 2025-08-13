#!/usr/bin/env python3
"""
Test script to generate structured log entries for testing the Grafana dashboard filters
"""
import requests
import json
import time
import random

# Test API endpoints to generate different types of logs
API_BASE = "http://localhost:8000"  # API Gateway
services = [
    {"name": "customer-service", "port": 8001, "codes": ["CUST_"]},
    {"name": "order-service", "port": 8002, "codes": ["ORD_"]},
    {"name": "pickup-service", "port": 8003, "codes": ["PKP_"]},
    {"name": "analytics-service", "port": 8006, "codes": ["ANL_"]},
    {"name": "auth-service", "port": 8009, "codes": ["AUTH_"]},
]

def test_health_endpoints():
    """Test health endpoints to generate activity logs"""
    print("Testing health endpoints to generate logs...")
    
    for service in services:
        try:
            url = f"http://localhost:{service['port']}/health"
            response = requests.get(url, timeout=5)
            print(f"✓ {service['name']}: {response.status_code}")
            time.sleep(0.5)
        except Exception as e:
            print(f"✗ {service['name']}: {e}")

def test_api_endpoints():
    """Test some API endpoints to generate business logs"""
    print("Testing API endpoints to generate business logs...")
    
    # Test customer endpoint (should generate auth errors due to no token)
    try:
        response = requests.get(f"http://localhost:8001/api/v1/customers", timeout=5)
        print(f"✓ Customer API: {response.status_code}")
    except Exception as e:
        print(f"✗ Customer API: {e}")
    
    # Test order endpoint
    try:
        response = requests.get(f"http://localhost:8002/api/v1/orders", timeout=5)
        print(f"✓ Order API: {response.status_code}")
    except Exception as e:
        print(f"✗ Order API: {e}")
    
    # Test analytics endpoint
    try:
        response = requests.get(f"http://localhost:8006/api/v1/analytics/dashboard", timeout=5)
        print(f"✓ Analytics API: {response.status_code}")
    except Exception as e:
        print(f"✗ Analytics API: {e}")

if __name__ == "__main__":
    print("🔥 Generating test logs for Grafana dashboard...")
    print("=" * 50)
    
    for i in range(3):
        print(f"\n📊 Round {i+1}/3")
        test_health_endpoints()
        test_api_endpoints()
        time.sleep(2)
    
    print("\n✅ Test log generation complete!")
    print("🎯 Now check your Grafana dashboard at http://localhost:3000")
    print("📈 Dashboard: Quenty Microservices Logs")
    print("🔍 Try the new filters:")
    print("   - Service: Filter by specific microservice")
    print("   - Log Level: Filter by ERROR, WARNING, INFO, DEBUG")
    print("   - Search Text: Free text search in logs")
    print("   - Message Code: Filter by service prefixes (AGW_, AUTH_, etc.)")