"""
Credential Manager for Carrier Integrations
Manages encrypted storage and retrieval of carrier API credentials
"""

import os
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
import structlog
from datetime import datetime

from .database import SessionLocal
from .models import CarrierCredential, CarrierType
from .utils.encryption import encrypt_data, decrypt_data

logger = structlog.get_logger()


class CredentialManager:
    """Manages carrier API credentials with encryption"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self.encryption_key = os.environ.get('ENCRYPTION_KEY')
        
        if not self.encryption_key:
            # Generate a key if not provided (for development only)
            logger.warning("No encryption key provided, generating one for development")
            self.encryption_key = Fernet.generate_key().decode()
        
        # Ensure key is properly formatted
        if len(self.encryption_key) < 32:
            self.encryption_key = self.encryption_key.ljust(32, '0')
    
    def store_credential(self, carrier: str, credential_type: str, 
                         credential_value: str, description: str = None) -> bool:
        """
        Store an encrypted credential in the database
        
        Args:
            carrier: Carrier name (DHL, FEDEX, UPS, etc.)
            credential_type: Type of credential (API_KEY, CLIENT_ID, etc.)
            credential_value: The actual credential value
            description: Optional description
        
        Returns:
            Boolean indicating success
        """
        try:
            # Check if credential already exists
            existing = self.db.query(CarrierCredential).filter(
                CarrierCredential.carrier == CarrierType[carrier],
                CarrierCredential.credential_type == credential_type
            ).first()
            
            # Encrypt the credential
            encrypted_value = encrypt_data(credential_value, self.encryption_key)
            
            if existing:
                # Update existing credential
                existing.encrypted_value = encrypted_value
                existing.description = description or existing.description
                existing.last_rotated = datetime.now()
                logger.info(f"Updated credential for {carrier} - {credential_type}")
            else:
                # Create new credential
                new_credential = CarrierCredential(
                    carrier=CarrierType[carrier],
                    credential_type=credential_type,
                    encrypted_value=encrypted_value,
                    description=description,
                    is_active=True,
                    last_rotated=datetime.now()
                )
                self.db.add(new_credential)
                logger.info(f"Stored new credential for {carrier} - {credential_type}")
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credential: {str(e)}")
            self.db.rollback()
            return False
    
    def get_credential(self, carrier: str, credential_type: str) -> Optional[str]:
        """
        Retrieve and decrypt a credential from the database
        
        Args:
            carrier: Carrier name
            credential_type: Type of credential
        
        Returns:
            Decrypted credential value or None
        """
        try:
            credential = self.db.query(CarrierCredential).filter(
                CarrierCredential.carrier == CarrierType[carrier],
                CarrierCredential.credential_type == credential_type,
                CarrierCredential.is_active == True
            ).first()
            
            if credential:
                decrypted_value = decrypt_data(
                    credential.encrypted_value, 
                    self.encryption_key
                )
                return decrypted_value
            
            logger.warning(f"No credential found for {carrier} - {credential_type}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential: {str(e)}")
            return None
    
    def get_all_credentials(self, carrier: str) -> Dict[str, str]:
        """
        Get all credentials for a specific carrier
        
        Args:
            carrier: Carrier name
        
        Returns:
            Dictionary of credential_type: value pairs
        """
        try:
            credentials = self.db.query(CarrierCredential).filter(
                CarrierCredential.carrier == CarrierType[carrier],
                CarrierCredential.is_active == True
            ).all()
            
            result = {}
            for cred in credentials:
                decrypted_value = decrypt_data(
                    cred.encrypted_value,
                    self.encryption_key
                )
                result[cred.credential_type] = decrypted_value
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {carrier}: {str(e)}")
            return {}
    
    def rotate_credential(self, carrier: str, credential_type: str, 
                         new_value: str) -> bool:
        """
        Rotate a credential (update with new value and mark old as inactive)
        
        Args:
            carrier: Carrier name
            credential_type: Type of credential
            new_value: New credential value
        
        Returns:
            Boolean indicating success
        """
        try:
            # Mark old credential as inactive
            old_credential = self.db.query(CarrierCredential).filter(
                CarrierCredential.carrier == CarrierType[carrier],
                CarrierCredential.credential_type == credential_type,
                CarrierCredential.is_active == True
            ).first()
            
            if old_credential:
                old_credential.is_active = False
            
            # Store new credential
            return self.store_credential(carrier, credential_type, new_value)
            
        except Exception as e:
            logger.error(f"Failed to rotate credential: {str(e)}")
            return False
    
    def deactivate_credential(self, carrier: str, credential_type: str) -> bool:
        """
        Deactivate a credential
        
        Args:
            carrier: Carrier name
            credential_type: Type of credential
        
        Returns:
            Boolean indicating success
        """
        try:
            credential = self.db.query(CarrierCredential).filter(
                CarrierCredential.carrier == CarrierType[carrier],
                CarrierCredential.credential_type == credential_type,
                CarrierCredential.is_active == True
            ).first()
            
            if credential:
                credential.is_active = False
                self.db.commit()
                logger.info(f"Deactivated credential for {carrier} - {credential_type}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to deactivate credential: {str(e)}")
            self.db.rollback()
            return False
    
    def load_credentials_from_env(self):
        """Load credentials from environment variables"""
        credentials = {
            'DHL': {
                'API_KEY': os.environ.get('DHL_API_KEY'),
                'API_SECRET': os.environ.get('DHL_API_SECRET'),
                'ACCOUNT_NUMBER': os.environ.get('DHL_ACCOUNT_NUMBER')
            },
            'FEDEX': {
                'CLIENT_ID': os.environ.get('FEDEX_CLIENT_ID'),
                'CLIENT_SECRET': os.environ.get('FEDEX_CLIENT_SECRET'),
                'ACCOUNT_NUMBER': os.environ.get('FEDEX_ACCOUNT_NUMBER')
            },
            'UPS': {
                'CLIENT_ID': os.environ.get('UPS_CLIENT_ID'),
                'CLIENT_SECRET': os.environ.get('UPS_CLIENT_SECRET'),
                'ACCOUNT_NUMBER': os.environ.get('UPS_ACCOUNT_NUMBER')
            },
            'SERVIENTREGA': {
                'USER': os.environ.get('SERVIENTREGA_USER'),
                'PASSWORD': os.environ.get('SERVIENTREGA_PASSWORD'),
                'BILLING_CODE': os.environ.get('SERVIENTREGA_BILLING_CODE')
            },
            'INTERRAPIDISIMO': {
                'API_KEY': os.environ.get('INTERRAPIDISIMO_API_KEY'),
                'CLIENT_CODE': os.environ.get('INTERRAPIDISIMO_CLIENT_CODE')
            }
        }
        
        # Store credentials in database
        for carrier, creds in credentials.items():
            for cred_type, cred_value in creds.items():
                if cred_value:
                    self.store_credential(carrier, cred_type, cred_value)
        
        logger.info("Loaded credentials from environment variables")
    
    def load_credentials_from_file(self, filepath: str):
        """
        Load credentials from a JSON file
        
        Args:
            filepath: Path to the JSON file containing credentials
        """
        try:
            with open(filepath, 'r') as f:
                credentials = json.load(f)
            
            for carrier, creds in credentials.items():
                for cred_type, cred_value in creds.items():
                    if cred_value:
                        self.store_credential(carrier.upper(), cred_type, cred_value)
            
            logger.info(f"Loaded credentials from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to load credentials from file: {str(e)}")
    
    def export_credential_template(self, filepath: str):
        """
        Export a template JSON file for credentials
        
        Args:
            filepath: Path where to save the template
        """
        template = {
            "DHL": {
                "API_KEY": "your-dhl-api-key",
                "API_SECRET": "your-dhl-api-secret",
                "ACCOUNT_NUMBER": "your-dhl-account-number"
            },
            "FEDEX": {
                "CLIENT_ID": "your-fedex-client-id",
                "CLIENT_SECRET": "your-fedex-client-secret",
                "ACCOUNT_NUMBER": "your-fedex-account-number"
            },
            "UPS": {
                "CLIENT_ID": "your-ups-client-id",
                "CLIENT_SECRET": "your-ups-client-secret",
                "ACCOUNT_NUMBER": "your-ups-account-number"
            },
            "SERVIENTREGA": {
                "USER": "your-servientrega-user",
                "PASSWORD": "your-servientrega-password",
                "BILLING_CODE": "your-billing-code"
            },
            "INTERRAPIDISIMO": {
                "API_KEY": "your-interrapidisimo-api-key",
                "CLIENT_CODE": "your-client-code"
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"Exported credential template to {filepath}")


# Singleton instance
_credential_manager = None

def get_credential_manager() -> CredentialManager:
    """Get singleton instance of CredentialManager"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager