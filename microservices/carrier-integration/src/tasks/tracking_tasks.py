from celery import Task
from ..celery_app import app
from typing import Dict, Any, List
import structlog
import asyncio
from datetime import datetime, timedelta

from ..database import SessionLocal
from ..models import TrackingEvent, ShippingLabel, CarrierType
from ..services.carrier_service import CarrierService

logger = structlog.get_logger()


class TrackingTask(Task):
    """Base task for tracking operations"""
    _db = None
    _carrier_service = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    @property
    def carrier_service(self):
        if self._carrier_service is None:
            self._carrier_service = CarrierService()
        return self._carrier_service
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._db is not None:
            self._db.close()
            self._db = None


@app.task(
    bind=True,
    base=TrackingTask,
    name='src.tasks.tracking_tasks.sync_tracking_async',
    max_retries=3
)
def sync_tracking_async(self, tracking_number: str, carrier: str):
    """
    Asynchronously sync tracking information for a shipment
    
    Args:
        tracking_number: Tracking number to sync
        carrier: Carrier name
    
    Returns:
        Updated tracking information
    """
    try:
        logger.info("Syncing tracking information",
                   task_id=self.request.id,
                   tracking_number=tracking_number,
                   carrier=carrier)
        
        # Get tracking info from carrier
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            tracking = loop.run_until_complete(
                self.carrier_service.track_shipment(carrier, tracking_number)
            )
            
            # Save tracking events to database
            for event in tracking.events:
                # Check if event already exists
                existing = self.db.query(TrackingEvent).filter(
                    TrackingEvent.tracking_number == tracking_number,
                    TrackingEvent.event_date == event.date,
                    TrackingEvent.status == event.status
                ).first()
                
                if not existing:
                    db_event = TrackingEvent(
                        tracking_number=tracking_number,
                        carrier=CarrierType[carrier],
                        event_date=event.date,
                        status=event.status,
                        description=event.description,
                        location=event.location,
                        raw_data=event.details
                    )
                    self.db.add(db_event)
            
            self.db.commit()
            
            # Check if delivered
            if tracking.status.lower() in ['delivered', 'entregado']:
                # Trigger delivery notification
                notify_delivery.delay(tracking_number, carrier, tracking.proof_of_delivery)
            
            # Check for exceptions or delays
            if tracking.status.lower() in ['exception', 'delayed', 'failed']:
                # Trigger exception notification
                notify_exception.delay(tracking_number, carrier, tracking.status)
            
            logger.info("Tracking synced successfully",
                       tracking_number=tracking_number,
                       status=tracking.status,
                       events_count=len(tracking.events))
            
            return {
                'tracking_number': tracking_number,
                'carrier': carrier,
                'status': tracking.status,
                'current_location': tracking.current_location,
                'events_count': len(tracking.events),
                'delivered': tracking.delivered_date is not None
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Tracking sync failed",
                    task_id=self.request.id,
                    tracking_number=tracking_number,
                    error=str(e))
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@app.task(
    bind=True,
    base=TrackingTask,
    name='src.tasks.tracking_tasks.sync_all_tracking'
)
def sync_all_tracking(self):
    """
    Sync tracking for all active shipments
    """
    try:
        logger.info("Starting bulk tracking sync", task_id=self.request.id)
        
        # Get all active shipments (not delivered)
        active_shipments = self.db.query(ShippingLabel).filter(
            ShippingLabel.created_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        synced_count = 0
        failed_count = 0
        
        for shipment in active_shipments:
            try:
                # Check if already delivered
                last_event = self.db.query(TrackingEvent).filter(
                    TrackingEvent.tracking_number == shipment.tracking_number
                ).order_by(TrackingEvent.event_date.desc()).first()
                
                if last_event and last_event.status.lower() in ['delivered', 'entregado']:
                    continue  # Skip delivered shipments
                
                # Queue tracking sync
                sync_tracking_async.delay(
                    shipment.tracking_number,
                    shipment.carrier.value
                )
                synced_count += 1
                
            except Exception as e:
                logger.error("Failed to queue tracking sync",
                           tracking_number=shipment.tracking_number,
                           error=str(e))
                failed_count += 1
        
        logger.info("Bulk tracking sync completed",
                   task_id=self.request.id,
                   synced_count=synced_count,
                   failed_count=failed_count)
        
        return {
            'synced': synced_count,
            'failed': failed_count,
            'total': len(active_shipments)
        }
        
    except Exception as e:
        logger.error("Bulk tracking sync failed",
                    task_id=self.request.id,
                    error=str(e))
        raise


@app.task(
    bind=True,
    base=TrackingTask,
    name='src.tasks.tracking_tasks.clean_old_tracking_events'
)
def clean_old_tracking_events(self, days_to_keep: int = 90):
    """
    Clean old tracking events from database
    
    Args:
        days_to_keep: Number of days to keep tracking events
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Delete old tracking events
        deleted_count = self.db.query(TrackingEvent).filter(
            TrackingEvent.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info("Old tracking events cleaned",
                   task_id=self.request.id,
                   deleted_count=deleted_count,
                   cutoff_date=cutoff_date)
        
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        logger.error("Failed to clean old tracking events",
                    task_id=self.request.id,
                    error=str(e))
        self.db.rollback()
        raise


@app.task(
    name='src.tasks.tracking_tasks.notify_delivery'
)
def notify_delivery(tracking_number: str, carrier: str, proof_of_delivery: Dict[str, Any]):
    """
    Send delivery notification
    """
    logger.info("Sending delivery notification",
               tracking_number=tracking_number,
               carrier=carrier)
    
    # TODO: Implement actual notification
    # - Send email to customer
    # - Update order status in order service
    # - Trigger payment settlement if COD
    # - Send webhook to merchant
    
    notification_data = {
        'event': 'delivery_confirmed',
        'tracking_number': tracking_number,
        'carrier': carrier,
        'proof_of_delivery': proof_of_delivery,
        'timestamp': datetime.now().isoformat()
    }
    
    # Example: Send to message queue
    # publish_to_queue('notifications.delivery', notification_data)
    
    return notification_data


@app.task(
    name='src.tasks.tracking_tasks.notify_exception'
)
def notify_exception(tracking_number: str, carrier: str, status: str):
    """
    Send exception notification for shipment issues
    """
    logger.warning("Sending exception notification",
                  tracking_number=tracking_number,
                  carrier=carrier,
                  status=status)
    
    # TODO: Implement actual notification
    # - Send alert to operations team
    # - Notify customer about delay
    # - Create support ticket if needed
    
    notification_data = {
        'event': 'shipment_exception',
        'tracking_number': tracking_number,
        'carrier': carrier,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }
    
    return notification_data


@app.task(
    bind=True,
    base=TrackingTask,
    name='src.tasks.tracking_tasks.batch_tracking_update'
)
def batch_tracking_update(self, tracking_numbers: List[str], carrier: str):
    """
    Update tracking for multiple shipments in batch
    """
    results = []
    
    for tracking_number in tracking_numbers:
        try:
            result = sync_tracking_async.apply_async(
                args=[tracking_number, carrier],
                queue='tracking'
            )
            results.append({
                'tracking_number': tracking_number,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            results.append({
                'tracking_number': tracking_number,
                'status': 'failed',
                'error': str(e)
            })
    
    return results


@app.task(
    bind=True,
    base=TrackingTask,
    name='src.tasks.tracking_tasks.analyze_delivery_performance'
)
def analyze_delivery_performance(self, carrier: str = None, days: int = 30):
    """
    Analyze delivery performance metrics
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(TrackingEvent).filter(
            TrackingEvent.created_at >= cutoff_date
        )
        
        if carrier:
            query = query.filter(TrackingEvent.carrier == CarrierType[carrier])
        
        events = query.all()
        
        # Calculate metrics
        total_shipments = len(set(e.tracking_number for e in events))
        delivered = len([e for e in events if e.status.lower() in ['delivered', 'entregado']])
        in_transit = len([e for e in events if e.status.lower() in ['in transit', 'en transito']])
        exceptions = len([e for e in events if e.status.lower() in ['exception', 'failed', 'delayed']])
        
        # Calculate average delivery time
        delivery_times = []
        for tracking_number in set(e.tracking_number for e in events):
            shipment_events = [e for e in events if e.tracking_number == tracking_number]
            shipment_events.sort(key=lambda x: x.event_date)
            
            if len(shipment_events) >= 2:
                first_event = shipment_events[0]
                last_event = shipment_events[-1]
                if last_event.status.lower() in ['delivered', 'entregado']:
                    delivery_time = (last_event.event_date - first_event.event_date).days
                    delivery_times.append(delivery_time)
        
        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
        
        metrics = {
            'carrier': carrier,
            'period_days': days,
            'total_shipments': total_shipments,
            'delivered': delivered,
            'in_transit': in_transit,
            'exceptions': exceptions,
            'delivery_rate': (delivered / total_shipments * 100) if total_shipments > 0 else 0,
            'exception_rate': (exceptions / total_shipments * 100) if total_shipments > 0 else 0,
            'avg_delivery_days': avg_delivery_time
        }
        
        logger.info("Delivery performance analyzed",
                   task_id=self.request.id,
                   metrics=metrics)
        
        return metrics
        
    except Exception as e:
        logger.error("Failed to analyze delivery performance",
                    task_id=self.request.id,
                    error=str(e))
        raise