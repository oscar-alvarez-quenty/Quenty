import httpx
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from ..config import settings
import json
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class MercadoLibreClient:
    """MercadoLibre API Client with OAuth2 support"""
    
    def __init__(self, access_token: Optional[str] = None):
        self.base_url = settings.meli_api_base_url
        self.auth_url = settings.meli_auth_url
        self.client_id = settings.meli_client_id
        self.client_secret = settings.meli_client_secret
        self.redirect_uri = settings.meli_redirect_uri
        self.access_token = access_token
        self.site_id = settings.meli_site_id
        
        # Rate limiting
        self.rate_limit_calls = settings.rate_limit_calls_per_second
        self.rate_limit_burst = settings.rate_limit_burst
        self._semaphore = asyncio.Semaphore(self.rate_limit_burst)
        self._last_call = datetime.now()
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        async with self._semaphore:
            now = datetime.now()
            time_since_last = (now - self._last_call).total_seconds()
            if time_since_last < 1.0 / self.rate_limit_calls:
                await asyncio.sleep(1.0 / self.rate_limit_calls - time_since_last)
            self._last_call = datetime.now()
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth2 authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri
        }
        if state:
            params["state"] = state
        
        return f"{self.auth_url}/authorization?{urlencode(params)}"
    
    async def get_access_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request with rate limiting"""
        await self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        headers["Content-Type"] = "application/json"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json() if response.text else {}
            except httpx.HTTPStatusError as e:
                logger.error(f"API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise
    
    # User Methods
    async def get_user_info(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user information"""
        endpoint = f"/users/{user_id}" if user_id else "/users/me"
        return await self._make_request("GET", endpoint)
    
    # Product Methods
    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get item details"""
        return await self._make_request("GET", f"/items/{item_id}")
    
    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item listing"""
        return await self._make_request("POST", "/items", json_data=item_data)
    
    async def update_item(self, item_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item"""
        return await self._make_request("PUT", f"/items/{item_id}", json_data=updates)
    
    async def update_item_status(self, item_id: str, status: str) -> Dict[str, Any]:
        """Update item status (active, paused, closed)"""
        return await self._make_request(
            "PUT",
            f"/items/{item_id}",
            json_data={"status": status}
        )
    
    async def get_items_by_seller(
        self,
        seller_id: str,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get items by seller"""
        params = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status
        
        return await self._make_request(
            "GET",
            f"/sites/{self.site_id}/search",
            params={**params, "seller_id": seller_id}
        )
    
    async def get_item_description(self, item_id: str) -> Dict[str, Any]:
        """Get item description"""
        return await self._make_request("GET", f"/items/{item_id}/description")
    
    async def update_item_description(self, item_id: str, description: str) -> Dict[str, Any]:
        """Update item description"""
        return await self._make_request(
            "PUT",
            f"/items/{item_id}/description",
            json_data={"plain_text": description}
        )
    
    # Inventory Methods
    async def update_item_stock(self, item_id: str, quantity: int) -> Dict[str, Any]:
        """Update item stock quantity"""
        return await self._make_request(
            "PUT",
            f"/items/{item_id}",
            json_data={"available_quantity": quantity}
        )
    
    # Order Methods
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details"""
        return await self._make_request("GET", f"/orders/{order_id}")
    
    async def get_orders(
        self,
        seller_id: Optional[str] = None,
        buyer_id: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get orders with filters"""
        params = {"offset": offset, "limit": limit}
        
        if seller_id:
            params["seller"] = seller_id
        if buyer_id:
            params["buyer"] = buyer_id
        if status:
            params["order.status"] = status
        if date_from:
            params["order.date_created.from"] = date_from.isoformat()
        if date_to:
            params["order.date_created.to"] = date_to.isoformat()
        
        endpoint = "/orders/search" if seller_id else f"/orders/search/recent"
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_order_items(self, order_id: str) -> Dict[str, Any]:
        """Get order items"""
        return await self._make_request("GET", f"/orders/{order_id}/items")
    
    async def update_order_note(self, order_id: str, note: str) -> Dict[str, Any]:
        """Add note to order"""
        return await self._make_request(
            "POST",
            f"/orders/{order_id}/notes",
            json_data={"note": note}
        )
    
    # Shipping Methods
    async def get_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """Get shipment details"""
        return await self._make_request("GET", f"/shipments/{shipment_id}")
    
    async def get_shipping_label(self, shipment_id: str) -> Dict[str, Any]:
        """Get shipping label"""
        return await self._make_request("GET", f"/shipments/{shipment_id}/label")
    
    async def create_shipment(self, order_id: str, shipping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create shipment for order"""
        return await self._make_request(
            "POST",
            f"/shipments",
            json_data={"order_id": order_id, **shipping_data}
        )
    
    # Question Methods
    async def get_question(self, question_id: str) -> Dict[str, Any]:
        """Get question details"""
        return await self._make_request("GET", f"/questions/{question_id}")
    
    async def get_questions(
        self,
        seller_id: Optional[str] = None,
        item_id: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get questions with filters"""
        endpoint = "/questions/search"
        params = {"offset": offset, "limit": limit}
        
        if seller_id:
            params["seller_id"] = seller_id
        if item_id:
            params["item"] = item_id
        if status:
            params["status"] = status
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def answer_question(self, question_id: str, answer_text: str) -> Dict[str, Any]:
        """Answer a question"""
        return await self._make_request(
            "POST",
            f"/answers",
            json_data={
                "question_id": question_id,
                "text": answer_text
            }
        )
    
    # Message Methods
    async def get_messages(
        self,
        order_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get messages"""
        params = {"offset": offset, "limit": limit}
        
        if order_id:
            endpoint = f"/messages/orders/{order_id}"
        elif seller_id:
            endpoint = "/messages/sellers"
            params["seller_id"] = seller_id
        else:
            endpoint = "/messages"
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def send_message(
        self,
        order_id: str,
        message_text: str,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send message for an order"""
        data = {
            "message": {
                "text": message_text
            }
        }
        if attachments:
            data["message"]["attachments"] = attachments
        
        return await self._make_request(
            "POST",
            f"/messages/orders/{order_id}",
            json_data=data
        )
    
    # Category Methods
    async def get_category(self, category_id: str) -> Dict[str, Any]:
        """Get category information"""
        return await self._make_request("GET", f"/categories/{category_id}")
    
    async def get_category_attributes(self, category_id: str) -> Dict[str, Any]:
        """Get category attributes"""
        return await self._make_request("GET", f"/categories/{category_id}/attributes")
    
    async def predict_category(self, title: str) -> Dict[str, Any]:
        """Predict category from title"""
        return await self._make_request(
            "GET",
            f"/sites/{self.site_id}/category_predictor/predict",
            params={"title": title}
        )
    
    # Search Methods
    async def search_items(
        self,
        query: str,
        category: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search items in marketplace"""
        params = {
            "q": query,
            "offset": offset,
            "limit": limit
        }
        if category:
            params["category"] = category
        
        return await self._make_request(
            "GET",
            f"/sites/{self.site_id}/search",
            params=params
        )
    
    # Notification Methods
    async def register_webhook(self, topic: str, callback_url: str) -> Dict[str, Any]:
        """Register webhook for notifications"""
        return await self._make_request(
            "POST",
            "/subscriptions",
            json_data={
                "topic": topic,
                "callback_url": callback_url,
                "user_id": "me"
            }
        )
    
    async def get_webhooks(self) -> Dict[str, Any]:
        """Get registered webhooks"""
        return await self._make_request("GET", "/subscriptions/me")
    
    async def delete_webhook(self, subscription_id: str) -> Dict[str, Any]:
        """Delete webhook subscription"""
        return await self._make_request("DELETE", f"/subscriptions/{subscription_id}")