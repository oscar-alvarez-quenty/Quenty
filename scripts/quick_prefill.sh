#!/bin/bash

echo "=== Quenty Quick Data Prefill ==="

# Get access token
echo "1. Logging in as admin..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "admin", "password": "AdminPassword123"}')

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$ACCESS_TOKEN" ]; then
    echo "✗ Failed to login"
    exit 1
fi

echo "✓ Logged in successfully"

# Create users
echo -e "\n2. Creating users..."

USERS='[
  {
    "username": "john.doe",
    "email": "john.doe@techsolutions.com",
    "password": "Password123!",
    "password_confirm": "Password123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+573001234567",
    "company_id": "COMP-TECH0001",
    "role": "admin"
  },
  {
    "username": "jane.smith",
    "email": "jane.smith@techsolutions.com",
    "password": "Password123!",
    "password_confirm": "Password123!",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+573002345678",
    "company_id": "COMP-TECH0001",
    "role": "manager"
  },
  {
    "username": "carlos.garcia",
    "email": "carlos.garcia@globallogistics.com",
    "password": "Password123!",
    "password_confirm": "Password123!",
    "first_name": "Carlos",
    "last_name": "Garcia",
    "phone": "+573003456789",
    "company_id": "COMP-GLOB0002",
    "role": "admin"
  }
]'

echo "$USERS" | python3 -c "
import sys, json
users = json.load(sys.stdin)
for user in users:
    print(json.dumps(user))
" | while read USER_JSON; do
    USERNAME=$(echo $USER_JSON | python3 -c "import sys, json; print(json.load(sys.stdin)['username'])")
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/v1/users \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d "$USER_JSON")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "201" ]; then
        echo "✓ Created user: $USERNAME"
    else
        echo "✗ Failed to create user: $USERNAME (HTTP $HTTP_CODE)"
    fi
done

# Create customers
echo -e "\n3. Creating customers..."

CUSTOMERS='[
  {
    "name": "Ana Lopez",
    "document_type": "CC",
    "document_number": "1234567890",
    "email": "ana.lopez@email.com",
    "phone": "+573004567890",
    "address": "Calle 123 #45-67",
    "city": "Bogotá",
    "state": "Cundinamarca",
    "country": "Colombia",
    "postal_code": "110111",
    "customer_type": "individual",
    "is_active": true
  },
  {
    "name": "Tech Startup SAS",
    "document_type": "NIT",
    "document_number": "900555666-7",
    "email": "info@techstartup.com",
    "phone": "+573005678901",
    "address": "Av. El Dorado #68-30",
    "city": "Bogotá",
    "state": "Cundinamarca",
    "country": "Colombia",
    "postal_code": "110911",
    "customer_type": "business",
    "is_active": true
  }
]'

echo "$CUSTOMERS" | python3 -c "
import sys, json
customers = json.load(sys.stdin)
for customer in customers:
    print(json.dumps(customer))
" | while read CUSTOMER_JSON; do
    NAME=$(echo $CUSTOMER_JSON | python3 -c "import sys, json; print(json.load(sys.stdin)['name'])")
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/v1/customers \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d "$CUSTOMER_JSON")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "201" ]; then
        echo "✓ Created customer: $NAME"
    else
        echo "✗ Failed to create customer: $NAME (HTTP $HTTP_CODE)"
    fi
done

echo -e "\n=== Prefill Complete ==="
echo "You can now login with:"
echo "  Username: john.doe / Password: Password123!"
echo "  Username: jane.smith / Password: Password123!"
echo "  Username: carlos.garcia / Password: Password123!"