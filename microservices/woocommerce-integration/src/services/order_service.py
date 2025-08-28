"""
Order Service
Manages order synchronization between WooCommerce and Quenty
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..api.woocommerce_client import WooCommerceClient
from ..models.entities import Order, OrderItem, OrderStatus, ShippingRequest
from ..utils.exceptions import OrderNotFoundError, ShippingError
from ..utils.carrier_integration import CarrierIntegrationClient

logger = structlog.get_logger()


class OrderService:
    """
    Service for managing orders between WooCommerce and Quenty
    Handles order synchronization, shipping requests, and status updates
    """
    
    def __init__(self, carrier_client: CarrierIntegrationClient):
        """
        Initialize order service
        
        Args:
            carrier_client: Client for carrier integration service
        """
        self.carrier_client = carrier_client
        self.wc_clients = {}  # Store ID -> WooCommerceClient mapping
    
    def register_store(self, store_id: str, wc_client: WooCommerceClient) -> None:
        """
        Register a WooCommerce store client
        
        Args:
            store_id: Store identifier
            wc_client: WooCommerce API client for the store
        """
        self.wc_clients[store_id] = wc_client
        logger.info(
            "store_registered",
            store_id=store_id,
            store_url=wc_client.store_url
        )
    
    async def create_order_from_woocommerce(
        self,
        store_id: str,
        wc_order: Dict[str, Any],
        db: AsyncSession
    ) -> Order:
        """
        Create an order in Quenty from WooCommerce order data
        
        Args:
            store_id: Store identifier
            wc_order: WooCommerce order data
            db: Database session
            
        Returns:
            Created order object
        """
        logger.info(
            "creating_order_from_woocommerce",
            store_id=store_id,
            wc_order_id=wc_order.get('id'),
            order_number=wc_order.get('number')
        )
        
        # Check if order already exists
        existing_order = await db.execute(
            select(Order).where(
                and_(
                    Order.store_id == store_id,
                    Order.wc_order_id == wc_order.get('id')
                )
            )
        )
        existing_order = existing_order.scalar_one_or_none()
        
        if existing_order:
            logger.warning(
                "order_already_exists",
                order_id=existing_order.id,
                wc_order_id=wc_order.get('id')
            )
            return existing_order
        
        # Create new order
        order = Order(
            store_id=store_id,
            wc_order_id=wc_order.get('id'),
            wc_order_number=wc_order.get('number'),
            status=OrderStatus(wc_order.get('status', 'pending')),
            customer_id=wc_order.get('customer_id'),
            customer_email=wc_order.get('billing', {}).get('email'),
            customer_name=f"{wc_order.get('billing', {}).get('first_name', '')} {wc_order.get('billing', {}).get('last_name', '')}".strip(),
            currency=wc_order.get('currency', 'USD'),
            total=Decimal(str(wc_order.get('total', 0))),
            subtotal=Decimal(str(wc_order.get('subtotal', 0))),
            shipping_total=Decimal(str(wc_order.get('shipping_total', 0))),
            tax_total=Decimal(str(wc_order.get('total_tax', 0))),
            discount_total=Decimal(str(wc_order.get('discount_total', 0))),
            billing_address=wc_order.get('billing'),
            shipping_address=wc_order.get('shipping'),
            payment_method=wc_order.get('payment_method'),
            payment_method_title=wc_order.get('payment_method_title'),
            transaction_id=wc_order.get('transaction_id'),
            date_created=datetime.fromisoformat(wc_order.get('date_created').replace('T', ' ').replace('Z', '')),
            date_modified=datetime.fromisoformat(wc_order.get('date_modified').replace('T', ' ').replace('Z', '')),
            metadata=wc_order.get('meta_data', []),
            created_at=datetime.utcnow()
        )
        
        db.add(order)
        await db.flush()  # Get order ID
        
        # Add order items
        for item_data in wc_order.get('line_items', []):
            order_item = OrderItem(
                order_id=order.id,
                wc_item_id=item_data.get('id'),
                product_id=item_data.get('product_id'),
                variation_id=item_data.get('variation_id'),
                name=item_data.get('name'),
                sku=item_data.get('sku'),
                quantity=item_data.get('quantity'),
                price=Decimal(str(item_data.get('price', 0))),
                subtotal=Decimal(str(item_data.get('subtotal', 0))),
                total=Decimal(str(item_data.get('total', 0))),
                tax_total=Decimal(str(item_data.get('total_tax', 0))),
                metadata=item_data.get('meta_data', [])
            )
            db.add(order_item)
        
        await db.commit()
        await db.refresh(order)
        
        logger.info(
            "order_created",
            order_id=order.id,
            wc_order_id=wc_order.get('id'),
            total=str(order.total),
            items_count=len(wc_order.get('line_items', []))
        )
        
        return order
    
    async def update_order_from_woocommerce(
        self,
        store_id: str,
        wc_order_id: int,
        wc_order: Dict[str, Any],
        db: AsyncSession
    ) -> Order:
        """
        Update an existing order from WooCommerce data
        
        Args:
            store_id: Store identifier
            wc_order_id: WooCommerce order ID
            wc_order: Updated WooCommerce order data
            db: Database session
            
        Returns:
            Updated order object
        """
        # Find existing order
        result = await db.execute(
            select(Order).where(
                and_(
                    Order.store_id == store_id,
                    Order.wc_order_id == wc_order_id
                )
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            # Create new order if doesn't exist
            return await self.create_order_from_woocommerce(store_id, wc_order, db)
        
        # Update order fields
        order.status = OrderStatus(wc_order.get('status', order.status.value))
        order.total = Decimal(str(wc_order.get('total', order.total)))
        order.subtotal = Decimal(str(wc_order.get('subtotal', order.subtotal)))
        order.shipping_total = Decimal(str(wc_order.get('shipping_total', order.shipping_total)))
        order.tax_total = Decimal(str(wc_order.get('total_tax', order.tax_total)))
        order.discount_total = Decimal(str(wc_order.get('discount_total', order.discount_total)))
        order.billing_address = wc_order.get('billing', order.billing_address)
        order.shipping_address = wc_order.get('shipping', order.shipping_address)
        order.date_modified = datetime.fromisoformat(wc_order.get('date_modified').replace('T', ' ').replace('Z', ''))
        order.updated_at = datetime.utcnow()
        order.metadata = wc_order.get('meta_data', order.metadata)
        
        await db.commit()
        await db.refresh(order)
        
        logger.info(
            "order_updated",
            order_id=order.id,
            wc_order_id=wc_order_id,
            status=order.status.value
        )
        
        return order
    
    async def mark_order_deleted(
        self,
        store_id: str,
        wc_order_id: int,
        db: AsyncSession
    ) -> Optional[Order]:
        """
        Mark an order as deleted (soft delete)
        
        Args:
            store_id: Store identifier
            wc_order_id: WooCommerce order ID
            db: Database session
            
        Returns:
            Deleted order object or None if not found
        """
        result = await db.execute(
            select(Order).where(
                and_(
                    Order.store_id == store_id,
                    Order.wc_order_id == wc_order_id
                )
            )
        )
        order = result.scalar_one_or_none()
        
        if order:
            order.deleted_at = datetime.utcnow()
            await db.commit()
            
            logger.info(
                "order_marked_deleted",
                order_id=order.id,
                wc_order_id=wc_order_id
            )
        
        return order
    
    async def create_shipping_request(
        self,
        order_id: int,
        db: AsyncSession,
        preferred_carrier: Optional[str] = None
    ) -> ShippingRequest:
        """
        Create a shipping request for an order
        
        Args:
            order_id: Order ID
            db: Database session
            preferred_carrier: Preferred carrier name (optional)
            
        Returns:
            Created shipping request
        """
        # Get order details
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")
        
        # Get order items
        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        items = items_result.scalars().all()
        
        # Calculate package dimensions and weight
        total_weight = self._calculate_total_weight(items)
        packages = self._create_packages(items)
        
        # Prepare shipping data
        shipping_data = {
            "origin": self._get_origin_address(),
            "destination": self._format_shipping_address(order.shipping_address),
            "packages": packages,
            "service_type": self._determine_service_type(order),
            "order_id": str(order.wc_order_id),
            "customer_email": order.customer_email
        }
        
        try:
            # Get shipping quote from carriers
            if preferred_carrier:
                quote = await self.carrier_client.get_quote(
                    carrier=preferred_carrier,
                    data=shipping_data
                )
            else:
                # Get best quote from all carriers
                quote = await self.carrier_client.get_best_quote(shipping_data)
            
            # Create shipping label
            label = await self.carrier_client.create_label(
                carrier=quote['carrier'],
                data=shipping_data
            )
            
            # Create shipping request record
            shipping_request = ShippingRequest(
                order_id=order_id,
                carrier=quote['carrier'],
                service_type=quote['service_type'],
                tracking_number=label['tracking_number'],
                label_url=label['label_url'],
                label_data=label.get('label_data'),
                cost=Decimal(str(quote['total_price'])),
                currency=quote['currency'],
                estimated_delivery=quote.get('estimated_delivery'),
                status='created',
                created_at=datetime.utcnow()
            )
            
            db.add(shipping_request)
            order.shipping_id = shipping_request.id
            order.tracking_number = label['tracking_number']
            
            await db.commit()
            await db.refresh(shipping_request)
            
            # Update WooCommerce order with tracking info
            await self._update_woocommerce_tracking(
                order=order,
                tracking_number=label['tracking_number'],
                carrier=quote['carrier']
            )
            
            logger.info(
                "shipping_request_created",
                order_id=order_id,
                shipping_id=shipping_request.id,
                carrier=quote['carrier'],
                tracking_number=label['tracking_number'],
                cost=str(quote['total_price'])
            )
            
            return shipping_request
            
        except Exception as e:
            logger.error(
                "shipping_request_failed",
                order_id=order_id,
                error=str(e)
            )
            raise ShippingError(f"Failed to create shipping request: {str(e)}")
    
    async def cancel_shipping(
        self,
        shipping_id: int,
        reason: str,
        db: AsyncSession
    ) -> bool:
        """
        Cancel a shipping request
        
        Args:
            shipping_id: Shipping request ID
            reason: Cancellation reason
            db: Database session
            
        Returns:
            True if cancelled successfully
        """
        result = await db.execute(
            select(ShippingRequest).where(ShippingRequest.id == shipping_id)
        )
        shipping = result.scalar_one_or_none()
        
        if not shipping:
            logger.warning(
                "shipping_not_found",
                shipping_id=shipping_id
            )
            return False
        
        # Cancel with carrier
        try:
            await self.carrier_client.cancel_shipment(
                carrier=shipping.carrier,
                tracking_number=shipping.tracking_number,
                reason=reason
            )
            
            shipping.status = 'cancelled'
            shipping.cancelled_at = datetime.utcnow()
            shipping.cancellation_reason = reason
            
            await db.commit()
            
            logger.info(
                "shipping_cancelled",
                shipping_id=shipping_id,
                tracking_number=shipping.tracking_number,
                reason=reason
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "shipping_cancellation_failed",
                shipping_id=shipping_id,
                error=str(e)
            )
            return False
    
    async def update_shipping_status(
        self,
        tracking_number: str,
        db: AsyncSession
    ) -> Optional[ShippingRequest]:
        """
        Update shipping status from carrier
        
        Args:
            tracking_number: Tracking number
            db: Database session
            
        Returns:
            Updated shipping request or None
        """
        result = await db.execute(
            select(ShippingRequest).where(
                ShippingRequest.tracking_number == tracking_number
            )
        )
        shipping = result.scalar_one_or_none()
        
        if not shipping:
            return None
        
        try:
            # Get tracking info from carrier
            tracking_info = await self.carrier_client.track_shipment(
                carrier=shipping.carrier,
                tracking_number=tracking_number
            )
            
            # Update shipping status
            shipping.status = tracking_info['status']
            shipping.current_location = tracking_info.get('current_location')
            shipping.tracking_events = tracking_info.get('events', [])
            shipping.delivered_at = tracking_info.get('delivered_at')
            shipping.updated_at = datetime.utcnow()
            
            await db.commit()
            
            # Update WooCommerce order if delivered
            if shipping.status == 'delivered':
                await self._mark_order_delivered(shipping.order_id, db)
            
            return shipping
            
        except Exception as e:
            logger.error(
                "tracking_update_failed",
                tracking_number=tracking_number,
                error=str(e)
            )
            return None
    
    async def sync_orders(
        self,
        store_id: str,
        since: Optional[datetime] = None,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Sync orders from WooCommerce
        
        Args:
            store_id: Store identifier
            since: Sync orders modified since this date
            db: Database session
            
        Returns:
            Sync results
        """
        wc_client = self.wc_clients.get(store_id)
        if not wc_client:
            raise ValueError(f"Store {store_id} not registered")
        
        logger.info(
            "starting_order_sync",
            store_id=store_id,
            since=since.isoformat() if since else None
        )
        
        created = 0
        updated = 0
        errors = []
        page = 1
        
        while True:
            try:
                # Fetch orders from WooCommerce
                orders = await wc_client.get_orders(
                    after=since,
                    per_page=100,
                    page=page,
                    orderby='modified',
                    order='asc'
                )
                
                if not orders:
                    break
                
                for wc_order in orders:
                    try:
                        # Check if order exists
                        result = await db.execute(
                            select(Order).where(
                                and_(
                                    Order.store_id == store_id,
                                    Order.wc_order_id == wc_order['id']
                                )
                            )
                        )
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            await self.update_order_from_woocommerce(
                                store_id=store_id,
                                wc_order_id=wc_order['id'],
                                wc_order=wc_order,
                                db=db
                            )
                            updated += 1
                        else:
                            await self.create_order_from_woocommerce(
                                store_id=store_id,
                                wc_order=wc_order,
                                db=db
                            )
                            created += 1
                            
                    except Exception as e:
                        logger.error(
                            "order_sync_error",
                            store_id=store_id,
                            wc_order_id=wc_order.get('id'),
                            error=str(e)
                        )
                        errors.append({
                            'order_id': wc_order.get('id'),
                            'error': str(e)
                        })
                
                page += 1
                
            except Exception as e:
                logger.error(
                    "order_sync_page_error",
                    store_id=store_id,
                    page=page,
                    error=str(e)
                )
                break
        
        logger.info(
            "order_sync_completed",
            store_id=store_id,
            created=created,
            updated=updated,
            errors=len(errors)
        )
        
        return {
            'created': created,
            'updated': updated,
            'errors': errors,
            'total': created + updated
        }
    
    def _calculate_total_weight(self, items: List[OrderItem]) -> float:
        """Calculate total weight of order items"""
        total_weight = 0.0
        for item in items:
            # Default weight if not specified
            weight = item.metadata.get('weight', 0.5) if isinstance(item.metadata, dict) else 0.5
            total_weight += weight * item.quantity
        return total_weight
    
    def _create_packages(self, items: List[OrderItem]) -> List[Dict]:
        """Create package specifications for shipping"""
        # Simple packaging logic - can be enhanced
        return [{
            "weight_kg": self._calculate_total_weight(items),
            "length_cm": 30,
            "width_cm": 20,
            "height_cm": 15,
            "description": "E-commerce order"
        }]
    
    def _get_origin_address(self) -> Dict[str, str]:
        """Get origin address for shipping"""
        # This should be configurable per store
        return {
            "street": "123 Warehouse St",
            "city": "Miami",
            "state": "FL",
            "postal_code": "33101",
            "country": "US",
            "contact_name": "Warehouse Manager",
            "contact_phone": "+13055551234"
        }
    
    def _format_shipping_address(self, address: Dict) -> Dict[str, str]:
        """Format WooCommerce address for carrier API"""
        return {
            "street": f"{address.get('address_1', '')} {address.get('address_2', '')}".strip(),
            "city": address.get('city', ''),
            "state": address.get('state', ''),
            "postal_code": address.get('postcode', ''),
            "country": address.get('country', ''),
            "contact_name": f"{address.get('first_name', '')} {address.get('last_name', '')}".strip(),
            "contact_phone": address.get('phone', ''),
            "contact_email": address.get('email', '')
        }
    
    def _determine_service_type(self, order: Order) -> str:
        """Determine shipping service type based on order"""
        # Logic to determine service type
        if order.total > 100:
            return "express"
        return "standard"
    
    async def _update_woocommerce_tracking(
        self,
        order: Order,
        tracking_number: str,
        carrier: str
    ) -> None:
        """Update WooCommerce order with tracking information"""
        wc_client = self.wc_clients.get(order.store_id)
        if not wc_client:
            return
        
        try:
            # Add order note with tracking info
            await wc_client.add_order_note(
                order_id=order.wc_order_id,
                note=f"Shipment created with {carrier}. Tracking: {tracking_number}",
                customer_note=True
            )
            
            # Update order metadata
            await wc_client.update_order(
                order_id=order.wc_order_id,
                order_data={
                    'meta_data': [
                        {'key': '_tracking_number', 'value': tracking_number},
                        {'key': '_tracking_carrier', 'value': carrier}
                    ]
                }
            )
        except Exception as e:
            logger.error(
                "woocommerce_tracking_update_failed",
                order_id=order.id,
                error=str(e)
            )
    
    async def _mark_order_delivered(self, order_id: int, db: AsyncSession) -> None:
        """Mark order as delivered"""
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if order:
            order.status = OrderStatus.COMPLETED
            order.delivered_at = datetime.utcnow()
            await db.commit()
            
            # Update WooCommerce order status
            wc_client = self.wc_clients.get(order.store_id)
            if wc_client:
                try:
                    await wc_client.update_order_status(
                        order_id=order.wc_order_id,
                        status='completed',
                        note='Order delivered successfully'
                    )
                except Exception as e:
                    logger.error(
                        "woocommerce_status_update_failed",
                        order_id=order.id,
                        error=str(e)
                    )


# Export class
__all__ = ['OrderService']