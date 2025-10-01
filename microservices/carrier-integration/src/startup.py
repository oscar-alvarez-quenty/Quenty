"""
Startup script to initialize all carriers from environment variables
"""

import os
import asyncio
import structlog
from typing import List, Dict, Any
from .services.carrier_service import CarrierService

logger = structlog.get_logger()


class CarrierInitializer:
    """Initializes all carrier integrations on startup"""

    def __init__(self, carrier_service: CarrierService = None):
        self.carrier_service = carrier_service or CarrierService()
        self.enabled_carriers = self._get_enabled_carriers()

    def _get_enabled_carriers(self) -> List[str]:
        """Get list of enabled carriers from environment"""
        # Check which carriers have credentials configured
        carriers = []

        # Check DHL
        if os.getenv('DHL_API_KEY') or os.getenv('DHL_USERNAME'):
            carriers.append('DHL')
            logger.info("DHL integration enabled")

        # Check UPS
        if os.getenv('UPS_CLIENT_ID'):
            carriers.append('UPS')
            logger.info("UPS integration enabled")

        # Check FedEx
        if os.getenv('FEDEX_CLIENT_ID'):
            carriers.append('FedEx')
            logger.info("FedEx integration enabled")

        # Check Servientrega
        if os.getenv('SERVIENTREGA_USER'):
            carriers.append('Servientrega')
            logger.info("Servientrega integration enabled")

        # Check Interrapidisimo
        if os.getenv('INTERRAPIDISIMO_API_KEY'):
            carriers.append('Interrapidisimo')
            logger.info("Interrapidisimo integration enabled")

        # Check Pasarex (optional)
        if os.getenv('PASAREX_API_KEY'):
            carriers.append('Pasarex')
            logger.info("Pasarex integration enabled")

        # Check Aeropost (optional)
        if os.getenv('AEROPOST_API_KEY'):
            carriers.append('Aeropost')
            logger.info("Aeropost integration enabled")

        return carriers

    async def initialize_all_carriers(self) -> Dict[str, bool]:
        """Initialize all enabled carriers"""
        results = {}

        for carrier in self.enabled_carriers:
            try:
                # Initialize carrier without credentials (will load from env)
                await self.carrier_service.initialize_carrier(carrier)
                results[carrier] = True
                logger.info(f"Successfully initialized {carrier}")
            except Exception as e:
                results[carrier] = False
                logger.error(f"Failed to initialize {carrier}: {str(e)}")

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get status of all carriers"""
        return {
            'enabled_carriers': self.enabled_carriers,
            'total_carriers': len(self.enabled_carriers),
            'initialized_carriers': list(self.carrier_service.carriers.keys())
        }


# Global instance
_initializer = None


async def initialize_carriers(carrier_service: CarrierService = None):
    """Initialize all carriers on application startup"""
    global _initializer

    try:
        _initializer = CarrierInitializer(carrier_service)
        results = await _initializer.initialize_all_carriers()

        # Log results
        successful = [c for c, success in results.items() if success]
        failed = [c for c, success in results.items() if not success]

        logger.info(
            "Carrier initialization complete",
            successful=successful,
            failed=failed,
            total=len(results)
        )

        if not successful:
            logger.warning("No carriers successfully initialized. Check your environment variables.")

        return results

    except Exception as e:
        logger.error(f"Failed to initialize carriers: {str(e)}")
        raise


def get_carrier_service() -> CarrierService:
    """Get the initialized carrier service"""
    if _initializer:
        return _initializer.carrier_service
    raise RuntimeError("Carriers not initialized. Call initialize_carriers() first.")


def get_carrier_status() -> Dict[str, Any]:
    """Get current carrier status"""
    if _initializer:
        return _initializer.get_status()
    return {
        'enabled_carriers': [],
        'total_carriers': 0,
        'initialized_carriers': [],
        'error': 'Carriers not initialized'
    }