"""
Product-related tasks for MercadoLibre
"""
from .celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def sync_all_products():
    logger.info("Syncing all MercadoLibre products")
    return {"status": "completed", "products_synced": 0}

@celery_app.task
def sync_product(product_id: str):
    logger.info(f"Syncing product {product_id}")
    return {"status": "completed", "product_id": product_id}

@celery_app.task
def update_inventory(product_id: str, quantity: int):
    logger.info(f"Updating inventory for product {product_id}: {quantity}")
    return {"status": "completed", "product_id": product_id, "quantity": quantity}