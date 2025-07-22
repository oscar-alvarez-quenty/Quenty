from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    SUPERUSER = "superuser"
    ADMIN = "admin"
    MANAGER = "manager"
    CUSTOMER = "customer"
    VIEWER = "viewer"

class CompanySize(str, Enum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"

class SubscriptionPlan(str, Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class OAuthProvider(str, Enum):
    GOOGLE = "google"
    AZURE = "azure"

# Base Models
class BaseTimestamp(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = Field(UserRole.CUSTOMER, description="User role")
    company_id: Optional[str] = Field(None, description="Associated company ID")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")
    password_confirm: str = Field(..., description="Password confirmation")
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None

class UserResponse(UserBase, BaseTimestamp):
    id: int
    unique_id: str
    email_verified: bool
    is_active: bool
    is_verified: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    permissions: List[str] = []
    
    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    unique_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    company_id: Optional[str] = None
    permissions: List[str] = []
    
    class Config:
        from_attributes = True

# Company Schemas
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Company name")
    business_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    website: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[CompanySize] = None
    legal_address: Optional[str] = None
    timezone: str = Field("UTC", description="Company timezone")

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[CompanySize] = None
    legal_address: Optional[str] = None
    timezone: Optional[str] = None
    subscription_plan: Optional[SubscriptionPlan] = None
    settings: Optional[Dict[str, Any]] = None

class CompanyResponse(CompanyBase, BaseTimestamp):
    id: int
    company_id: str
    logo_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    subscription_plan: str
    settings: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True

# Authentication Schemas
class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Keep user logged in for longer")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    new_password_confirm: str
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    new_password_confirm: str
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# OAuth Schemas
class OAuthLoginRequest(BaseModel):
    provider: OAuthProvider
    redirect_uri: Optional[str] = None

class OAuthCallbackRequest(BaseModel):
    provider: OAuthProvider
    code: str
    state: Optional[str] = None

class OAuthAccountResponse(BaseModel):
    id: int
    provider: str
    provider_email: Optional[str] = None
    provider_username: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Session Management
class UserSessionResponse(BaseModel):
    id: int
    session_id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    is_active: bool
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    
    class Config:
        from_attributes = True

# Role and Permission Schemas
class RoleBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    permissions: List[str] = []

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int
    is_system_role: bool
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PermissionResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    category: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    
    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    company_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    result: Optional[str] = None
    details: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True

# Document Type Schemas
class DocumentTypeResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    country_code: Optional[str] = None
    category: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True

# Pagination
class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

class PaginatedUsers(PaginatedResponse):
    users: List[UserResponse]

class PaginatedCompanies(PaginatedResponse):
    companies: List[CompanyResponse]

class PaginatedAuditLogs(PaginatedResponse):
    audit_logs: List[AuditLogResponse]

# Health Check
class HealthCheck(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str] = {}

# Error Response
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime