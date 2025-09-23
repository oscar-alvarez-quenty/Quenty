"""
WooCommerce Webhook Handler
Processes incoming webhooks from WooCommerce stores
"""

import json
import hmac
import hashlib
import base64
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import get_db
from ..models.entities import WebhookEvent, Order, Product, Customer
from ..services.order_service import OrderService
from ..services.product_service import ProductService
from ..services.notification_service import NotificationService
from ..utils.exceptions import WebhookValidationError

logger = structlog.get_logger()


class WebhookTopic(Enum):
    """WooCommerce webhook topics"""
    # Order events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_DELETED = "order.deleted"
    ORDER_RESTORED = "order.restored"
    
    # Product events
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_RESTORED = "product.restored"
    
    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    
    # Coupon events
    COUPON_CREATED = "coupon.created"
    COUPON_UPDATED = "coupon.updated"
    COUPON_DELETED = "coupon.deleted"


class WooCommerceWebhookHandler:
    """
    Handles incoming webhooks from WooCommerce stores
    Validates signatures and processes events
    """
    
    def __init__(
        self,
        order_service: OrderService,
        product_service: ProductService,
        notification_service: NotificationService
    ):
        """
        Initialize webhook handler
        
        Args:
            order_service: Service for order management
            product_service: Service for product management
            notification_service: Service for notifications
        """
        self.order_service = order_service
        self.product_service = product_service
        self.notification_service = notification_service
        
        # Map topics to handler methods
        self.topic_handlers = {
            WebhookTopic.ORDER_CREATED: self._handle_order_created,
            WebhookTopic.ORDER_UPDATED: self._handle_order_updated,
            WebhookTopic.ORDER_DELETED: self._handle_order_deleted,
            WebhookTopic.PRODUCT_CREATED: self._handle_product_created,
            WebhookTopic.PRODUCT_UPDATED: self._handle_product_updated,
            WebhookTopic.PRODUCT_DELETED: self._handle_product_deleted,
            WebhookTopic.CUSTOMER_CREATED: self._handle_customer_created,
            WebhookTopic.CUSTOMER_UPDATED: self._handle_customer_updated,
            WebhookTopic.CUSTOMER_DELETED: self._handle_customer_deleted,
        }
    
    def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate WooCommerce webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Signature from X-WC-Webhook-Signature header
            secret: Webhook secret key
            
        Returns:
            True if signature is valid
            
        Raises:
            WebhookValidationError: If signature is invalid
        """
        # Calculate expected signature
        expected_signature = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(
                "webhook_signature_validation_failed",
                provided_signature=signature[:20] + "...",
                expected_signature=expected_signature[:20] + "..."
            )
            raise WebhookValidationError("Invalid webhook signature")
        
        return True
    
    async def process_webhook(
        self,
        store_id: str,
        topic: str,
        webhook_id: str,
        payload: Dict[str, Any],
        signature: str,
        secret: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process incoming webhook from WooCommerce
        
        Args:
            store_id: Store identifier
            topic: Webhook topic (e.g., 'order.created')
            webhook_id: WooCommerce webhook ID
            payload: Webhook payload data
            signature: Webhook signature for validation
            secret: Webhook secret for validation
            db: Database session
            
        Returns:
            Processing result
        """
        # Log webhook receipt
        logger.info(
            "webhook_received",
            store_id=store_id,
            topic=topic,
            webhook_id=webhook_id
        )
        
        # Validate signature
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        self.validate_signature(payload_bytes, signature, secret)
        
        # Store webhook event
        webhook_event = WebhookEvent(
            store_id=store_id,
            webhook_id=webhook_id,
            topic=topic,
            payload=payload,
            signature=signature,
            received_at=datetime.utcnow(),
            status="processing"
        )
        db.add(webhook_event)
        await db.commit()
        
        try:
            # Parse topic
            topic_enum = WebhookTopic(topic)
            
            # Get handler for topic
            handler = self.topic_handlers.get(topic_enum)
            if not handler:
                logger.warning(
                    "no_handler_for_webhook_topic",
                    topic=topic
                )
                webhook_event.status = "skipped"
                webhook_event.processed_at = datetime.utcnow()
                await db.commit()
                return {"status": "skipped", "reason": "No handler for topic"}
            
            # Process webhook with appropriate handler
            result = await handler(store_id, payload, db)
            
            # Update webhook event status
            webhook_event.status = "processed"
            webhook_event.processed_at = datetime.utcnow()
            webhook_event.result = result
            await db.commit()
            
            logger.info(
                "webhook_processed_successfully",
                store_id=store_id,
                topic=topic,
                webhook_id=webhook_id
            )
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(
                "webhook_processing_error",
                store_id=store_id,
                topic=topic,
                error=str(e)
            )
            
            # Update webhook event with error
            webhook_event.status = "failed"
            webhook_event.processed_at = datetime.utcnow()
            webhook_event.error = str(e)
            await db.commit()
            
            raise
    
    # ============= Order Event Handlers =============
    
    async def _handle_order_created(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle order created webhook
        
        Args:
            store_id: Store identifier
            payload: Order data from webhook
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_order_created",
            store_id=store_id,
            order_id=payload.get('id'),
            order_number=payload.get('number')
        )
        
        # Create order in our system
        order = await self.order_service.create_order_from_woocommerce(
            store_id=store_id,
            wc_order=payload,
            db=db
        )
        
        # Check if shipping is needed
        if payload.get('status') in ['processing', 'completed']:
            # Create shipping request with carriers
            shipping_result = await self.order_service.create_shipping_request(
                order_id=order.id,
                db=db
            )
            
            # Send notification
            await self.notification_service.send_order_confirmation(
                order_id=order.id,
                customer_email=payload.get('billing', {}).get('email')
            )
        
        return {
            "order_id": order.id,
            "wc_order_id": payload.get('id'),
            "status": "created",
            "shipping_requested": payload.get('status') in ['processing', 'completed']
        }
    
    async def _handle_order_updated(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle order updated webhook
        
        Args:
            store_id: Store identifier
            payload: Updated order data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_order_updated",
            store_id=store_id,
            order_id=payload.get('id'),
            status=payload.get('status')
        )
        
        # Update order in our system
        order = await self.order_service.update_order_from_woocommerce(
            store_id=store_id,
            wc_order_id=payload.get('id'),
            wc_order=payload,
            db=db
        )
        
        # Handle status changes
        old_status = order.status
        new_status = payload.get('status')
        
        if old_status != new_status:
            await self._handle_order_status_change(
                order=order,
                old_status=old_status,
                new_status=new_status,
                db=db
            )
        
        return {
            "order_id": order.id,
            "wc_order_id": payload.get('id'),
            "status": "updated",
            "status_changed": old_status != new_status
        }
    
    async def _handle_order_deleted(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle order deleted webhook
        
        Args:
            store_id: Store identifier
            payload: Deleted order data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_order_deleted",
            store_id=store_id,
            order_id=payload.get('id')
        )
        
        # Mark order as deleted in our system
        order = await self.order_service.mark_order_deleted(
            store_id=store_id,
            wc_order_id=payload.get('id'),
            db=db
        )
        
        # Cancel any pending shipments
        if order and order.shipping_id:
            await self.order_service.cancel_shipping(
                shipping_id=order.shipping_id,
                reason="Order deleted in WooCommerce",
                db=db
            )
        
        return {
            "order_id": order.id if order else None,
            "wc_order_id": payload.get('id'),
            "status": "deleted",
            "shipping_cancelled": bool(order and order.shipping_id)
        }
    
    async def _handle_order_status_change(
        self,
        order: Order,
        old_status: str,
        new_status: str,
        db: AsyncSession
    ) -> None:
        """
        Handle order status change logic
        
        Args:
            order: Order object
            old_status: Previous status
            new_status: New status
            db: Database session
        """
        # Status change mappings
        status_actions = {
            'processing': self._handle_order_processing,
            'completed': self._handle_order_completed,
            'cancelled': self._handle_order_cancelled,
            'refunded': self._handle_order_refunded,
            'failed': self._handle_order_failed,
            'on-hold': self._handle_order_on_hold
        }
        
        # Execute action for new status
        action = status_actions.get(new_status)
        if action:
            await action(order, db)
        
        # Update order status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        await db.commit()
    
    async def _handle_order_processing(self, order: Order, db: AsyncSession) -> None:
        """Handle order moved to processing status"""
        # Create shipping label if not exists
        if not order.shipping_id:
            shipping = await self.order_service.create_shipping_request(
                order_id=order.id,
                db=db
            )
            order.shipping_id = shipping.id
        
        # Send processing notification
        await self.notification_service.send_order_processing(
            order_id=order.id,
            customer_email=order.customer_email
        )
    
    async def _handle_order_completed(self, order: Order, db: AsyncSession) -> None:
        """Handle order moved to completed status"""
        # Mark as delivered in shipping system
        if order.shipping_id:
            await self.order_service.mark_delivered(
                shipping_id=order.shipping_id,
                db=db
            )
        
        # Send completion notification
        await self.notification_service.send_order_completed(
            order_id=order.id,
            customer_email=order.customer_email
        )
    
    async def _handle_order_cancelled(self, order: Order, db: AsyncSession) -> None:
        """Handle order cancellation"""
        # Cancel shipping if exists
        if order.shipping_id:
            await self.order_service.cancel_shipping(
                shipping_id=order.shipping_id,
                reason="Order cancelled",
                db=db
            )
        
        # Send cancellation notification
        await self.notification_service.send_order_cancelled(
            order_id=order.id,
            customer_email=order.customer_email
        )
    
    async def _handle_order_refunded(self, order: Order, db: AsyncSession) -> None:
        """Handle order refund"""
        # Process return shipping if needed
        if order.shipping_id:
            await self.order_service.create_return_shipping(
                order_id=order.id,
                shipping_id=order.shipping_id,
                db=db
            )
        
        # Send refund notification
        await self.notification_service.send_order_refunded(
            order_id=order.id,
            customer_email=order.customer_email
        )
    
    async def _handle_order_failed(self, order: Order, db: AsyncSession) -> None:
        """Handle failed order"""
        # Cancel any pending operations
        if order.shipping_id:
            await self.order_service.cancel_shipping(
                shipping_id=order.shipping_id,
                reason="Order failed",
                db=db
            )
        
        # Send failure notification
        await self.notification_service.send_order_failed(
            order_id=order.id,
            customer_email=order.customer_email
        )
    
    async def _handle_order_on_hold(self, order: Order, db: AsyncSession) -> None:
        """Handle order put on hold"""
        # Pause shipping operations
        if order.shipping_id:
            await self.order_service.pause_shipping(
                shipping_id=order.shipping_id,
                db=db
            )
        
        # Send on-hold notification
        await self.notification_service.send_order_on_hold(
            order_id=order.id,
            customer_email=order.customer_email
        )
    
    # ============= Product Event Handlers =============
    
    async def _handle_product_created(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle product created webhook
        
        Args:
            store_id: Store identifier
            payload: Product data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_product_created",
            store_id=store_id,
            product_id=payload.get('id'),
            sku=payload.get('sku')
        )
        
        # Create product in our system
        product = await self.product_service.create_product_from_woocommerce(
            store_id=store_id,
            wc_product=payload,
            db=db
        )
        
        return {
            "product_id": product.id,
            "wc_product_id": payload.get('id'),
            "sku": payload.get('sku'),
            "status": "created"
        }
    
    async def _handle_product_updated(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle product updated webhook
        
        Args:
            store_id: Store identifier
            payload: Updated product data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_product_updated",
            store_id=store_id,
            product_id=payload.get('id'),
            sku=payload.get('sku')
        )
        
        # Update product in our system
        product = await self.product_service.update_product_from_woocommerce(
            store_id=store_id,
            wc_product_id=payload.get('id'),
            wc_product=payload,
            db=db
        )
        
        # Check for stock changes
        if 'stock_quantity' in payload:
            await self.product_service.sync_inventory(
                product_id=product.id,
                quantity=payload.get('stock_quantity'),
                db=db
            )
        
        return {
            "product_id": product.id,
            "wc_product_id": payload.get('id'),
            "sku": payload.get('sku'),
            "status": "updated",
            "stock_updated": 'stock_quantity' in payload
        }
    
    async def _handle_product_deleted(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle product deleted webhook
        
        Args:
            store_id: Store identifier
            payload: Deleted product data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_product_deleted",
            store_id=store_id,
            product_id=payload.get('id')
        )
        
        # Mark product as deleted
        product = await self.product_service.mark_product_deleted(
            store_id=store_id,
            wc_product_id=payload.get('id'),
            db=db
        )
        
        return {
            "product_id": product.id if product else None,
            "wc_product_id": payload.get('id'),
            "status": "deleted"
        }
    
    # ============= Customer Event Handlers =============
    
    async def _handle_customer_created(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle customer created webhook
        
        Args:
            store_id: Store identifier
            payload: Customer data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_customer_created",
            store_id=store_id,
            customer_id=payload.get('id'),
            email=payload.get('email')
        )
        
        # Create customer record
        customer = Customer(
            store_id=store_id,
            wc_customer_id=payload.get('id'),
            email=payload.get('email'),
            first_name=payload.get('first_name'),
            last_name=payload.get('last_name'),
            username=payload.get('username'),
            billing_address=payload.get('billing'),
            shipping_address=payload.get('shipping'),
            created_at=datetime.utcnow()
        )
        db.add(customer)
        await db.commit()
        
        # Send welcome email
        await self.notification_service.send_customer_welcome(
            customer_email=payload.get('email'),
            customer_name=f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip()
        )
        
        return {
            "customer_id": customer.id,
            "wc_customer_id": payload.get('id'),
            "email": payload.get('email'),
            "status": "created"
        }
    
    async def _handle_customer_updated(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle customer updated webhook
        
        Args:
            store_id: Store identifier
            payload: Updated customer data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_customer_updated",
            store_id=store_id,
            customer_id=payload.get('id')
        )
        
        # Update customer record
        customer = await db.query(Customer).filter(
            Customer.store_id == store_id,
            Customer.wc_customer_id == payload.get('id')
        ).first()
        
        if customer:
            customer.email = payload.get('email')
            customer.first_name = payload.get('first_name')
            customer.last_name = payload.get('last_name')
            customer.billing_address = payload.get('billing')
            customer.shipping_address = payload.get('shipping')
            customer.updated_at = datetime.utcnow()
            await db.commit()
        
        return {
            "customer_id": customer.id if customer else None,
            "wc_customer_id": payload.get('id'),
            "status": "updated"
        }
    
    async def _handle_customer_deleted(
        self,
        store_id: str,
        payload: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Handle customer deleted webhook
        
        Args:
            store_id: Store identifier
            payload: Deleted customer data
            db: Database session
            
        Returns:
            Processing result
        """
        logger.info(
            "processing_customer_deleted",
            store_id=store_id,
            customer_id=payload.get('id')
        )
        
        # Mark customer as deleted (soft delete)
        customer = await db.query(Customer).filter(
            Customer.store_id == store_id,
            Customer.wc_customer_id == payload.get('id')
        ).first()
        
        if customer:
            customer.deleted_at = datetime.utcnow()
            await db.commit()
        
        return {
            "customer_id": customer.id if customer else None,
            "wc_customer_id": payload.get('id'),
            "status": "deleted"
        }
    
    async def batch_process_webhooks(
        self,
        webhooks: List[Dict[str, Any]],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Process multiple webhooks in batch
        
        Args:
            webhooks: List of webhook data
            db: Database session
            
        Returns:
            List of processing results
        """
        results = []
        
        for webhook in webhooks:
            try:
                result = await self.process_webhook(
                    store_id=webhook['store_id'],
                    topic=webhook['topic'],
                    webhook_id=webhook['webhook_id'],
                    payload=webhook['payload'],
                    signature=webhook['signature'],
                    secret=webhook['secret'],
                    db=db
                )
                results.append(result)
            except Exception as e:
                logger.error(
                    "batch_webhook_processing_error",
                    webhook_id=webhook.get('webhook_id'),
                    error=str(e)
                )
                results.append({
                    "status": "failed",
                    "webhook_id": webhook.get('webhook_id'),
                    "error": str(e)
                })
        
        return results


# Export classes
__all__ = ['WooCommerceWebhookHandler', 'WebhookTopic']