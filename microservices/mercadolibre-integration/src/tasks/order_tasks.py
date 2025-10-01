"""
Order-related tasks for MercadoLibre
"""
from .celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def sync_recent_orders():
    logger.info("Syncing recent MercadoLibre orders")
    return {"status": "completed", "orders_synced": 0}

@celery_app.task
def sync_order(order_id: str):
    logger.info(f"Syncing order {order_id}")
    return {"status": "completed", "order_id": order_id}

@celery_app.task
def process_new_order(order_data: dict):
    logger.info(f"Processing new order")
    return {"status": "processed"}