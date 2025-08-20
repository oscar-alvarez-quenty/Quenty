from celery import Task
from ..celery_app import app
from typing import Dict, Any
import structlog
import httpx
from datetime import datetime

from ..database import SessionLocal
from ..models import TrackingEvent, CarrierType, ApiCallLog

logger = structlog.get_logger()


class WebhookTask(Task):
    """Base task for webhook processing"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._db is not None:
            self._db.close()
            self._db = None


@app.task(
    bind=True,
    base=WebhookTask,
    name='src.tasks.webhook_tasks.process_webhook_async',
    max_retries=5,
    default_retry_delay=30
)
def process_webhook_async(self, carrier: str, webhook_type: str, data: Dict[str, Any]):
    """
    Process webhook data asynchronously
    
    Args:
        carrier: Carrier name
        webhook_type: Type of webhook (tracking, pod, exception, etc.)
        data: Webhook payload
    
    Returns:
        Processing result
    """
    try:
        logger.info("Processing webhook",
                   task_id=self.request.id,
                   carrier=carrier,
                   webhook_type=webhook_type)
        
        # Log the webhook call
        api_log = ApiCallLog(
            carrier=CarrierType[carrier.upper()],
            endpoint=f"webhook/{webhook_type}",
            method="POST",
            request_data=data,
            status_code=200,
            latency_ms=0
        )
        self.db.add(api_log)
        
        # Process based on webhook type
        if webhook_type == "tracking":
            result = process_tracking_webhook(self, carrier, data)
        elif webhook_type == "pod":
            result = process_pod_webhook(self, carrier, data)
        elif webhook_type == "exception":
            result = process_exception_webhook(self, carrier, data)
        elif webhook_type == "status_change":
            result = process_status_change_webhook(self, carrier, data)
        else:
            logger.warning("Unknown webhook type",
                          webhook_type=webhook_type,
                          carrier=carrier)
            result = {'status': 'unknown_type'}
        
        # Update API log with result
        api_log.response_data = result
        self.db.commit()
        
        logger.info("Webhook processed successfully",
                   task_id=self.request.id,
                   carrier=carrier,
                   webhook_type=webhook_type)
        
        return result
        
    except Exception as e:
        logger.error("Webhook processing failed",
                    task_id=self.request.id,
                    carrier=carrier,
                    webhook_type=webhook_type,
                    error=str(e))
        
        # Log the error
        if 'api_log' in locals():
            api_log.error_message = str(e)
            api_log.status_code = 500
            self.db.commit()
        
        raise self.retry(exc=e)


def process_tracking_webhook(task: WebhookTask, carrier: str, data: Dict[str, Any]):
    """Process tracking update webhook"""
    tracking_number = extract_tracking_number(carrier, data)
    events = extract_tracking_events(carrier, data)
    
    saved_count = 0
    for event in events:
        # Check if event already exists
        existing = task.db.query(TrackingEvent).filter(
            TrackingEvent.tracking_number == tracking_number,
            TrackingEvent.event_date == event['date'],
            TrackingEvent.status == event['status']
        ).first()
        
        if not existing:
            db_event = TrackingEvent(
                tracking_number=tracking_number,
                carrier=CarrierType[carrier.upper()],
                event_date=event['date'],
                status=event['status'],
                description=event['description'],
                location=event.get('location'),
                raw_data=event
            )
            task.db.add(db_event)
            saved_count += 1
    
    task.db.commit()
    
    # Check for important status changes
    if any(e['status'].lower() in ['delivered', 'exception', 'failed'] for e in events):
        # Trigger notifications
        from .tracking_tasks import notify_delivery, notify_exception
        
        for event in events:
            if event['status'].lower() == 'delivered':
                notify_delivery.delay(tracking_number, carrier, event)
            elif event['status'].lower() in ['exception', 'failed']:
                notify_exception.delay(tracking_number, carrier, event['status'])
    
    return {
        'status': 'processed',
        'tracking_number': tracking_number,
        'events_saved': saved_count
    }


def process_pod_webhook(task: WebhookTask, carrier: str, data: Dict[str, Any]):
    """Process proof of delivery webhook"""
    tracking_number = extract_tracking_number(carrier, data)
    pod_data = extract_pod_data(carrier, data)
    
    # Save delivery confirmation
    db_event = TrackingEvent(
        tracking_number=tracking_number,
        carrier=CarrierType[carrier.upper()],
        event_date=pod_data.get('delivery_date', datetime.now()),
        status="DELIVERED",
        description=f"Delivered to {pod_data.get('recipient', 'recipient')}",
        location=pod_data.get('location'),
        raw_data=data
    )
    task.db.add(db_event)
    task.db.commit()
    
    # Send delivery confirmation
    send_delivery_confirmation.delay(tracking_number, carrier, pod_data)
    
    return {
        'status': 'processed',
        'tracking_number': tracking_number,
        'delivered': True
    }


def process_exception_webhook(task: WebhookTask, carrier: str, data: Dict[str, Any]):
    """Process shipment exception webhook"""
    tracking_number = extract_tracking_number(carrier, data)
    exception_data = extract_exception_data(carrier, data)
    
    # Save exception event
    db_event = TrackingEvent(
        tracking_number=tracking_number,
        carrier=CarrierType[carrier.upper()],
        event_date=exception_data.get('date', datetime.now()),
        status="EXCEPTION",
        description=exception_data.get('description', 'Shipment exception'),
        location=exception_data.get('location'),
        raw_data=data
    )
    task.db.add(db_event)
    task.db.commit()
    
    # Trigger exception handling
    handle_shipment_exception.delay(tracking_number, carrier, exception_data)
    
    return {
        'status': 'processed',
        'tracking_number': tracking_number,
        'exception': True
    }


def process_status_change_webhook(task: WebhookTask, carrier: str, data: Dict[str, Any]):
    """Process general status change webhook"""
    tracking_number = extract_tracking_number(carrier, data)
    new_status = data.get('status', 'UNKNOWN')
    
    # Save status change
    db_event = TrackingEvent(
        tracking_number=tracking_number,
        carrier=CarrierType[carrier.upper()],
        event_date=datetime.now(),
        status=new_status,
        description=data.get('description', f'Status changed to {new_status}'),
        location=data.get('location'),
        raw_data=data
    )
    task.db.add(db_event)
    task.db.commit()
    
    return {
        'status': 'processed',
        'tracking_number': tracking_number,
        'new_status': new_status
    }


def extract_tracking_number(carrier: str, data: Dict[str, Any]) -> str:
    """Extract tracking number from webhook data based on carrier"""
    carrier_fields = {
        'DHL': 'trackingNumber',
        'FEDEX': 'trackingInfo.trackingNumber',
        'UPS': 'TrackingNumber',
        'SERVIENTREGA': 'NumeroGuia',
        'INTERRAPIDISIMO': 'numeroRemesa'
    }
    
    field = carrier_fields.get(carrier.upper(), 'tracking_number')
    
    # Handle nested fields
    if '.' in field:
        parts = field.split('.')
        value = data
        for part in parts:
            value = value.get(part, {})
        return value
    
    return data.get(field, '')


def extract_tracking_events(carrier: str, data: Dict[str, Any]) -> list:
    """Extract tracking events from webhook data"""
    events = []
    
    if carrier.upper() == 'DHL':
        for event in data.get('events', []):
            events.append({
                'date': datetime.fromisoformat(event['timestamp']),
                'status': event['statusCode'],
                'description': event['description'],
                'location': event.get('location', {}).get('address', {}).get('addressLocality')
            })
    
    elif carrier.upper() == 'FEDEX':
        for event in data.get('trackingInfo', {}).get('scanEvents', []):
            events.append({
                'date': datetime.fromisoformat(event['date']),
                'status': event['derivedStatus'],
                'description': event['eventDescription'],
                'location': event.get('scanLocation')
            })
    
    # Add other carrier mappings...
    
    return events


def extract_pod_data(carrier: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract proof of delivery data"""
    pod_data = {}
    
    if carrier.upper() == 'DHL':
        pod_data = {
            'delivery_date': datetime.fromisoformat(data.get('deliveryDate')),
            'recipient': data.get('proofOfDelivery', {}).get('signedBy'),
            'signature': data.get('proofOfDelivery', {}).get('signature'),
            'location': data.get('deliveryLocation')
        }
    
    # Add other carrier mappings...
    
    return pod_data


