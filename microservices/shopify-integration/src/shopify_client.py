"""
Shopify API Client with authentication and rate limiting
"""
import time
import hashlib
import hmac
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode
import logging
from functools import wraps
import json

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for Shopify API calls"""
    
    def __init__(self, calls_per_second: float = 2.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
        self.bucket_size = 40  # Shopify's bucket size
        self.available_calls = 40
        self.last_refill = time.time()
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        
        # Refill bucket (2 calls per second)
        time_passed = current_time - self.last_refill
        calls_to_add = time_passed * self.calls_per_second
        self.available_calls = min(self.bucket_size, self.available_calls + calls_to_add)
        self.last_refill = current_time
        
        # Wait if no calls available
        if self.available_calls < 1:
            wait_time = (1 - self.available_calls) / self.calls_per_second
            logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            self.available_calls = 1
        
        self.available_calls -= 1
        self.last_call = current_time


def rate_limited(func):
    """Decorator to apply rate limiting to API calls"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.rate_limiter.wait_if_needed()
        return func(self, *args, **kwargs)
    return wrapper


class ShopifyAPIClient:
    """
    Shopify API Client for REST Admin API and GraphQL API
    Supports OAuth 2.0 and private app authentication
    """
    
    API_VERSION = "2024-01"
    GRAPHQL_VERSION = "2024-01"
    
    def __init__(self, shop_domain: str, access_token: str = None, 
                 api_key: str = None, api_secret: str = None,
                 private_app: bool = False):
        """
        Initialize Shopify API Client
        
        Args:
            shop_domain: The shop's domain (e.g., 'myshop.myshopify.com')
            access_token: OAuth access token or private app password
            api_key: API key for OAuth or private app
            api_secret: API secret for OAuth validation
            private_app: Whether this is a private app
        """
        self.shop_domain = shop_domain.replace('https://', '').replace('http://', '')
        self.access_token = access_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.private_app = private_app
        
        # Base URLs
        self.base_url = f"https://{self.shop_domain}/admin/api/{self.API_VERSION}"
        self.graphql_url = f"https://{self.shop_domain}/admin/api/{self.GRAPHQL_VERSION}/graphql.json"
        
        # Rate limiter
        self.rate_limiter = RateLimiter()
        
        # Session
        self.session = requests.Session()
        self._setup_authentication()
        
        # API call metrics
        self.api_calls_made = 0
        self.api_calls_remaining = None
        
    def _setup_authentication(self):
        """Setup authentication headers"""
        if self.private_app and self.api_key and self.access_token:
            # Private app uses basic auth
            credentials = f"{self.api_key}:{self.access_token}"
            encoded = base64.b64encode(credentials.encode()).decode()
            self.session.headers.update({
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json'
            })
        elif self.access_token:
            # OAuth uses bearer token
            self.session.headers.update({
                'X-Shopify-Access-Token': self.access_token,
                'Content-Type': 'application/json'
            })
    
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """
        Verify webhook authenticity
        
        Args:
            data: Raw request body
            hmac_header: X-Shopify-Hmac-Sha256 header value
        
        Returns:
            True if webhook is authentic
        """
        if not self.api_secret:
            logger.warning("API secret not set, cannot verify webhook")
            return False
        
        calculated_hmac = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(calculated_hmac, hmac_header)
    
    def verify_request(self, query_params: Dict[str, str]) -> bool:
        """
        Verify request from Shopify (OAuth callback, app proxy, etc.)
        
        Args:
            query_params: Query parameters from request
        
        Returns:
            True if request is authentic
        """
        if not self.api_secret:
            logger.warning("API secret not set, cannot verify request")
            return False
        
        # Get the hmac
        hmac_to_verify = query_params.pop('hmac', None)
        if not hmac_to_verify:
            return False
        
        # Create query string
        encoded_params = urlencode(sorted(query_params.items()))
        
        # Calculate hmac
        calculated_hmac = hmac.new(
            self.api_secret.encode('utf-8'),
            encoded_params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hmac, hmac_to_verify)
    
    @rate_limited
    def _make_request(self, method: str, endpoint: str, 
                     params: Dict = None, data: Dict = None,
                     json_data: Dict = None) -> Dict[str, Any]:
        """
        Make HTTP request to Shopify API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Form data
            json_data: JSON data
        
        Returns:
            API response
        """
        url = f"{self.base_url}/{endpoint}.json" if not endpoint.endswith('.json') else f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data
            )
            
            # Track API limits
            if 'X-Shopify-Shop-Api-Call-Limit' in response.headers:
                limit = response.headers['X-Shopify-Shop-Api-Call-Limit']
                used, total = limit.split('/')
                self.api_calls_made = int(used)
                self.api_calls_remaining = int(total) - int(used)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, params, data, json_data)
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """GET request"""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """POST request"""
        return self._make_request('POST', endpoint, json_data=data)
    
    def put(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """PUT request"""
        return self._make_request('PUT', endpoint, json_data=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        return self._make_request('DELETE', endpoint)
    
    @rate_limited
    def graphql(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """
        Execute GraphQL query
        
        Args:
            query: GraphQL query string
            variables: Query variables
        
        Returns:
            GraphQL response
        """
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            response = self.session.post(self.graphql_url, json=payload)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"GraphQL rate limited, retrying after {retry_after} seconds")
                time.sleep(retry_after)
                return self.graphql(query, variables)
            
            response.raise_for_status()
            result = response.json()
            
            # Check for GraphQL errors
            if 'errors' in result:
                logger.error(f"GraphQL errors: {result['errors']}")
            
            # Check for throttled status
            if 'extensions' in result and 'cost' in result['extensions']:
                cost_info = result['extensions']['cost']
                if cost_info.get('throttleStatus') == 'THROTTLED':
                    logger.warning("GraphQL query throttled")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL request failed: {e}")
            raise
    
    def get_shop_info(self) -> Dict[str, Any]:
        """Get shop information"""
        return self.get('shop')
    
    def get_api_permissions(self) -> List[str]:
        """Get current API permissions/scopes"""
        shop_info = self.get_shop_info()
        return shop_info.get('shop', {}).get('api_permissions', [])
    
    def paginate(self, endpoint: str, params: Dict = None, limit: int = 250) -> List[Dict]:
        """
        Paginate through all results
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Items per page (max 250)
        
        Returns:
            All items from paginated results
        """
        all_items = []
        params = params or {}
        params['limit'] = min(limit, 250)
        
        while True:
            response = self.get(endpoint, params)
            
            # Extract items based on endpoint
            resource_name = endpoint.split('/')[0].replace('-', '_')
            items = response.get(resource_name, [])
            
            if not items:
                break
            
            all_items.extend(items)
            
            # Check for next page
            if len(items) < params['limit']:
                break
            
            # Use cursor-based pagination if available
            if 'page_info' in response:
                params['page_info'] = response['page_info']
                params.pop('since_id', None)
            else:
                # Fall back to since_id pagination
                params['since_id'] = items[-1]['id']
        
        return all_items
    
    def bulk_operation(self, query: str) -> str:
        """
        Start a bulk operation for large data exports
        
        Args:
            query: GraphQL bulk query
        
        Returns:
            Bulk operation ID
        """
        mutation = """
        mutation {
            bulkOperationRunQuery(
                query: "%s"
            ) {
                bulkOperation {
                    id
                    status
                    errorCode
                    createdAt
                    completedAt
                    objectCount
                    fileSize
                    url
                    partialDataUrl
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """ % query.replace('"', '\\"').replace('\n', '\\n')
        
        result = self.graphql(mutation)
        
        if result.get('data', {}).get('bulkOperationRunQuery', {}).get('userErrors'):
            errors = result['data']['bulkOperationRunQuery']['userErrors']
            raise Exception(f"Bulk operation failed: {errors}")
        
        return result['data']['bulkOperationRunQuery']['bulkOperation']['id']
    
    def check_bulk_operation(self, operation_id: str) -> Dict[str, Any]:
        """
        Check status of bulk operation
        
        Args:
            operation_id: Bulk operation ID
        
        Returns:
            Operation status and results
        """
        query = """
        query {
            node(id: "%s") {
                ... on BulkOperation {
                    id
                    status
                    errorCode
                    createdAt
                    completedAt
                    objectCount
                    fileSize
                    url
                    partialDataUrl
                }
            }
        }
        """ % operation_id
        
        result = self.graphql(query)
        return result['data']['node']
    
    def wait_for_bulk_operation(self, operation_id: str, 
                               timeout: int = 3600,
                               poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for bulk operation to complete
        
        Args:
            operation_id: Bulk operation ID
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
        
        Returns:
            Completed operation details
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_bulk_operation(operation_id)
            
            if status['status'] == 'COMPLETED':
                return status
            elif status['status'] == 'FAILED':
                raise Exception(f"Bulk operation failed: {status.get('errorCode')}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Bulk operation timed out after {timeout} seconds")


class ShopifyOAuth:
    """Handle Shopify OAuth flow"""
    
    def __init__(self, api_key: str, api_secret: str, scopes: List[str],
                 redirect_uri: str):
        """
        Initialize OAuth handler
        
        Args:
            api_key: Shopify app API key
            api_secret: Shopify app API secret
            scopes: List of required scopes
            redirect_uri: OAuth callback URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.scopes = scopes
        self.redirect_uri = redirect_uri
    
    def get_authorization_url(self, shop_domain: str, state: str = None) -> str:
        """
        Get OAuth authorization URL
        
        Args:
            shop_domain: Shop domain
            state: Optional state parameter for CSRF protection
        
        Returns:
            Authorization URL
        """
        params = {
            'client_id': self.api_key,
            'scope': ','.join(self.scopes),
            'redirect_uri': self.redirect_uri
        }
        
        if state:
            params['state'] = state
        
        shop_domain = shop_domain.replace('https://', '').replace('http://', '')
        return f"https://{shop_domain}/admin/oauth/authorize?{urlencode(params)}"
    
    def request_access_token(self, shop_domain: str, code: str) -> Dict[str, str]:
        """
        Exchange authorization code for access token
        
        Args:
            shop_domain: Shop domain
            code: Authorization code
        
        Returns:
            Access token and scope
        """
        shop_domain = shop_domain.replace('https://', '').replace('http://', '')
        url = f"https://{shop_domain}/admin/oauth/access_token"
        
        payload = {
            'client_id': self.api_key,
            'client_secret': self.api_secret,
            'code': code
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            raise