#!/bin/bash

echo "=== Starting Quenty Data Prefill Process ==="
echo "==========================================="

# Wait a bit for services to stabilize
echo "Waiting for services to stabilize..."
sleep 5

# First, create companies in the auth database
echo -e "\n1. Creating companies in auth database..."
docker exec -i quenty-auth-db psql -U auth -d auth_db < scripts/init_companies.sql

if [ $? -eq 0 ]; then
    echo "✓ Companies created successfully"
else
    echo "✗ Failed to create companies"
    exit 1
fi

# Run the prefill script using requests library
echo -e "\n2. Running prefill data script..."
python3 scripts/prefill_data_simple.py

echo -e "\n=== Prefill Process Complete ==="