def extract_exception_data(carrier: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract exception data from webhook"""
    return {
        'date': datetime.now(),
        'description': data.get('exceptionDescription', 'Unknown exception'),
        'location': data.get('location'),
        'reason': data.get('reason'),
        'action_required': data.get('actionRequired', False)
    }


@app.task(
    name='src.tasks.webhook_tasks.send_delivery_confirmation'
)
def send_delivery_confirmation(tracking_number: str, carrier: str, pod_data: Dict[str, Any]):
    """Send delivery confirmation to relevant parties"""
    logger.info("Sending delivery confirmation",
               tracking_number=tracking_number,
               carrier=carrier)
    
    # TODO: Implement actual notifications
    # - Email customer
    # - Update order service
    # - Trigger payment settlement
    # - Send merchant webhook
    
    return {'status': 'notification_sent'}


@app.task(
    name='src.tasks.webhook_tasks.handle_shipment_exception'
)
def handle_shipment_exception(tracking_number: str, carrier: str, exception_data: Dict[str, Any]):
    """Handle shipment exceptions"""
    logger.warning("Handling shipment exception",
                  tracking_number=tracking_number,
                  carrier=carrier,
                  exception=exception_data)
    
    # Determine action based on exception type
    if exception_data.get('action_required'):
        # Create support ticket
        create_support_ticket.delay(tracking_number, carrier, exception_data)
    
    # Notify customer
    notify_customer_exception.delay(tracking_number, exception_data)
    
    return {'status': 'exception_handled'}


@app.task(
    name='src.tasks.webhook_tasks.create_support_ticket'
)
def create_support_ticket(tracking_number: str, carrier: str, exception_data: Dict[str, Any]):
    """Create support ticket for shipment exception"""
    logger.info("Creating support ticket",
               tracking_number=tracking_number,
               carrier=carrier)
    
    # TODO: Integrate with support system
    ticket_data = {
        'tracking_number': tracking_number,
        'carrier': carrier,
        'issue': exception_data.get('description'),
        'priority': 'high' if exception_data.get('action_required') else 'medium',
        'created_at': datetime.now().isoformat()
    }
    
    return ticket_data


@app.task(
    name='src.tasks.webhook_tasks.notify_customer_exception'
)
def notify_customer_exception(tracking_number: str, exception_data: Dict[str, Any]):
    """Notify customer about shipment exception"""
    logger.info("Notifying customer about exception",
               tracking_number=tracking_number)
    
    # TODO: Implement customer notification
    # - Send email/SMS
    # - Update tracking page
    # - Send push notification
    
    return {'status': 'customer_notified'}


@app.task(
    bind=True,
    base=WebhookTask,
    name='src.tasks.webhook_tasks.batch_process_webhooks',
    max_retries=3
)
def batch_process_webhooks(self, webhooks: list[Dict[str, Any]]):
    """Process multiple webhooks in batch"""
    results = []
    
    for webhook in webhooks:
        try:
            result = process_webhook_async.apply_async(
                args=[
                    webhook['carrier'],
                    webhook['type'],
                    webhook['data']
                ],
                queue='webhooks'
            )
            results.append({
                'webhook_id': webhook.get('id'),
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            results.append({
                'webhook_id': webhook.get('id'),
                'status': 'failed',
                'error': str(e)
            })
    
    return results