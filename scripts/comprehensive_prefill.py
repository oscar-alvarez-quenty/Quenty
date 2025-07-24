#!/usr/bin/env python3
"""
Comprehensive prefill script for all Quenty microservices databases
Runs with Docker and populates all systems with realistic test data
"""
import requests
import json
import time
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

BASE_URL = "http://localhost:8000"

class QuantyPrefiller:
    def __init__(self):
        self.access_token = None
        self.companies = []
        self.users = []
        self.customers = []
        self.products = []
        self.orders = []
        self.pickups = []
        self.returns = []
        self.franchises = []
        self.territories = []
        self.manifests = []
        self.carriers = []
        self.countries = []
        self.credit_applications = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def generate_id(self, prefix: str = "", length: int = 8) -> str:
        """Generate random ID"""
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        return f"{prefix}{random_part}" if prefix else random_part
        
    def generate_phone(self) -> str:
        """Generate Colombian phone number"""
        return f"+57{random.randint(3000000000, 3999999999)}"
        
    def wait_for_services(self, max_attempts: int = 30) -> bool:
        """Wait for API Gateway to be ready"""
        self.log("Waiting for API Gateway to be ready...")
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    self.log("✓ API Gateway is ready")
                    return True
            except:
                pass
            time.sleep(2)
        
        self.log("✗ API Gateway failed to start", "ERROR")
        return False
        
    def login_admin(self) -> bool:
        """Login with admin credentials"""
        self.log("Logging in as admin...")
        login_data = {
            "username_or_email": "admin",
            "password": "AdminPassword123"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.log("✓ Successfully logged in as admin")
                return True
            else:
                self.log(f"✗ Login failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Login error: {e}", "ERROR")
            return False
            
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        } if self.access_token else {"Content-Type": "application/json"}
        
    def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
        """Make API request with proper headers"""
        url = f"{BASE_URL}{endpoint}"
        headers = self.get_headers()
        
        if method.upper() == "GET":
            return requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            return requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            return requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            return requests.delete(url, headers=headers)
            
    def prefill_countries(self):
        """Create countries for international shipping"""
        self.log("Creating countries...")
        
        countries_data = [
            {"code": "US", "name": "United States", "currency": "USD", "is_active": True},
            {"code": "CA", "name": "Canada", "currency": "CAD", "is_active": True},
            {"code": "MX", "name": "Mexico", "currency": "MXN", "is_active": True},
            {"code": "BR", "name": "Brazil", "currency": "BRL", "is_active": True},
            {"code": "AR", "name": "Argentina", "currency": "ARS", "is_active": True},
            {"code": "CO", "name": "Colombia", "currency": "COP", "is_active": True},
            {"code": "ES", "name": "Spain", "currency": "EUR", "is_active": True},
            {"code": "FR", "name": "France", "currency": "EUR", "is_active": True},
        ]
        
        for country_data in countries_data:
            try:
                response = self.make_request("POST", "/api/v1/countries", country_data)
                if response.status_code == 201:
                    country = response.json()
                    self.countries.append(country)
                    self.log(f"✓ Created country: {country_data['name']}")
                else:
                    self.log(f"✗ Failed to create country {country_data['name']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating country {country_data['name']}: {e}")
                
    def prefill_carriers(self):
        """Create shipping carriers"""
        self.log("Creating carriers...")
        
        carriers_data = [
            {"name": "DHL Express", "code": "DHL", "is_active": True, "supports_tracking": True},
            {"name": "FedEx International", "code": "FEDEX", "is_active": True, "supports_tracking": True},
            {"name": "UPS Worldwide", "code": "UPS", "is_active": True, "supports_tracking": True},
            {"name": "TNT Express", "code": "TNT", "is_active": True, "supports_tracking": True},
            {"name": "Servientrega", "code": "SERV", "is_active": True, "supports_tracking": True},
        ]
        
        for carrier_data in carriers_data:
            try:
                response = self.make_request("POST", "/api/v1/carriers", carrier_data)
                if response.status_code == 201:
                    carrier = response.json()
                    self.carriers.append(carrier)
                    self.log(f"✓ Created carrier: {carrier_data['name']}")
                else:
                    self.log(f"✗ Failed to create carrier {carrier_data['name']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating carrier {carrier_data['name']}: {e}")
                
    def prefill_products(self):
        """Create products for orders"""
        self.log("Creating products...")
        
        products_data = [
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
            },
            {
                "name": "Samsung Galaxy S24",
                "sku": "SAMSUNG-S24-001",
                "description": "Android flagship smartphone",
                "price": 3800000,
                "weight": 0.168,
                "dimensions": {"length": 14.7, "width": 7.06, "height": 0.76},
                "category": "Electronics",
                "stock_quantity": 25,
                "is_active": True
            },
            {
                "name": "MacBook Air M3",
                "sku": "APPLE-MBA-M3-001",
                "description": "Apple MacBook Air with M3 chip",
                "price": 4800000,
                "weight": 1.24,
                "dimensions": {"length": 30.41, "width": 21.5, "height": 1.13},
                "category": "Electronics",
                "stock_quantity": 20,
                "is_active": True
            },
            {
                "name": "Gaming Mouse Logitech G Pro",
                "sku": "LOGI-GPRO-001",
                "description": "Professional gaming mouse",
                "price": 280000,
                "weight": 0.08,
                "dimensions": {"length": 12.5, "width": 6.3, "height": 4.0},
                "category": "Accessories",
                "stock_quantity": 100,
                "is_active": True
            },
            {
                "name": "Mechanical Keyboard",
                "sku": "MECH-KB-001",
                "description": "RGB mechanical keyboard with Cherry MX switches",
                "price": 450000,
                "weight": 1.2,
                "dimensions": {"length": 44, "width": 13, "height": 3.5},
                "category": "Accessories",
                "stock_quantity": 75,
                "is_active": True
            },
            {
                "name": "4K Monitor 27 inch",
                "sku": "MON-4K27-001",
                "description": "27-inch 4K UHD monitor",
                "price": 1200000,
                "weight": 6.2,
                "dimensions": {"length": 61.3, "width": 36.6, "height": 18.5},
                "category": "Electronics",
                "stock_quantity": 40,
                "is_active": True
            },
            {
                "name": "Wireless Headphones",
                "sku": "AUDIO-WH-001",
                "description": "Noise-cancelling wireless headphones",
                "price": 650000,
                "weight": 0.25,
                "dimensions": {"length": 18, "width": 16, "height": 8},
                "category": "Audio",
                "stock_quantity": 60,
                "is_active": True
            }
        ]
        
        for product_data in products_data:
            try:
                response = self.make_request("POST", "/api/v1/products", product_data)
                if response.status_code == 201:
                    product = response.json()
                    self.products.append(product)
                    self.log(f"✓ Created product: {product_data['name']}")
                else:
                    self.log(f"✗ Failed to create product {product_data['name']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating product {product_data['name']}: {e}")
                
    def prefill_customers(self):
        """Create customer profiles"""
        self.log("Creating customers...")
        
        # First get the existing users to link profiles
        users_response = self.make_request("GET", "/api/v1/users")
        if users_response.status_code == 200:
            self.users = users_response.json().get("items", [])
            
        customers_data = [
            {
                "user_id": "test.user" if self.users else "USER-TEST0001",
                "customer_type": "individual",
                "credit_limit": 5000000,
                "credit_used": 0,
                "payment_terms": 30,
                "preferred_payment_method": "credit_card",
                "default_shipping_address": {
                    "street": "Calle 123 #45-67",
                    "city": "Bogotá",
                    "state": "Cundinamarca",
                    "country": "Colombia",
                    "postal_code": "110111"
                },
                "billing_address": {
                    "street": "Calle 123 #45-67", 
                    "city": "Bogotá",
                    "state": "Cundinamarca",
                    "country": "Colombia",
                    "postal_code": "110111"
                },
                "customer_status": "active",
                "loyalty_points": 1500,
                "email_notifications": True,
                "sms_notifications": True,
                "marketing_emails": True
            },
            {
                "user_id": self.generate_id("USER-", 8),
                "customer_type": "business",
                "credit_limit": 50000000,
                "credit_used": 5000000,
                "payment_terms": 45,
                "preferred_payment_method": "bank_transfer",
                "default_shipping_address": {
                    "street": "Av. El Dorado #68-30",
                    "city": "Bogotá",
                    "state": "Cundinamarca",
                    "country": "Colombia",
                    "postal_code": "110911"
                },
                "billing_address": {
                    "street": "Av. El Dorado #68-30",
                    "city": "Bogotá", 
                    "state": "Cundinamarca",
                    "country": "Colombia",
                    "postal_code": "110911"
                },
                "customer_status": "active",
                "loyalty_points": 15000,
                "email_notifications": True,
                "sms_notifications": False,
                "marketing_emails": True
            },
            {
                "user_id": self.generate_id("USER-", 8),
                "customer_type": "individual", 
                "credit_limit": 3000000,
                "credit_used": 500000,
                "payment_terms": 15,
                "preferred_payment_method": "debit_card",
                "default_shipping_address": {
                    "street": "Carrera 50 #100-20",
                    "city": "Medellín",
                    "state": "Antioquia",
                    "country": "Colombia",
                    "postal_code": "050001"
                },
                "billing_address": {
                    "street": "Carrera 50 #100-20",
                    "city": "Medellín",
                    "state": "Antioquia", 
                    "country": "Colombia",
                    "postal_code": "050001"
                },
                "customer_status": "active",
                "loyalty_points": 750,
                "email_notifications": True,
                "sms_notifications": True,
                "marketing_emails": False
            }
        ]
        
        for customer_data in customers_data:
            try:
                response = self.make_request("POST", "/api/v1/customers", customer_data)
                if response.status_code == 201:
                    customer = response.json()
                    self.customers.append(customer)
                    self.log(f"✓ Created customer profile for: {customer_data['user_id']}")
                else:
                    self.log(f"✗ Failed to create customer {customer_data['user_id']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating customer {customer_data['user_id']}: {e}")
                
    def prefill_orders(self):
        """Create orders"""
        self.log("Creating orders...")
        
        if not self.customers or not self.products:
            self.log("No customers or products available for orders")
            return
            
        # Create multiple orders
        for i in range(6):
            customer = random.choice(self.customers)
            num_items = random.randint(1, 3)
            order_items = []
            total_amount = 0
            
            selected_products = random.sample(self.products, min(num_items, len(self.products)))
            
            for product in selected_products:
                quantity = random.randint(1, 2)
                item_total = product["price"] * quantity
                total_amount += item_total
                
                order_items.append({
                    "product_id": product["id"],
                    "quantity": quantity,
                    "unit_price": product["price"],
                    "total_price": item_total
                })
                
            order_data = {
                "customer_id": customer["id"],
                "order_type": random.choice(["standard", "express", "scheduled"]),
                "items": order_items,
                "total_amount": total_amount,
                "currency": "COP",
                "shipping_address": customer["default_shipping_address"],
                "billing_address": customer["billing_address"],
                "notes": f"Test order #{i+1}",
                "priority": random.choice(["normal", "high"]),
                "status": random.choice(["pending", "confirmed", "processing"])
            }
            
            try:
                response = self.make_request("POST", "/api/v1/orders", order_data)
                if response.status_code == 201:
                    order = response.json()
                    self.orders.append(order)
                    self.log(f"✓ Created order #{i+1} for customer {customer['id']}")
                else:
                    self.log(f"✗ Failed to create order #{i+1}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating order #{i+1}: {e}")
                
    def prefill_territories(self):
        """Create franchise territories"""
        self.log("Creating territories...")
        
        territories_data = [
            {
                "code": "BOG001",
                "name": "Bogotá Centro",
                "description": "Downtown Bogotá territory",
                "is_available": True,
                "population": 800000,
                "area_km2": 150
            },
            {
                "code": "BOG002", 
                "name": "Bogotá Norte",
                "description": "North Bogotá territory",
                "is_available": True,
                "population": 1200000,
                "area_km2": 200
            },
            {
                "code": "MED001",
                "name": "Medellín Centro",
                "description": "Downtown Medellín territory",
                "is_available": True,
                "population": 600000,
                "area_km2": 120
            },
            {
                "code": "CAL001",
                "name": "Cali Valle",
                "description": "Cali Valle territory",
                "is_available": True,
                "population": 700000,
                "area_km2": 180
            }
        ]
        
        for territory_data in territories_data:
            try:
                response = self.make_request("POST", "/api/v1/territories", territory_data)
                if response.status_code == 201:
                    territory = response.json()
                    self.territories.append(territory)
                    self.log(f"✓ Created territory: {territory_data['name']}")
                else:
                    self.log(f"✗ Failed to create territory {territory_data['name']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating territory {territory_data['name']}: {e}")
                
    def prefill_franchises(self):
        """Create franchises"""
        self.log("Creating franchises...")
        
        franchises_data = [
            {
                "name": "Quenty Bogotá Centro",
                "franchisee_name": "Carlos Rodriguez",
                "franchisee_email": "carlos@quantybog.com",
                "franchisee_phone": self.generate_phone(),
                "territory_code": "BOG001",
                "investment_amount": 150000000,
                "monthly_fee": 2500000,
                "status": "active",
                "start_date": "2024-01-15",
                "contract_end_date": "2029-01-15"
            },
            {
                "name": "Quenty Medellín",
                "franchisee_name": "Ana García",
                "franchisee_email": "ana@quantymed.com", 
                "franchisee_phone": self.generate_phone(),
                "territory_code": "MED001",
                "investment_amount": 120000000,
                "monthly_fee": 2000000,
                "status": "active",
                "start_date": "2024-03-01",
                "contract_end_date": "2029-03-01"
            }
        ]
        
        for franchise_data in franchises_data:
            try:
                response = self.make_request("POST", "/api/v1/franchises", franchise_data)
                if response.status_code == 201:
                    franchise = response.json()
                    self.franchises.append(franchise)
                    self.log(f"✓ Created franchise: {franchise_data['name']}")
                else:
                    self.log(f"✗ Failed to create franchise {franchise_data['name']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating franchise {franchise_data['name']}: {e}")
                
    def prefill_pickups(self):
        """Create pickup requests"""
        self.log("Creating pickups...")
        
        if not self.orders:
            self.log("No orders available for pickups")
            return
            
        for i, order in enumerate(self.orders[:4]):  # Create pickups for first 4 orders
            pickup_data = {
                "order_id": order["id"],
                "pickup_address": order["shipping_address"],
                "pickup_date": (datetime.now() + timedelta(days=random.randint(1, 5))).isoformat(),
                "pickup_time_window": {
                    "start": "09:00",
                    "end": "17:00"
                },
                "special_instructions": "Call before arrival",
                "contact_name": f"Contact {i+1}",
                "contact_phone": self.generate_phone(),
                "status": random.choice(["scheduled", "assigned", "completed"])
            }
            
            try:
                response = self.make_request("POST", "/api/v1/pickups", pickup_data)
                if response.status_code == 201:
                    pickup = response.json()
                    self.pickups.append(pickup)
                    self.log(f"✓ Created pickup for order {order['id']}")
                else:
                    self.log(f"✗ Failed to create pickup for order {order['id']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating pickup for order {order['id']}: {e}")
                
    def prefill_returns(self):
        """Create return requests"""
        self.log("Creating returns...")
        
        if not self.orders:
            self.log("No orders available for returns")
            return
            
        # Create returns for some completed orders
        for i, order in enumerate(self.orders[:3]):
            return_data = {
                "order_id": order["id"],
                "customer_id": order["customer_id"],
                "reason": random.choice(["defective", "wrong_item", "not_satisfied", "damaged_shipping"]),
                "description": f"Return request #{i+1} - Item not as expected",
                "requested_resolution": random.choice(["refund", "replacement", "store_credit"]),
                "return_items": [
                    {
                        "product_id": order["items"][0]["product_id"],
                        "quantity": 1,
                        "reason": "defective"
                    }
                ],
                "status": random.choice(["pending", "approved", "rejected"])
            }
            
            try:
                response = self.make_request("POST", "/api/v1/returns", return_data)
                if response.status_code == 201:
                    return_item = response.json()
                    self.returns.append(return_item)
                    self.log(f"✓ Created return for order {order['id']}")
                else:
                    self.log(f"✗ Failed to create return for order {order['id']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating return for order {order['id']}: {e}")
                
    def prefill_manifests(self):
        """Create shipping manifests"""
        self.log("Creating manifests...")
        
        if not self.carriers:
            self.log("No carriers available for manifests")
            return
            
        manifests_data = [
            {
                "manifest_number": f"MAN{self.generate_id('', 6)}",
                "carrier_id": self.carriers[0]["id"] if self.carriers else 1,
                "destination_country": "US",
                "departure_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "draft",
                "total_weight": 15.5,
                "total_value": 25000000,
                "currency": "COP"
            },
            {
                "manifest_number": f"MAN{self.generate_id('', 6)}",
                "carrier_id": self.carriers[1]["id"] if len(self.carriers) > 1 else 1,
                "destination_country": "CA", 
                "departure_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "status": "confirmed",
                "total_weight": 22.8,
                "total_value": 18000000,
                "currency": "COP"
            }
        ]
        
        for manifest_data in manifests_data:
            try:
                response = self.make_request("POST", "/api/v1/manifests", manifest_data)
                if response.status_code == 201:
                    manifest = response.json()
                    self.manifests.append(manifest)
                    self.log(f"✓ Created manifest: {manifest_data['manifest_number']}")
                else:
                    self.log(f"✗ Failed to create manifest {manifest_data['manifest_number']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating manifest {manifest_data['manifest_number']}: {e}")
                
    def prefill_credit_applications(self):
        """Create microcredit applications"""
        self.log("Creating credit applications...")
        
        if not self.customers:
            self.log("No customers available for credit applications")
            return
            
        for i, customer in enumerate(self.customers[:2]):  # Create applications for first 2 customers
            application_data = {
                "customer_id": customer["id"],
                "requested_amount": random.randint(1000000, 10000000),
                "purpose": random.choice(["business_expansion", "inventory_purchase", "equipment", "working_capital"]),
                "term_months": random.choice([6, 12, 18, 24]),
                "monthly_income": random.randint(3000000, 15000000),
                "monthly_expenses": random.randint(1500000, 8000000),
                "credit_score": random.randint(650, 850),
                "employment_status": random.choice(["employed", "self_employed", "business_owner"]),
                "years_in_business": random.randint(1, 10),
                "status": random.choice(["pending", "under_review", "approved", "rejected"])
            }
            
            try:
                response = self.make_request("POST", "/api/v1/microcredit/applications", application_data)
                if response.status_code == 201:
                    application = response.json()
                    self.credit_applications.append(application)
                    self.log(f"✓ Created credit application for customer {customer['id']}")
                else:
                    self.log(f"✗ Failed to create credit application: {response.text}")
            except Exception as e:
                self.log(f"✗ Error creating credit application: {e}")
                
    def generate_analytics_data(self):
        """Generate some analytics metrics"""
        self.log("Generating analytics data...")
        
        metrics_data = [
            {
                "metric_name": "total_orders",
                "value": len(self.orders),
                "timestamp": datetime.now().isoformat(),
                "tags": {"period": "daily"}
            },
            {
                "metric_name": "total_revenue",
                "value": sum(order.get("total_amount", 0) for order in self.orders),
                "timestamp": datetime.now().isoformat(),
                "tags": {"currency": "COP", "period": "daily"}
            },
            {
                "metric_name": "active_customers",
                "value": len([c for c in self.customers if c.get("customer_status") == "active"]),
                "timestamp": datetime.now().isoformat(),
                "tags": {"period": "daily"}
            },
            {
                "metric_name": "pending_pickups",
                "value": len([p for p in self.pickups if p.get("status") == "scheduled"]),
                "timestamp": datetime.now().isoformat(),
                "tags": {"period": "daily"}
            }
        ]
        
        for metric_data in metrics_data:
            try:
                response = self.make_request("POST", "/api/v1/analytics/metrics", metric_data)
                if response.status_code == 201:
                    self.log(f"✓ Generated metric: {metric_data['metric_name']}")
                else:
                    self.log(f"✗ Failed to generate metric {metric_data['metric_name']}: {response.text}")
            except Exception as e:
                self.log(f"✗ Error generating metric {metric_data['metric_name']}: {e}")
                
    def print_summary(self):
        """Print comprehensive summary"""
        self.log("=== COMPREHENSIVE PREFILL SUMMARY ===")
        self.log(f"Countries: {len(self.countries)}")
        self.log(f"Carriers: {len(self.carriers)}")
        self.log(f"Products: {len(self.products)}")
        self.log(f"Customers: {len(self.customers)}")
        self.log(f"Orders: {len(self.orders)}")
        self.log(f"Pickups: {len(self.pickups)}")
        self.log(f"Returns: {len(self.returns)}")
        self.log(f"Territories: {len(self.territories)}")
        self.log(f"Franchises: {len(self.franchises)}")
        self.log(f"Manifests: {len(self.manifests)}")
        self.log(f"Credit Applications: {len(self.credit_applications)}")
        self.log("=" * 50)
        self.log("All microservices databases have been populated with test data!")
        self.log("You can now test all endpoints and business workflows.")
        
    def run_comprehensive_prefill(self):
        """Run the complete prefill process"""
        self.log("Starting comprehensive Quenty database prefill...")
        
        if not self.wait_for_services():
            return False
            
        if not self.login_admin():
            return False
            
        # Populate all systems in logical order
        try:
            self.prefill_countries()
            self.prefill_carriers()
            self.prefill_products()
            self.prefill_customers()
            self.prefill_orders()
            self.prefill_territories()
            self.prefill_franchises() 
            self.prefill_pickups()
            self.prefill_returns()
            self.prefill_manifests()
            self.prefill_credit_applications()
            self.generate_analytics_data()
            
            self.print_summary()
            return True
            
        except Exception as e:
            self.log(f"Error during prefill process: {e}", "ERROR")
            return False

def main():
    prefiller = QuantyPrefiller()
    success = prefiller.run_comprehensive_prefill()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()