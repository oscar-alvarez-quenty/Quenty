"""
WooCommerce REST API Client
Handles all interactions with WooCommerce stores
"""

import httpx
import hmac
import hashlib
import base64
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from urllib.parse import urlencode, quote
import structlog

logger = structlog.get_logger()


class WooCommerceClient:
    """
    WooCommerce REST API v3 client with OAuth 1.0a authentication
    Supports both HTTP and HTTPS connections
    """
    
    def __init__(
        self, 
        store_url: str, 
        consumer_key: str, 
        consumer_secret: str,
        version: str = "wc/v3",
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize WooCommerce client
        
        Args:
            store_url: The WooCommerce store URL (e.g., https://mystore.com)
            consumer_key: WooCommerce REST API consumer key
            consumer_secret: WooCommerce REST API consumer secret
            version: API version (default: wc/v3)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.store_url = store_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.version = version
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Determine if OAuth is needed (for HTTP connections)
        self.use_oauth = not self.store_url.startswith('https')
        
        # Base API URL
        self.api_url = f"{self.store_url}/wp-json/{self.version}"
        
        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            verify=verify_ssl,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=100)
        )
        
        logger.info(
            "woocommerce_client_initialized",
            store_url=self.store_url,
            api_version=version
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close HTTP client connections"""
        await self.client.aclose()
    
    def _get_auth_params(self) -> Dict[str, str]:
        """
        Get authentication parameters for the request
        For HTTPS: Use basic auth with consumer key/secret
        For HTTP: Use OAuth 1.0a (not recommended for production)
        """
        if not self.use_oauth:
            # HTTPS - use basic auth
            return {}
        else:
            # HTTP - use OAuth 1.0a (simplified version)
            import time
            import random
            
            oauth_params = {
                'oauth_consumer_key': self.consumer_key,
                'oauth_timestamp': str(int(time.time())),
                'oauth_nonce': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32)),
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_version': '1.0'
            }
            return oauth_params
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for HTTPS requests"""
        if not self.use_oauth:
            # Basic authentication for HTTPS
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return {'Authorization': f'Basic {encoded}'}
        return {}
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make an authenticated request to WooCommerce API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., 'orders', 'products/123')
            params: Query parameters
            data: Request body data
            
        Returns:
            HTTP response object
        """
        url = f"{self.api_url}/{endpoint}"
        
        # Add authentication
        headers = self._get_auth_headers()
        if self.use_oauth:
            # Add OAuth parameters to URL for HTTP
            oauth_params = self._get_auth_params()
            if params:
                params.update(oauth_params)
            else:
                params = oauth_params
        
        # Log request
        logger.debug(
            "woocommerce_api_request",
            method=method,
            endpoint=endpoint,
            url=url
        )
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                **kwargs
            )
            
            # Log response
            logger.debug(
                "woocommerce_api_response",
                status_code=response.status_code,
                endpoint=endpoint
            )
            
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "woocommerce_api_error",
                status_code=e.response.status_code,
                error=e.response.text,
                endpoint=endpoint
            )
            raise WooCommerceAPIError(
                f"WooCommerce API error: {e.response.status_code}",
                status_code=e.response.status_code,
                response=e.response.text
            )
        except Exception as e:
            logger.error(
                "woocommerce_request_error",
                error=str(e),
                endpoint=endpoint
            )
            raise
    
    # ============= Orders Management =============
    
    async def get_orders(
        self,
        status: Optional[str] = None,
        per_page: int = 10,
        page: int = 1,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
        customer: Optional[int] = None,
        product: Optional[int] = None,
        orderby: str = "date",
        order: str = "desc"
    ) -> List[Dict]:
        """
        Retrieve orders from WooCommerce
        
        Args:
            status: Filter by order status (pending, processing, completed, etc.)
            per_page: Number of orders per page
            page: Page number
            after: Orders after this date
            before: Orders before this date
            customer: Filter by customer ID
            product: Filter by product ID
            orderby: Sort orders by (date, id, include, title, slug)
            order: Sort order (asc, desc)
            
        Returns:
            List of order objects
        """
        params = {
            'per_page': per_page,
            'page': page,
            'orderby': orderby,
            'order': order
        }
        
        if status:
            params['status'] = status
        if after:
            params['after'] = after.isoformat()
        if before:
            params['before'] = before.isoformat()
        if customer:
            params['customer'] = customer
        if product:
            params['product'] = product
        
        response = await self._request('GET', 'orders', params=params)
        return response.json()
    
    async def get_order(self, order_id: int) -> Dict:
        """
        Get a specific order by ID
        
        Args:
            order_id: The order ID
            
        Returns:
            Order object
        """
        response = await self._request('GET', f'orders/{order_id}')
        return response.json()
    
    async def create_order(self, order_data: Dict) -> Dict:
        """
        Create a new order in WooCommerce
        
        Args:
            order_data: Order data including customer, products, shipping, etc.
            
        Returns:
            Created order object
        """
        response = await self._request('POST', 'orders', data=order_data)
        return response.json()
    
    async def update_order(self, order_id: int, order_data: Dict) -> Dict:
        """
        Update an existing order
        
        Args:
            order_id: The order ID to update
            order_data: Updated order data
            
        Returns:
            Updated order object
        """
        response = await self._request('PUT', f'orders/{order_id}', data=order_data)
        return response.json()
    
    async def update_order_status(
        self,
        order_id: int,
        status: str,
        note: Optional[str] = None
    ) -> Dict:
        """
        Update order status
        
        Args:
            order_id: The order ID
            status: New status (pending, processing, on-hold, completed, cancelled, refunded, failed)
            note: Optional status change note
            
        Returns:
            Updated order object
        """
        data = {'status': status}
        if note:
            data['customer_note'] = note
        
        return await self.update_order(order_id, data)
    
    async def delete_order(self, order_id: int, force: bool = False) -> Dict:
        """
        Delete an order
        
        Args:
            order_id: The order ID to delete
            force: Whether to permanently delete (True) or trash (False)
            
        Returns:
            Deleted order object
        """
        params = {'force': force}
        response = await self._request('DELETE', f'orders/{order_id}', params=params)
        return response.json()
    
    async def add_order_note(
        self,
        order_id: int,
        note: str,
        customer_note: bool = False
    ) -> Dict:
        """
        Add a note to an order
        
        Args:
            order_id: The order ID
            note: The note content
            customer_note: Whether this note is for customer (True) or internal (False)
            
        Returns:
            Created note object
        """
        data = {
            'note': note,
            'customer_note': customer_note
        }
        response = await self._request('POST', f'orders/{order_id}/notes', data=data)
        return response.json()
    
    # ============= Products Management =============
    
    async def get_products(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None,
        category: Optional[int] = None,
        tag: Optional[int] = None,
        status: str = "publish",
        type: Optional[str] = None,
        sku: Optional[str] = None,
        featured: Optional[bool] = None,
        in_stock: Optional[bool] = None,
        on_sale: Optional[bool] = None,
        orderby: str = "date",
        order: str = "desc"
    ) -> List[Dict]:
        """
        Retrieve products from WooCommerce
        
        Args:
            per_page: Number of products per page
            page: Page number
            search: Search products
            category: Filter by category ID
            tag: Filter by tag ID
            status: Product status (publish, draft, pending)
            type: Product type (simple, grouped, external, variable)
            sku: Filter by SKU
            featured: Filter featured products
            in_stock: Filter in-stock products
            on_sale: Filter on-sale products
            orderby: Sort field
            order: Sort order
            
        Returns:
            List of product objects
        """
        params = {
            'per_page': per_page,
            'page': page,
            'status': status,
            'orderby': orderby,
            'order': order
        }
        
        if search:
            params['search'] = search
        if category:
            params['category'] = category
        if tag:
            params['tag'] = tag
        if type:
            params['type'] = type
        if sku:
            params['sku'] = sku
        if featured is not None:
            params['featured'] = featured
        if in_stock is not None:
            params['in_stock'] = in_stock
        if on_sale is not None:
            params['on_sale'] = on_sale
        
        response = await self._request('GET', 'products', params=params)
        return response.json()
    
    async def get_product(self, product_id: int) -> Dict:
        """
        Get a specific product by ID
        
        Args:
            product_id: The product ID
            
        Returns:
            Product object
        """
        response = await self._request('GET', f'products/{product_id}')
        return response.json()
    
    async def create_product(self, product_data: Dict) -> Dict:
        """
        Create a new product
        
        Args:
            product_data: Product data
            
        Returns:
            Created product object
        """
        response = await self._request('POST', 'products', data=product_data)
        return response.json()
    
    async def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """
        Update a product
        
        Args:
            product_id: The product ID
            product_data: Updated product data
            
        Returns:
            Updated product object
        """
        response = await self._request('PUT', f'products/{product_id}', data=product_data)
        return response.json()
    
    async def update_stock(
        self,
        product_id: int,
        quantity: int,
        manage_stock: bool = True
    ) -> Dict:
        """
        Update product stock quantity
        
        Args:
            product_id: The product ID
            quantity: New stock quantity
            manage_stock: Whether to manage stock
            
        Returns:
            Updated product object
        """
        data = {
            'stock_quantity': quantity,
            'manage_stock': manage_stock,
            'in_stock': quantity > 0
        }
        return await self.update_product(product_id, data)
    
    async def batch_update_products(self, updates: List[Dict]) -> Dict:
        """
        Batch update multiple products
        
        Args:
            updates: List of product updates
            
        Returns:
            Batch operation result
        """
        data = {'update': updates}
        response = await self._request('POST', 'products/batch', data=data)
        return response.json()
    
    # ============= Customers Management =============
    
    async def get_customers(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        orderby: str = "registered_date",
        order: str = "desc"
    ) -> List[Dict]:
        """
        Retrieve customers from WooCommerce
        
        Args:
            per_page: Number of customers per page
            page: Page number
            search: Search customers
            email: Filter by email
            role: Filter by user role
            orderby: Sort field
            order: Sort order
            
        Returns:
            List of customer objects
        """
        params = {
            'per_page': per_page,
            'page': page,
            'orderby': orderby,
            'order': order
        }
        
        if search:
            params['search'] = search
        if email:
            params['email'] = email
        if role:
            params['role'] = role
        
        response = await self._request('GET', 'customers', params=params)
        return response.json()
    
    async def get_customer(self, customer_id: int) -> Dict:
        """
        Get a specific customer by ID
        
        Args:
            customer_id: The customer ID
            
        Returns:
            Customer object
        """
        response = await self._request('GET', f'customers/{customer_id}')
        return response.json()
    
    async def create_customer(self, customer_data: Dict) -> Dict:
        """
        Create a new customer
        
        Args:
            customer_data: Customer data including email, name, billing/shipping addresses
            
        Returns:
            Created customer object
        """
        response = await self._request('POST', 'customers', data=customer_data)
        return response.json()
    
    async def update_customer(self, customer_id: int, customer_data: Dict) -> Dict:
        """
        Update a customer
        
        Args:
            customer_id: The customer ID
            customer_data: Updated customer data
            
        Returns:
            Updated customer object
        """
        response = await self._request('PUT', f'customers/{customer_id}', data=customer_data)
        return response.json()
    
    # ============= Shipping Methods =============
    
    async def get_shipping_zones(self) -> List[Dict]:
        """
        Get all shipping zones
        
        Returns:
            List of shipping zone objects
        """
        response = await self._request('GET', 'shipping/zones')
        return response.json()
    
    async def get_shipping_zone(self, zone_id: int) -> Dict:
        """
        Get a specific shipping zone
        
        Args:
            zone_id: The shipping zone ID
            
        Returns:
            Shipping zone object
        """
        response = await self._request('GET', f'shipping/zones/{zone_id}')
        return response.json()
    
    async def get_shipping_methods(self, zone_id: int) -> List[Dict]:
        """
        Get shipping methods for a zone
        
        Args:
            zone_id: The shipping zone ID
            
        Returns:
            List of shipping method objects
        """
        response = await self._request('GET', f'shipping/zones/{zone_id}/methods')
        return response.json()
    
    async def update_shipping_method(
        self,
        zone_id: int,
        method_id: int,
        settings: Dict
    ) -> Dict:
        """
        Update a shipping method
        
        Args:
            zone_id: The shipping zone ID
            method_id: The shipping method ID
            settings: Updated settings
            
        Returns:
            Updated shipping method object
        """
        response = await self._request(
            'PUT',
            f'shipping/zones/{zone_id}/methods/{method_id}',
            data=settings
        )
        return response.json()
    
    # ============= Coupons Management =============
    
    async def get_coupons(
        self,
        per_page: int = 10,
        page: int = 1,
        code: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve coupons
        
        Args:
            per_page: Number of coupons per page
            page: Page number
            code: Filter by coupon code
            
        Returns:
            List of coupon objects
        """
        params = {
            'per_page': per_page,
            'page': page
        }
        
        if code:
            params['code'] = code
        
        response = await self._request('GET', 'coupons', params=params)
        return response.json()
    
    async def create_coupon(self, coupon_data: Dict) -> Dict:
        """
        Create a new coupon
        
        Args:
            coupon_data: Coupon data
            
        Returns:
            Created coupon object
        """
        response = await self._request('POST', 'coupons', data=coupon_data)
        return response.json()
    
    # ============= Webhooks Management =============
    
    async def get_webhooks(self) -> List[Dict]:
        """
        Get all webhooks
        
        Returns:
            List of webhook objects
        """
        response = await self._request('GET', 'webhooks')
        return response.json()
    
    async def create_webhook(
        self,
        name: str,
        topic: str,
        delivery_url: str,
        secret: Optional[str] = None,
        status: str = "active"
    ) -> Dict:
        """
        Create a new webhook
        
        Args:
            name: Webhook name
            topic: Event topic (e.g., 'order.created', 'order.updated')
            delivery_url: URL to deliver the webhook
            secret: Secret key for payload verification
            status: Webhook status (active, paused, disabled)
            
        Returns:
            Created webhook object
        """
        data = {
            'name': name,
            'topic': topic,
            'delivery_url': delivery_url,
            'status': status
        }
        
        if secret:
            data['secret'] = secret
        
        response = await self._request('POST', 'webhooks', data=data)
        return response.json()
    
    async def update_webhook(self, webhook_id: int, webhook_data: Dict) -> Dict:
        """
        Update a webhook
        
        Args:
            webhook_id: The webhook ID
            webhook_data: Updated webhook data
            
        Returns:
            Updated webhook object
        """
        response = await self._request('PUT', f'webhooks/{webhook_id}', data=webhook_data)
        return response.json()
    
    async def delete_webhook(self, webhook_id: int) -> Dict:
        """
        Delete a webhook
        
        Args:
            webhook_id: The webhook ID
            
        Returns:
            Deleted webhook object
        """
        response = await self._request('DELETE', f'webhooks/{webhook_id}')
        return response.json()
    
    # ============= Reports & Analytics =============
    
    async def get_sales_report(
        self,
        period: str = "week",
        date_min: Optional[str] = None,
        date_max: Optional[str] = None
    ) -> Dict:
        """
        Get sales report
        
        Args:
            period: Report period (week, month, last_month, year)
            date_min: Start date (YYYY-MM-DD)
            date_max: End date (YYYY-MM-DD)
            
        Returns:
            Sales report data
        """
        params = {'period': period}
        
        if date_min:
            params['date_min'] = date_min
        if date_max:
            params['date_max'] = date_max
        
        response = await self._request('GET', 'reports/sales', params=params)
        return response.json()
    
    async def get_top_sellers_report(
        self,
        period: str = "week",
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top sellers report
        
        Args:
            period: Report period
            limit: Number of products to return
            
        Returns:
            Top selling products
        """
        params = {
            'period': period,
            'limit': limit
        }
        
        response = await self._request('GET', 'reports/top_sellers', params=params)
        return response.json()
    
    # ============= System Status =============
    
    async def get_system_status(self) -> Dict:
        """
        Get WooCommerce system status
        
        Returns:
            System status information
        """
        response = await self._request('GET', 'system_status')
        return response.json()
    
    async def get_payment_gateways(self) -> List[Dict]:
        """
        Get available payment gateways
        
        Returns:
            List of payment gateway objects
        """
        response = await self._request('GET', 'payment_gateways')
        return response.json()
    
    async def get_tax_rates(self) -> List[Dict]:
        """
        Get tax rates
        
        Returns:
            List of tax rate objects
        """
        response = await self._request('GET', 'taxes')
        return response.json()
    
    # ============= Utility Methods =============
    
    async def verify_credentials(self) -> bool:
        """
        Verify that the API credentials are valid
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            await self.get_system_status()
            return True
        except Exception as e:
            logger.error(
                "woocommerce_credential_verification_failed",
                error=str(e)
            )
            return False
    
    async def get_store_info(self) -> Dict:
        """
        Get basic store information
        
        Returns:
            Store information including name, URL, WooCommerce version
        """
        system_status = await self.get_system_status()
        
        return {
            'store_url': self.store_url,
            'woocommerce_version': system_status.get('environment', {}).get('version'),
            'wordpress_version': system_status.get('environment', {}).get('wp_version'),
            'timezone': system_status.get('settings', {}).get('timezone'),
            'currency': system_status.get('settings', {}).get('currency'),
            'currency_symbol': system_status.get('settings', {}).get('currency_symbol')
        }
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate WooCommerce webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header (X-WC-Webhook-Signature)
            secret: Webhook secret
            
        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return hmac.compare_digest(signature, expected_signature)


class WooCommerceAPIError(Exception):
    """Custom exception for WooCommerce API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


# Export classes
__all__ = ['WooCommerceClient', 'WooCommerceAPIError']