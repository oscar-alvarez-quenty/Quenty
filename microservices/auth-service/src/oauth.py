from typing import Dict, Optional, Any
import httpx
from authlib.integrations.base_client import OAuthError
from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from .config import settings
from .models import User, OAuthAccount, Company
from .security import generate_jwt_token
import structlog
import uuid
from datetime import datetime, timedelta

logger = structlog.get_logger()

class OAuthProvider:
    """Base OAuth provider class"""
    
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.scope = None
        self.authorization_url = None
        self.token_url = None
        self.user_info_url = None
    
    async def get_authorization_url(self, state: str) -> str:
        """Get OAuth authorization URL"""
        raise NotImplementedError
    
    async def get_access_token(self, code: str, state: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        raise NotImplementedError
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        raise NotImplementedError
    
    def extract_user_data(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized user data from provider response"""
        raise NotImplementedError

class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth provider"""
    
    def __init__(self):
        super().__init__()
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.scope = "openid email profile"
        self.authorization_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    async def get_authorization_url(self, state: str) -> str:
        """Get Google OAuth authorization URL"""
        if not self.client_id:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google OAuth not configured"
            )
        
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        
        authorization_url, _ = client.create_authorization_url(
            self.authorization_url,
            state=state,
            access_type="offline",
            include_granted_scopes="true"
        )
        
        return authorization_url
    
    async def get_access_token(self, code: str, state: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri
        )
        
        try:
            token = await client.fetch_token(
                self.token_url,
                code=code,
                grant_type="authorization_code"
            )
            return token
        except OAuthError as e:
            logger.error("Google OAuth token exchange failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth token exchange failed: {str(e)}"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.error("Failed to fetch Google user info", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user information"
                )
    
    def extract_user_data(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized user data from Google response"""
        return {
            "provider_user_id": user_info.get("id"),
            "email": user_info.get("email"),
            "email_verified": user_info.get("verified_email", False),
            "first_name": user_info.get("given_name"),
            "last_name": user_info.get("family_name"),
            "full_name": user_info.get("name"),
            "avatar_url": user_info.get("picture"),
            "username": user_info.get("email", "").split("@")[0],
            "provider_data": user_info
        }

class AzureOAuthProvider(OAuthProvider):
    """Azure/Microsoft OAuth provider"""
    
    def __init__(self):
        super().__init__()
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.tenant_id = settings.azure_tenant_id or "common"
        self.redirect_uri = settings.azure_redirect_uri
        self.scope = "openid profile email User.Read"
        self.authorization_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.user_info_url = "https://graph.microsoft.com/v1.0/me"
    
    async def get_authorization_url(self, state: str) -> str:
        """Get Azure OAuth authorization URL"""
        if not self.client_id:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Azure OAuth not configured"
            )
        
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        
        authorization_url, _ = client.create_authorization_url(
            self.authorization_url,
            state=state,
            response_type="code"
        )
        
        return authorization_url
    
    async def get_access_token(self, code: str, state: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri
        )
        
        try:
            token = await client.fetch_token(
                self.token_url,
                code=code,
                grant_type="authorization_code"
            )
            return token
        except OAuthError as e:
            logger.error("Azure OAuth token exchange failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth token exchange failed: {str(e)}"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.user_info_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.error("Failed to fetch Azure user info", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user information"
                )
    
    def extract_user_data(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized user data from Azure response"""
        return {
            "provider_user_id": user_info.get("id"),
            "email": user_info.get("mail") or user_info.get("userPrincipalName"),
            "email_verified": True,  # Azure emails are generally verified
            "first_name": user_info.get("givenName"),
            "last_name": user_info.get("surname"),
            "full_name": user_info.get("displayName"),
            "username": user_info.get("userPrincipalName", "").split("@")[0],
            "provider_data": user_info
        }

class OAuthService:
    """OAuth service for managing OAuth authentication"""
    
    def __init__(self):
        self.providers = {
            "google": GoogleOAuthProvider(),
            "azure": AzureOAuthProvider()
        }
    
    def get_provider(self, provider_name: str) -> OAuthProvider:
        """Get OAuth provider by name"""
        provider = self.providers.get(provider_name)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider_name}"
            )
        return provider
    
    async def get_authorization_url(self, provider_name: str, state: str = None) -> str:
        """Get OAuth authorization URL"""
        provider = self.get_provider(provider_name)
        if not state:
            state = str(uuid.uuid4())
        return await provider.get_authorization_url(state)
    
    async def handle_callback(
        self, 
        db: AsyncSession,
        provider_name: str, 
        code: str, 
        state: str = None
    ) -> Dict[str, Any]:
        """Handle OAuth callback and return user data"""
        provider = self.get_provider(provider_name)
        
        # Exchange code for access token
        token_data = await provider.get_access_token(code, state)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token"
            )
        
        # Get user information
        user_info = await provider.get_user_info(access_token)
        user_data = provider.extract_user_data(user_info)
        
        # Find or create OAuth account
        oauth_account = await self.find_or_create_oauth_account(
            db, provider_name, user_data, token_data
        )
        
        # Find or create user
        user = await self.find_or_create_user(db, oauth_account, user_data)
        
        return {
            "user": user,
            "oauth_account": oauth_account,
            "token_data": token_data
        }
    
    async def find_or_create_oauth_account(
        self, 
        db: AsyncSession,
        provider_name: str,
        user_data: Dict[str, Any],
        token_data: Dict[str, Any]
    ) -> OAuthAccount:
        """Find existing or create new OAuth account"""
        provider_user_id = user_data["provider_user_id"]
        
        # Look for existing OAuth account
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider_name,
            OAuthAccount.provider_user_id == provider_user_id
        )
        result = await db.execute(stmt)
        oauth_account = result.scalar_one_or_none()
        
        if oauth_account:
            # Update existing account
            oauth_account.access_token = token_data.get("access_token")
            oauth_account.refresh_token = token_data.get("refresh_token")
            oauth_account.provider_email = user_data.get("email")
            oauth_account.provider_username = user_data.get("username")
            oauth_account.provider_data = user_data.get("provider_data", {})
            oauth_account.updated_at = datetime.utcnow()
            
            # Set token expiration if provided
            expires_in = token_data.get("expires_in")
            if expires_in:
                oauth_account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        else:
            # Create new OAuth account (without user_id for now)
            oauth_account = OAuthAccount(
                provider=provider_name,
                provider_user_id=provider_user_id,
                provider_email=user_data.get("email"),
                provider_username=user_data.get("username"),
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                provider_data=user_data.get("provider_data", {})
            )
            
            # Set token expiration if provided
            expires_in = token_data.get("expires_in")
            if expires_in:
                oauth_account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            db.add(oauth_account)
        
        await db.commit()
        return oauth_account
    
    async def find_or_create_user(
        self, 
        db: AsyncSession,
        oauth_account: OAuthAccount,
        user_data: Dict[str, Any]
    ) -> User:
        """Find existing or create new user from OAuth data"""
        email = user_data.get("email")
        
        # First, try to find user by email
        user = None
        if email:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
        
        if user:
            # Link existing user to OAuth account if not already linked
            if not oauth_account.user_id:
                oauth_account.user_id = user.id
                await db.commit()
            
            # Update user info from OAuth provider if newer
            if user_data.get("avatar_url") and not user.avatar_url:
                user.avatar_url = user_data["avatar_url"]
            
            if user_data.get("email_verified") and not user.email_verified:
                user.email_verified = True
                user.is_verified = True
            
            await db.commit()
        else:
            # Create new user
            unique_id = f"USER-{str(uuid.uuid4())[:8].upper()}"
            username = user_data.get("username", "")
            
            # Ensure username is unique
            username = await self.generate_unique_username(db, username)
            
            user = User(
                unique_id=unique_id,
                username=username,
                email=email,
                email_verified=user_data.get("email_verified", False),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                avatar_url=user_data.get("avatar_url"),
                is_active=True,
                is_verified=user_data.get("email_verified", False),
                role="customer",
                # No password_hash for OAuth-only users
                password_hash=None
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Link OAuth account to user
            oauth_account.user_id = user.id
            await db.commit()
        
        return user
    
    async def generate_unique_username(self, db: AsyncSession, base_username: str) -> str:
        """Generate a unique username"""
        if not base_username:
            base_username = "user"
        
        # Clean username
        base_username = "".join(c for c in base_username if c.isalnum() or c in "_-")
        if not base_username:
            base_username = "user"
        
        username = base_username
        counter = 1
        
        while True:
            # Check if username exists
            stmt = select(User).where(User.username == username)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                return username
            
            # Try with counter
            username = f"{base_username}{counter}"
            counter += 1
            
            # Prevent infinite loop
            if counter > 1000:
                username = f"{base_username}_{str(uuid.uuid4())[:8]}"
                break
        
        return username
    
    async def unlink_oauth_account(self, db: AsyncSession, user_id: int, provider: str):
        """Unlink OAuth account from user"""
        stmt = select(OAuthAccount).where(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == provider
        )
        result = await db.execute(stmt)
        oauth_account = result.scalar_one_or_none()
        
        if oauth_account:
            await db.delete(oauth_account)
            await db.commit()
            logger.info("OAuth account unlinked", user_id=user_id, provider=provider)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth account not found for provider: {provider}"
            )
    
    async def refresh_oauth_token(
        self, 
        db: AsyncSession,
        oauth_account: OAuthAccount
    ) -> Optional[Dict[str, Any]]:
        """Refresh OAuth access token if refresh token is available"""
        if not oauth_account.refresh_token:
            return None
        
        provider = self.get_provider(oauth_account.provider)
        
        # This would need to be implemented per provider
        # For now, return None to indicate refresh is not available
        logger.warning(
            "OAuth token refresh not implemented", 
            provider=oauth_account.provider
        )
        return None

# Global OAuth service instance
oauth_service = OAuthService()