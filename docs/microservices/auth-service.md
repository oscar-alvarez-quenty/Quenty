# Auth Service Documentation

## Overview

The Auth Service is the centralized authentication and authorization service for the Quenty platform. It provides JWT-based authentication, role-based access control (RBAC), and permission management for all microservices.

## Service Details

- **Port**: 8009
- **Database**: PostgreSQL (auth_db)
- **Base URL**: `http://localhost:8009`
- **Health Check**: `GET /health`

## Core Features

### 1. Authentication
- JWT token generation and validation
- Refresh token management
- Password hashing and verification
- Session management
- Multi-factor authentication support

### 2. Authorization
- Role-based access control (RBAC)
- Permission-based access control
- Resource-level permissions
- Dynamic permission assignment

### 3. User Management
- User registration and onboarding
- Profile management
- Password reset and recovery
- Account activation and deactivation

### 4. Role Management
- Dynamic role creation and management
- Permission assignment to roles
- Hierarchical role structures
- Default role templates

## Data Models

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True)
    username = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="user")
    user_permissions = relationship("UserPermission", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
```

### Role Model
```python
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    is_system_role = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="role")
    user_roles = relationship("UserRole", back_populates="role")
```

### Permission Model
```python
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    permission_id = Column(String(255), unique=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    resource = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")
    user_permissions = relationship("UserPermission", back_populates="permission")
```

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "username": "john_doe",
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
}
```

**Response:**
```json
{
    "user_id": "USER-ABCD1234",
    "username": "john_doe",
    "email": "john.doe@example.com",
    "is_active": false,
    "verification_required": true,
    "message": "Registration successful. Please verify your email."
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "john_doe",
    "password": "SecurePass123!"
}
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "user_id": "USER-ABCD1234",
        "username": "john_doe",
        "email": "john.doe@example.com",
        "roles": ["customer"],
        "permissions": ["orders:read", "profile:update"]
    }
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### User Management Endpoints

#### Get User Profile
```http
GET /api/v1/profile
Authorization: Bearer <access_token>
```

#### Update User Profile
```http
PUT /api/v1/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
}
```

#### Change Password
```http
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "current_password": "OldPass123!",
    "new_password": "NewPass456!"
}
```

### Admin Endpoints

#### List Users (Admin)
```http
GET /api/v1/admin/users?limit=20&offset=0
Authorization: Bearer <admin_access_token>
```

#### Create Role (Admin)
```http
POST /api/v1/admin/roles
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
    "name": "franchise_manager",
    "description": "Manages franchise operations",
    "permissions": ["franchises:create", "franchises:read", "franchises:update"]
}
```

#### Assign Role to User (Admin)
```http
POST /api/v1/admin/users/{user_id}/roles
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
    "role_id": "ROLE-FMGR1234"
}
```

## Authentication Flow

### 1. User Registration
```mermaid
sequenceDiagram
    participant Client
    participant AuthService
    participant Database
    participant EmailService
    
    Client->>AuthService: POST /auth/register
    AuthService->>Database: Create user (inactive)
    AuthService->>EmailService: Send verification email
    AuthService->>Client: Registration success
    Client->>AuthService: GET /auth/verify/{token}
    AuthService->>Database: Activate user
    AuthService->>Client: Verification success
```

### 2. Login Flow
```mermaid
sequenceDiagram
    participant Client
    participant AuthService
    participant Database
    
    Client->>AuthService: POST /auth/login
    AuthService->>Database: Validate credentials
    AuthService->>Database: Get user roles/permissions
    AuthService->>AuthService: Generate JWT tokens
    AuthService->>Database: Store refresh token
    AuthService->>Client: Return tokens + user data
```

### 3. Token Validation (by other services)
```mermaid
sequenceDiagram
    participant ClientService
    participant AuthService
    participant Database
    
    ClientService->>AuthService: Validate token
    AuthService->>AuthService: Verify JWT signature
    AuthService->>Database: Check token blacklist
    AuthService->>Database: Get user permissions
    AuthService->>ClientService: Return user data
