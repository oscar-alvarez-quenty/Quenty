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

class UserType(str, Enum):
    NATURAL = "natural"
    JURIDICA = "juridica"

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
    
    @classmethod
    def from_user(cls, user):
        """Create UserResponse from User model with proper role handling"""
        return cls(
            id=user.id,
            unique_id=user.unique_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role=user.role.code if user.role else UserRole.CUSTOMER,
            company_id=user.company_id,
            email_verified=user.email_verified,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            avatar_url=user.avatar_url,
            last_login=user.last_login,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            permissions=user.additional_permissions or [],
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
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
    role: Optional[str] = None
    company_id: Optional[str] = None
    permissions: List[str] = []
    
    @classmethod
    def from_user(cls, user, permissions: List[str] = None):
        """Create UserProfile from User model with proper role handling"""
        return cls(
            id=user.id,
            unique_id=user.unique_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role=user.role.code if user.role else None,
            company_id=user.company_id,
            permissions=permissions or []
        )
    
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

# Public Registration Schemas
class CompanyRegistrationData(BaseModel):
    """Company data for juridica registration"""
    name: str = Field(..., min_length=2, max_length=200, description="Company legal name")
    nit: str = Field(..., min_length=9, max_length=20, description="Company NIT number")

    @validator('nit')
    def validate_nit(cls, v):
        # Remove any non-numeric characters
        nit_clean = ''.join(filter(str.isdigit, v))
        if len(nit_clean) < 9:
            raise ValueError('NIT must be at least 9 digits')
        return nit_clean

class PublicUserRegistration(BaseModel):
    """Public user registration schema"""
    user_type: UserType = Field(..., description="Type of user: natural or juridica")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    password_confirm: str = Field(..., description="Password confirmation")
    document_type_code: str = Field(..., description="Document type code (cedula, nit, passport, etc.)")
    document_number: str = Field(..., min_length=5, max_length=100, description="Document number")
    first_name: Optional[str] = Field(None, max_length=100, description="First name (for natural users)")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name (for natural users)")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    terms_accepted: bool = Field(..., description="User accepts terms and conditions")
    privacy_policy_accepted: bool = Field(..., description="User accepts privacy policy")
    marketing_consent: bool = Field(False, description="User consents to marketing communications")
    company_data: Optional[CompanyRegistrationData] = Field(None, description="Company data (required for juridica)")

    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('terms_accepted')
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v

    @validator('privacy_policy_accepted')
    def privacy_must_be_accepted(cls, v):
        if not v:
            raise ValueError('Privacy policy must be accepted')
        return v

    @validator('company_data')
    def validate_company_data(cls, v, values):
        user_type = values.get('user_type')
        if user_type == UserType.JURIDICA and not v:
            raise ValueError('Company data is required for juridica registration')
        if user_type == UserType.NATURAL and v:
            raise ValueError('Company data should not be provided for natural registration')
        return v

    @validator('first_name', 'last_name')
    def validate_names_for_natural(cls, v, values, field):
        user_type = values.get('user_type')
        if user_type == UserType.NATURAL and not v:
            raise ValueError(f'{field.name} is required for natural user registration')
        return v

class PublicRegistrationResponse(BaseModel):
    """Response after successful public registration"""
    message: str
    user_id: int
    unique_id: str
    email: str
    user_type: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

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