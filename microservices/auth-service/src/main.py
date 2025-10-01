from fastapi import FastAPI, HTTPException, Depends, Request, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
import structlog
import uuid
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

from .config import settings
from .database import get_db, init_db, close_db
from .models import User, Company, OAuthAccount, UserSession, PasswordResetToken, Role, Permission, AuditLog, DocumentType
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserProfile, PaginatedUsers,
    CompanyCreate, CompanyUpdate, CompanyResponse, PaginatedCompanies,
    LoginRequest, TokenResponse, RefreshTokenRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, OAuthLoginRequest, OAuthCallbackRequest,
    UserSessionResponse, RoleResponse, PermissionResponse, AuditLogResponse,
    DocumentTypeResponse, HealthCheck, ErrorResponse,
    PublicUserRegistration, PublicRegistrationResponse, UserType
)
from .security import (
    authenticate_user, get_password_hash, generate_jwt_token, decode_jwt_token,
    get_current_user, get_user_permissions, create_user_session, get_user_session,
    create_password_reset_token, verify_password_reset_token, require_permissions,
    revoke_user_session, SecurityMiddleware, verify_password
)
from .oauth import oauth_service
from .email_service import email_service

# Import logging configuration
import os
import logging
try:
    from .logging_config import LOGGING_MESSAGES, ERROR_MESSAGES, INFO_MESSAGES, DEBUG_MESSAGES, WARNING_MESSAGES
except ImportError:
    # Fallback if logging_config is not available
    LOGGING_MESSAGES = ERROR_MESSAGES = INFO_MESSAGES = DEBUG_MESSAGES = WARNING_MESSAGES = {}

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Set log level from environment
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = structlog.get_logger("auth-service")