```

## Security Features

### 1. Password Security
- **Hashing**: bcrypt with configurable rounds
- **Complexity**: Minimum 8 characters, mixed case, numbers, special characters
- **History**: Prevents reuse of last 5 passwords
- **Expiration**: Optional password expiration policies

### 2. Token Security
- **JWT**: Short-lived access tokens (30 minutes)
- **Refresh Tokens**: Long-lived, single-use tokens (7 days)
- **Blacklisting**: Revoked tokens are blacklisted
- **Rotation**: Automatic refresh token rotation

### 3. Rate Limiting
- **Login Attempts**: 5 attempts per 15 minutes per IP
- **Registration**: 3 registrations per hour per IP
- **Password Reset**: 3 attempts per hour per email

### 4. Account Security
- **Account Lockout**: After 5 failed login attempts
- **Email Verification**: Required for account activation
- **Suspicious Activity**: Automatic notifications and logging

## Permission System

### Permission Format
Permissions follow the format: `resource:action`
- Examples: `orders:read`, `users:create`, `analytics:admin`

### System Permissions
| Permission | Description |
|------------|-------------|
| `*` | Super admin (all permissions) |
| `users:*` | Full user management |
| `users:read` | View users |
| `users:create` | Create users |
| `users:update` | Update users |
| `users:delete` | Delete users |
| `orders:*` | Full order management |
| `orders:read` | View orders |
| `orders:create` | Create orders |
| `analytics:read` | View analytics |
| `analytics:admin` | Manage analytics |
| `franchises:*` | Full franchise management |
| `returns:*` | Full returns management |

### Default Roles
| Role | Description | Permissions |
|------|-------------|-------------|
| `super_admin` | System administrator | `*` |
| `admin` | Platform administrator | `users:*`, `orders:*`, `analytics:admin` |
| `franchise_manager` | Franchise manager | `franchises:*`, `territories:read` |
| `customer_service` | Support agent | `orders:read`, `customers:read`, `returns:*` |
| `customer` | End user | `profile:update`, `orders:read` |

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://auth:auth_pass@auth-db:5432/auth_db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Initial Admin User
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=AdminPassword123
INITIAL_ADMIN_EMAIL=admin@quenty.com
INITIAL_ADMIN_FIRST_NAME=System
INITIAL_ADMIN_LAST_NAME=Administrator

# Rate Limiting
RATE_LIMIT_LOGIN=5/15min
RATE_LIMIT_REGISTER=3/hour
RATE_LIMIT_PASSWORD_RESET=3/hour

# Security
PASSWORD_MIN_LENGTH=8
ACCOUNT_LOCKOUT_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=15min
```

## Integration with Other Services

### Service Authentication
Other microservices authenticate requests using the Auth Service:

```python
import requests

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(f"{AUTH_SERVICE_URL}/api/v1/profile", headers=headers, timeout=5)
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        return response.json()
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
```

### Permission Checking
```python
def require_permissions(permissions: List[str]):
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        if "*" in user_permissions:
            return current_user
            
        if not any(perm in user_permissions for perm in permissions):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return current_user
    
    return permission_checker
```

## Monitoring and Logging

### Health Checks
- **Database**: Connection and query performance
- **JWT**: Token generation and validation
- **External Services**: Email service availability

### Audit Logging
All authentication events are logged:
- User login/logout
- Permission changes
- Role assignments
- Failed authentication attempts
- Password changes

### Metrics
- Authentication success/failure rates
- Token generation frequency
- User session duration
- Permission check frequency

## Troubleshooting

### Common Issues

#### 1. Invalid JWT Token
**Error**: `401 Unauthorized - Invalid token`
**Solution**: 
- Check token expiration
- Verify JWT secret key configuration
- Ensure token is properly formatted in Authorization header

#### 2. Database Connection Issues
**Error**: `503 Service Unavailable - Database connection failed`
**Solution**:
- Verify database credentials and connectivity
- Check if auth-db container is running
- Review database connection pool settings

#### 3. Permission Denied
**Error**: `403 Forbidden - Insufficient permissions`
**Solution**:
- Verify user has required role/permissions
- Check permission format (resource:action)
- Ensure user account is active

#### 4. Account Locked
**Error**: `423 Locked - Account temporarily locked`
**Solution**:
- Wait for lockout period to expire
- Admin can manually unlock account
- Check for suspicious activity

### Debug Commands
```bash
# Check service health
curl http://localhost:8009/health

# Test authentication
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPassword123"}'

# Validate token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8009/api/v1/profile
```