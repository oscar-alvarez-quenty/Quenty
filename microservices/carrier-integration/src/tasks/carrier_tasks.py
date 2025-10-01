from celery import Task, group, chain
from celery.exceptions import SoftTimeLimitExceeded
from ..celery_app import app
from typing import Dict, Any, List, Optional
import structlog
import asyncio
from datetime import datetime, timedelta

from ..services.carrier_service import CarrierService
from ..services.fallback_service import FallbackService
from ..schemas import QuoteRequest, LabelRequest, PickupRequest
from ..database import SessionLocal
from ..models import ShippingQuote, ShippingLabel, CarrierHealthStatus, CarrierType, ServiceStatus

logger = structlog.get_logger()


class CarrierTask(Task):
    """Base task class with database session management"""
    _db = None
    _carrier_service = None
    _fallback_service = None
    
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
    
    @property
    def fallback_service(self):
        if self._fallback_service is None:
            self._fallback_service = FallbackService()
        return self._fallback_service
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Clean up database session after task completion"""
        if self._db is not None:
            self._db.close()
            self._db = None


@app.task(
    bind=True,
    base=CarrierTask,
    name='src.tasks.carrier_tasks.get_quote_async',
    max_retries=3,
    default_retry_delay=60
)
def get_quote_async(self, quote_data: Dict[str, Any], callback_url: Optional[str] = None):
    """
    Asynchronously get shipping quote from carrier
    
    Args:
        quote_data: Quote request data
        callback_url: Optional URL to POST results to
    
    Returns:
        Quote response data
    """
    try:
        logger.info("Processing async quote request", 
                   task_id=self.request.id,
                   carrier=quote_data.get('carrier'))
        
        # Create quote request object
        quote_request = QuoteRequest(**quote_data)
        
        # Run async operation in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if quote_data.get('carrier'):
                # Get quote from specific carrier
                quote = loop.run_until_complete(
                    self.carrier_service.get_quote(quote_data['carrier'], quote_request)
                )
            else:
                # Get best quote from all carriers
                quote = loop.run_until_complete(
                    self.carrier_service.get_best_quote(quote_request)
                )
            
            # Save quote to database
            db_quote = ShippingQuote(
                quote_id=quote.quote_id,
                carrier=CarrierType[quote.carrier],
                origin_country=quote_data['origin']['country'],
                origin_city=quote_data['origin']['city'],
                destination_country=quote_data['destination']['country'],
                destination_city=quote_data['destination']['city'],
                weight_kg=sum(pkg['weight_kg'] for pkg in quote_data['packages']),
                dimensions_cm={
                    "packages": quote_data['packages']
                },
                service_type=quote.service_type,
                amount=quote.amount,
                currency=quote.currency,
                estimated_days=quote.estimated_days,
                valid_until=quote.valid_until
            )
            self.db.add(db_quote)
            self.db.commit()
            
            result = {
                'success': True,
                'quote_id': quote.quote_id,
                'carrier': quote.carrier,
                'amount': quote.amount,
                'currency': quote.currency,
                'estimated_days': quote.estimated_days,
                'valid_until': quote.valid_until.isoformat()
            }
            
            # Send callback if provided
            if callback_url:
                send_callback.delay(callback_url, result)
            
            logger.info("Quote processed successfully",
                       task_id=self.request.id,
                       quote_id=quote.quote_id)
            
            return result
            
        finally:
            loop.close()
            
    except SoftTimeLimitExceeded:
        logger.error("Quote task timeout", task_id=self.request.id)
        raise self.retry(countdown=120)
        
    except Exception as e:
        logger.error("Quote task failed", 
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e, countdown=60)


@app.task(
    bind=True,
    base=CarrierTask,
    name='src.tasks.carrier_tasks.generate_label_async',
    max_retries=3,
    default_retry_delay=60
)
def generate_label_async(self, label_data: Dict[str, Any], callback_url: Optional[str] = None):
    """
    Asynchronously generate shipping label
    
    Args:
        label_data: Label request data
        callback_url: Optional URL to POST results to
    
    Returns:
        Label response data
    """
    try:
        logger.info("Processing async label generation",
                   task_id=self.request.id,
                   carrier=label_data.get('carrier'),
                   order_id=label_data.get('order_id'))
        
        # Create label request object
        label_request = LabelRequest(**label_data)
        
        # Run async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            label = loop.run_until_complete(
                self.carrier_service.generate_label(label_data['carrier'], label_request)
            )
            
            # Save label to database
            db_label = ShippingLabel(
                order_id=label_data['order_id'],
                carrier=CarrierType[label.carrier],
                tracking_number=label.tracking_number,
                label_url=label.label_url,
                label_data=label.label_data,
                awb_number=label.awb_number,
                service_type=label_data.get('service_type', 'standard')
            )
            self.db.add(db_label)
            self.db.commit()
            
            result = {
                'success': True,
                'tracking_number': label.tracking_number,
                'carrier': label.carrier,
                'label_url': label.label_url,
                'label_data': label.label_data[:100] if label.label_data else None,  # Truncate for response
                'estimated_delivery': label.estimated_delivery.isoformat(),
                'cost': label.cost,
                'currency': label.currency
            }
            
            # Start async tracking
            sync_tracking_async.delay(label.tracking_number, label.carrier)
            
            # Send callback if provided
            if callback_url:
                send_callback.delay(callback_url, result)
            
            logger.info("Label generated successfully",
                       task_id=self.request.id,
                       tracking_number=label.tracking_number)
            
            return result
            
        finally:
            loop.close()
            
    except SoftTimeLimitExceeded:
        logger.error("Label generation timeout", task_id=self.request.id)
        raise self.retry(countdown=120)
        
    except Exception as e:
        logger.error("Label generation failed",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e, countdown=60)


@app.task(
    bind=True,
    base=CarrierTask,
    name='src.tasks.carrier_tasks.schedule_pickup_async',
    max_retries=3
)
def schedule_pickup_async(self, pickup_data: Dict[str, Any], callback_url: Optional[str] = None):
    """
    Asynchronously schedule pickup with carrier
    """
    try:
        logger.info("Processing async pickup scheduling",
                   task_id=self.request.id,
                   carrier=pickup_data.get('carrier'))
        
        pickup_request = PickupRequest(**pickup_data)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            pickup = loop.run_until_complete(
                self.carrier_service.schedule_pickup(pickup_data['carrier'], pickup_request)
            )
            
            result = {
                'success': True,
                'confirmation_number': pickup.confirmation_number,
                'carrier': pickup.carrier,
                'pickup_date': pickup.pickup_date.isoformat(),
                'pickup_window': pickup.pickup_window,
                'status': pickup.status
            }
            
            if callback_url:
                send_callback.delay(callback_url, result)
            
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Pickup scheduling failed",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e, countdown=60)


@app.task(
    bind=True,
    name='src.tasks.carrier_tasks.get_multiple_quotes_async'
)
def get_multiple_quotes_async(self, quote_data: Dict[str, Any]):
    """
    Get quotes from multiple carriers in parallel
    """
    carriers = ['DHL', 'FedEx', 'UPS', 'Servientrega', 'Interrapidisimo']
    
    # Create a group of tasks to run in parallel
    job = group(
        get_quote_async.s({**quote_data, 'carrier': carrier})
        for carrier in carriers
    )
    
    # Execute all tasks in parallel
    result = job.apply_async()
    
    # Wait for all results
    quotes = result.get(timeout=30)
    
    # Return best quote
    best_quote = min(quotes, key=lambda q: q.get('amount', float('inf')) if q.get('success') else float('inf'))
    
    return best_quote


@app.task(
    bind=True,
    base=CarrierTask,
    name='src.tasks.carrier_tasks.health_check_all_carriers'
)
def health_check_all_carriers(self):
    """
    Check health status of all carriers
    """
    carriers = ['DHL', 'FedEx', 'UPS', 'Servientrega', 'Interrapidisimo']
    health_results = {}
    
    for carrier in carriers:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                health = loop.run_until_complete(
                    self.carrier_service.get_health_status(carrier)
                )
                
                # Update database
                db_health = self.db.query(CarrierHealthStatus).filter(
                    CarrierHealthStatus.carrier == CarrierType[carrier]
                ).first()
                
                if not db_health:
                    db_health = CarrierHealthStatus(carrier=CarrierType[carrier])
                    self.db.add(db_health)
                
                db_health.status = ServiceStatus[health.get('status', 'unknown').upper()]
                db_health.latency_ms = health.get('latency_ms')
                db_health.error_rate = health.get('error_rate')
                db_health.last_check = datetime.now()
                
                if health.get('status') == 'operational':
                    db_health.last_success = datetime.now()
                    db_health.consecutive_failures = 0
                else:
                    db_health.consecutive_failures += 1
                
                self.db.commit()
                
                health_results[carrier] = health
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Health check failed for {carrier}", error=str(e))
            health_results[carrier] = {
                'status': 'error',
                'error': str(e)
            }
    
    # Send alerts if any carrier is down
    down_carriers = [c for c, h in health_results.items() if h.get('status') != 'operational']
    if down_carriers:
        send_carrier_alert.delay(down_carriers, health_results)
    
    return health_results


@app.task(
    name='src.tasks.carrier_tasks.send_callback'
)
def send_callback(callback_url: str, data: Dict[str, Any]):
    """
    Send callback to specified URL
    """
    import httpx
    
    try:
        with httpx.Client() as client:
            response = client.post(
                callback_url,
                json=data,
                timeout=10.0
            )
            response.raise_for_status()
            
        logger.info("Callback sent successfully", url=callback_url)
        
    except Exception as e:
        logger.error("Failed to send callback",
                    url=callback_url,
                    error=str(e))


@app.task(
    name='src.tasks.carrier_tasks.send_carrier_alert'
)
def send_carrier_alert(down_carriers: List[str], health_results: Dict[str, Any]):
    """
    Send alert about carrier health issues
    """
    logger.warning("Carriers experiencing issues",
                  down_carriers=down_carriers,
                  health_results=health_results)
    
    # TODO: Implement actual alerting (email, SMS, Slack, etc.)
    # This could integrate with notification service
    pass


@app.task(
    bind=True,
    name='src.tasks.carrier_tasks.urgent_shipment',
    queue='priority'
)
def urgent_shipment(self, shipment_data: Dict[str, Any]):
    """
    Process urgent shipment with high priority
    """
    logger.info("Processing urgent shipment", task_id=self.request.id)
    
    # Chain quote and label generation
    chain(
        get_quote_async.s(shipment_data),
        generate_label_async.s(shipment_data)
    ).apply_async(priority=10)
    
    return {'status': 'urgent_processing_started'}