"""
Shopify Orders Module
Handles order management, fulfillment, refunds, and transactions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class OrdersModule:
    """
    Manage Shopify orders, fulfillments, and transactions
    """
    
    def __init__(self, client):
        """
        Initialize Orders module
        
        Args:
            client: ShopifyAPIClient instance
        """
        self.client = client
    
    # Order CRUD Operations
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order
        
        Args:
            order_data: Order information including line items, customer, etc.
        
        Returns:
            Created order data
        """
        logger.info(f"Creating order for customer {order_data.get('customer', {}).get('email')}")
        response = self.client.post('orders', {'order': order_data})
        return response.get('order', {})
    
    def get_order(self, order_id: int, fields: List[str] = None) -> Dict[str, Any]:
        """
        Get a single order by ID
        
        Args:
            order_id: Order ID
            fields: List of fields to include
        
        Returns:
            Order data
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        
        response = self.client.get(f'orders/{order_id}', params)
        return response.get('order', {})
    
    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order
        
        Args:
            order_id: Order ID
            order_data: Updated order information
        
        Returns:
            Updated order data
        """
        logger.info(f"Updating order {order_id}")
        response = self.client.put(f'orders/{order_id}', {'order': order_data})
        return response.get('order', {})
    
    def cancel_order(self, order_id: int, **kwargs) -> Dict[str, Any]:
        """
        Cancel an order
        
        Args:
            order_id: Order ID
            amount: Amount to refund
            currency: Currency for refund
            restock: Whether to restock items
            reason: Cancellation reason
            email: Whether to send cancellation email
            note: Internal note about cancellation
        
        Returns:
            Cancelled order data
        """
        logger.info(f"Cancelling order {order_id}")
        response = self.client.post(f'orders/{order_id}/cancel', kwargs)
        return response.get('order', {})
    
    def close_order(self, order_id: int) -> Dict[str, Any]:
        """
        Close an order
        
        Args:
            order_id: Order ID
        
        Returns:
            Closed order data
        """
        logger.info(f"Closing order {order_id}")
        response = self.client.post(f'orders/{order_id}/close')
        return response.get('order', {})
    
    def reopen_order(self, order_id: int) -> Dict[str, Any]:
        """
        Reopen a closed order
        
        Args:
            order_id: Order ID
        
        Returns:
            Reopened order data
        """
        logger.info(f"Reopening order {order_id}")
        response = self.client.post(f'orders/{order_id}/open')
        return response.get('order', {})
    
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order
        
        Args:
            order_id: Order ID
        
        Returns:
            True if successful
        """
        logger.info(f"Deleting order {order_id}")
        self.client.delete(f'orders/{order_id}')
        return True
    
    def list_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """
        List orders with optional filters
        
        Args:
            limit: Number of orders to retrieve
            page: Page number
            since_id: Restrict results after specified ID
            created_at_min: Show orders created after date
            created_at_max: Show orders created before date
            updated_at_min: Show orders updated after date
            updated_at_max: Show orders updated before date
            processed_at_min: Show orders processed after date
            processed_at_max: Show orders processed before date
            status: Filter by status (open, closed, cancelled, any)
            financial_status: Filter by financial status
            fulfillment_status: Filter by fulfillment status
            fields: Comma-separated list of fields to include
            
        Returns:
            List of orders
        """
        return self.client.paginate('orders', kwargs)
    
    def count_orders(self, **kwargs) -> int:
        """
        Count orders matching criteria
        
        Args:
            Same filters as list_orders
        
        Returns:
            Order count
        """
        response = self.client.get('orders/count', kwargs)
        return response.get('count', 0)
    
    # Fulfillment Operations
    
    def create_fulfillment(self, order_id: int, fulfillment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a fulfillment for an order
        
        Args:
            order_id: Order ID
            fulfillment_data: Fulfillment information
        
        Returns:
            Created fulfillment data
        """
        logger.info(f"Creating fulfillment for order {order_id}")
        response = self.client.post(f'orders/{order_id}/fulfillments', 
                                   {'fulfillment': fulfillment_data})
        return response.get('fulfillment', {})
    
    def get_fulfillment(self, order_id: int, fulfillment_id: int) -> Dict[str, Any]:
        """
        Get a single fulfillment
        
        Args:
            order_id: Order ID
            fulfillment_id: Fulfillment ID
        
        Returns:
            Fulfillment data
        """
        response = self.client.get(f'orders/{order_id}/fulfillments/{fulfillment_id}')
        return response.get('fulfillment', {})
    
    def update_fulfillment(self, order_id: int, fulfillment_id: int,
                          fulfillment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a fulfillment
        
        Args:
            order_id: Order ID
            fulfillment_id: Fulfillment ID
            fulfillment_data: Updated fulfillment information
        
        Returns:
            Updated fulfillment data
        """
        logger.info(f"Updating fulfillment {fulfillment_id} for order {order_id}")
        response = self.client.put(f'orders/{order_id}/fulfillments/{fulfillment_id}',
                                  {'fulfillment': fulfillment_data})
        return response.get('fulfillment', {})
    
    def cancel_fulfillment(self, order_id: int, fulfillment_id: int) -> Dict[str, Any]:
        """
        Cancel a fulfillment
        
        Args:
            order_id: Order ID
            fulfillment_id: Fulfillment ID
        
        Returns:
            Cancelled fulfillment data
        """
        logger.info(f"Cancelling fulfillment {fulfillment_id} for order {order_id}")
        response = self.client.post(f'orders/{order_id}/fulfillments/{fulfillment_id}/cancel')
        return response.get('fulfillment', {})
    
    def complete_fulfillment(self, order_id: int, fulfillment_id: int) -> Dict[str, Any]:
        """
        Complete a fulfillment
        
        Args:
            order_id: Order ID
            fulfillment_id: Fulfillment ID
        
        Returns:
            Completed fulfillment data
        """
        logger.info(f"Completing fulfillment {fulfillment_id} for order {order_id}")
        response = self.client.post(f'orders/{order_id}/fulfillments/{fulfillment_id}/complete')
        return response.get('fulfillment', {})
    
    def list_fulfillments(self, order_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        List all fulfillments for an order
        
        Args:
            order_id: Order ID
            created_at_min: Show fulfillments created after date
            created_at_max: Show fulfillments created before date
            updated_at_min: Show fulfillments updated after date
            updated_at_max: Show fulfillments updated before date
            fields: Comma-separated list of fields to include
        
        Returns:
            List of fulfillments
        """
        return self.client.paginate(f'orders/{order_id}/fulfillments', kwargs)
    
    def count_fulfillments(self, order_id: int) -> int:
        """
        Count fulfillments for an order
        
        Args:
            order_id: Order ID
        
        Returns:
            Fulfillment count
        """
        response = self.client.get(f'orders/{order_id}/fulfillments/count')
        return response.get('count', 0)
    
    # Refund Operations
    
    def create_refund(self, order_id: int, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a refund for an order
        
        Args:
            order_id: Order ID
            refund_data: Refund information
        
        Returns:
            Created refund data
        """
        logger.info(f"Creating refund for order {order_id}")
        response = self.client.post(f'orders/{order_id}/refunds', {'refund': refund_data})
        return response.get('refund', {})
    
    def get_refund(self, order_id: int, refund_id: int) -> Dict[str, Any]:
        """
        Get a single refund
        
        Args:
            order_id: Order ID
            refund_id: Refund ID
        
        Returns:
            Refund data
        """
        response = self.client.get(f'orders/{order_id}/refunds/{refund_id}')
        return response.get('refund', {})
    
    def list_refunds(self, order_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        List all refunds for an order
        
        Args:
            order_id: Order ID
            fields: Comma-separated list of fields to include
        
        Returns:
            List of refunds
        """
        return self.client.paginate(f'orders/{order_id}/refunds', kwargs)
    
    def calculate_refund(self, order_id: int, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate refund without creating it
        
        Args:
            order_id: Order ID
            refund_data: Refund calculation data
        
        Returns:
            Calculated refund details
        """
        response = self.client.post(f'orders/{order_id}/refunds/calculate', 
                                   {'refund': refund_data})
        return response.get('refund', {})
    
    # Transaction Operations
    
    def create_transaction(self, order_id: int, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a transaction for an order
        
        Args:
            order_id: Order ID
            transaction_data: Transaction information
        
        Returns:
            Created transaction data
        """
        logger.info(f"Creating transaction for order {order_id}")
        response = self.client.post(f'orders/{order_id}/transactions', 
                                   {'transaction': transaction_data})
        return response.get('transaction', {})
    
    def get_transaction(self, order_id: int, transaction_id: int) -> Dict[str, Any]:
        """
        Get a single transaction
        
        Args:
            order_id: Order ID
            transaction_id: Transaction ID
        
        Returns:
            Transaction data
        """
        response = self.client.get(f'orders/{order_id}/transactions/{transaction_id}')
        return response.get('transaction', {})
    
    def list_transactions(self, order_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        List all transactions for an order
        
        Args:
            order_id: Order ID
            since_id: Restrict results after specified ID
            fields: Comma-separated list of fields to include
        
        Returns:
            List of transactions
        """
        return self.client.paginate(f'orders/{order_id}/transactions', kwargs)
    
    def count_transactions(self, order_id: int) -> int:
        """
        Count transactions for an order
        
        Args:
            order_id: Order ID
        
        Returns:
            Transaction count
        """
        response = self.client.get(f'orders/{order_id}/transactions/count')
        return response.get('count', 0)
    
    # Risk Analysis
    
    def get_order_risks(self, order_id: int) -> List[Dict[str, Any]]:
        """
        Get risk analysis for an order
        
        Args:
            order_id: Order ID
        
        Returns:
            List of risk assessments
        """
        response = self.client.get(f'orders/{order_id}/risks')
        return response.get('risks', [])
    
    def create_order_risk(self, order_id: int, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a risk assessment for an order
        
        Args:
            order_id: Order ID
            risk_data: Risk information
        
        Returns:
            Created risk assessment
        """
        response = self.client.post(f'orders/{order_id}/risks', {'risk': risk_data})
        return response.get('risk', {})
    
    def update_order_risk(self, order_id: int, risk_id: int, 
                         risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a risk assessment
        
        Args:
            order_id: Order ID
            risk_id: Risk ID
            risk_data: Updated risk information
        
        Returns:
            Updated risk assessment
        """
        response = self.client.put(f'orders/{order_id}/risks/{risk_id}', {'risk': risk_data})
        return response.get('risk', {})
    
    def delete_order_risk(self, order_id: int, risk_id: int) -> bool:
        """
        Delete a risk assessment
        
        Args:
            order_id: Order ID
            risk_id: Risk ID
        
        Returns:
            True if successful
        """
        self.client.delete(f'orders/{order_id}/risks/{risk_id}')
        return True
    
    # Order Events
    
    def get_order_events(self, order_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get events for an order
        
        Args:
            order_id: Order ID
            limit: Number of events to retrieve
            page: Page number
            since_id: Restrict results after specified ID
            created_at_min: Show events created after date
            created_at_max: Show events created before date
            filter: Event type filter
            verb: Event verb filter
            
        Returns:
            List of events
        """
        return self.client.paginate(f'orders/{order_id}/events', kwargs)
    
    # Bulk Operations
    
    def bulk_fulfill_orders(self, fulfillments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk fulfill multiple orders
        
        Args:
            fulfillments: List of fulfillment data with order_id
        
        Returns:
            List of created fulfillments
        """
        results = []
        for fulfillment in fulfillments:
            try:
                order_id = fulfillment.pop('order_id')
                result = self.create_fulfillment(order_id, fulfillment)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to fulfill order {fulfillment.get('order_id')}: {e}")
                results.append({'error': str(e), 'order_id': fulfillment.get('order_id')})
        
        return results
    
    def export_orders(self, **kwargs) -> str:
        """
        Export orders using bulk operations
        
        Args:
            status: Order status filter
            created_at_min: Export orders created after date
            created_at_max: Export orders created before date
            
        Returns:
            Bulk operation ID
        """
        query = """
        {
            orders(query: "%s") {
                edges {
                    node {
                        id
                        name
                        email
                        createdAt
                        updatedAt
                        cancelledAt
                        closedAt
                        processedAt
                        customer {
                            id
                            email
                            firstName
                            lastName
                        }
                        totalPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }
                        lineItems {
                            edges {
                                node {
                                    title
                                    quantity
                                    variant {
                                        id
                                        sku
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        filters = []
        if kwargs.get('status'):
            filters.append(f"status:{kwargs['status']}")
        if kwargs.get('created_at_min'):
            filters.append(f"created_at:>={kwargs['created_at_min']}")
        if kwargs.get('created_at_max'):
            filters.append(f"created_at:<={kwargs['created_at_max']}")
        
        query_filter = ' AND '.join(filters) if filters else ''
        query = query % query_filter
        
        return self.client.bulk_operation(query)
    
    # Analytics
    
    def get_order_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get order metrics for a date range
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            Order metrics
        """
        orders = self.list_orders(
            created_at_min=start_date.isoformat(),
            created_at_max=end_date.isoformat()
        )
        
        total_revenue = Decimal('0')
        total_orders = len(orders)
        fulfilled_orders = 0
        cancelled_orders = 0
        
        for order in orders:
            total_revenue += Decimal(order.get('total_price', '0'))
            
            if order.get('fulfillment_status') == 'fulfilled':
                fulfilled_orders += 1
            
            if order.get('cancelled_at'):
                cancelled_orders += 1
        
        return {
            'total_orders': total_orders,
            'total_revenue': str(total_revenue),
            'average_order_value': str(total_revenue / total_orders) if total_orders > 0 else '0',
            'fulfilled_orders': fulfilled_orders,
            'cancelled_orders': cancelled_orders,
            'fulfillment_rate': fulfilled_orders / total_orders if total_orders > 0 else 0,
            'cancellation_rate': cancelled_orders / total_orders if total_orders > 0 else 0
        }
    
    def get_top_selling_products(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get top selling products
        
        Args:
            limit: Number of products to return
            days: Number of days to analyze
        
        Returns:
            List of top selling products
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        orders = self.list_orders(
            created_at_min=start_date.isoformat(),
            created_at_max=end_date.isoformat(),
            status='any'
        )
        
        product_sales = {}
        
        for order in orders:
            for line_item in order.get('line_items', []):
                product_id = line_item.get('product_id')
                if product_id:
                    if product_id not in product_sales:
                        product_sales[product_id] = {
                            'product_id': product_id,
                            'title': line_item.get('title'),
                            'quantity_sold': 0,
                            'total_revenue': Decimal('0')
                        }
                    
                    product_sales[product_id]['quantity_sold'] += line_item.get('quantity', 0)
                    product_sales[product_id]['total_revenue'] += Decimal(line_item.get('price', '0')) * line_item.get('quantity', 0)
        
        # Sort by quantity sold
        top_products = sorted(
            product_sales.values(),
            key=lambda x: x['quantity_sold'],
            reverse=True
        )[:limit]
        
        # Convert Decimal to string for JSON serialization
        for product in top_products:
            product['total_revenue'] = str(product['total_revenue'])
        
        return top_products