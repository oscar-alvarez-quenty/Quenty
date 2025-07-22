from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings
from .models import User, UserSession, OAuthAccount, Role
from .database import get_db
import secrets
import hashlib
import structlog
import uuid
from datetime import timezone

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token extraction
security = HTTPBearer()

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("Password verification error", error=str(e))
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

async def get_user_permissions(db: AsyncSession, user: User) -> list[str]:
    """Get all permissions for a user including role-based permissions"""
    permissions = set()
    
    # Add role-based permissions (role should already be loaded via selectinload)
    if user.role and user.role.permissions:
        permissions.update(user.role.permissions)
    
    # Add additional user-specific permissions
    if user.additional_permissions:
        permissions.update(user.additional_permissions)
    
    return list(permissions)

def generate_jwt_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow() - timedelta(seconds=30)  # Set iat 30 seconds in the past to avoid timing issues
    })
    
    # Debug: Print JTI being used in token (should always be provided by caller now)
    print(f"DEBUG: Generating JWT token with JTI: {to_encode.get('jti', 'NOT_PROVIDED')}")
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT token", error=str(e))
        raise AuthenticationError("Invalid token")

async def authenticate_user(db: AsyncSession, username_or_email: str, password: str) -> Optional[User]:
    """Authenticate a user with username/email and password"""
    try:
        # Find user by username or email with eager loading of role relationship
        stmt = select(User).options(selectinload(User.role)).where(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.info("User not found", username_or_email=username_or_email)
            return None
        
        # Check if user is active
        if not user.is_active:
            logger.info("User account is inactive", user_id=user.id)
            return None
        
        # Check if user is locked
        if user.is_locked:
            logger.info("User account is locked", user_id=user.id)
            return None
        
        # Verify password
        if not user.password_hash:
            logger.info("User has no password (OAuth only)", user_id=user.id)
            return None
        
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            await increment_failed_login_attempts(db, user)
            logger.info("Password verification failed", user_id=user.id)
            return None
        
        # Reset failed login attempts on successful authentication
        if user.failed_login_attempts > 0:
            await reset_failed_login_attempts(db, user)
        
        # Update last login
        stmt = update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
        await db.execute(stmt)
        # Let the parent transaction handle the commit
        
        logger.info("User authenticated successfully", user_id=user.id)
        return user
        
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        return None

async def increment_failed_login_attempts(db: AsyncSession, user: User):
    """Increment failed login attempts and lock account if necessary"""
    failed_attempts = user.failed_login_attempts + 1
    locked_until = None
    
    if failed_attempts >= settings.max_login_attempts:
        locked_until = datetime.utcnow() + timedelta(minutes=settings.lockout_duration_minutes)
        logger.warning("User account locked due to failed login attempts", 
                      user_id=user.id, failed_attempts=failed_attempts)
    
    stmt = update(User).where(User.id == user.id).values(
        failed_login_attempts=failed_attempts,
        locked_until=locked_until
    )
    await db.execute(stmt)
    # Let the parent transaction handle the commit

async def reset_failed_login_attempts(db: AsyncSession, user: User):
    """Reset failed login attempts"""
    stmt = update(User).where(User.id == user.id).values(
        failed_login_attempts=0,
        locked_until=None
    )
    await db.execute(stmt)
    # Let the parent transaction handle the commit

async def create_user_session(
    db: AsyncSession, 
    user: User, 
    request: Request,
    token_type: str = "access",
    expires_delta: Optional[timedelta] = None
) -> UserSession:
    """Create a new user session"""
    if expires_delta is None:
        if token_type == "refresh":
            expires_delta = timedelta(days=settings.jwt_refresh_expiration_days)
        else:
            expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    
    expires_at = datetime.utcnow() + expires_delta
    session_id = str(uuid.uuid4())
    jti = str(uuid.uuid4())
    
    # Extract client information
    user_agent = request.headers.get("user-agent", "Unknown")
    ip_address = request.client.host if request.client else None
    
    session = UserSession(
        user_id=user.id,
        session_id=session_id,
        jti=jti,
        token_type=token_type,
        device_info=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(session)
    # Let the parent transaction handle the commit
    await db.flush()  # Flush to get the ID without committing
    await db.refresh(session)
    
    # Debug: Print created session JTI
    print(f"DEBUG: Created session with JTI: {session.jti}, ID: {session.id}")
    
    return session

async def get_user_session(db: AsyncSession, jti: str) -> Optional[UserSession]:
    """Get user session by JWT ID"""
    stmt = select(UserSession).where(UserSession.jti == jti, UserSession.is_active == True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def revoke_user_session(db: AsyncSession, session: UserSession):
    """Revoke a user session"""
    stmt = update(UserSession).where(UserSession.id == session.id).values(
        is_active=False,
        revoked_at=datetime.utcnow()
    )
    await db.execute(stmt)
    # Let the parent transaction handle the commit

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        # Decode JWT token
        payload = decode_jwt_token(credentials.credentials)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if not user_id or not jti:
            raise AuthenticationError("Invalid token payload")
        
        # Verify session exists and is active
        session = await get_user_session(db, jti)
        if not session or session.is_expired:
            raise AuthenticationError("Session expired or invalid")
        
        # Get user with eager loading of role relationship
        stmt = select(User).options(selectinload(User.role)).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        # Update last activity
        stmt = update(UserSession).where(UserSession.id == session.id).values(
            last_activity=datetime.utcnow()
        )
        await db.execute(stmt)
        # Let the parent transaction handle the commit
        
        return user
        
    except jwt.PyJWTError as e:
        logger.warning("JWT validation error", error=str(e))
        raise AuthenticationError("Invalid token")
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise AuthenticationError("Authentication failed")

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (additional validation)"""
    if not current_user.is_active:
        raise AuthenticationError("User account is inactive")
    return current_user

async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise AuthorizationError("Superuser access required")
    return current_user

def require_permissions(permissions: list[str]):
    """Decorator factory to require specific permissions"""
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        # Superusers have all permissions
        if current_user.is_superuser:
            return current_user
        
        # Get user permissions
        user_permissions = await get_user_permissions(db, current_user)
        user_permissions_set = set(user_permissions)
        required_permissions = set(permissions)
        
        # Check for wildcard permission
        if "*" in user_permissions_set:
            return current_user
        
        # Check if user has required permissions
        if not required_permissions.issubset(user_permissions_set):
            missing_perms = required_permissions - user_permissions_set
            raise AuthorizationError(f"Missing permissions: {', '.join(missing_perms)}")
        
        return current_user
    
    return permission_checker

def require_roles(roles: list[str]):
    """Decorator factory to require specific roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.code if current_user.role else None
        if user_role not in roles:
            raise AuthorizationError(f"Required roles: {', '.join(roles)}")
        return current_user
    
    return role_checker

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def hash_token(token: str) -> str:
    """Hash a token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

async def create_password_reset_token(db: AsyncSession, user: User) -> str:
    """Create a password reset token"""
    from .models import PasswordResetToken
    
    # Generate secure token
    token = generate_secure_token()
    token_hash = hash_token(token)
    
    # Create token record
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
    )
    
    db.add(reset_token)
    # Let the parent transaction handle the commit
    await db.flush()  # Flush to get the ID without committing
    
    return token

async def verify_password_reset_token(db: AsyncSession, token: str) -> Optional[User]:
    """Verify password reset token and return user"""
    from .models import PasswordResetToken
    
    token_hash = hash_token(token)
    
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.is_used == False
    ).join(User)
    
    result = await db.execute(stmt)
    reset_token = result.scalar_one_or_none()
    
    if not reset_token or not reset_token.is_valid:
        return None
    
    return reset_token.user

class SecurityMiddleware:
    """Security middleware for additional protections"""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get client IP address considering proxies"""
        # Check for forwarded IP headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def extract_device_info(request: Request) -> Dict[str, str]:
        """Extract device information from request headers"""
        return {
            "user_agent": request.headers.get("user-agent", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept": request.headers.get("accept", "")
        }