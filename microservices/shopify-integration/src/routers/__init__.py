"""
Shopify Integration Routers
"""
from .auth import router as auth_router
from .products import router as products_router
from .orders import router as orders_router
from .customers import router as customers_router
from .inventory import router as inventory_router
from .webhooks import router as webhooks_router
from .sync import router as sync_router
from .stores import router as stores_router

__all__ = [
    'auth_router',
    'products_router',
    'orders_router',
    'customers_router',
    'inventory_router',
    'webhooks_router',
    'sync_router',
    'stores_router'
]