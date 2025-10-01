"""
Shopify Webhooks Module
Handles webhook management, subscriptions, and event processing
"""
from typing import List, Dict, Any, Optional, Callable
import logging
import json
import hashlib
import hmac
import base64
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WebhookTopic(Enum):
    """Shopify webhook topics"""
    # App
    APP_UNINSTALLED = "app/uninstalled"
    
    # Cart
    CARTS_CREATE = "carts/create"
    CARTS_UPDATE = "carts/update"
    
    # Checkout
    CHECKOUTS_CREATE = "checkouts/create"
    CHECKOUTS_UPDATE = "checkouts/update"
    CHECKOUTS_DELETE = "checkouts/delete"
    
    # Collection
    COLLECTION_LISTINGS_ADD = "collection_listings/add"
    COLLECTION_LISTINGS_REMOVE = "collection_listings/remove"
    COLLECTION_LISTINGS_UPDATE = "collection_listings/update"
    COLLECTIONS_CREATE = "collections/create"
    COLLECTIONS_UPDATE = "collections/update"
    COLLECTIONS_DELETE = "collections/delete"
    
    # Customer
    CUSTOMERS_CREATE = "customers/create"
    CUSTOMERS_UPDATE = "customers/update"
    CUSTOMERS_DELETE = "customers/delete"
    CUSTOMERS_DISABLE = "customers/disable"
    CUSTOMERS_ENABLE = "customers/enable"
    CUSTOMER_GROUPS_CREATE = "customer_groups/create"
    CUSTOMER_GROUPS_UPDATE = "customer_groups/update"
    CUSTOMER_GROUPS_DELETE = "customer_groups/delete"
    
    # Draft Order
    DRAFT_ORDERS_CREATE = "draft_orders/create"
    DRAFT_ORDERS_UPDATE = "draft_orders/update"
    DRAFT_ORDERS_DELETE = "draft_orders/delete"
    
    # Fulfillment
    FULFILLMENTS_CREATE = "fulfillments/create"
    FULFILLMENTS_UPDATE = "fulfillments/update"
    FULFILLMENT_EVENTS_CREATE = "fulfillment_events/create"
    FULFILLMENT_EVENTS_DELETE = "fulfillment_events/delete"
    
    # Inventory
    INVENTORY_ITEMS_CREATE = "inventory_items/create"
    INVENTORY_ITEMS_UPDATE = "inventory_items/update"
    INVENTORY_ITEMS_DELETE = "inventory_items/delete"
    INVENTORY_LEVELS_CONNECT = "inventory_levels/connect"
    INVENTORY_LEVELS_UPDATE = "inventory_levels/update"
    INVENTORY_LEVELS_DISCONNECT = "inventory_levels/disconnect"
    
    # Location
    LOCATIONS_CREATE = "locations/create"
    LOCATIONS_UPDATE = "locations/update"
    LOCATIONS_DELETE = "locations/delete"
    
    # Order
    ORDERS_CREATE = "orders/create"
    ORDERS_UPDATE = "orders/updated"
    ORDERS_DELETE = "orders/delete"
    ORDERS_CANCELLED = "orders/cancelled"
    ORDERS_FULFILLED = "orders/fulfilled"
    ORDERS_PAID = "orders/paid"
    ORDERS_PARTIALLY_FULFILLED = "orders/partially_fulfilled"
    ORDER_TRANSACTIONS_CREATE = "order_transactions/create"
    
    # Product
    PRODUCTS_CREATE = "products/create"
    PRODUCTS_UPDATE = "products/update"
    PRODUCTS_DELETE = "products/delete"
    PRODUCT_LISTINGS_ADD = "product_listings/add"
    PRODUCT_LISTINGS_REMOVE = "product_listings/remove"
    PRODUCT_LISTINGS_UPDATE = "product_listings/update"
    
    # Refund
    REFUNDS_CREATE = "refunds/create"
    
    # Shop
    SHOP_UPDATE = "shop/update"
    
    # Theme
    THEMES_CREATE = "themes/create"
    THEMES_UPDATE = "themes/update"
    THEMES_DELETE = "themes/delete"
    THEMES_PUBLISH = "themes/publish"


