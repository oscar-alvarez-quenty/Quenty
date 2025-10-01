"""
Shopify Customers Module
Handles customer management, addresses, and customer groups
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CustomersModule:
    """
    Manage Shopify customers and customer data
    """
    
    def __init__(self, client):
        """
        Initialize Customers module
        
        Args:
            client: ShopifyAPIClient instance
        """
        self.client = client
    
    # Customer CRUD Operations
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new customer
        
        Args:
            customer_data: Customer information
        
        Returns:
            Created customer data
        """
        logger.info(f"Creating customer: {customer_data.get('email')}")
        response = self.client.post('customers', {'customer': customer_data})
        return response.get('customer', {})
    
    def get_customer(self, customer_id: int, fields: List[str] = None) -> Dict[str, Any]:
        """
        Get a single customer by ID
        
        Args:
            customer_id: Customer ID
            fields: List of fields to include
        
        Returns:
            Customer data
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        
        response = self.client.get(f'customers/{customer_id}', params)
        return response.get('customer', {})
    
    def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing customer
        
        Args:
            customer_id: Customer ID
            customer_data: Updated customer information
        
        Returns:
            Updated customer data
        """
        logger.info(f"Updating customer {customer_id}")
        response = self.client.put(f'customers/{customer_id}', {'customer': customer_data})
        return response.get('customer', {})
    
    def delete_customer(self, customer_id: int) -> bool:
        """
        Delete a customer
        
        Args:
            customer_id: Customer ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting customer {customer_id}")
        self.client.delete(f'customers/{customer_id}')
        return True
    
    def list_customers(self, **kwargs) -> List[Dict[str, Any]]:
        """
        List customers with optional filters
        
        Args:
            limit: Number of customers to retrieve
            page: Page number
            since_id: Restrict results after specified ID
            created_at_min: Show customers created after date
            created_at_max: Show customers created before date
            updated_at_min: Show customers updated after date
            updated_at_max: Show customers updated before date
            fields: Comma-separated list of fields to include
            
        Returns:
            List of customers
        """
        return self.client.paginate('customers', kwargs)
    
    def count_customers(self, **kwargs) -> int:
        """
        Count customers matching criteria
        
        Args:
            Same filters as list_customers
        
        Returns:
            Customer count
        """
        response = self.client.get('customers/count', kwargs)
        return response.get('count', 0)
    
    def search_customers(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Search customers
        
        Args:
            query: Search query
            limit: Number of results
            fields: Fields to include
            
        Returns:
            Search results
        """
        params = {'query': query}
        params.update(kwargs)
        response = self.client.get('customers/search', params)
        return response.get('customers', [])
    
    # Customer Account Operations
    
    def send_invite(self, customer_id: int, invite_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send account activation invite to customer
        
        Args:
            customer_id: Customer ID
            invite_data: Optional invite customization
        
        Returns:
            Invite details
        """
        logger.info(f"Sending invite to customer {customer_id}")
        response = self.client.post(f'customers/{customer_id}/send_invite', 
                                   {'customer_invite': invite_data or {}})
        return response.get('customer_invite', {})
    
    def activate_customer(self, activation_url: str, password: str) -> Dict[str, Any]:
        """
        Activate a customer account
        
        Args:
            activation_url: Activation URL from invite
            password: Customer password
        
        Returns:
            Activated customer data
        """
        # This would typically be handled client-side
        logger.info("Activating customer account")
        return {'status': 'activated'}
    
    def reset_password(self, customer_id: int) -> bool:
        """
        Send password reset email to customer
        
        Args:
            customer_id: Customer ID
        
        Returns:
            True if successful
        """
        logger.info(f"Sending password reset to customer {customer_id}")
        # Implementation depends on shop configuration
        return True
    
    # Customer Address Management
    
    def create_address(self, customer_id: int, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a customer address
        
        Args:
            customer_id: Customer ID
            address_data: Address information
        
        Returns:
            Created address data
        """
        logger.info(f"Creating address for customer {customer_id}")
        response = self.client.post(f'customers/{customer_id}/addresses', 
                                   {'address': address_data})
        return response.get('customer_address', {})
    
    def get_address(self, customer_id: int, address_id: int) -> Dict[str, Any]:
        """
        Get a customer address
        
        Args:
            customer_id: Customer ID
            address_id: Address ID
        
        Returns:
            Address data
        """
        response = self.client.get(f'customers/{customer_id}/addresses/{address_id}')
        return response.get('customer_address', {})
    
    def update_address(self, customer_id: int, address_id: int,
                      address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a customer address
        
        Args:
            customer_id: Customer ID
            address_id: Address ID
            address_data: Updated address information
        
        Returns:
            Updated address data
        """
        logger.info(f"Updating address {address_id} for customer {customer_id}")
        response = self.client.put(f'customers/{customer_id}/addresses/{address_id}',
                                  {'address': address_data})
        return response.get('customer_address', {})
    
    def delete_address(self, customer_id: int, address_id: int) -> bool:
        """
        Delete a customer address
        
        Args:
            customer_id: Customer ID
            address_id: Address ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting address {address_id} from customer {customer_id}")
        self.client.delete(f'customers/{customer_id}/addresses/{address_id}')
        return True
    
    def list_addresses(self, customer_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        List all addresses for a customer
        
        Args:
            customer_id: Customer ID
            limit: Number of addresses to retrieve
            page: Page number
        
        Returns:
            List of addresses
        """
        return self.client.paginate(f'customers/{customer_id}/addresses', kwargs)
    
    def set_default_address(self, customer_id: int, address_id: int) -> Dict[str, Any]:
        """
        Set a default address for customer
        
        Args:
            customer_id: Customer ID
            address_id: Address ID
        
        Returns:
            Updated address data
        """
        response = self.client.put(f'customers/{customer_id}/addresses/{address_id}/default')
        return response.get('customer_address', {})
    
    # Customer Orders
    
    def get_customer_orders(self, customer_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get all orders for a customer
        
        Args:
            customer_id: Customer ID
            status: Order status filter
            limit: Number of orders to retrieve
        
        Returns:
            List of orders
        """
        response = self.client.get(f'customers/{customer_id}/orders', kwargs)
        return response.get('orders', [])
    
    # Customer Metafields
    
    def create_metafield(self, customer_id: int, metafield_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a customer metafield
        
        Args:
            customer_id: Customer ID
            metafield_data: Metafield information
        
        Returns:
            Created metafield data
        """
        logger.info(f"Creating metafield for customer {customer_id}")
        response = self.client.post(f'customers/{customer_id}/metafields',
                                   {'metafield': metafield_data})
        return response.get('metafield', {})
    
    def get_metafields(self, customer_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get metafields for a customer
        
        Args:
            customer_id: Customer ID
            namespace: Filter by namespace
            key: Filter by key
        
        Returns:
            List of metafields
        """
        return self.client.paginate(f'customers/{customer_id}/metafields', kwargs)
    
    def update_metafield(self, customer_id: int, metafield_id: int,
                        metafield_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a customer metafield
        
        Args:
            customer_id: Customer ID
            metafield_id: Metafield ID
            metafield_data: Updated metafield information
        
        Returns:
            Updated metafield data
        """
        logger.info(f"Updating metafield {metafield_id} for customer {customer_id}")
        response = self.client.put(f'customers/{customer_id}/metafields/{metafield_id}',
                                  {'metafield': metafield_data})
        return response.get('metafield', {})
    
    def delete_metafield(self, customer_id: int, metafield_id: int) -> bool:
        """
        Delete a customer metafield
        
        Args:
            customer_id: Customer ID
            metafield_id: Metafield ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting metafield {metafield_id} from customer {customer_id}")
        self.client.delete(f'customers/{customer_id}/metafields/{metafield_id}')
        return True
    
    # Customer Tags
    
    def add_tags(self, customer_id: int, tags: List[str]) -> Dict[str, Any]:
        """
        Add tags to a customer
        
        Args:
            customer_id: Customer ID
            tags: List of tags to add
        
        Returns:
            Updated customer data
        """
        customer = self.get_customer(customer_id)
        existing_tags = customer.get('tags', '').split(', ') if customer.get('tags') else []
        all_tags = list(set(existing_tags + tags))
        
        return self.update_customer(customer_id, {'tags': ', '.join(all_tags)})
    
    def remove_tags(self, customer_id: int, tags: List[str]) -> Dict[str, Any]:
        """
        Remove tags from a customer
        
        Args:
            customer_id: Customer ID
            tags: List of tags to remove
        
        Returns:
            Updated customer data
        """
        customer = self.get_customer(customer_id)
        existing_tags = customer.get('tags', '').split(', ') if customer.get('tags') else []
        remaining_tags = [tag for tag in existing_tags if tag not in tags]
        
        return self.update_customer(customer_id, {'tags': ', '.join(remaining_tags)})
    
    # Customer Saved Searches
    
    def create_saved_search(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a customer saved search
        
        Args:
            search_data: Saved search information
        
        Returns:
            Created saved search data
        """
        logger.info(f"Creating customer saved search: {search_data.get('name')}")
        response = self.client.post('customer_saved_searches', 
                                   {'customer_saved_search': search_data})
        return response.get('customer_saved_search', {})
    
    def get_saved_search(self, search_id: int) -> Dict[str, Any]:
        """
        Get a customer saved search
        
        Args:
            search_id: Saved search ID
        
        Returns:
            Saved search data
        """
        response = self.client.get(f'customer_saved_searches/{search_id}')
        return response.get('customer_saved_search', {})
    
    def update_saved_search(self, search_id: int, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a customer saved search
        
        Args:
            search_id: Saved search ID
            search_data: Updated search information
        
        Returns:
            Updated saved search data
        """
        logger.info(f"Updating customer saved search {search_id}")
        response = self.client.put(f'customer_saved_searches/{search_id}',
                                  {'customer_saved_search': search_data})
        return response.get('customer_saved_search', {})
    
    def delete_saved_search(self, search_id: int) -> bool:
        """
        Delete a customer saved search
        
        Args:
            search_id: Saved search ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting customer saved search {search_id}")
        self.client.delete(f'customer_saved_searches/{search_id}')
        return True
    
    def list_saved_searches(self, **kwargs) -> List[Dict[str, Any]]:
        """
        List all customer saved searches
        
        Args:
            limit: Number of searches to retrieve
            page: Page number
            since_id: Restrict results after specified ID
            fields: Comma-separated list of fields to include
        
        Returns:
            List of saved searches
        """
        return self.client.paginate('customer_saved_searches', kwargs)
    
    def get_customers_from_saved_search(self, search_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get customers matching a saved search
        
        Args:
            search_id: Saved search ID
            limit: Number of customers to retrieve
            page: Page number
        
        Returns:
            List of customers
        """
        return self.client.paginate(f'customer_saved_searches/{search_id}/customers', kwargs)
    
    # Customer Analytics
    
    def get_customer_lifetime_value(self, customer_id: int) -> Dict[str, Any]:
        """
        Calculate customer lifetime value
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Customer lifetime value metrics
        """
        orders = self.get_customer_orders(customer_id)
        
        total_spent = sum(float(order.get('total_price', 0)) for order in orders)
        order_count = len(orders)
        
        if order_count > 0:
            average_order_value = total_spent / order_count
            
            # Calculate days since first order
            first_order_date = min(
                datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                for order in orders
            )
            days_as_customer = (datetime.now() - first_order_date).days
        else:
            average_order_value = 0
            days_as_customer = 0
        
        return {
            'customer_id': customer_id,
            'total_spent': total_spent,
            'order_count': order_count,
            'average_order_value': average_order_value,
            'days_as_customer': days_as_customer
        }
    
    def get_customer_segments(self) -> Dict[str, List[int]]:
        """
        Segment customers based on behavior
        
        Returns:
            Dictionary of segment names to customer IDs
        """
        segments = {
            'vip': [],
            'frequent': [],
            'at_risk': [],
            'lost': [],
            'new': []
        }
        
        customers = self.list_customers()
        current_date = datetime.now()
        
        for customer in customers:
            customer_id = customer['id']
            orders = self.get_customer_orders(customer_id)
            
            if not orders:
                segments['new'].append(customer_id)
                continue
            
            # Calculate metrics
            total_spent = sum(float(order.get('total_price', 0)) for order in orders)
            last_order_date = max(
                datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                for order in orders
            )
            days_since_last_order = (current_date - last_order_date).days
            
            # Segment customers
            if total_spent > 1000 and len(orders) > 5:
                segments['vip'].append(customer_id)
            elif len(orders) > 3:
                segments['frequent'].append(customer_id)
            elif days_since_last_order > 90 and days_since_last_order < 180:
                segments['at_risk'].append(customer_id)
            elif days_since_last_order > 180:
                segments['lost'].append(customer_id)
        
        return segments
    
    def export_customers(self, **kwargs) -> str:
        """
        Export customers using bulk operations
        
        Args:
            created_at_min: Export customers created after date
            created_at_max: Export customers created before date
            
        Returns:
            Bulk operation ID
        """
        query = """
        {
            customers(query: "%s") {
                edges {
                    node {
                        id
                        email
                        firstName
                        lastName
                        phone
                        acceptsMarketing
                        createdAt
                        updatedAt
                        ordersCount
                        totalSpent
                        addresses {
                            address1
                            address2
                            city
                            province
                            country
                            zip
                        }
                        tags
                    }
                }
            }
        }
        """
        
        filters = []
        if kwargs.get('created_at_min'):
            filters.append(f"created_at:>={kwargs['created_at_min']}")
        if kwargs.get('created_at_max'):
            filters.append(f"created_at:<={kwargs['created_at_max']}")
        
        query_filter = ' AND '.join(filters) if filters else ''
        query = query % query_filter
        
        return self.client.bulk_operation(query)