# Create FastAPI app
app = FastAPI(
    title="Quenty Authentication Service",
    description="Comprehensive user management and authentication microservice with JWT and OAuth support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security instance
security = HTTPBearer()

# Prometheus metrics
auth_requests_total = Counter(
    'auth_requests_total',
    'Total number of authentication requests',
    ['method', 'endpoint', 'status']
)
auth_request_duration = Histogram(
    'auth_request_duration_seconds',
    'Duration of authentication requests in seconds',
    ['method', 'endpoint']
)
active_sessions = Counter(
    'auth_active_sessions_total',
    'Total number of active user sessions',
    ['token_type']
)
failed_login_attempts = Counter(
    'auth_failed_login_attempts_total',
    'Total number of failed login attempts'
)

async def create_initial_admin_user():
    """Create initial admin user if configured and no users exist"""
    if not all([settings.initial_admin_username, settings.initial_admin_password, settings.initial_admin_email]):
        return
    
    db_gen = get_db()
    db = await db_gen.__anext__()
    
    try:
        # Check if any users exist
        result = await db.execute(select(func.count(User.id)))
        user_count = result.scalar()
        
        if user_count > 0:
            logger.info("Users already exist, skipping initial admin creation")
            return
            
        # Get superuser role
        role_result = await db.execute(select(Role).where(Role.code == "superuser"))
        superuser_role = role_result.scalar_one_or_none()
        
        if not superuser_role:
            logger.error("Superuser role not found, cannot create initial admin")
            return
        
        # Create initial admin user
        hashed_password = get_password_hash(settings.initial_admin_password)
        admin_user = User(
            username=settings.initial_admin_username,
            email=settings.initial_admin_email,
            first_name=settings.initial_admin_first_name,
            last_name=settings.initial_admin_last_name,
            password_hash=hashed_password,
            role_id=superuser_role.id,
            is_superuser=True,
            is_active=True,
            is_verified=True,
            email_verified=True,
            unique_id=str(uuid.uuid4())
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        logger.info(
            "Initial admin user created successfully",
            username=settings.initial_admin_username,
            email=settings.initial_admin_email
        )
        
    except Exception as e:
        logger.error("Failed to create initial admin user", error=str(e))
        await db.rollback()
    finally:
        await db.close()

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        await init_db()
        
        # Initialize default roles and permissions if needed
        await initialize_default_data()
        
        # Create initial admin user if configured
        await create_initial_admin_user()
        
        logger.info("Auth service started successfully")
        
    except Exception as e:
        logger.error("Failed to start auth service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await close_db()
        logger.info("Auth service shutdown successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

async def initialize_default_data():
    """Initialize default roles, permissions, and document types"""
    async for db in get_db():
        try:
            # Create default roles if they don't exist
            default_roles = [
                {"name": "Super Administrator", "code": "superuser", "permissions": ["*"], "is_system_role": True},
                {"name": "Administrator", "code": "admin", "permissions": ["users:*", "companies:*", "roles:*"], "is_system_role": True},
                {"name": "Manager", "code": "manager", "permissions": ["users:read", "orders:*", "shipping:*"], "is_system_role": True},
                {"name": "Customer", "code": "customer", "permissions": ["profile:*", "orders:read"], "is_system_role": True, "is_default": True},
                {"name": "Viewer", "code": "viewer", "permissions": ["profile:read", "orders:read"], "is_system_role": True}
            ]
            
            for role_data in default_roles:
                stmt = select(Role).where(Role.code == role_data["code"])
                result = await db.execute(stmt)
                existing_role = result.scalar_one_or_none()
                
                if not existing_role:
                    role = Role(**role_data)
                    db.add(role)
            
            # Create default permissions
            default_permissions = [
                {"name": "All Permissions", "code": "*", "category": "system", "resource": "*", "action": "*", "is_system_permission": True},
                {"name": "Read Users", "code": "users:read", "category": "users", "resource": "user", "action": "read", "is_system_permission": True},
                {"name": "Create Users", "code": "users:create", "category": "users", "resource": "user", "action": "create", "is_system_permission": True},
                {"name": "Update Users", "code": "users:update", "category": "users", "resource": "user", "action": "update", "is_system_permission": True},
                {"name": "Delete Users", "code": "users:delete", "category": "users", "resource": "user", "action": "delete", "is_system_permission": True},
                {"name": "All User Operations", "code": "users:*", "category": "users", "resource": "user", "action": "*", "is_system_permission": True},
                {"name": "Manage Profile", "code": "profile:*", "category": "profile", "resource": "profile", "action": "*", "is_system_permission": True},
                {"name": "Read Orders", "code": "orders:read", "category": "orders", "resource": "order", "action": "read", "is_system_permission": True},
                {"name": "All Order Operations", "code": "orders:*", "category": "orders", "resource": "order", "action": "*", "is_system_permission": True},
            ]
            
            for perm_data in default_permissions:
                stmt = select(Permission).where(Permission.code == perm_data["code"])
                result = await db.execute(stmt)
                existing_perm = result.scalar_one_or_none()
                
                if not existing_perm:
                    permission = Permission(**perm_data)
                    db.add(permission)
            
            # Create default document types
            default_document_types = [
                {"name": "Cédula de Ciudadanía", "code": "cedula", "country_code": "CO", "category": "personal"},
                {"name": "Passport", "code": "passport", "category": "personal"},
                {"name": "Driver's License", "code": "drivers_license", "category": "personal"},
                {"name": "NIT", "code": "nit", "country_code": "CO", "category": "business"},
                {"name": "RUT", "code": "rut", "country_code": "CO", "category": "business"},
                {"name": "Tax ID", "code": "tax_id", "category": "business"},
            ]
            
            for doc_data in default_document_types:
                stmt = select(DocumentType).where(DocumentType.code == doc_data["code"])
                result = await db.execute(stmt)
                existing_doc = result.scalar_one_or_none()
                
                if not existing_doc:
                    doc_type = DocumentType(**doc_data)
                    db.add(doc_type)
            
            await db.commit()
            logger.info("Default data initialized")
            
        except Exception as e:
            logger.error("Failed to initialize default data", error=str(e))
        break

# Health Check
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        service="auth-service",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        dependencies={
            "database": "healthy",
            "redis": "healthy"
        }
    )

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Authentication Endpoints
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    start_time = time.time()
    try:
        # Authenticate user
        user = await authenticate_user(db, login_data.username_or_email, login_data.password)
        if not user:
            failed_login_attempts.inc()
            auth_requests_total.labels(method='POST', endpoint='/api/v1/auth/login', status='401').inc()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token session
        access_expires = timedelta(minutes=settings.jwt_expiration_minutes)
        if login_data.remember_me:
            access_expires = timedelta(hours=24)  # Longer session if remember me
        
        access_session = await create_user_session(db, user, request, "access", access_expires)
        
        # Create refresh token session
        refresh_expires = timedelta(days=settings.jwt_refresh_expiration_days)
        refresh_session = await create_user_session(db, user, request, "refresh", refresh_expires)
        
        # Generate JWT tokens
        print(f"DEBUG MAIN: About to generate access token with JTI: {access_session.jti}")
        access_token = generate_jwt_token({
            "sub": str(user.id),
            "jti": access_session.jti,
            "type": "access"
        }, access_expires)
        print(f"DEBUG MAIN: Generated access token: {access_token[:50]}...")
        
        refresh_token = generate_jwt_token({
            "sub": str(user.id),
            "jti": refresh_session.jti,
            "type": "refresh"
        }, refresh_expires)
        
        # Log successful login
        await log_audit_event(db, user, "login", "authentication", str(user.id), request, "success")
        
        # Get user permissions for profile
        permissions = await get_user_permissions(db, user)
        
        # Track metrics
        auth_requests_total.labels(method='POST', endpoint='/api/v1/auth/login', status='200').inc()
        auth_request_duration.labels(method='POST', endpoint='/api/v1/auth/login').observe(time.time() - start_time)
        active_sessions.labels(token_type='access').inc()
        active_sessions.labels(token_type='refresh').inc()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_expires.total_seconds()),
            user=UserProfile.from_user(user, permissions)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Decode refresh token
        payload = decode_jwt_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        # Verify refresh session
        session = await get_user_session(db, jti)
        if not session or session.token_type != "refresh" or session.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user with eager loading of role relationship
        stmt = select(User).options(selectinload(User.role)).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token session
        access_expires = timedelta(minutes=settings.jwt_expiration_minutes)
        access_session = await create_user_session(db, user, request, "access", access_expires)
        
        # Generate new access token
        access_token = generate_jwt_token({
            "sub": str(user.id),
            "jti": access_session.jti,
            "type": "access"
        }, access_expires)
        
        # Get user permissions for profile
        permissions = await get_user_permissions(db, user)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # Keep same refresh token
            expires_in=int(access_expires.total_seconds()),
            user=UserProfile.from_user(user, permissions)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@app.post("/api/v1/auth/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and revoke current session"""
    try:
        # Get current session from token
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.replace("Bearer ", "")
            payload = decode_jwt_token(token)
            jti = payload.get("jti")
            
            # Revoke current session
            session = await get_user_session(db, jti)
            if session:
                await revoke_user_session(db, session)
        
        # Log logout
        await log_audit_event(db, current_user, "logout", "authentication", str(current_user.id), request, "success")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error("Logout error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# OAuth Endpoints
@app.get("/api/v1/auth/{provider}/login")
async def oauth_login(provider: str, redirect_uri: Optional[str] = None):
    """Initiate OAuth login flow"""
    try:
        state = str(uuid.uuid4())
        authorization_url = await oauth_service.get_authorization_url(provider, state)
        
        # In production, you might want to store the state in Redis for validation
        return {"authorization_url": authorization_url, "state": state}
        
    except Exception as e:
        logger.error("OAuth login error", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth login failed: {str(e)}"
        )

@app.get("/api/v1/auth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback"""
    try:
        # Handle OAuth callback
        result = await oauth_service.handle_callback(db, provider, code, state)
        user = result["user"]
        
        # Create user session
        access_expires = timedelta(minutes=settings.jwt_expiration_minutes)
        access_session = await create_user_session(db, user, request, "access", access_expires)
        
        refresh_expires = timedelta(days=settings.jwt_refresh_expiration_days)
        refresh_session = await create_user_session(db, user, request, "refresh", refresh_expires)
        
        # Generate JWT tokens
        access_token = generate_jwt_token({
            "sub": str(user.id),
            "jti": access_session.jti,
            "type": "access"
        }, access_expires)
        
        refresh_token = generate_jwt_token({
            "sub": str(user.id),
            "jti": refresh_session.jti,
            "type": "refresh"
        }, refresh_expires)
        
        # Log successful OAuth login
        await log_audit_event(db, user, f"oauth_login_{provider}", "authentication", str(user.id), request, "success")
        
        # Get user permissions for profile
        permissions = await get_user_permissions(db, user)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_expires.total_seconds()),
            user=UserProfile.from_user(user, permissions)
        )
        
    except Exception as e:
        logger.error("OAuth callback error", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}"
        )

# User Management Endpoints
@app.get("/api/v1/users", response_model=PaginatedUsers)
async def get_users(
    limit: int = 20,
    offset: int = 0,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    company_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_permissions(["users:read"])),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of users"""
    try:
        # Build query
        stmt = select(User).options(selectinload(User.company), selectinload(User.role))
        
        # Apply filters
        filters = []
        if role:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if company_id:
            filters.append(User.company_id == company_id)
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        # Get total count
        count_stmt = select(func.count(User.id))
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        return PaginatedUsers(
            users=[UserResponse.from_user(user) for user in users],
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total,
            has_previous=offset > 0
        )
        
    except Exception as e:
        logger.error("Get users error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    try:
        # Check permissions (users can view their own profile, or need users:read permission)
        if current_user.id != user_id and "users:read" not in (current_user.permissions or []) and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stmt = select(User).options(selectinload(User.company), selectinload(User.role)).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_user(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get user error", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@app.post("/api/v1/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(require_permissions(["users:create"])),
    db: AsyncSession = Depends(get_db)
):
    """Create new user"""
    try:
        # Check if username or email already exists
        stmt = select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.username == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists"
                )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            unique_id=f"USER-{str(uuid.uuid4())[:8].upper()}",
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role,
            company_id=user_data.company_id,
            is_active=True,
            is_verified=False,
            permissions=[]
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Log user creation
        await log_audit_event(db, current_user, "create_user", "user", str(user.id), request, "success")
        
        return UserResponse.from_user(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Create user error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@app.put("/api/v1/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user"""
    try:
        # Check permissions
        if current_user.id != user_id and "users:update" not in (current_user.permissions or []) and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get user
        stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        # Log user update
        await log_audit_event(db, current_user, "update_user", "user", str(user.id), request, "success")
        
        return UserResponse.from_user(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update user error", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@app.delete("/api/v1/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_permissions(["users:delete"])),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (soft delete by deactivating)"""
    try:
        # Get user
        stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete by deactivating
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # Log user deletion
        await log_audit_event(db, current_user, "delete_user", "user", str(user.id), request, "success")
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete user error", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

# Profile Management
@app.get("/api/v1/profile", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile with permissions"""
    # Get user permissions from role and additional permissions
    permissions = await get_user_permissions(db, current_user)
    
    # Create user profile using the from_user method
    return UserProfile.from_user(current_user, permissions)

@app.put("/api/v1/profile", response_model=UserProfile)
async def update_profile(
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    try:
        # Update fields (excluding role and permissions for profile updates)
        allowed_fields = ['first_name', 'last_name', 'phone', 'avatar_url']
        update_data = user_data.dict(include=allowed_fields, exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(current_user)
        
        # Log profile update
        await log_audit_event(db, current_user, "update_profile", "profile", str(current_user.id), request, "success")
        
        # Get user permissions for profile
        permissions = await get_user_permissions(db, current_user)
        
        return UserProfile.from_user(current_user, permissions)
        
    except Exception as e:
        logger.error("Update profile error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

# Password Management
@app.post("/api/v1/auth/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not current_user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth users cannot change password"
            )

        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Update password
        new_password_hash = get_password_hash(password_data.new_password)
        current_user.password_hash = new_password_hash
        current_user.password_changed_at = datetime.utcnow()
        current_user.updated_at = datetime.utcnow()

        await db.commit()

        # Log password change
        await log_audit_event(db, current_user, "change_password", "authentication", str(current_user.id), request, "success")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Change password error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@app.post("/api/v1/auth/register", response_model=PublicRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def public_register(
    registration_data: PublicUserRegistration,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Public user registration endpoint (no authentication required)"""
    try:
        # Check if email already exists
        existing_user = await db.execute(
            select(User).where(User.email == registration_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Get document type by code
        doc_type_result = await db.execute(
            select(DocumentType).where(DocumentType.code == registration_data.document_type_code)
        )
        doc_type = doc_type_result.scalar_one_or_none()
        if not doc_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type: {registration_data.document_type_code}"
            )

        # Check if document number already exists
        existing_doc = await db.execute(
            select(User).where(User.document_number == registration_data.document_number)
        )
        if existing_doc.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document number already registered"
            )

        # Get default role
        default_role_result = await db.execute(
            select(Role).where(Role.is_default == True)
        )
        default_role = default_role_result.scalar_one_or_none()

        company_id = None

        # Handle company registration for juridica users
        if registration_data.user_type == UserType.JURIDICA:
            # Check if NIT already exists
            existing_company = await db.execute(
                select(Company).where(Company.document_number == registration_data.company_data.nit)
            )
            if existing_company.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Company NIT already registered"
                )

            # Create company
            company = Company(
                name=registration_data.company_data.name,
                document_type="nit",
                document_number=registration_data.company_data.nit,
                is_active=True,
                is_verified=False
            )
            db.add(company)
            await db.flush()  # Get company_id
            company_id = company.company_id

        # Generate username from email
        username = registration_data.email.split('@')[0]
        # Ensure username uniqueness by adding numbers if needed
        base_username = username
        counter = 1
        while True:
            existing = await db.execute(select(User).where(User.username == username))
            if not existing.scalar_one_or_none():
                break
            username = f"{base_username}{counter}"
            counter += 1

        # Create user
        user = User(
            username=username,
            email=registration_data.email,
            password_hash=get_password_hash(registration_data.password),
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            phone=registration_data.phone,
            user_type=registration_data.user_type.value,
            document_type_id=doc_type.id,
            document_number=registration_data.document_number,
            terms_accepted=registration_data.terms_accepted,
            terms_accepted_at=datetime.utcnow() if registration_data.terms_accepted else None,
            privacy_policy_accepted=registration_data.privacy_policy_accepted,
            privacy_policy_accepted_at=datetime.utcnow() if registration_data.privacy_policy_accepted else None,
            marketing_consent=registration_data.marketing_consent,
            marketing_consent_at=datetime.utcnow() if registration_data.marketing_consent else None,
            company_id=company_id,
            role_id=default_role.id if default_role else None,
            is_active=True,
            is_verified=False,
            email_verified=False
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create access token session
        access_expires = timedelta(minutes=settings.jwt_expiration_minutes)
        access_session = await create_user_session(db, user, request, "access", access_expires)

        # Create refresh token session
        refresh_expires = timedelta(days=settings.jwt_refresh_expiration_days)
        refresh_session = await create_user_session(db, user, request, "refresh", refresh_expires)

        # Generate JWT tokens
        access_token = generate_jwt_token({
            "sub": str(user.id),
            "jti": access_session.jti,
            "type": "access"
        }, access_expires)

        refresh_token = generate_jwt_token({
            "sub": str(user.id),
            "jti": refresh_session.jti,
            "type": "refresh"
        }, refresh_expires)

        # Send welcome email (async, don't wait for it)
        try:
            user_name = user.full_name if registration_data.user_type == UserType.NATURAL else registration_data.company_data.name
            email_service.send_welcome_email(user.email, user_name, user.user_type)
        except Exception as e:
            logger.error("Failed to send welcome email", user_id=user.id, error=str(e))

        # Log registration
        await log_audit_event(db, user, "register", "user", str(user.id), request, "success", {"user_type": user.user_type})

        return PublicRegistrationResponse(
            message="Registration successful",
            user_id=user.id,
            unique_id=user.unique_id,
            email=user.email,
            user_type=user.user_type,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_expires.total_seconds())
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/api/v1/auth/password-reset/request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset - sends email with reset link"""
    try:
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == reset_request.email)
        )
        user = result.scalar_one_or_none()

        # Always return success to prevent email enumeration
        if not user:
            logger.warning("Password reset requested for non-existent email", email=reset_request.email)
            return {"message": "If the email exists, a password reset link has been sent"}

        # Check if user has password (OAuth users don't)
        if not user.password_hash:
            logger.warning("Password reset requested for OAuth-only user", user_id=user.id)
            return {"message": "If the email exists, a password reset link has been sent"}

        # Create password reset token
        token_value = await create_password_reset_token(db, user)

        # Send password reset email
        try:
            email_sent = email_service.send_password_reset_email(
                to_email=user.email,
                reset_token=token_value,
                user_name=user.full_name
            )
            if not email_sent:
                logger.error("Failed to send password reset email", user_id=user.id)
        except Exception as e:
            logger.error("Error sending password reset email", user_id=user.id, error=str(e))

        # Log password reset request
        await log_audit_event(db, user, "password_reset_request", "authentication", str(user.id), request, "success")

        return {"message": "If the email exists, a password reset link has been sent"}

    except Exception as e:
        logger.error("Password reset request error", error=str(e))
        # Still return success to prevent enumeration
        return {"message": "If the email exists, a password reset link has been sent"}

@app.post("/api/v1/auth/password-reset/confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Confirm password reset with token"""
    try:
        # Verify reset token
        user = await verify_password_reset_token(db, reset_confirm.token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Update password
        new_password_hash = get_password_hash(reset_confirm.new_password)
        user.password_hash = new_password_hash
        user.password_changed_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()

        # Mark token as used
        token_result = await db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.token == reset_confirm.token,
                    PasswordResetToken.is_used == False
                )
            )
        )
        token = token_result.scalar_one_or_none()
        if token:
            token.is_used = True

        await db.commit()

        # Revoke all existing sessions for security
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id)
            .values(is_revoked=True, revoked_at=datetime.utcnow())
        )
        await db.commit()

        # Log password reset
        await log_audit_event(db, user, "password_reset_confirm", "authentication", str(user.id), request, "success")

        return {"message": "Password reset successful. Please log in with your new password."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password reset confirm error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# Helper function for audit logging
async def log_audit_event(
    db: AsyncSession,
    user: Optional[User],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    request: Request,
    result: str,
    details: dict = None
):
    """Log audit event"""
    try:
        audit_log = AuditLog(
            user_id=user.id if user else None,
            company_id=user.company_id if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=SecurityMiddleware.get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            details=details or {},
            result=result
        )
        
        db.add(audit_log)
        await db.commit()
        
    except Exception as e:
        logger.error("Failed to log audit event", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)