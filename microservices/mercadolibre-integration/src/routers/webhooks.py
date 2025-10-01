from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import hmac
import hashlib
from datetime import datetime
from ..database import get_db
from ..models import MercadoLibreWebhook, MercadoLibreAccount
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/notification")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Receive webhook notification from MercadoLibre"""
    try:
        # Get request body
        body = await request.json()
        
        # Verify webhook signature if configured
        if settings.webhook_secret:
            signature = request.headers.get("X-Signature")
            if not verify_signature(body, signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Save webhook event
        webhook = MercadoLibreWebhook(
            user_id=body.get("user_id"),
            resource=body.get("resource"),
            topic=body.get("topic"),
            application_id=body.get("application_id"),
            attempts=body.get("attempts", 0),
            sent=datetime.fromisoformat(body.get("sent")) if body.get("sent") else None,
            received=datetime.utcnow(),
            payload=body
        )
        db.add(webhook)
        await db.commit()
        
        # Process webhook based on topic
        await process_webhook(body, db)
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def verify_signature(body: dict, signature: str) -> bool:
    """Verify webhook signature"""
    try:
        # Create signature
        message = f"{body.get('resource')},{body.get('user_id')}"
        expected_signature = hmac.new(
            settings.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


async def process_webhook(body: dict, db: AsyncSession):
    """Process webhook based on topic"""
    topic = body.get("topic")
    resource = body.get("resource")
    user_id = body.get("user_id")
    
    logger.info(f"Processing webhook: topic={topic}, resource={resource}")
    
    try:
        if topic == "orders":
            await process_order_webhook(resource, user_id, db)
        elif topic == "items":
            await process_item_webhook(resource, user_id, db)
        elif topic == "questions":
            await process_question_webhook(resource, user_id, db)
        elif topic == "messages":
            await process_message_webhook(resource, user_id, db)
        elif topic == "shipments":
            await process_shipment_webhook(resource, user_id, db)
        else:
            logger.warning(f"Unknown webhook topic: {topic}")
    except Exception as e:
        logger.error(f"Failed to process {topic} webhook: {e}")


async def process_order_webhook(resource: str, user_id: str, db: AsyncSession):
    """Process order webhook"""
    # Extract order ID from resource
    order_id = resource.split("/")[-1] if resource else None
    
    if not order_id:
        return
    
    # Get account
    result = await db.execute(
        select(MercadoLibreAccount).where(
            MercadoLibreAccount.user_id == user_id
        )
    )
    account = result.scalar_one_or_none()
    
    if account:
        from ..services.order_service import OrderService
        service = OrderService(db)
        await service.get_order_details(account, order_id)


async def process_item_webhook(resource: str, user_id: str, db: AsyncSession):
    """Process item webhook"""
    # Extract item ID from resource
    item_id = resource.split("/")[-1] if resource else None
    
    if not item_id:
        return
    
    # Get account
    result = await db.execute(
        select(MercadoLibreAccount).where(
            MercadoLibreAccount.user_id == user_id
        )
    )
    account = result.scalar_one_or_none()
    
    if account:
        from ..services.meli_client import MercadoLibreClient
        client = MercadoLibreClient(access_token=account.access_token)
        item = await client.get_item(item_id)
        # Update item in database


async def process_question_webhook(resource: str, user_id: str, db: AsyncSession):
    """Process question webhook"""
    # Extract question ID from resource
    question_id = resource.split("/")[-1] if resource else None
    
    if not question_id:
        return
    
    # Get account and sync question
    result = await db.execute(
        select(MercadoLibreAccount).where(
            MercadoLibreAccount.user_id == user_id
        )
    )
    account = result.scalar_one_or_none()
    
    if account:
        from ..services.meli_client import MercadoLibreClient
        client = MercadoLibreClient(access_token=account.access_token)
        question = await client.get_question(question_id)
        # Update question in database


async def process_message_webhook(resource: str, user_id: str, db: AsyncSession):
    """Process message webhook"""
    logger.info(f"Processing message webhook for user {user_id}")
    # Similar processing for messages


async def process_shipment_webhook(resource: str, user_id: str, db: AsyncSession):
    """Process shipment webhook"""
    logger.info(f"Processing shipment webhook for user {user_id}")
    # Similar processing for shipments


@router.post("/register")
async def register_webhook(
    webhook_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Register webhook with MercadoLibre"""
    try:
        account_id = webhook_data.get("account_id")
        topic = webhook_data.get("topic")
        callback_url = webhook_data.get("callback_url", f"{settings.webhook_base_url}/webhooks/notification")
        
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == account_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        from ..services.meli_client import MercadoLibreClient
        client = MercadoLibreClient(access_token=account.access_token)
        result = await client.register_webhook(topic, callback_url)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to register webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_webhooks(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List registered webhooks"""
    try:
        # Get account
        result = await db.execute(
            select(MercadoLibreAccount).where(
                MercadoLibreAccount.id == account_id
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        from ..services.meli_client import MercadoLibreClient
        client = MercadoLibreClient(access_token=account.access_token)
        webhooks = await client.get_webhooks()
        
        return webhooks
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))