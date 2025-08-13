#!/usr/bin/env python3
"""
Script to add Prometheus metrics endpoints to all microservices
"""
import os
import re

# Microservices to update
services = [
    ("order", "order-service"),
    ("analytics", "analytics-service"),
    ("franchise", "franchise-service"),
    ("international-shipping", "intl-shipping-service"),
    ("microcredit", "microcredit-service"),
    ("pickup", "pickup-service"),
    ("reverse-logistics", "reverse-logistics-service"),
    ("api-gateway", "api-gateway")
]

# Template for imports
IMPORT_TEMPLATE = """from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time"""

# Template for metrics definitions
def get_metrics_template(service_name):
    service_underscore = service_name.replace("-", "_")
    return f"""
# Prometheus metrics
{service_underscore}_operations_total = Counter(
    '{service_underscore}_operations_total',
    'Total number of {service_name} operations',
    ['operation', 'status']
)
{service_underscore}_request_duration = Histogram(
    '{service_underscore}_request_duration_seconds',
    'Duration of {service_name} requests in seconds',
    ['method', 'endpoint']
)
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)"""

# Template for metrics endpoint
METRICS_ENDPOINT_TEMPLATE = """
@app.get("/metrics")
async def get_metrics():
    \"\"\"Prometheus metrics endpoint\"\"\"
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)"""

def add_metrics_to_service(service_dir, service_name):
    """Add metrics endpoint to a service"""
    main_file = f"/home/jhunter/devel/QUENTY/Quenty/microservices/{service_dir}/src/main.py"
    
    if not os.path.exists(main_file):
        print(f"Warning: {main_file} not found")
        return False
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if metrics already exist
    if "/metrics" in content:
        print(f"Metrics endpoint already exists in {service_name}")
        return True
    
    # Add imports after other imports
    if "from prometheus_client import" not in content:
        # Find the last import line
        import_pattern = r'((?:from .* import .*\n|import .*\n)+)'
        match = re.search(import_pattern, content)
        if match:
            last_import_pos = match.end()
            # Insert prometheus imports before the last local import
            local_import_pattern = r'\nfrom \.(models|database|logging_config)'
            local_match = re.search(local_import_pattern, content)
            if local_match:
                insert_pos = local_match.start()
                content = content[:insert_pos] + "\n" + IMPORT_TEMPLATE + content[insert_pos:]
            else:
                content = content[:last_import_pos] + IMPORT_TEMPLATE + "\n" + content[last_import_pos:]
    
    # Add metrics definitions after app creation
    if f"{service_name.replace('-', '_')}_operations_total" not in content:
        app_pattern = r'(app = FastAPI\([^)]+\))'
        match = re.search(app_pattern, content)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + get_metrics_template(service_name) + content[insert_pos:]
    
    # Add metrics endpoint after health check
    if "@app.get(\"/metrics\")" not in content:
        health_pattern = r'(@app\.get\("/health"\)[^}]+})'
        match = re.search(health_pattern, content, re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + METRICS_ENDPOINT_TEMPLATE + content[insert_pos:]
    
    # Write back the modified content
    with open(main_file, 'w') as f:
        f.write(content)
    
    print(f"✓ Added metrics endpoint to {service_name}")
    return True

# Process all services
for service_dir, service_name in services:
    add_metrics_to_service(service_dir, service_name)

print("\nAll services have been updated with metrics endpoints!")