class WebhooksModule:
    """
    Manage Shopify webhooks and event handling
    """
    
    def __init__(self, client):
        """
        Initialize Webhooks module
        
        Args:
            client: ShopifyAPIClient instance
        """
        self.client = client
        self.handlers = {}
    
    # Webhook CRUD Operations
    
    def create_webhook(self, topic: str, address: str, 
                       format: str = "json", **kwargs) -> Dict[str, Any]:
        """
        Create a webhook subscription
        
        Args:
            topic: Webhook topic (e.g., 'orders/create')
            address: URL to receive webhook
            format: Format of webhook (json or xml)
            api_version: API version for webhook
            
        Returns:
            Created webhook data
        """
        logger.info(f"Creating webhook for topic: {topic}")
        
        webhook_data = {
            'topic': topic,
            'address': address,
            'format': format
        }
        
        if kwargs.get('api_version'):
            webhook_data['api_version'] = kwargs['api_version']
        
        if kwargs.get('fields'):
            webhook_data['fields'] = kwargs['fields']
        
        response = self.client.post('webhooks', {'webhook': webhook_data})
        return response.get('webhook', {})
    
    def get_webhook(self, webhook_id: int, fields: List[str] = None) -> Dict[str, Any]:
        """
        Get a single webhook
        
        Args:
            webhook_id: Webhook ID
            fields: List of fields to include
        
        Returns:
            Webhook data
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        
        response = self.client.get(f'webhooks/{webhook_id}', params)
        return response.get('webhook', {})
    
    def update_webhook(self, webhook_id: int, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a webhook
        
        Args:
            webhook_id: Webhook ID
            webhook_data: Updated webhook information
        
        Returns:
            Updated webhook data
        """
        logger.info(f"Updating webhook {webhook_id}")
        response = self.client.put(f'webhooks/{webhook_id}', {'webhook': webhook_data})
        return response.get('webhook', {})
    
    def delete_webhook(self, webhook_id: int) -> bool:
        """
        Delete a webhook
        
        Args:
            webhook_id: Webhook ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting webhook {webhook_id}")
        self.client.delete(f'webhooks/{webhook_id}')
        return True
    
    def list_webhooks(self, **kwargs) -> List[Dict[str, Any]]:
        """
        List all webhooks
        
        Args:
            address: Filter by address
            topic: Filter by topic
            created_at_min: Show webhooks created after date
            created_at_max: Show webhooks created before date
            updated_at_min: Show webhooks updated after date
            updated_at_max: Show webhooks updated before date
            fields: Comma-separated list of fields to include
            limit: Number of results
            since_id: Restrict results after specified ID
            
        Returns:
            List of webhooks
        """
        return self.client.paginate('webhooks', kwargs)
    
    def count_webhooks(self, **kwargs) -> int:
        """
        Count webhooks
        
        Args:
            address: Filter by address
            topic: Filter by topic
        
        Returns:
            Webhook count
        """
        response = self.client.get('webhooks/count', kwargs)
        return response.get('count', 0)
    
    # Webhook Verification
    
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """
        Verify webhook authenticity
        
        Args:
            data: Raw request body
            hmac_header: X-Shopify-Hmac-Sha256 header value
        
        Returns:
            True if webhook is authentic
        """
        return self.client.verify_webhook(data, hmac_header)
    
    # Webhook Registration
    
    def register_all_webhooks(self, base_url: str, topics: List[str] = None) -> Dict[str, Any]:
        """
        Register multiple webhooks at once
        
        Args:
            base_url: Base URL for webhook endpoints
            topics: List of topics to register (or all if None)
        
        Returns:
            Registration results
        """
        if not topics:
            # Register common webhooks
            topics = [
                WebhookTopic.ORDERS_CREATE.value,
                WebhookTopic.ORDERS_UPDATE.value,
                WebhookTopic.ORDERS_CANCELLED.value,
                WebhookTopic.ORDERS_FULFILLED.value,
                WebhookTopic.ORDERS_PAID.value,
                WebhookTopic.CUSTOMERS_CREATE.value,
                WebhookTopic.CUSTOMERS_UPDATE.value,
                WebhookTopic.PRODUCTS_CREATE.value,
                WebhookTopic.PRODUCTS_UPDATE.value,
                WebhookTopic.PRODUCTS_DELETE.value,
                WebhookTopic.INVENTORY_LEVELS_UPDATE.value,
                WebhookTopic.APP_UNINSTALLED.value
            ]
        
        registered = []
        failed = []
        
        for topic in topics:
            try:
                # Create endpoint URL for each topic
                endpoint = f"{base_url}/webhooks/{topic.replace('/', '-')}"
                
                webhook = self.create_webhook(
                    topic=topic,
                    address=endpoint
                )
                registered.append(webhook)
                logger.info(f"Registered webhook for {topic}")
                
            except Exception as e:
                logger.error(f"Failed to register webhook for {topic}: {e}")
                failed.append({'topic': topic, 'error': str(e)})
        
        return {
            'registered': registered,
            'failed': failed,
            'total_registered': len(registered),
            'total_failed': len(failed)
        }
    
    def unregister_all_webhooks(self) -> Dict[str, Any]:
        """
        Unregister all webhooks
        
        Returns:
            Unregistration results
        """
        webhooks = self.list_webhooks()
        deleted = 0
        failed = 0
        
        for webhook in webhooks:
            try:
                self.delete_webhook(webhook['id'])
                deleted += 1
                logger.info(f"Deleted webhook {webhook['id']} for topic {webhook['topic']}")
            except Exception as e:
                logger.error(f"Failed to delete webhook {webhook['id']}: {e}")
                failed += 1
        
        return {
            'deleted': deleted,
            'failed': failed,
            'total': len(webhooks)
        }
    
    def update_webhook_endpoints(self, old_base_url: str, new_base_url: str) -> Dict[str, Any]:
        """
        Update all webhook endpoints to new URL
        
        Args:
            old_base_url: Old base URL
            new_base_url: New base URL
        
        Returns:
            Update results
        """
        webhooks = self.list_webhooks()
        updated = []
        failed = []
        
        for webhook in webhooks:
            if webhook['address'].startswith(old_base_url):
                try:
                    new_address = webhook['address'].replace(old_base_url, new_base_url)
                    updated_webhook = self.update_webhook(
                        webhook['id'],
                        {'address': new_address}
                    )
                    updated.append(updated_webhook)
                    logger.info(f"Updated webhook {webhook['id']} endpoint")
                    
                except Exception as e:
                    logger.error(f"Failed to update webhook {webhook['id']}: {e}")
                    failed.append({'webhook': webhook, 'error': str(e)})
        
        return {
            'updated': updated,
            'failed': failed,
            'total_updated': len(updated),
            'total_failed': len(failed)
        }
    
    # Webhook Event Handling
    
    def register_handler(self, topic: str, handler: Callable):
        """
        Register a handler for webhook topic
        
        Args:
            topic: Webhook topic
            handler: Handler function
        """
        if topic not in self.handlers:
            self.handlers[topic] = []
        
        self.handlers[topic].append(handler)
        logger.info(f"Registered handler for topic: {topic}")
    
    def process_webhook(self, topic: str, data: Dict[str, Any], 
                       headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Process incoming webhook
        
        Args:
            topic: Webhook topic
            data: Webhook payload
            headers: Webhook headers
        
        Returns:
            Processing results
        """
        logger.info(f"Processing webhook for topic: {topic}")
        
        # Verify webhook if possible
        if headers.get('X-Shopify-Hmac-Sha256'):
            raw_body = json.dumps(data).encode('utf-8')
            if not self.verify_webhook(raw_body, headers['X-Shopify-Hmac-Sha256']):
                logger.error("Webhook verification failed")
                return {'status': 'failed', 'error': 'Verification failed'}
        
        # Get handlers for topic
        handlers = self.handlers.get(topic, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for topic: {topic}")
            return {'status': 'no_handler', 'topic': topic}
        
        results = []
        for handler in handlers:
            try:
                result = handler(data, headers)
                results.append({
                    'handler': handler.__name__,
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed: {e}")
                results.append({
                    'handler': handler.__name__,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'status': 'processed',
            'topic': topic,
            'handlers_called': len(handlers),
            'results': results
        }
    
    # Webhook Notifications
    
    def create_notification(self, topic: str, message: str = None) -> Dict[str, Any]:
        """
        Create a webhook notification
        
        Args:
            topic: Notification topic
            message: Optional message
        
        Returns:
            Notification details
        """
        # This would integrate with your notification system
        notification = {
            'id': f"notif_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'topic': topic,
            'message': message or f"Webhook event: {topic}",
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        logger.info(f"Created notification for topic: {topic}")
        return notification
    
    # Webhook Testing
    
    def test_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """
        Send a test notification for a webhook
        
        Args:
            webhook_id: Webhook ID
        
        Returns:
            Test results
        """
        # Shopify doesn't have a built-in test endpoint, 
        # so we'll simulate it
        webhook = self.get_webhook(webhook_id)
        
        test_payload = {
            'test': True,
            'webhook_id': webhook_id,
            'topic': webhook['topic'],
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Testing webhook {webhook_id}")
        
        return {
            'webhook_id': webhook_id,
            'topic': webhook['topic'],
            'address': webhook['address'],
            'test_payload': test_payload,
            'status': 'test_sent'
        }
    
    def validate_webhook_endpoint(self, url: str) -> Dict[str, Any]:
        """
        Validate webhook endpoint is accessible
        
        Args:
            url: Webhook endpoint URL
        
        Returns:
            Validation results
        """
        import requests
        
        try:
            # Send a test request to the endpoint
            response = requests.post(
                url,
                json={'test': True},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return {
                'url': url,
                'status_code': response.status_code,
                'valid': response.status_code < 400,
                'response_time': response.elapsed.total_seconds()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'url': url,
                'valid': False,
                'error': str(e)
            }
    
    # Webhook Monitoring
    
    def get_webhook_metrics(self) -> Dict[str, Any]:
        """
        Get webhook metrics and statistics
        
        Returns:
            Webhook metrics
        """
        webhooks = self.list_webhooks()
        
        # Group by topic
        topics = {}
        for webhook in webhooks:
            topic = webhook['topic']
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(webhook)
        
        # Calculate metrics
        metrics = {
            'total_webhooks': len(webhooks),
            'topics': list(topics.keys()),
            'topic_count': len(topics),
            'webhooks_by_topic': {
                topic: len(webhooks) 
                for topic, webhooks in topics.items()
            },
            'api_versions': list(set(
                w.get('api_version', 'unknown') 
                for w in webhooks
            ))
        }
        
        return metrics
    
    def get_failed_notifications(self, since: datetime = None) -> List[Dict[str, Any]]:
        """
        Get failed webhook notifications
        
        Args:
            since: Get failures since this date
        
        Returns:
            List of failed notifications
        """
        # This would integrate with your notification/logging system
        # For now, return a placeholder
        return []
    
    # Bulk Operations
    
    def bulk_create_webhooks(self, webhooks_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple webhooks
        
        Args:
            webhooks_data: List of webhook configurations
        
        Returns:
            Creation results
        """
        created = []
        failed = []
        
        for webhook_data in webhooks_data:
            try:
                webhook = self.create_webhook(**webhook_data)
                created.append(webhook)
            except Exception as e:
                logger.error(f"Failed to create webhook: {e}")
                failed.append({'data': webhook_data, 'error': str(e)})
        
        return {
            'created': created,
            'failed': failed,
            'total_created': len(created),
            'total_failed': len(failed)
        }