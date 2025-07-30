"""
Carrier Integration Factory
Factory class to create and manage different carrier integrations
"""

from typing import Dict, Optional, Type
from .base import CarrierIntegrationBase
from .dhl import DHLIntegration
from .fedex import FedExIntegration  
from .ups import UPSIntegration


class CarrierFactory:
    """Factory to create carrier integration instances"""
    
    _integrations: Dict[str, Type[CarrierIntegrationBase]] = {
        "DHL": DHLIntegration,
        "FEDEX": FedExIntegration,
        "UPS": UPSIntegration
    }
    
    @classmethod
    def create_integration(
        self, 
        carrier_code: str, 
        config: Dict[str, str], 
        sandbox: bool = True
    ) -> Optional[CarrierIntegrationBase]:
        """
        Create a carrier integration instance
        
        Args:
            carrier_code: The carrier code (DHL, FEDEX, UPS)
            config: Configuration dictionary with API credentials
            sandbox: Whether to use sandbox/test environment
            
        Returns:
            CarrierIntegrationBase instance or None if carrier not supported
        """
        
        integration_class = self._integrations.get(carrier_code.upper())
        if not integration_class:
            return None
        
        try:
            if carrier_code.upper() == "DHL":
                return integration_class(
                    api_key=config.get("api_key", ""),
                    api_secret=config.get("api_secret", ""),
                    sandbox=sandbox
                )
            
            elif carrier_code.upper() == "FEDEX":
                return integration_class(
                    api_key=config.get("api_key", ""),
                    api_secret=config.get("api_secret", ""),
                    account_number=config.get("account_number", ""),
                    sandbox=sandbox
                )
            
            elif carrier_code.upper() == "UPS":
                return integration_class(
                    api_key=config.get("api_key", ""),
                    user_id=config.get("user_id", ""),
                    password=config.get("password", ""),
                    account_number=config.get("account_number", ""),
                    sandbox=sandbox
                )
            
        except Exception as e:
            print(f"Error creating {carrier_code} integration: {e}")
            return None
    
    @classmethod
    def get_supported_carriers(cls) -> list[str]:
        """Get list of supported carrier codes"""
        return list(cls._integrations.keys())
    
    @classmethod
    def is_supported(cls, carrier_code: str) -> bool:
        """Check if carrier is supported"""
        return carrier_code.upper() in cls._integrations


# Configuration templates for each carrier
CARRIER_CONFIG_TEMPLATES = {
    "DHL": {
        "required_fields": ["api_key", "api_secret"],
        "optional_fields": [],
        "description": "DHL Express API integration requires API key and secret"
    },
    "FEDEX": {
        "required_fields": ["api_key", "api_secret", "account_number"],
        "optional_fields": [],
        "description": "FedEx API integration requires API key, secret, and account number"
    },
    "UPS": {
        "required_fields": ["api_key", "user_id", "password", "account_number"],
        "optional_fields": [],
        "description": "UPS API integration requires API key, user ID, password, and account number"
    }
}