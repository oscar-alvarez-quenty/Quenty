import os
import json
from cryptography.fernet import Fernet
from typing import Dict, Any

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"Warning: Using generated encryption key. Set ENCRYPTION_KEY environment variable in production.")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Encrypt credentials dictionary to string"""
    try:
        # Convert to JSON
        json_str = json.dumps(credentials)
        
        # Encrypt
        encrypted = cipher_suite.encrypt(json_str.encode())
        
        return encrypted.decode()
        
    except Exception as e:
        raise Exception(f"Failed to encrypt credentials: {str(e)}")

def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
    """Decrypt credentials string to dictionary"""
    try:
        # Decrypt
        decrypted = cipher_suite.decrypt(encrypted.encode())
        
        # Parse JSON
        credentials = json.loads(decrypted.decode())
        
        return credentials
        
    except Exception as e:
        raise Exception(f"Failed to decrypt credentials: {str(e)}")