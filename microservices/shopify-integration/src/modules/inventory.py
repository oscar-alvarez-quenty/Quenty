"""
Shopify Inventory Module
Handles inventory management, locations, and stock tracking
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InventoryModule:
    """
    Manage Shopify inventory levels and locations
    """
    
    def __init__(self, client):
        """
        Initialize Inventory module
        
        Args:
            client: ShopifyAPIClient instance
        """
        self.client = client
    
    # Location Management
    
    def list_locations(self, **kwargs) -> List[Dict[str, Any]]:
        """
        List all locations
        
        Args:
            active: Filter by active status
            
        Returns:
            List of locations
        """
        return self.client.paginate('locations', kwargs)
    
    def get_location(self, location_id: int) -> Dict[str, Any]:
        """
        Get a single location
        
        Args:
            location_id: Location ID
        
        Returns:
            Location data
        """
        response = self.client.get(f'locations/{location_id}')
        return response.get('location', {})
    
    def count_locations(self) -> int:
        """
        Count all locations
        
        Returns:
            Location count
        """
        response = self.client.get('locations/count')
        return response.get('count', 0)
    
    def update_location(self, location_id: int, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a location
        
        Args:
            location_id: Location ID
            location_data: Updated location information
        
        Returns:
            Updated location data
        """
        logger.info(f"Updating location {location_id}")
        response = self.client.put(f'locations/{location_id}', {'location': location_data})
        return response.get('location', {})
    
    # Inventory Level Management
    
    def get_inventory_levels(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get inventory levels
        
        Args:
            location_ids: List of location IDs
            inventory_item_ids: List of inventory item IDs
            limit: Number of results
            
        Returns:
            List of inventory levels
        """
        params = {}
        if kwargs.get('location_ids'):
            params['location_ids'] = ','.join(map(str, kwargs['location_ids']))
        if kwargs.get('inventory_item_ids'):
            params['inventory_item_ids'] = ','.join(map(str, kwargs['inventory_item_ids']))
        if kwargs.get('limit'):
            params['limit'] = kwargs['limit']
        
        response = self.client.get('inventory_levels', params)
        return response.get('inventory_levels', [])
    
    def set_inventory_level(self, location_id: int, inventory_item_id: int,
                           available: int, disconnect_if_necessary: bool = False) -> Dict[str, Any]:
        """
        Set inventory level at a location
        
        Args:
            location_id: Location ID
            inventory_item_id: Inventory item ID
            available: Available quantity
            disconnect_if_necessary: Disconnect if necessary
        
        Returns:
            Updated inventory level
        """
        logger.info(f"Setting inventory level for item {inventory_item_id} at location {location_id}")
        
        data = {
            'location_id': location_id,
            'inventory_item_id': inventory_item_id,
            'available': available
        }
        
        if disconnect_if_necessary:
            data['disconnect_if_necessary'] = True
        
        response = self.client.post('inventory_levels/set', data)
        return response.get('inventory_level', {})
    
    def adjust_inventory_level(self, location_id: int, inventory_item_id: int,
                              available_adjustment: int) -> Dict[str, Any]:
        """
        Adjust inventory level at a location
        
        Args:
            location_id: Location ID
            inventory_item_id: Inventory item ID
            available_adjustment: Quantity adjustment (positive or negative)
        
        Returns:
            Updated inventory level
        """
        logger.info(f"Adjusting inventory for item {inventory_item_id} by {available_adjustment}")
        
        data = {
            'location_id': location_id,
            'inventory_item_id': inventory_item_id,
            'available_adjustment': available_adjustment
        }
        
        response = self.client.post('inventory_levels/adjust', data)
        return response.get('inventory_level', {})
    
    def connect_inventory_location(self, location_id: int, inventory_item_id: int,
                                  relocate_if_necessary: bool = False) -> Dict[str, Any]:
        """
        Connect an inventory item to a location
        
        Args:
            location_id: Location ID
            inventory_item_id: Inventory item ID
            relocate_if_necessary: Relocate if necessary
        
        Returns:
            Connected inventory level
        """
        logger.info(f"Connecting item {inventory_item_id} to location {location_id}")
        
        data = {
            'location_id': location_id,
            'inventory_item_id': inventory_item_id
        }
        
        if relocate_if_necessary:
            data['relocate_if_necessary'] = True
        
        response = self.client.post('inventory_levels/connect', data)
        return response.get('inventory_level', {})
    
    def delete_inventory_level(self, inventory_item_id: int, location_id: int) -> bool:
        """
        Delete inventory level (disconnect item from location)
        
        Args:
            inventory_item_id: Inventory item ID
            location_id: Location ID
        
        Returns:
            True if successful
        """
        logger.info(f"Disconnecting item {inventory_item_id} from location {location_id}")
        self.client.delete(f'inventory_levels?inventory_item_id={inventory_item_id}&location_id={location_id}')
        return True
    
    # Inventory Item Management
    
    def get_inventory_item(self, inventory_item_id: int) -> Dict[str, Any]:
        """
        Get an inventory item
        
        Args:
            inventory_item_id: Inventory item ID
        
        Returns:
            Inventory item data
        """
        response = self.client.get(f'inventory_items/{inventory_item_id}')
        return response.get('inventory_item', {})
    
    def list_inventory_items(self, ids: List[int], limit: int = 50) -> List[Dict[str, Any]]:
        """
        List inventory items
        
        Args:
            ids: List of inventory item IDs
            limit: Number of results
        
        Returns:
            List of inventory items
        """
        params = {
            'ids': ','.join(map(str, ids)),
            'limit': limit
        }
        response = self.client.get('inventory_items', params)
        return response.get('inventory_items', [])
    
    def update_inventory_item(self, inventory_item_id: int,
                             item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an inventory item
        
        Args:
            inventory_item_id: Inventory item ID
            item_data: Updated item information
        
        Returns:
            Updated inventory item
        """
        logger.info(f"Updating inventory item {inventory_item_id}")
        response = self.client.put(f'inventory_items/{inventory_item_id}',
                                  {'inventory_item': item_data})
        return response.get('inventory_item', {})
    
    # Bulk Operations
    
    def bulk_adjust_inventory(self, adjustments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk adjust inventory levels
        
        Args:
            adjustments: List of adjustments with location_id, inventory_item_id, and adjustment
        
        Returns:
            List of updated inventory levels
        """
        results = []
        for adjustment in adjustments:
            try:
                result = self.adjust_inventory_level(
                    location_id=adjustment['location_id'],
                    inventory_item_id=adjustment['inventory_item_id'],
                    available_adjustment=adjustment['adjustment']
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to adjust inventory: {e}")
                results.append({
                    'error': str(e),
                    'adjustment': adjustment
                })
        
        return results
    
    def bulk_set_inventory(self, inventory_levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk set inventory levels
        
        Args:
            inventory_levels: List of inventory levels with location_id, inventory_item_id, and available
        
        Returns:
            List of updated inventory levels
        """
        results = []
        for level in inventory_levels:
            try:
                result = self.set_inventory_level(
                    location_id=level['location_id'],
                    inventory_item_id=level['inventory_item_id'],
                    available=level['available']
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to set inventory level: {e}")
                results.append({
                    'error': str(e),
                    'level': level
                })
        
        return results
    
    def transfer_inventory(self, from_location_id: int, to_location_id: int,
                          inventory_item_id: int, quantity: int) -> Dict[str, Any]:
        """
        Transfer inventory between locations
        
        Args:
            from_location_id: Source location ID
            to_location_id: Destination location ID
            inventory_item_id: Inventory item ID
            quantity: Quantity to transfer
        
        Returns:
            Transfer results
        """
        logger.info(f"Transferring {quantity} of item {inventory_item_id} from {from_location_id} to {to_location_id}")
        
        # Adjust source location (decrease)
        source_result = self.adjust_inventory_level(
            location_id=from_location_id,
            inventory_item_id=inventory_item_id,
            available_adjustment=-quantity
        )
        
        # Adjust destination location (increase)
        dest_result = self.adjust_inventory_level(
            location_id=to_location_id,
            inventory_item_id=inventory_item_id,
            available_adjustment=quantity
        )
        
        return {
            'from_location': source_result,
            'to_location': dest_result,
            'quantity_transferred': quantity
        }
    
    # Inventory Tracking
    
    def get_low_stock_items(self, threshold: int = 10, location_id: int = None) -> List[Dict[str, Any]]:
        """
        Get items with low stock
        
        Args:
            threshold: Stock level threshold
            location_id: Optional location ID filter
        
        Returns:
            List of low stock items
        """
        low_stock_items = []
        
        # Get all locations or specific location
        if location_id:
            locations = [{'id': location_id}]
        else:
            locations = self.list_locations(active=True)
        
        for location in locations:
            # This would need to be implemented with proper pagination
            # and filtering based on your specific needs
            inventory_levels = self.get_inventory_levels(
                location_ids=[location['id']],
                limit=250
            )
            
            for level in inventory_levels:
                if level.get('available', 0) < threshold:
                    low_stock_items.append({
                        'location_id': location['id'],
                        'inventory_item_id': level['inventory_item_id'],
                        'available': level['available'],
                        'location_name': location.get('name', 'Unknown')
                    })
        
        return low_stock_items
    
    def get_inventory_value(self, location_id: int = None) -> Dict[str, Any]:
        """
        Calculate total inventory value
        
        Args:
            location_id: Optional location ID filter
        
        Returns:
            Inventory value summary
        """
        total_units = 0
        total_value = 0.0
        items_count = 0
        
        # Get inventory levels
        kwargs = {}
        if location_id:
            kwargs['location_ids'] = [location_id]
        
        inventory_levels = self.get_inventory_levels(**kwargs)
        
        for level in inventory_levels:
            if level.get('available', 0) > 0:
                # Get inventory item details
                item = self.get_inventory_item(level['inventory_item_id'])
                
                quantity = level['available']
                cost = float(item.get('cost', 0))
                
                total_units += quantity
                total_value += quantity * cost
                items_count += 1
        
        return {
            'total_units': total_units,
            'total_value': total_value,
            'unique_items': items_count,
            'average_cost_per_unit': total_value / total_units if total_units > 0 else 0
        }
    
    def get_inventory_movement(self, inventory_item_id: int, 
                              start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Track inventory movement for an item
        
        Args:
            inventory_item_id: Inventory item ID
            start_date: Start date
            end_date: End date
        
        Returns:
            Inventory movement summary
        """
        # This would typically use GraphQL for more detailed movement tracking
        graphql_query = """
        query inventoryMovement($itemId: ID!, $startDate: DateTime!, $endDate: DateTime!) {
            inventoryItem(id: $itemId) {
                id
                sku
                inventoryHistoryUrl
                inventoryLevels(first: 10) {
                    edges {
                        node {
                            available
                            location {
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'itemId': f'gid://shopify/InventoryItem/{inventory_item_id}',
            'startDate': start_date.isoformat(),
            'endDate': end_date.isoformat()
        }
        
        result = self.client.graphql(graphql_query, variables)
        
        return result.get('data', {}).get('inventoryItem', {})
    
    def sync_inventory_with_external(self, external_inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync inventory with external system
        
        Args:
            external_inventory: List of external inventory data
        
        Returns:
            Sync results
        """
        synced = []
        failed = []
        
        for item in external_inventory:
            try:
                # Find inventory item by SKU
                # This would need proper SKU to inventory_item_id mapping
                inventory_item_id = item.get('inventory_item_id')
                location_id = item.get('location_id')
                available = item.get('available')
                
                if not all([inventory_item_id, location_id, available is not None]):
                    raise ValueError("Missing required fields")
                
                result = self.set_inventory_level(
                    location_id=location_id,
                    inventory_item_id=inventory_item_id,
                    available=available
                )
                synced.append(result)
                
            except Exception as e:
                logger.error(f"Failed to sync inventory item: {e}")
                failed.append({
                    'item': item,
                    'error': str(e)
                })
        
        return {
            'synced_count': len(synced),
            'failed_count': len(failed),
            'synced_items': synced,
            'failed_items': failed
        }
    
    def create_inventory_adjustment(self, reason: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create an inventory adjustment with reason tracking
        
        Args:
            reason: Reason for adjustment
            changes: List of inventory changes
        
        Returns:
            Adjustment results
        """
        adjustment_id = datetime.now().strftime('%Y%m%d%H%M%S')
        results = []
        
        for change in changes:
            try:
                result = self.adjust_inventory_level(
                    location_id=change['location_id'],
                    inventory_item_id=change['inventory_item_id'],
                    available_adjustment=change['adjustment']
                )
                
                # Add metadata
                result['adjustment_reason'] = reason
                result['adjustment_id'] = adjustment_id
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to adjust inventory: {e}")
                results.append({
                    'error': str(e),
                    'change': change
                })
        
        return {
            'adjustment_id': adjustment_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'changes': results
        }
    
    def reserve_inventory(self, inventory_item_id: int, location_id: int,
                         quantity: int, order_id: str = None) -> Dict[str, Any]:
        """
        Reserve inventory for an order
        
        Args:
            inventory_item_id: Inventory item ID
            location_id: Location ID
            quantity: Quantity to reserve
            order_id: Optional order ID for tracking
        
        Returns:
            Reservation details
        """
        # Shopify doesn't have built-in reservations, so we adjust available quantity
        # In a real implementation, you'd track reservations separately
        
        result = self.adjust_inventory_level(
            location_id=location_id,
            inventory_item_id=inventory_item_id,
            available_adjustment=-quantity
        )
        
        return {
            'reservation_id': f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'inventory_item_id': inventory_item_id,
            'location_id': location_id,
            'quantity_reserved': quantity,
            'order_id': order_id,
            'inventory_level': result
        }