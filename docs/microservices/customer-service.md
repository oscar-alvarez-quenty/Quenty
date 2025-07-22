# Customer Service Documentation

## Overview

The Customer Service is responsible for managing users, companies, and authentication within the Quenty platform. It provides comprehensive user management capabilities adapted from the quentyhub-api.

## Service Details

- **Port**: 8001
- **Database**: PostgreSQL (customer_db)
- **Base URL**: `http://localhost:8001`
- **Health Check**: `GET /health`

## Core Features

### 1. User Management
- User registration and profile management
- Authentication and session handling
- Role-based access control
- User analytics and reporting

### 2. Company Management
- Company registration and onboarding
- Business profile management
- Company analytics and metrics
- User-company relationships

### 3. Document Types
- Document type configuration
- Identity verification support
- Regional document standards

## Data Models

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(255), unique=True, index=True)
    username = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    role = Column(String(50), default="customer")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    company_id = Column(String(255), ForeignKey("companies.company_id"))
    
    # Relationships
    company = relationship("Company", back_populates="users")
```

### Company Model
```python
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(255), unique=True, index=True)
    name = Column(String(500))
    business_name = Column(String(500))
    document_type = Column(String(50))
    document_number = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="company")
```

### Document Type Model
```python
class DocumentType(Base):
    __tablename__ = "document_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    code = Column(String(50), unique=True)
    description = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## API Endpoints

### User Endpoints

#### Get Users
```http
GET /api/v1/users
```
**Query Parameters:**
- `limit` (int): Number of records to return (default: 20, max: 100)
- `offset` (int): Number of records to skip (default: 0)

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "role": "customer",
      "is_active": true,
      "company_id": "COMP-001"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get User by ID
```http
GET /api/v1/users/{user_id}
```
**Response:**
```json
{
  "id": 1,
  "unique_id": "USER-10000000",
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "address": "123 Main St",
  "number_document_identity": "123456789",
  "document_type": "passport",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "company_id": "COMP-001",
  "role": "customer",
  "last_login": "2025-07-22T02:10:06.300453",
  "date_joined": "2025-06-22T02:10:06.300454",
  "created_at": "2025-06-22T02:10:06.300459",
  "updated_at": "2025-07-22T02:10:06.300466"
}
```

#### Create User
```http
POST /api/v1/users
```
**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "address": "123 Main St",
  "number_document_identity": "123456789",
  "document_type": "passport",
  "company_id": "COMP-001",
  "role": "customer"
}
```

#### Update User
```http
PUT /api/v1/users/{user_id}
```
**Request Body:** (Partial update supported)
```json
{
  "first_name": "Updated Name",
  "phone": "+9876543210",
  "active": true
}
```

#### Delete User
```http
DELETE /api/v1/users/{user_id}
```

### Company Endpoints

#### Get Companies
```http
GET /api/v1/companies
```
**Response:**
```json
{
  "companies": [
    {
      "id": 1,
      "name": "Logistics Corp",
      "company_key": "LOGISTIC-001",
      "status": "active",
      "days_credit": 30,
      "total_users": 25,
      "total_active_users": 23
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Company by ID
```http
GET /api/v1/companies/{company_id}
```

#### Create Company
```http
POST /api/v1/companies
```
**Request Body:**
```json
{
  "name": "New Company",
  "business_name": "New Company LLC",
  "document_type": "NIT",
  "document_number": "123456789"
}
```

#### Update Company
```http
PUT /api/v1/companies/{company_id}
```

#### Delete Company
```http
DELETE /api/v1/companies/{company_id}
```

### Analytics Endpoints

#### Company Analytics
```http
GET /api/v1/companies/analytics
```
**Response:**
```json
{
  "total_companies": 50,
  "active_companies": 47,
  "inactive_companies": 3,
  "companies_by_status": {
    "active": 47,
    "inactive": 2,
    "suspended": 1
  },
  "total_users": 1250,
  "users_by_role": {
    "admin": 15,
    "manager": 125,
    "customer": 1100,
    "viewer": 10
  },
  "new_companies_last_30_days": 8,
  "new_users_last_30_days": 125
}
```

### Configuration Endpoints

#### User Roles
```http
GET /api/v1/users/roles
```
**Response:**
```json
{
  "roles": [
    {
      "name": "Admin",
      "code": "admin",
      "permissions": ["all"]
    },
    {
      "name": "Customer",
      "code": "customer",
      "permissions": ["read"]
    }
  ]
}
```

#### Document Types
```http
GET /api/v1/document-types
```
**Response:**
```json
[
  {
    "id": 1,
    "name": "Cédula de Ciudadanía",
    "code": "cedula",
    "description": "Documento de identidad para ciudadanos",
    "active": true,
    "created_at": "2025-07-22T02:12:35.206723"
  }
]
```

## Database Schema

### Tables
1. **users** - User account information and authentication
2. **companies** - Company profiles and business information
3. **document_types** - Supported document types for verification

### Relationships
- **User → Company**: Many-to-One (users belong to companies)
- **Company → Users**: One-to-Many (companies have multiple users)

### Indexes
- `users.unique_id` (unique)
- `users.username` (unique)
- `users.email` (unique)
- `companies.company_id` (unique)
- `companies.document_number` (unique)

## Configuration

### Environment Variables
```bash
SERVICE_NAME=customer-service
DATABASE_URL=postgresql+asyncpg://customer:customer_pass@customer-db:5432/customer_db
REDIS_URL=redis://redis:6379/1
CONSUL_HOST=consul
CONSUL_PORT=8500
LOG_LEVEL=INFO
```

### Database Connection
- **Driver**: AsyncPG (PostgreSQL async driver)
- **Pool Size**: Configured for high concurrency
- **Connection Timeout**: 30 seconds
- **Echo**: Enabled in development for SQL query logging

## Security Features

### Authentication
- JWT token-based authentication
- Password hashing using bcrypt
- Session management with Redis

### Authorization
- Role-based access control (RBAC)
- Permission-based resource access
- Company-level data isolation

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting for API endpoints

## Integration Points

### Outbound Integrations
- **Order Service**: User validation for order creation
- **Shipping Service**: Company verification for manifests
- **External APIs**: Third-party authentication providers

### Inbound Integrations
- **API Gateway**: Authentication and request routing
- **Analytics Service**: User and company metrics
- **Notification Service**: User communication

## Monitoring & Observability

### Health Checks
- Database connectivity check
- Redis connectivity check
- Service dependency validation

### Metrics
- User registration rates
- Authentication success/failure rates
- Company onboarding metrics
- API response times

### Logging
- Structured logging with structured log
- User action audit trails
- Security event logging
- Performance metrics

## Error Handling

### HTTP Status Codes
- `200 OK` - Successful operation
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (duplicate)
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "USER_NOT_FOUND",
  "timestamp": "2025-07-22T02:12:35.206723Z"
}
```

## Testing

### Unit Tests
- Model validation tests
- Business logic tests
- Utility function tests

### Integration Tests
- API endpoint tests
- Database integration tests
- External service mocking

### Load Tests
- Concurrent user creation
- Authentication throughput
- Database connection pooling

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

### Docker Development
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.microservices.yml up customer-service
```