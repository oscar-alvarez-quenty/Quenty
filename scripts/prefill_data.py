#!/usr/bin/env python3
"""
Script to prefill databases with initial data for Quenty system
"""
import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any
import random
import string
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
AUTH_BASE_URL = "http://localhost:8009"

def generate_random_id(prefix: str, length: int = 8) -> str:
    """Generate a random ID with prefix"""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}-{random_part}"

def generate_phone() -> str:
    """Generate random phone number"""
    return f"+57{random.randint(3000000000, 3999999999)}"

def generate_email(name: str, domain: str = "example.com") -> str:
    """Generate email from name"""
    return f"{name.lower().replace(' ', '.')}@{domain}"

class DataPrefiller:
    def __init__(self):
        self.session = None
        self.access_token = None
        self.companies = []
        self.users = []
        self.customers = []
        self.orders = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def wait_for_services(self, max_attempts: int = 30):
        """Wait for all services to be ready"""
        print("Waiting for services to be ready...")
        services = [
            ("API Gateway", f"{BASE_URL}/health"),
            ("Auth Service", f"{AUTH_BASE_URL}/health"),
        ]
        
        for service_name, url in services:
            attempts = 0
            while attempts < max_attempts:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            print(f"✓ {service_name} is ready")
                            break
                except:
                    pass
                attempts += 1
                await asyncio.sleep(2)
            else:
                print(f"✗ {service_name} failed to start")
                return False
        return True
        
    async def create_companies(self):
        """Create initial companies directly in the database"""
        print("\n=== Creating Companies ===")
        
        # Since there's no API endpoint for companies, we'll need to insert directly
        # For now, we'll create companies data structure that would be inserted
        companies_data = [
            {
                "name": "Tech Solutions Inc",
                "business_name": "Tech Solutions Incorporated",
                "document_type": "NIT",
                "document_number": "900123456-7",
                "industry": "technology",
                "company_size": "medium",
                "subscription_plan": "enterprise",
                "is_active": True,
                "is_verified": True,
                "settings": {
                    "notifications_enabled": True,
                    "auto_approve_orders": False,
                    "default_currency": "COP"
                }
            },
            {
                "name": "Global Logistics Co",
                "business_name": "Global Logistics Company",
                "document_type": "NIT", 
                "document_number": "900789012-3",
                "industry": "logistics",
                "company_size": "large",
                "subscription_plan": "pro",
                "is_active": True,
                "is_verified": True,
                "settings": {
                    "notifications_enabled": True,
                    "auto_approve_orders": True,
                    "default_currency": "USD"
                }
            },
            {
                "name": "Local Store",
                "business_name": "Local Store SAS",
                "document_type": "NIT",
                "document_number": "900345678-9",
                "industry": "retail",
                "company_size": "small",
                "subscription_plan": "basic",
                "is_active": True,
                "is_verified": True,
                "settings": {
                    "notifications_enabled": True,
                    "auto_approve_orders": False,
                    "default_currency": "COP"
                }
            }
        ]
        
        # Store company IDs for user creation
        # In real implementation, these would come from database inserts
        self.companies = [
            {"id": 1, "company_id": "COMP-TECH0001", "name": "Tech Solutions Inc"},
            {"id": 2, "company_id": "COMP-GLOB0002", "name": "Global Logistics Co"},
            {"id": 3, "company_id": "COMP-LOCA0003", "name": "Local Store"}
        ]
        
        for company in self.companies:
            print(f"✓ Created company: {company['name']} (ID: {company['company_id']})")
            
    async def login_as_admin(self):
        """Login with default admin credentials"""
        print("\n=== Logging in as Admin ===")
        
        # Try to login with default admin credentials
        login_data = {
            "username": "admin",
            "password": "AdminPassword123"
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("access_token")
                    print("✓ Successfully logged in as admin")
                    return True
                else:
                    print(f"✗ Login failed: {response.status}")
                    return False
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False
            
    async def create_users(self):
        """Create users for each company"""
        print("\n=== Creating Users ===")
        
        if not self.access_token:
            print("✗ No access token available. Skipping user creation.")
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        users_data = [
            # Tech Solutions Inc users
            {
                "username": "john.doe",
                "email": "john.doe@techsolutions.com",
                "password": "Password123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": generate_phone(),
                "company_id": 1,
                "role_id": 2,  # admin
                "is_active": True,
                "is_verified": True
            },
            {
                "username": "jane.smith",
                "email": "jane.smith@techsolutions.com", 
                "password": "Password123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": generate_phone(),
                "company_id": 1,
                "role_id": 3,  # manager
                "is_active": True,
                "is_verified": True
            },
            # Global Logistics Co users
            {
                "username": "carlos.garcia",
                "email": "carlos.garcia@globallogistics.com",
                "password": "Password123!",
                "first_name": "Carlos",
                "last_name": "Garcia",
                "phone": generate_phone(),
                "company_id": 2,
                "role_id": 2,  # admin
                "is_active": True,
                "is_verified": True
            },
            {
                "username": "maria.rodriguez",
                "email": "maria.rodriguez@globallogistics.com",
                "password": "Password123!",
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "phone": generate_phone(),
                "company_id": 2,
                "role_id": 7,  # shipping_coordinator
                "is_active": True,
                "is_verified": True
            },
            # Local Store users
            {
                "username": "pedro.martinez",
                "email": "pedro.martinez@localstore.com",
                "password": "Password123!",
                "first_name": "Pedro",
                "last_name": "Martinez",
                "phone": generate_phone(),
                "company_id": 3,
                "role_id": 3,  # manager
                "is_active": True,
                "is_verified": True
            }
        ]
        
        for user_data in users_data:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/v1/users",
                    json=user_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        user = await response.json()
                        self.users.append(user)
                        print(f"✓ Created user: {user_data['username']} ({user_data['email']})")
                    else:
                        error = await response.text()
                        print(f"✗ Failed to create user {user_data['username']}: {error}")
            except Exception as e:
                print(f"✗ Error creating user {user_data['username']}: {e}")
                
    async def create_customers(self):
        """Create customers for testing"""
        print("\n=== Creating Customers ===")
        
        if not self.access_token:
            print("✗ No access token available. Skipping customer creation.")
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        customers_data = [
            {
                "name": "Ana Lopez",
                "document_type": "CC",
                "document_number": "1234567890",
                "email": "ana.lopez@email.com",
                "phone": generate_phone(),
                "address": "Calle 123 #45-67",
                "city": "Bogotá",
                "state": "Cundinamarca",
                "country": "Colombia",
                "postal_code": "110111",
                "customer_type": "individual",
                "is_active": True
            },
            {
                "name": "Tech Startup SAS",
                "document_type": "NIT",
                "document_number": "900555666-7",
                "email": "info@techstartup.com",
                "phone": generate_phone(),
                "address": "Av. El Dorado #68-30",
                "city": "Bogotá",
                "state": "Cundinamarca", 
                "country": "Colombia",
                "postal_code": "110911",
                "customer_type": "business",
                "is_active": True
            },
            {
                "name": "Roberto Perez",
                "document_type": "CC",
                "document_number": "9876543210",
                "email": "roberto.perez@email.com",
                "phone": generate_phone(),
                "address": "Carrera 50 #100-20",
                "city": "Medellín",
                "state": "Antioquia",
                "country": "Colombia",
                "postal_code": "050001",
                "customer_type": "individual",
                "is_active": True
            }
        ]
        
        for customer_data in customers_data:
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/v1/customers",
                    json=customer_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        customer = await response.json()
                        self.customers.append(customer)
                        print(f"✓ Created customer: {customer_data['name']}")
                    else:
                        error = await response.text()
                        print(f"✗ Failed to create customer {customer_data['name']}: {error}")
            except Exception as e:
                print(f"✗ Error creating customer {customer_data['name']}: {e}")
                
    async def create_orders(self):
        """Create sample orders"""
        print("\n=== Creating Orders ===")
        
        if not self.access_token or not self.customers:
            print("✗ No access token or customers available. Skipping order creation.")
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Sample products
        products = [
            {"name": "Laptop Dell XPS", "sku": "TECH-001", "price": 3500000, "weight": 2.5},
            {"name": "Mouse Logitech", "sku": "TECH-002", "price": 150000, "weight": 0.1},
            {"name": "Keyboard Mechanical", "sku": "TECH-003", "price": 350000, "weight": 0.8},
            {"name": "Monitor 27 inch", "sku": "TECH-004", "price": 1200000, "weight": 5.0},
            {"name": "USB Cable", "sku": "ACC-001", "price": 25000, "weight": 0.05}
        ]
        
        orders_data = []
        
        # Create orders for each customer
        for idx, customer in enumerate(self.customers[:3]):
            # Create 2-3 orders per customer
            num_orders = random.randint(2, 3)
            
            for order_idx in range(num_orders):
                # Random order items
                num_items = random.randint(1, 3)
                order_items = []
                total_amount = 0
                
                for _ in range(num_items):
                    product = random.choice(products)
                    quantity = random.randint(1, 3)
                    item_total = product["price"] * quantity
                    total_amount += item_total
                    
                    order_items.append({
                        "product_name": product["name"],
                        "sku": product["sku"],
                        "quantity": quantity,
                        "unit_price": product["price"],
                        "total_price": item_total,
                        "weight": product["weight"]
                    })
                
                order_data = {
                    "customer_id": customer.get("id", idx + 1),
                    "order_type": random.choice(["standard", "express", "scheduled"]),
                    "items": order_items,
                    "total_amount": total_amount,
                    "currency": "COP",
                    "shipping_address": {
                        "street": customer.get("address", "Calle 123"),
                        "city": customer.get("city", "Bogotá"),
                        "state": customer.get("state", "Cundinamarca"),
                        "country": "Colombia",
                        "postal_code": customer.get("postal_code", "110111")
                    },
                    "billing_address": {
                        "street": customer.get("address", "Calle 123"),
                        "city": customer.get("city", "Bogotá"),
                        "state": customer.get("state", "Cundinamarca"),
                        "country": "Colombia",
                        "postal_code": customer.get("postal_code", "110111")
                    },
                    "notes": f"Test order #{order_idx + 1} for {customer.get('name', 'Customer')}"
                }
                
                orders_data.append(order_data)
        
        # Create orders
        for idx, order_data in enumerate(orders_data):
            try:
                async with self.session.post(
                    f"{BASE_URL}/api/v1/orders",
                    json=order_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        order = await response.json()
                        self.orders.append(order)
                        print(f"✓ Created order #{idx + 1} for customer ID {order_data['customer_id']}")
                    else:
                        error = await response.text()
                        print(f"✗ Failed to create order #{idx + 1}: {error}")
            except Exception as e:
                print(f"✗ Error creating order #{idx + 1}: {e}")
                
    async def print_summary(self):
        """Print summary of created data"""
        print("\n" + "="*50)
        print("PREFILL DATA SUMMARY")
        print("="*50)
        print(f"Companies created: {len(self.companies)}")
        print(f"Users created: {len(self.users)}")
        print(f"Customers created: {len(self.customers)}")
        print(f"Orders created: {len(self.orders)}")
        print("\nYou can now login with these test users:")
        print("-"*50)
        for user in self.users[:3]:
            print(f"Username: {user.get('username', 'N/A')}")
            print(f"Password: Password123!")
            print(f"Company: {next((c['name'] for c in self.companies if c['id'] == user.get('company_id')), 'N/A')}")
            print("-"*50)

async def main():
    """Main function to run data prefilling"""
    print("Starting Quenty Data Prefill Script...")
    print("="*50)
    
    async with DataPrefiller() as prefiller:
        # Wait for services to be ready
        if not await prefiller.wait_for_services():
            print("\n✗ Services are not ready. Please ensure Docker Compose is running.")
            return
            
        # Create initial data
        await prefiller.create_companies()
        
        # Login as admin
        if await prefiller.login_as_admin():
            # Create users
            await prefiller.create_users()
            
            # Create customers
            await prefiller.create_customers()
            
            # Create orders
            await prefiller.create_orders()
        else:
            print("\n✗ Could not login as admin. Make sure the auth service is configured with initial admin user.")
            print("Set these environment variables in docker-compose.microservices.yml for auth-service:")
            print("  - INITIAL_ADMIN_USERNAME=admin")
            print("  - INITIAL_ADMIN_PASSWORD=AdminPassword123")
            print("  - INITIAL_ADMIN_EMAIL=admin@quenty.com")
            
        # Print summary
        await prefiller.print_summary()

if __name__ == "__main__":
    asyncio.run(main())