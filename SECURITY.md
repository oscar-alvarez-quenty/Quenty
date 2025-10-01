# Quenty Platform - Security Implementation Guide

**Version:** 1.0
**Last Updated:** 2025-10-01
**Status:** Implementation Guide

---

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Encryption](#data-encryption)
4. [Network Security](#network-security)
5. [API Security](#api-security)
6. [Database Security](#database-security)
7. [Secrets Management](#secrets-management)
8. [Security Monitoring](#security-monitoring)
9. [Incident Response](#incident-response)
10. [Compliance & Standards](#compliance--standards)

---

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Perimeter Security                    │
│  - Firewall rules                               │
│  - DDoS protection                              │
│  - SSL/TLS termination                          │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  Layer 2: API Gateway Security                  │
│  - JWT validation                               │
│  - Rate limiting                                │
│  - Input validation                             │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  Layer 3: Service-Level Security                │
│  - Service authentication                       │
│  - Authorization checks                         │
│  - Data validation                              │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│  Layer 4: Data Security                         │
│  - Encryption at rest                           │
│  - Encryption in transit                        │
│  - Access controls                              │
└─────────────────────────────────────────────────┘
```

### Threat Model

**External Threats:**
- ❌ Unauthorized API access
- ❌ DDoS attacks
- ❌ SQL injection
- ❌ XSS attacks
- ❌ CSRF attacks
- ❌ Man-in-the-middle attacks

**Internal Threats:**
- ❌ Privilege escalation
- ❌ Data leakage
- ❌ Insider threats
- ❌ Misconfigured services

---

## Authentication & Authorization

### JWT-Based Authentication

#### Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_unique_id",
    "email": "user@example.com",
    "roles": ["customer", "admin"],
    "permissions": ["orders:read", "orders:write"],
    "exp": 1735689600,
    "iat": 1735686000,
    "jti": "unique_token_id"
  }
}
```

#### Token Lifecycle

**Access Tokens:**
- **Lifetime**: 30 minutes
- **Storage**: Client-side (memory, not localStorage)
- **Purpose**: API authentication

**Refresh Tokens:**
- **Lifetime**: 7 days
- **Storage**: HttpOnly secure cookie
- **Purpose**: Obtain new access tokens
- **Rotation**: New refresh token issued on each use

#### Implementation Example

```python
# auth-service/src/security.py

from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)
```

### Role-Based Access Control (RBAC)

#### Roles

```python
ROLES = {
    "superadmin": {
        "description": "Full system access",
        "permissions": ["*:*"]  # All permissions
    },
    "admin": {
        "description": "Administrative access",
        "permissions": [
            "users:*",
            "orders:*",
            "products:*",
            "customers:*",
            "analytics:read"
        ]
    },
    "customer": {
        "description": "Standard customer",
        "permissions": [
            "orders:read:own",
            "orders:create",
            "profile:*:own"
        ]
    },
    "driver": {
        "description": "Delivery driver",
        "permissions": [
            "pickups:read",
            "pickups:update:assigned",
            "routes:read:own"
        ]
    },
    "franchise_owner": {
        "description": "Franchise operator",
        "permissions": [
            "franchises:read:own",
            "franchises:update:own",
            "orders:read:territory",
            "analytics:read:own"
        ]
    }
}
```

#### Permission Check Middleware

```python
from fastapi import Depends, HTTPException, status
from typing import List

def require_permissions(required_permissions: List[str]):
    """Decorator to check user permissions"""
    def permission_checker(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])

        # Check if user has wildcard permission
        if "*:*" in user_permissions:
            return current_user

        # Check each required permission
        for required in required_permissions:
            if not has_permission(user_permissions, required):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {required}"
                )

        return current_user

    return permission_checker

def has_permission(user_permissions: List[str], required: str) -> bool:
    """Check if user has specific permission"""
    resource, action = required.split(":")

    for perm in user_permissions:
        perm_resource, perm_action = perm.split(":")

        # Check exact match or wildcard
        if perm_resource in (resource, "*") and perm_action in (action, "*"):
            return True

    return False
```

### OAuth 2.0 Integration

#### Supported Providers

1. **Google OAuth**
2. **Shopify OAuth** (for merchant stores)
3. **MercadoLibre OAuth** (for sellers)
4. **WooCommerce API Keys** (REST API authentication)

#### OAuth Flow Example (Shopify)

```python
# shopify-integration/src/routers/auth.py

from fastapi import APIRouter, HTTPException
import httpx
import os

router = APIRouter()

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_SCOPES = "read_products,write_products,read_orders,write_orders"

@router.get("/api/v1/auth/install")
async def shopify_install(shop: str):
    """Initiate Shopify OAuth flow"""
    redirect_uri = f"https://your-domain.com/api/v1/shopify/auth/callback"

    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={SHOPIFY_API_KEY}&"
        f"scope={SHOPIFY_SCOPES}&"
        f"redirect_uri={redirect_uri}"
    )

    return {"auth_url": auth_url}

@router.get("/api/v1/auth/callback")
async def shopify_callback(shop: str, code: str):
    """Handle Shopify OAuth callback"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://{shop}/admin/oauth/access_token",
            json={
                "client_id": SHOPIFY_API_KEY,
                "client_secret": SHOPIFY_API_SECRET,
                "code": code
            }
        )

        if response.status_code == 200:
            data = response.json()
            access_token = data["access_token"]

            # Store encrypted token in database
            await store_shopify_credentials(shop, access_token)

            return {"status": "success", "shop": shop}
        else:
            raise HTTPException(status_code=400, detail="OAuth failed")
```

---

## Data Encryption

### Encryption at Rest

#### Database Encryption

**PostgreSQL Configuration:**
```sql
-- Enable transparent data encryption (TDE)
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/path/to/server.crt';
ALTER SYSTEM SET ssl_key_file = '/path/to/server.key';
```

#### Field-Level Encryption

**Sensitive fields that MUST be encrypted:**

```python
# Fields requiring encryption
ENCRYPTED_FIELDS = [
    # Auth service
    "oauth_tokens.access_token",
    "oauth_tokens.refresh_token",

    # Carrier integration
    "carrier_credentials.encrypted_credentials",
    "shipping_carriers.api_key",
    "shipping_carriers.api_password",

    # E-commerce integrations
    "shopify_stores.access_token",
    "meli_accounts.access_token",
    "meli_accounts.refresh_token",
    "stores.consumer_secret",  # WooCommerce
]
```

#### AES-256-GCM Encryption Implementation

```python
# carrier-integration/src/utils/encryption.py

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os
import base64

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()
SALT = os.getenv("ENCRYPTION_SALT", "quenty_salt_v1").encode()

def derive_key(master_key: bytes, salt: bytes) -> bytes:
    """Derive encryption key using PBKDF2"""
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(master_key)

def encrypt_data(plaintext: str) -> str:
    """Encrypt data using AES-256-GCM"""
    key = derive_key(ENCRYPTION_KEY, SALT)
    aesgcm = AESGCM(key)

    # Generate random nonce (96 bits for GCM)
    nonce = os.urandom(12)

    # Encrypt
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    # Combine nonce + ciphertext and encode as base64
    encrypted = nonce + ciphertext
    return base64.b64encode(encrypted).decode()

def decrypt_data(encrypted: str) -> str:
    """Decrypt data using AES-256-GCM"""
    key = derive_key(ENCRYPTION_KEY, SALT)
    aesgcm = AESGCM(key)

    # Decode base64
    encrypted_bytes = base64.b64decode(encrypted)

    # Extract nonce (first 12 bytes) and ciphertext
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]

    # Decrypt
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()

# Usage example
carrier_credentials = {
    "username": "dhl_user",
    "password": "secret_password",
    "account_number": "123456"
}

import json
encrypted = encrypt_data(json.dumps(carrier_credentials))
# Store 'encrypted' in database

# Later, retrieve and decrypt
decrypted = decrypt_data(encrypted)
credentials = json.loads(decrypted)
```

### Encryption in Transit

#### TLS/SSL Configuration

**Nginx SSL Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.quenty.com;

    # SSL certificates
    ssl_certificate /etc/ssl/certs/quenty.crt;
    ssl_certificate_key /etc/ssl/private/quenty.key;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://api-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Network Security

### Network Isolation

```yaml
# docker-compose security configuration
services:
  api-gateway:
    networks:
      - public_network
      - internal_network
    ports:
      - "8080:8000"  # Only gateway exposed

  auth-service:
    networks:
      - internal_network  # Internal only
    # No external ports

  customer-service:
    networks:
      - internal_network  # Internal only
```

### Firewall Rules

```bash
# iptables rules (example for production server)

# Allow SSH (only from specific IPs)
iptables -A INPUT -p tcp --dport 22 -s 203.0.113.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j DROP

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow API Gateway
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Block all other inbound traffic
iptables -A INPUT -j DROP

# Allow all outbound traffic
iptables -A OUTPUT -j ACCEPT
```

---

## API Security

### Rate Limiting

```python
# api-gateway/src/middleware.py

from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# Apply rate limits
@app.get("/api/v1/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request):
    ...

@app.get("/api/v1/orders")
@limiter.limit("100/minute")  # 100 requests per minute
async def list_orders(request: Request):
    ...
```

### Input Validation

```python
# Using Pydantic for request validation

from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    username: constr(min_length=3, max_length=50, regex="^[a-zA-Z0-9_]+$")
    password: constr(min_length=8, max_length=128)
    first_name: constr(max_length=100)
    last_name: constr(max_length=100)
    phone: Optional[constr(regex=r"^\+?1?\d{9,15}$")]

    @validator('password')
    def password_complexity(cls, v):
        """Enforce password complexity"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        if not any(c in '!@#$%^&*()_+-=' for c in v):
            raise ValueError('Password must contain special character')
        return v
```

### CORS Configuration

```python
# api-gateway/src/main.py

from fastapi.middleware.cors import CORSMiddleware

# Restrictive CORS for production
ALLOWED_ORIGINS = [
    "https://app.quenty.com",
    "https://admin.quenty.com",
    "https://mobile-api.quenty.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,  # Cache preflight for 1 hour
)
```

### SQL Injection Prevention

```python
# ALWAYS use parameterized queries with SQLAlchemy

from sqlalchemy import select

# ✅ SAFE - Parameterized query
async def get_user_by_email(email: str):
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# ❌ UNSAFE - String interpolation (NEVER DO THIS)
# query = f"SELECT * FROM users WHERE email = '{email}'"
```

---

## Database Security

### Connection Security

```python
# database.py configuration

DATABASE_URL = (
    "postgresql+asyncpg://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
    "?ssl=require"  # Force SSL connection
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Don't log SQL (sensitive data)
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "ssl": "require",
        "server_settings": {
            "application_name": "quenty_service"
        }
    }
)
```

### Database User Permissions

```sql
-- Create dedicated database users for each service

-- Auth service user
CREATE USER auth_service WITH PASSWORD 'strong_password_here';
GRANT CONNECT ON DATABASE auth_db TO auth_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO auth_service;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO auth_service;

-- Read-only analytics user
CREATE USER analytics_readonly WITH PASSWORD 'another_strong_password';
GRANT CONNECT ON DATABASE auth_db TO analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- Prevent table drops
REVOKE DROP ON ALL TABLES IN SCHEMA public FROM auth_service;
```

### Audit Logging

```sql
-- Enable PostgreSQL audit logging
ALTER SYSTEM SET log_statement = 'mod';  -- Log all data-modifying statements
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
```

---

## Secrets Management

### Environment Variables

**DO NOT commit to git:**
- `.env`
- `.env.production`
- `.env.carriers`

**DO commit to git:**
- `.env.example` (template without actual secrets)

### Secrets Storage Hierarchy

```
Priority 1: Environment Variables (Docker secrets, Kubernetes secrets)
Priority 2: Secrets Manager (AWS Secrets Manager, HashiCorp Vault)
Priority 3: Encrypted config files (last resort)
Priority 4: NEVER hardcode in source code
```

### HashiCorp Vault Integration (Recommended for Production)

```python
# utils/vault_client.py

import hvac
import os

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

def get_secret(path: str, key: str) -> str:
    """Retrieve secret from Vault"""
    secret = client.secrets.kv.v2.read_secret_version(path=path)
    return secret['data']['data'][key]

# Usage
DB_PASSWORD = get_secret("quenty/database", "password")
JWT_SECRET = get_secret("quenty/auth", "jwt_secret_key")
```

---

## Security Monitoring

### Metrics to Monitor

```python
# Prometheus metrics for security events

from prometheus_client import Counter, Histogram

# Authentication failures
auth_failures = Counter(
    'auth_failures_total',
    'Total authentication failures',
    ['service', 'reason']
)

# Suspicious activity
suspicious_activity = Counter(
    'suspicious_activity_total',
    'Suspicious activity detected',
    ['type', 'severity']
)

# API request duration (detect DDoS)
request_duration = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint', 'status']
)

# Failed authorization attempts
authz_failures = Counter(
    'authorization_failures_total',
    'Failed authorization attempts',
    ['service', 'resource', 'action']
)
```

### Security Alerts

**Set up alerts for:**
- Multiple failed login attempts (>5 in 5 minutes)
- Unusual API request patterns
- Database connection errors
- Encryption/decryption failures
- High error rates (>5% of requests)
- Slow query performance (>2 seconds)

### Logging Best Practices

```python
import structlog
import logging

logger = structlog.get_logger()

# ✅ GOOD - Log security events without sensitive data
logger.info(
    "user_login_success",
    user_id=user.id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# ❌ BAD - Don't log passwords, tokens, or PII
# logger.info(f"Login attempt: {email} with password {password}")
```

---

## Incident Response

### Security Incident Response Plan

#### 1. Detection
- Monitor security alerts
- Review logs regularly
- User reports

#### 2. Containment
- Isolate affected services
- Revoke compromised credentials
- Block malicious IPs

#### 3. Investigation
- Analyze logs and metrics
- Determine scope of breach
- Identify attack vector

#### 4. Remediation
- Patch vulnerabilities
- Reset credentials
- Update security rules

#### 5. Recovery
- Restore from backups if needed
- Resume normal operations
- Verify system integrity

#### 6. Post-Incident
- Document lessons learned
- Update security procedures
- Communicate with stakeholders

### Emergency Contacts

```yaml
Security Team:
  - Lead: security@quenty.com
  - On-call: +57-XXX-XXX-XXXX

Escalation:
  - Level 1: Team Lead (0-30 min)
  - Level 2: CTO (30-60 min)
  - Level 3: CEO (>60 min or data breach)
```

---

## Compliance & Standards

### OWASP Top 10 Mitigation

| Risk | Mitigation |
|------|------------|
| A01 Broken Access Control | RBAC, JWT validation, permission checks |
| A02 Cryptographic Failures | AES-256-GCM, TLS 1.3, bcrypt for passwords |
| A03 Injection | Parameterized queries, input validation |
| A04 Insecure Design | Security by design, threat modeling |
| A05 Security Misconfiguration | Hardened configs, regular audits |
| A06 Vulnerable Components | Automated dependency scanning |
| A07 Authentication Failures | MFA support, account lockout, JWT |
| A08 Software/Data Integrity | Code signing, checksum validation |
| A09 Logging Failures | Centralized logging, security alerts |
| A10 SSRF | Whitelist external API calls |

### Data Privacy Compliance

**GDPR Compliance (if applicable):**
- User consent management
- Right to access (export data)
- Right to erasure (delete user data)
- Data portability
- Privacy by design

**CCPA Compliance (if applicable):**
- Disclosure of data collection
- Opt-out mechanism
- Data sale prohibition

### Security Checklist

#### Pre-Deployment
- [ ] All secrets removed from code
- [ ] SSL/TLS certificates configured
- [ ] Database credentials encrypted
- [ ] CORS configured properly
- [ ] Rate limiting enabled
- [ ] Input validation implemented
- [ ] Security headers configured
- [ ] Dependency vulnerabilities scanned
- [ ] Penetration testing completed

#### Post-Deployment
- [ ] Monitor security alerts
- [ ] Review access logs
- [ ] Check for unauthorized access
- [ ] Verify backup procedures
- [ ] Test incident response
- [ ] Update security documentation

---

## Security Tools

### Recommended Tools

1. **Dependency Scanning**: Snyk, Dependabot
2. **SAST**: Bandit (Python), SonarQube
3. **DAST**: OWASP ZAP, Burp Suite
4. **Secret Scanning**: GitGuardian, TruffleHog
5. **Container Scanning**: Trivy, Clair
6. **Monitoring**: Prometheus, Grafana, ELK Stack

### Automated Security Checks

```yaml
# .github/workflows/security.yml

name: Security Checks

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r . -f json -o bandit-report.json

      - name: Run Safety
        run: |
          pip install safety
          safety check --json

      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-01
**Next Review:** 2025-11-01
**Owner:** Quenty Security Team
