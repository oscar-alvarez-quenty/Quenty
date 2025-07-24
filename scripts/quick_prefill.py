#!/usr/bin/env python3
"""
Quick prefill script for essential Quenty microservices data
"""
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def login_admin():
    """Login with admin credentials"""
    log("Logging in as admin...")
    login_data = {
        "username_or_email": "admin",
        "password": "AdminPassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            log("✓ Successfully logged in as admin")
            return access_token
        else:
            log(f"✗ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        log(f"✗ Login error: {e}")
        return None

def make_request(method, endpoint, token, data=None):
    """Make authenticated API request"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "GET":
            response = requests.get(url, headers=headers)
        else:
            return None
            
        return response
    except Exception as e:
        log(f"✗ Request error: {e}")
        return None

def create_countries(token):
    """Create essential countries"""
    log("Creating countries...")
    countries = [
        {"code": "US", "name": "United States", "currency": "USD", "is_active": True},
        {"code": "CO", "name": "Colombia", "currency": "COP", "is_active": True},
        {"code": "CA", "name": "Canada", "currency": "CAD", "is_active": True},
    ]
    
    created = 0
    for country in countries:
        response = make_request("POST", "/api/v1/countries", token, country)
        if response and response.status_code == 201:
            log(f"✓ Created country: {country['name']}")
            created += 1
        else:
            log(f"✗ Failed to create country {country['name']}: {response.text if response else 'No response'}")
    
    return created

def create_carriers(token):
    """Create essential carriers"""
    log("Creating carriers...")
    carriers = [
        {"name": "DHL Express", "code": "DHL", "is_active": True, "supports_tracking": True},
        {"name": "FedEx International", "code": "FEDEX", "is_active": True, "supports_tracking": True},
    ]
    
    created = 0
    for carrier in carriers:
        response = make_request("POST", "/api/v1/carriers", token, carrier)
        if response and response.status_code == 201:
            log(f"✓ Created carrier: {carrier['name']}")
            created += 1
        else:
            log(f"✗ Failed to create carrier {carrier['name']}: {response.text if response else 'No response'}")
    
    return created

def create_products(token):
    """Create essential products"""
    log("Creating products...")
    products = [
        {
            "name": "Laptop Dell XPS 13",
            "sku": "DELL-XPS13-001",
            "description": "13-inch ultrabook with Intel i7 processor",
            "price": 3500000,
            "weight": 1.2,
            "dimensions": {"length": 30, "width": 20, "height": 1.5},
            "category": "Electronics",
            "stock_quantity": 50,
            "is_active": True
        },
        {
            "name": "iPhone 15 Pro",
            "sku": "APPLE-IP15P-001", 
            "description": "Latest iPhone with Pro features",
            "price": 4200000,
            "weight": 0.187,
            "dimensions": {"length": 14.67, "width": 7.08, "height": 0.83},
            "category": "Electronics",
            "stock_quantity": 30,
            "is_active": True
        }
    ]
    
    created = 0
    for product in products:
        response = make_request("POST", "/api/v1/products", token, product)
        if response and response.status_code == 201:
            log(f"✓ Created product: {product['name']}")
            created += 1
        else:
            log(f"✗ Failed to create product {product['name']}: {response.text if response else 'No response'}")
    
    return created

def create_analytics_data(token):
    """Create some analytics metrics"""
    log("Creating analytics metrics...")
    metrics = [
        {
            "metric_type": "revenue",
            "name": "daily_revenue",
            "value": 1500000,
            "unit": "COP",
            "tags": {"source": "orders", "period": "daily"}
        },
        {
            "metric_type": "orders", 
            "name": "total_orders",
            "value": 15,
            "unit": "count",
            "tags": {"source": "order_service", "period": "daily"}
        },
        {
            "metric_type": "customers",
            "name": "active_customers", 
            "value": 8,
            "unit": "count",
            "tags": {"source": "customer_service", "period": "daily"}
        }
    ]
    
    created = 0
    for metric in metrics:
        response = make_request("POST", "/api/v1/analytics/metrics", token, metric)
        if response and response.status_code == 201:
            log(f"✓ Created metric: {metric['name']}")
            created += 1
        else:
            log(f"✗ Failed to create metric {metric['name']}: {response.text if response else 'No response'}")
    
    return created

def main():
    log("Starting quick prefill for Quenty databases...")
    
    # Login
    token = login_admin()
    if not token:
        log("✗ Failed to authenticate. Exiting.")
        return False
    
    # Create data
    countries = create_countries(token)
    carriers = create_carriers(token)
    products = create_products(token)
    metrics = create_analytics_data(token)
    
    # Summary
    log("=== QUICK PREFILL SUMMARY ===")
    log(f"Countries: {countries}")
    log(f"Carriers: {carriers}")  
    log(f"Products: {products}")
    log(f"Analytics Metrics: {metrics}")
    log("==============================")
    log("Quick prefill completed!")
    
    return True

if __name__ == "__main__":
    main()