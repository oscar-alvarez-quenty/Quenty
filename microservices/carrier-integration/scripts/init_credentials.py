#!/usr/bin/env python3
"""
Initialize carrier credentials for development/testing
This script creates test credentials for all carriers
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.credentials_manager import CredentialManager
from src.database import SessionLocal, engine
from src.models import Base

def init_test_credentials():
    """Initialize test credentials for all carriers"""
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Initialize credential manager
    db = SessionLocal()
    manager = CredentialManager(db)
    
    # Test credentials (these are dummy values for development)
    test_credentials = {
        "DHL": {
            "API_KEY": "TEST_DHL_API_KEY_123456789",
            "API_SECRET": "TEST_DHL_SECRET_ABCDEFGHIJ",
            "ACCOUNT_NUMBER": "123456789"
        },
        "FEDEX": {
            "CLIENT_ID": "TEST_FEDEX_CLIENT_ID_XYZ",
            "CLIENT_SECRET": "TEST_FEDEX_SECRET_123ABC",
            "ACCOUNT_NUMBER": "510087380"
        },
        "UPS": {
            "CLIENT_ID": "TEST_UPS_CLIENT_ID_ABC123",
            "CLIENT_SECRET": "TEST_UPS_SECRET_XYZ789",
            "ACCOUNT_NUMBER": "A1B2C3"
        },
        "SERVIENTREGA": {
            "USER": "test_servientrega_user",
            "PASSWORD": "test_password_123",
            "BILLING_CODE": "TEST_BILLING_001"
        },
        "INTERRAPIDISIMO": {
            "API_KEY": "TEST_INTER_API_KEY_999",
            "CLIENT_CODE": "CLIENT_TEST_001"
        }
    }
    
    print("Initializing test credentials...")
    
    for carrier, creds in test_credentials.items():
        print(f"\nSetting up {carrier} credentials:")
        for cred_type, cred_value in creds.items():
            success = manager.store_credential(
                carrier=carrier,
                credential_type=cred_type,
                credential_value=cred_value,
                description=f"Test credential for {carrier} - {cred_type}"
            )
            if success:
                print(f"  ✓ {cred_type} stored successfully")
            else:
                print(f"  ✗ Failed to store {cred_type}")
    
    # Export template for production use
    template_path = Path(__file__).parent.parent / "credentials_template.json"
    manager.export_credential_template(str(template_path))
    print(f"\nCredential template exported to: {template_path}")
    
    # Verify credentials
    print("\nVerifying stored credentials:")
    for carrier in test_credentials.keys():
        stored_creds = manager.get_all_credentials(carrier)
        if stored_creds:
            print(f"  ✓ {carrier}: {len(stored_creds)} credentials found")
        else:
            print(f"  ✗ {carrier}: No credentials found")
    
    db.close()
    print("\nCredential initialization complete!")

def init_production_credentials():
    """Initialize production credentials from environment or file"""
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Initialize credential manager
    db = SessionLocal()
    manager = CredentialManager(db)
    
    # Check if credentials file exists
    creds_file = Path("/app/credentials/production_credentials.json")
    
    if creds_file.exists():
        print(f"Loading credentials from {creds_file}")
        manager.load_credentials_from_file(str(creds_file))
    else:
        print("Loading credentials from environment variables")
        manager.load_credentials_from_env()
    
    # Verify credentials
    carriers = ['DHL', 'FEDEX', 'UPS', 'SERVIENTREGA', 'INTERRAPIDISIMO']
    print("\nVerifying credentials:")
    
    for carrier in carriers:
        stored_creds = manager.get_all_credentials(carrier)
        if stored_creds:
            print(f"  ✓ {carrier}: {len(stored_creds)} credentials configured")
        else:
            print(f"  ⚠ {carrier}: No credentials configured")
    
    db.close()
    print("\nCredential initialization complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize carrier credentials")
    parser.add_argument(
        "--production", 
        action="store_true",
        help="Initialize production credentials from environment/file"
    )
    
    args = parser.parse_args()
    
    if args.production:
        init_production_credentials()
    else:
        init_test_credentials()