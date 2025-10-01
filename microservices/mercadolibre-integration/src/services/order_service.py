import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models import (
    MercadoLibreOrder, MercadoLibreShipment, MercadoLibreAccount,
    MercadoLibreMessage, OrderStatus
)
from .meli_client import MercadoLibreClient
import asyncio

logger = logging.getLogger(__name__)


class OrderService:
    """Service for managing MercadoLibre orders"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_orders(
        self,
        account: MercadoLibreAccount,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync orders from MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        # Default to last 30 days if no date range specified
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        sync_stats = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            offset = 0
            limit = 50
            
            while True:
                # Get orders from MercadoLibre
                response = await client.get_orders(
                    seller_id=account.user_id,
                    status=status_filter,
                    date_from=date_from,
                    date_to=date_to,
                    offset=offset,
                    limit=limit
                )
                
                orders = response.get("results", [])
                if not orders:
                    break
                
                # Process each order
                for order_data in orders:
                    try:
                        await self._sync_order_to_db(account, order_data)
                        sync_stats["updated"] += 1
                    except Exception as e:
                        logger.error(f"Failed to sync order {order_data['id']}: {str(e)}")
                        sync_stats["failed"] += 1
                        sync_stats["errors"].append({
                            "order_id": order_data["id"],
                            "error": str(e)
                        })
                
                sync_stats["total"] += len(orders)
                
                # Check if there are more orders
                if len(orders) < limit:
                    break
                
                offset += limit
                await asyncio.sleep(0.5)  # Rate limiting
            
            await self.db.commit()
            logger.info(f"Order sync completed: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"Order sync failed: {str(e)}")
            await self.db.rollback()
            raise
    
    async def _sync_order_to_db(
        self,
        account: MercadoLibreAccount,
        order_data: Dict[str, Any]
    ):
        """Sync single order to database"""
        
        # Check if order exists
        result = await self.db.execute(
            select(MercadoLibreOrder).where(
                MercadoLibreOrder.meli_order_id == str(order_data["id"])
            )
        )
        order = result.scalar_one_or_none()
        
        # Map status
        status_mapping = {
            "confirmed": OrderStatus.CONFIRMED,
            "payment_required": OrderStatus.PAYMENT_REQUIRED,
            "payment_in_process": OrderStatus.PAYMENT_IN_PROCESS,
            "partially_paid": OrderStatus.PARTIALLY_PAID,
            "paid": OrderStatus.PAID,
            "cancelled": OrderStatus.CANCELLED,
            "invalid": OrderStatus.INVALID
        }
        
        order_fields = {
            "account_id": account.id,
            "meli_order_id": str(order_data["id"]),
            "status": status_mapping.get(order_data["status"], OrderStatus.INVALID),
            "status_detail": order_data.get("status_detail"),
            "date_created": self._parse_datetime(order_data.get("date_created")),
            "date_closed": self._parse_datetime(order_data.get("date_closed")),
            "date_last_updated": self._parse_datetime(order_data.get("date_last_updated")),
            "expiration_date": self._parse_datetime(order_data.get("expiration_date")),
            "buyer": order_data.get("buyer"),
            "seller": order_data.get("seller"),
            "order_items": order_data.get("order_items", []),
            "total_amount": order_data.get("total_amount"),
            "currency_id": order_data.get("currency_id"),
            "payments": order_data.get("payments", []),
            "shipping": order_data.get("shipping"),
            "pack_id": order_data.get("pack_id"),
            "pickup_id": order_data.get("pickup_id"),
            "feedback": order_data.get("feedback"),
            "tags": order_data.get("tags", []),
            "fulfilled": order_data.get("fulfilled", False),
            "manufacturing_ending_date": self._parse_datetime(order_data.get("manufacturing_ending_date")),
            "mediations": order_data.get("mediations", [])
        }
        
        if order:
            # Update existing order
            for key, value in order_fields.items():
                setattr(order, key, value)
        else:
            # Create new order
            order = MercadoLibreOrder(**order_fields)
            self.db.add(order)
        
        await self.db.flush()
        
        # Sync shipment if exists
        if order_data.get("shipping") and order_data["shipping"].get("id"):
            await self._sync_shipment_to_db(order, order_data["shipping"])
    
    async def _sync_shipment_to_db(
        self,
        order: MercadoLibreOrder,
        shipping_data: Dict[str, Any]
    ):
        """Sync shipment information to database"""
        
        if not shipping_data.get("id"):
            return
        
        # Check if shipment exists
        result = await self.db.execute(
            select(MercadoLibreShipment).where(
                MercadoLibreShipment.shipment_id == str(shipping_data["id"])
            )
        )
        shipment = result.scalar_one_or_none()
        
        shipment_fields = {
            "order_id": order.id,
            "shipment_id": str(shipping_data["id"]),
            "status": shipping_data.get("status"),
            "substatus": shipping_data.get("substatus"),
            "tracking_number": shipping_data.get("tracking_number"),
            "tracking_method": shipping_data.get("tracking_method"),
            "service_id": str(shipping_data.get("service_id")) if shipping_data.get("service_id") else None,
            "shipping_mode": shipping_data.get("mode"),
            "shipping_option": shipping_data.get("shipping_option"),
            "sender_address": shipping_data.get("sender_address"),
            "receiver_address": shipping_data.get("receiver_address"),
            "date_created": self._parse_datetime(shipping_data.get("date_created")),
            "last_updated": self._parse_datetime(shipping_data.get("last_updated")),
            "date_first_printed": self._parse_datetime(shipping_data.get("date_first_printed")),
            "logistic_type": shipping_data.get("logistic_type"),
            "cost": shipping_data.get("cost"),
            "currency_id": shipping_data.get("currency_id")
        }
        
        if shipment:
            # Update existing shipment
            for key, value in shipment_fields.items():
                setattr(shipment, key, value)
        else:
            # Create new shipment
            shipment = MercadoLibreShipment(**shipment_fields)
            self.db.add(shipment)
    
    async def get_order_details(
        self,
        account: MercadoLibreAccount,
        order_id: str
    ) -> Dict[str, Any]:
        """Get detailed order information from MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            # Get order from MercadoLibre
            order_data = await client.get_order(order_id)
            
            # Sync to database
            await self._sync_order_to_db(account, order_data)
            await self.db.commit()
            
            return {
                "success": True,
                "order": order_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_shipping_label(
        self,
        account: MercadoLibreAccount,
        shipment_id: str
    ) -> Dict[str, Any]:
        """Get shipping label for a shipment"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            label_data = await client.get_shipping_label(shipment_id)
            
            return {
                "success": True,
                "label": label_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get shipping label {shipment_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_order_note(
        self,
        account: MercadoLibreAccount,
        order_id: str,
        note: str
    ) -> Dict[str, Any]:
        """Add internal note to order"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            response = await client.update_order_note(order_id, note)
            
            return {
                "success": True,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Failed to add note to order {order_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_message_to_buyer(
        self,
        account: MercadoLibreAccount,
        order_id: str,
        message: str,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send message to buyer about an order"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            response = await client.send_message(order_id, message, attachments)
            
            # Save message to database
            msg = MercadoLibreMessage(
                order_id=order_id,
                message_id=response.get("id"),
                conversation_id=response.get("conversation_id"),
                from_user_id=account.user_id,
                to_user_id=response.get("to", {}).get("user_id"),
                text=message,
                attachments=attachments,
                date_created=datetime.utcnow(),
                status="sent"
            )
            self.db.add(msg)
            await self.db.commit()
            
            return {
                "success": True,
                "message": response
            }
            
        except Exception as e:
            logger.error(f"Failed to send message for order {order_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_order_messages(
        self,
        account: MercadoLibreAccount,
        order_id: str
    ) -> Dict[str, Any]:
        """Get messages for an order"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            messages = await client.get_messages(order_id=order_id)
            
            # Sync messages to database
            for msg_data in messages.get("results", []):
                await self._sync_message_to_db(order_id, msg_data)
            
            await self.db.commit()
            
            return {
                "success": True,
                "messages": messages.get("results", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get messages for order {order_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _sync_message_to_db(
        self,
        order_id: str,
        message_data: Dict[str, Any]
    ):
        """Sync message to database"""
        
        # Get order from database
        result = await self.db.execute(
            select(MercadoLibreOrder).where(
                MercadoLibreOrder.meli_order_id == order_id
            )
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return
        
        # Check if message exists
        result = await self.db.execute(
            select(MercadoLibreMessage).where(
                MercadoLibreMessage.message_id == str(message_data["id"])
            )
        )
        message = result.scalar_one_or_none()
        
        message_fields = {
            "order_id": order.id,
            "message_id": str(message_data["id"]),
            "conversation_id": message_data.get("conversation_id"),
            "from_user_id": message_data.get("from", {}).get("user_id"),
            "to_user_id": message_data.get("to", {}).get("user_id"),
            "text": message_data.get("text"),
            "attachments": message_data.get("attachments", []),
            "date_created": self._parse_datetime(message_data.get("date_created")),
            "date_received": self._parse_datetime(message_data.get("date_received")),
            "date_available": self._parse_datetime(message_data.get("date_available")),
            "date_notified": self._parse_datetime(message_data.get("date_notified")),
            "date_read": self._parse_datetime(message_data.get("date_read")),
            "status": message_data.get("status")
        }
        
        if message:
            # Update existing message
            for key, value in message_fields.items():
                setattr(message, key, value)
        else:
            # Create new message
            message = MercadoLibreMessage(**message_fields)
            self.db.add(message)
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from MercadoLibre API"""
        if not date_str:
            return None
        try:
            # Remove Z and add +00:00 for timezone
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None
    
    async def get_pending_orders(
        self,
        account: MercadoLibreAccount
    ) -> List[MercadoLibreOrder]:
        """Get pending orders that need attention"""
        
        result = await self.db.execute(
            select(MercadoLibreOrder).where(
                MercadoLibreOrder.account_id == account.id,
                MercadoLibreOrder.status.in_([
                    OrderStatus.CONFIRMED,
                    OrderStatus.PAYMENT_REQUIRED,
                    OrderStatus.PAYMENT_IN_PROCESS
                ])
            ).order_by(MercadoLibreOrder.date_created.desc())
        )
        
        return result.scalars().all()