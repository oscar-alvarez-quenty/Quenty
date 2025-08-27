"""
Credential management API endpoints
Secure endpoints for managing carrier API credentials
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Optional, List
import os
import structlog

from ..database import get_db
from ..credentials_manager import CredentialManager
from ..models import CarrierType

logger = structlog.get_logger()

router = APIRouter(prefix="/credentials", tags=["Credentials"])
security = HTTPBearer()

# Admin API key for credential management
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "admin-secret-key-change-in-production")


class CredentialRequest(BaseModel):
    """Request model for storing credentials"""
    carrier: str
    credential_type: str
    credential_value: str
    description: Optional[str] = None


class CredentialRotateRequest(BaseModel):
    """Request model for rotating credentials"""
    carrier: str
    credential_type: str
    new_value: str


class CredentialResponse(BaseModel):
    """Response model for credential operations"""
    success: bool
    message: str


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authorization for credential management"""
    if credentials.credentials != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials"
        )
    return credentials.credentials


@router.post("/store", response_model=CredentialResponse)
async def store_credential(
    request: CredentialRequest,
    db=Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """
    Store a new credential or update existing one
    
    Requires admin authentication
    """
    try:
        # Validate carrier
        if request.carrier not in [c.value for c in CarrierType]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid carrier: {request.carrier}"
            )
        
        manager = CredentialManager(db)
        success = manager.store_credential(
            carrier=request.carrier,
            credential_type=request.credential_type,
            credential_value=request.credential_value,
            description=request.description
        )
        
        if success:
            logger.info(f"Credential stored for {request.carrier}")
            return CredentialResponse(
                success=True,
                message=f"Credential stored successfully for {request.carrier}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store credential"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/rotate", response_model=CredentialResponse)
async def rotate_credential(
    request: CredentialRotateRequest,
    db=Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """
    Rotate an existing credential
    
    Marks the old credential as inactive and stores the new one
    """
    try:
        manager = CredentialManager(db)
        success = manager.rotate_credential(
            carrier=request.carrier,
            credential_type=request.credential_type,
            new_value=request.new_value
        )
        
        if success:
            logger.info(f"Credential rotated for {request.carrier}")
            return CredentialResponse(
                success=True,
                message=f"Credential rotated successfully for {request.carrier}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rotate credential"
            )
            
    except Exception as e:
        logger.error(f"Error rotating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{carrier}/{credential_type}", response_model=CredentialResponse)
async def deactivate_credential(
    carrier: str,
    credential_type: str,
    db=Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """
    Deactivate a specific credential
    
    The credential is marked as inactive but not deleted
    """
    try:
        manager = CredentialManager(db)
        success = manager.deactivate_credential(carrier, credential_type)
        
        if success:
            logger.info(f"Credential deactivated for {carrier}")
            return CredentialResponse(
                success=True,
                message=f"Credential deactivated for {carrier}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
            
    except Exception as e:
        logger.error(f"Error deactivating credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/status/{carrier}")
async def get_credential_status(
    carrier: str,
    db=Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """
    Get status of credentials for a specific carrier
    
    Returns credential types configured but not the actual values
    """
    try:
        manager = CredentialManager(db)
        credentials = manager.get_all_credentials(carrier)
        
        # Return only credential types, not values
        credential_status = {
            "carrier": carrier,
            "configured_credentials": list(credentials.keys()),
            "is_configured": len(credentials) > 0
        }
        
        return credential_status
        
    except Exception as e:
        logger.error(f"Error getting credential status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/status")
async def get_all_credential_status(
    db=Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """
    Get status of credentials for all carriers
    
    Returns a summary of configured credentials
    """
    try:
        manager = CredentialManager(db)
        carriers = [c.value for c in CarrierType]
        
        status_list = []
        for carrier in carriers:
            credentials = manager.get_all_credentials(carrier)
            status_list.append({
                "carrier": carrier,
                "configured_credentials": list(credentials.keys()),
                "is_configured": len(credentials) > 0,
                "credential_count": len(credentials)
            })
        
        return {
            "carriers": status_list,
            "total_configured": sum(1 for s in status_list if s["is_configured"])
        }
        
    except Exception as e:
        logger.error(f"Error getting credential status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/initialize")
async def initialize_credentials(
    environment: str = "development",
    db=Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """
    Initialize credentials from environment variables or default test values
    
    Args:
        environment: "development" or "production"
    """
    try:
        manager = CredentialManager(db)
        
        if environment == "production":
            # Load from environment variables
            manager.load_credentials_from_env()
            message = "Credentials loaded from environment variables"
        else:
            # Load test credentials
            test_credentials = {
                "DHL": {
                    "API_KEY": "TEST_DHL_KEY",
                    "API_SECRET": "TEST_DHL_SECRET",
                    "ACCOUNT_NUMBER": "123456789"
                },
                "FEDEX": {
                    "CLIENT_ID": "TEST_FEDEX_ID",
                    "CLIENT_SECRET": "TEST_FEDEX_SECRET",
                    "ACCOUNT_NUMBER": "510087380"
                },
                "UPS": {
                    "CLIENT_ID": "TEST_UPS_ID",
                    "CLIENT_SECRET": "TEST_UPS_SECRET",
                    "ACCOUNT_NUMBER": "A1B2C3"
                },
                "SERVIENTREGA": {
                    "USER": "test_user",
                    "PASSWORD": "test_pass",
                    "BILLING_CODE": "TEST001"
                },
                "INTERRAPIDISIMO": {
                    "API_KEY": "TEST_INTER_KEY",
                    "CLIENT_CODE": "TEST001"
                }
            }
            
            for carrier, creds in test_credentials.items():
                for cred_type, cred_value in creds.items():
                    manager.store_credential(carrier, cred_type, cred_value)
            
            message = "Test credentials initialized"
        
        logger.info(f"Credentials initialized for {environment}")
        return CredentialResponse(
            success=True,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error initializing credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize credentials"
        )