from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import logging
import uuid
from ..database import get_db
from ..models import MercadoLibreAccount, TokenStatus
from ..services.meli_client import MercadoLibreClient
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/connect")
async def connect_account():
    """Initiate OAuth2 flow to connect MercadoLibre account"""
    try:
        client = MercadoLibreClient()
        state = uuid.uuid4().hex  # Generate random state for security
        auth_url = client.get_auth_url(state)
        
        return {
            "auth_url": auth_url,
            "state": state,
            "message": "Redirect user to auth_url to authorize the application"
        }
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth2 callback from MercadoLibre"""
    try:
        client = MercadoLibreClient()
        
        # Exchange code for access token
        token_data = await client.get_access_token(code)
        
        # Get user information
        client.access_token = token_data["access_token"]
        user_info = await client.get_user_info()
        
        # Check if account already exists
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.user_id == str(user_info["id"])
            )
        )
        account = result.scalar_one_or_none()
        
        if account:
            # Update existing account
            account.access_token = token_data["access_token"]
            account.refresh_token = token_data["refresh_token"]
            account.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_data["expires_in"]
            )
            account.token_status = TokenStatus.ACTIVE
            account.nickname = user_info.get("nickname")
            account.email = user_info.get("email")
        else:
            # Create new account
            account = MercadoLibreAccount(
                user_id=str(user_info["id"]),
                nickname=user_info.get("nickname"),
                email=user_info.get("email"),
                site_id=user_info.get("site_id"),
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expires_at=datetime.utcnow() + timedelta(
                    seconds=token_data["expires_in"]
                ),
                token_status=TokenStatus.ACTIVE,
                reputation=user_info.get("seller_reputation"),
                registration_date=datetime.fromisoformat(
                    user_info.get("registration_date", datetime.utcnow().isoformat())
                )
            )
            db.add(account)
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Account connected successfully",
            "account_id": account.id,
            "user_id": account.user_id,
            "nickname": account.nickname
        }
        
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/{account_id}")
async def refresh_token(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token for an account"""
    try:
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        client = MercadoLibreClient()
        
        # Refresh token
        token_data = await client.refresh_access_token(account.refresh_token)
        
        # Update account
        account.access_token = token_data["access_token"]
        account.refresh_token = token_data["refresh_token"]
        account.token_expires_at = datetime.utcnow() + timedelta(
            seconds=token_data["expires_in"]
        )
        account.token_status = TokenStatus.ACTIVE
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "expires_at": account.token_expires_at
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/disconnect/{account_id}")
async def disconnect_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Disconnect a MercadoLibre account"""
    try:
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(MercadoLibreAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Mark as inactive
        account.is_active = False
        account.token_status = TokenStatus.REVOKED
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Account disconnected successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to disconnect account: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))