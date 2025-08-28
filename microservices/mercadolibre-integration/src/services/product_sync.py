import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models import MercadoLibreProduct, MercadoLibreInventory, MercadoLibreAccount, ListingStatus
from .meli_client import MercadoLibreClient
import asyncio

logger = logging.getLogger(__name__)


class ProductSyncService:
    """Service for synchronizing products with MercadoLibre"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_products_from_meli(
        self,
        account: MercadoLibreAccount,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync products from MercadoLibre to local database"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        sync_stats = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Get all items from MercadoLibre
            offset = 0
            limit = 50
            
            while True:
                response = await client.get_items_by_seller(
                    seller_id=account.user_id,
                    status=status_filter,
                    offset=offset,
                    limit=limit
                )
                
                items = response.get("results", [])
                if not items:
                    break
                
                # Process each item
                for item_summary in items:
                    try:
                        # Get full item details
                        item = await client.get_item(item_summary["id"])
                        
                        # Get item description
                        try:
                            description = await client.get_item_description(item_summary["id"])
                        except:
                            description = {"plain_text": ""}
                        
                        # Sync to database
                        await self._sync_product_to_db(account, item, description)
                        sync_stats["updated"] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to sync item {item_summary['id']}: {str(e)}")
                        sync_stats["failed"] += 1
                        sync_stats["errors"].append({
                            "item_id": item_summary["id"],
                            "error": str(e)
                        })
                
                sync_stats["total"] += len(items)
                
                # Check if there are more items
                if len(items) < limit:
                    break
                    
                offset += limit
                await asyncio.sleep(0.5)  # Rate limiting
            
            await self.db.commit()
            logger.info(f"Product sync completed: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"Product sync failed: {str(e)}")
            await self.db.rollback()
            raise
    
    async def _sync_product_to_db(
        self,
        account: MercadoLibreAccount,
        item: Dict[str, Any],
        description: Dict[str, Any]
    ):
        """Sync single product to database"""
        
        # Check if product exists
        result = await self.db.execute(
            select(MercadoLibreProduct).where(
                MercadoLibreProduct.meli_item_id == item["id"]
            )
        )
        product = result.scalar_one_or_none()
        
        # Map status
        status_mapping = {
            "active": ListingStatus.ACTIVE,
            "paused": ListingStatus.PAUSED,
            "closed": ListingStatus.CLOSED,
            "under_review": ListingStatus.UNDER_REVIEW,
            "inactive": ListingStatus.INACTIVE
        }
        
        product_data = {
            "account_id": account.id,
            "meli_item_id": item["id"],
            "title": item["title"],
            "category_id": item["category_id"],
            "price": float(item["price"]),
            "currency_id": item["currency_id"],
            "available_quantity": item.get("available_quantity", 0),
            "sold_quantity": item.get("sold_quantity", 0),
            "buying_mode": item.get("buying_mode"),
            "listing_type_id": item.get("listing_type_id"),
            "condition": item.get("condition"),
            "permalink": item.get("permalink"),
            "thumbnail": item.get("thumbnail"),
            "pictures": [pic["url"] for pic in item.get("pictures", [])],
            "video_id": item.get("video_id"),
            "descriptions": [description.get("plain_text", "")],
            "attributes": item.get("attributes", []),
            "variations": item.get("variations", []),
            "shipping": item.get("shipping", {}),
            "status": status_mapping.get(item["status"], ListingStatus.INACTIVE),
            "health": item.get("health"),
            "warranty": item.get("warranty"),
            "catalog_product_id": item.get("catalog_product_id"),
            "tags": item.get("tags", []),
            "date_created": datetime.fromisoformat(item["date_created"].replace("Z", "+00:00")),
            "last_updated": datetime.fromisoformat(item["last_updated"].replace("Z", "+00:00")),
            "start_time": datetime.fromisoformat(item["start_time"].replace("Z", "+00:00")) if item.get("start_time") else None,
            "stop_time": datetime.fromisoformat(item["stop_time"].replace("Z", "+00:00")) if item.get("stop_time") else None,
        }
        
        if product:
            # Update existing product
            for key, value in product_data.items():
                setattr(product, key, value)
        else:
            # Create new product
            product = MercadoLibreProduct(**product_data)
            self.db.add(product)
        
        await self.db.flush()
        
        # Update or create inventory record
        result = await self.db.execute(
            select(MercadoLibreInventory).where(
                MercadoLibreInventory.product_id == product.id
            )
        )
        inventory = result.scalar_one_or_none()
        
        if inventory:
            inventory.available_quantity = item.get("available_quantity", 0)
            inventory.sold_quantity = item.get("sold_quantity", 0)
            inventory.last_sync = datetime.utcnow()
            inventory.sync_status = "synced"
        else:
            inventory = MercadoLibreInventory(
                product_id=product.id,
                available_quantity=item.get("available_quantity", 0),
                sold_quantity=item.get("sold_quantity", 0),
                last_sync=datetime.utcnow(),
                sync_status="synced"
            )
            self.db.add(inventory)
    
    async def publish_product_to_meli(
        self,
        account: MercadoLibreAccount,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Publish a new product to MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            # Validate required fields
            required_fields = ["title", "category_id", "price", "currency_id", "available_quantity", "condition"]
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create item on MercadoLibre
            item_data = {
                "title": product_data["title"],
                "category_id": product_data["category_id"],
                "price": product_data["price"],
                "currency_id": product_data.get("currency_id", settings.site_config["currency"]),
                "available_quantity": product_data["available_quantity"],
                "buying_mode": product_data.get("buying_mode", "buy_it_now"),
                "listing_type_id": product_data.get("listing_type_id", "free"),
                "condition": product_data["condition"],
                "pictures": product_data.get("pictures", []),
                "attributes": product_data.get("attributes", []),
                "shipping": product_data.get("shipping", {
                    "mode": "not_specified",
                    "local_pick_up": False,
                    "free_shipping": False
                }),
                "site_id": settings.meli_site_id
            }
            
            # Add optional fields
            if "description" in product_data:
                item_data["descriptions"] = [{"plain_text": product_data["description"]}]
            if "video_id" in product_data:
                item_data["video_id"] = product_data["video_id"]
            if "warranty" in product_data:
                item_data["warranty"] = product_data["warranty"]
            if "variations" in product_data:
                item_data["variations"] = product_data["variations"]
            
            # Create item
            response = await client.create_item(item_data)
            
            # Save to database
            await self._sync_product_to_db(account, response, {"plain_text": product_data.get("description", "")})
            await self.db.commit()
            
            logger.info(f"Product published successfully: {response['id']}")
            return {
                "success": True,
                "item_id": response["id"],
                "permalink": response["permalink"],
                "data": response
            }
            
        except Exception as e:
            logger.error(f"Failed to publish product: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_product_on_meli(
        self,
        account: MercadoLibreAccount,
        item_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update product on MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            # Update on MercadoLibre
            response = await client.update_item(item_id, updates)
            
            # Update description separately if provided
            if "description" in updates:
                await client.update_item_description(item_id, updates["description"])
            
            # Sync changes to database
            await self._sync_product_to_db(
                account,
                response,
                {"plain_text": updates.get("description", "")}
            )
            await self.db.commit()
            
            return {
                "success": True,
                "item_id": item_id,
                "data": response
            }
            
        except Exception as e:
            logger.error(f"Failed to update product {item_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_stock_on_meli(
        self,
        account: MercadoLibreAccount,
        item_id: str,
        quantity: int
    ) -> Dict[str, Any]:
        """Update product stock on MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            # Update stock on MercadoLibre
            response = await client.update_item_stock(item_id, quantity)
            
            # Update local inventory
            result = await self.db.execute(
                select(MercadoLibreProduct).where(
                    MercadoLibreProduct.meli_item_id == item_id
                )
            )
            product = result.scalar_one_or_none()
            
            if product:
                product.available_quantity = quantity
                
                # Update inventory record
                result = await self.db.execute(
                    select(MercadoLibreInventory).where(
                        MercadoLibreInventory.product_id == product.id
                    )
                )
                inventory = result.scalar_one_or_none()
                
                if inventory:
                    inventory.available_quantity = quantity
                    inventory.last_sync = datetime.utcnow()
                else:
                    inventory = MercadoLibreInventory(
                        product_id=product.id,
                        available_quantity=quantity,
                        last_sync=datetime.utcnow(),
                        sync_status="synced"
                    )
                    self.db.add(inventory)
            
            await self.db.commit()
            
            return {
                "success": True,
                "item_id": item_id,
                "new_quantity": quantity
            }
            
        except Exception as e:
            logger.error(f"Failed to update stock for {item_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def pause_product(
        self,
        account: MercadoLibreAccount,
        item_id: str
    ) -> Dict[str, Any]:
        """Pause product listing on MercadoLibre"""
        
        return await self._update_product_status(account, item_id, "paused")
    
    async def activate_product(
        self,
        account: MercadoLibreAccount,
        item_id: str
    ) -> Dict[str, Any]:
        """Activate product listing on MercadoLibre"""
        
        return await self._update_product_status(account, item_id, "active")
    
    async def close_product(
        self,
        account: MercadoLibreAccount,
        item_id: str
    ) -> Dict[str, Any]:
        """Close product listing on MercadoLibre"""
        
        return await self._update_product_status(account, item_id, "closed")
    
    async def _update_product_status(
        self,
        account: MercadoLibreAccount,
        item_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Update product status on MercadoLibre"""
        
        client = MercadoLibreClient(access_token=account.access_token)
        
        try:
            # Update status on MercadoLibre
            response = await client.update_item_status(item_id, status)
            
            # Update local database
            result = await self.db.execute(
                select(MercadoLibreProduct).where(
                    MercadoLibreProduct.meli_item_id == item_id
                )
            )
            product = result.scalar_one_or_none()
            
            if product:
                status_mapping = {
                    "active": ListingStatus.ACTIVE,
                    "paused": ListingStatus.PAUSED,
                    "closed": ListingStatus.CLOSED
                }
                product.status = status_mapping.get(status, ListingStatus.INACTIVE)
            
            await self.db.commit()
            
            return {
                "success": True,
                "item_id": item_id,
                "new_status": status
            }
            
        except Exception as e:
            logger.error(f"Failed to update status for {item_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }