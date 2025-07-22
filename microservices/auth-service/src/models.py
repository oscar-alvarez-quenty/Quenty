from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime, timedelta
import uuid

class User(Base):
    """User model with authentication and profile information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(255), unique=True, index=True, default=lambda: f"USER-{str(uuid.uuid4())[:8].upper()}")
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    
    # Profile Information
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    avatar_url = Column(String(500))
    
    # User Status and Security
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Authentication Security
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Company Association
    company_id = Column(String(255), ForeignKey("companies.company_id"), nullable=True)
    
    # Role and Permissions
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    additional_permissions = Column(JSON, default=list)  # Additional permissions beyond role
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    role = relationship("Role", back_populates="users")
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    @property
    def is_locked(self):
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class Company(Base):
    """Company/Organization model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(String(255), unique=True, index=True, nullable=False, default=lambda: f"COMP-{str(uuid.uuid4())[:8].upper()}")
    
    # Company Information
    name = Column(String(500), nullable=False)
    business_name = Column(String(500))
    description = Column(Text)
    website = Column(String(500))
    logo_url = Column(String(500))
    
    # Legal Information
    document_type = Column(String(50))  # NIT, RUT, TAX_ID, etc.
    document_number = Column(String(100), unique=True)
    legal_address = Column(Text)
    
    # Business Configuration
    industry = Column(String(100))
    company_size = Column(String(50))  # startup, small, medium, large, enterprise
    timezone = Column(String(50), default="UTC")
    
    # Status and Settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    subscription_plan = Column(String(50), default="basic")  # basic, pro, enterprise
    settings = Column(JSON, default=dict)  # Company-specific settings
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="company")
    audit_logs = relationship("AuditLog", back_populates="company")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', company_id='{self.company_id}')>"

class OAuthAccount(Base):
    """OAuth account linking (Google, Azure, etc.)"""
    __tablename__ = "oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # OAuth Provider Information
    provider = Column(String(50), nullable=False)  # google, azure, github, etc.
    provider_user_id = Column(String(255), nullable=False)
    provider_email = Column(String(255))
    provider_username = Column(String(255))
    
    # OAuth Data
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    scope = Column(String(500))
    
    # Provider Profile Data
    provider_data = Column(JSON, default=dict)  # Store additional provider data
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    # Unique constraint to prevent duplicate accounts
    __table_args__ = (UniqueConstraint('provider', 'provider_user_id', name='unique_provider_user'),)
    
    def __repr__(self):
        return f"<OAuthAccount(id={self.id}, provider='{self.provider}', user_id={self.user_id})>"

class UserSession(Base):
    """User session management for JWT tokens"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Session Information
    device_info = Column(String(500))  # User agent, device info
    ip_address = Column(String(45))  # IPv4 or IPv6
    location = Column(String(255))  # City, Country
    
    # Token Information
    jti = Column(String(255), unique=True, index=True, nullable=False)  # JWT ID
    token_type = Column(String(50), default="access", nullable=False)  # access, refresh
    
    # Session Status
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}')>"

class PasswordResetToken(Base):
    """Password reset tokens"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Token Information
    token = Column(String(255), unique=True, index=True, nullable=False)
    token_hash = Column(String(255), nullable=False)  # Hashed version for security
    
    # Token Status
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="password_resets")
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"

class Role(Base):
    """Role definitions for RBAC"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text)
    
    # Role Configuration
    permissions = Column(JSON, default=list)  # List of permissions
    is_system_role = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted
    is_default = Column(Boolean, default=False, nullable=False)  # Default role for new users
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', code='{self.code}')>"

class Permission(Base):
    """Permission definitions"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    
    # Permission Organization
    category = Column(String(50))  # users, orders, shipping, admin, etc.
    resource = Column(String(50))  # The resource this permission applies to
    action = Column(String(50))   # create, read, update, delete, etc.
    
    # Permission Status
    is_system_permission = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}', action='{self.action}')>"

class AuditLog(Base):
    """Audit log for tracking user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(String(255), ForeignKey("companies.company_id"), nullable=True)
    
    # Action Information
    action = Column(String(100), nullable=False)  # login, logout, create_user, etc.
    resource_type = Column(String(50))  # user, company, order, etc.
    resource_id = Column(String(255))   # ID of the affected resource
    
    # Request Information
    ip_address = Column(String(45))
    user_agent = Column(String(1000))
    request_id = Column(String(255))
    
    # Action Details
    details = Column(JSON, default=dict)  # Additional action details
    result = Column(String(50))  # success, failure, error
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    company = relationship("Company", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"

class DocumentType(Base):
    """Document types for user/company verification"""
    __tablename__ = "document_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    # Document Configuration
    country_code = Column(String(10))  # Country this document type applies to
    category = Column(String(50))  # personal, business, government
    validation_regex = Column(String(500))  # Regex for document format validation
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DocumentType(id={self.id}, name='{self.name}', code='{self.code}')>"