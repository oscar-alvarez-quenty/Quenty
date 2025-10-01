from celery import Task
from ..celery_app import app
from typing import Dict, Any, Optional
import structlog
from datetime import datetime, timedelta

from ..database import SessionLocal
from ..models import ExchangeRate
from ..exchange_rate.banco_republica import BancoRepublicaClient

logger = structlog.get_logger()


class ExchangeRateTask(Task):
    """Base task for exchange rate operations"""
    _db = None
    _banco_client = None
    
    @property 
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    @property
    def banco_client(self):
        if self._banco_client is None:
            self._banco_client = BancoRepublicaClient()
        return self._banco_client
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._db is not None:
            self._db.close()
            self._db = None


@app.task(
    bind=True,
    base=ExchangeRateTask,
    name='src.tasks.exchange_rate_tasks.update_trm',
    max_retries=5,
    default_retry_delay=300  # 5 minutes
)
def update_trm(self):
    """
    Update TRM from Banco de la República
    This task is scheduled to run daily at 6:00 AM
    """
    try:
        logger.info("Updating TRM from Banco de la República",
                   task_id=self.request.id)
        
        # Get current TRM
        trm_data = self.banco_client.get_current_trm()
        
        if not trm_data:
            raise Exception("Failed to get TRM data")
        
        # Check if TRM for today already exists
        existing = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == "COP",
            ExchangeRate.to_currency == "USD",
            ExchangeRate.valid_date == trm_data['valid_date'].date()
        ).first()
        
        if existing:
            # Update existing record
            existing.rate = trm_data['rate']
            existing.source = trm_data['source']
            logger.info("TRM updated (existing record)",
                       rate=trm_data['rate'],
                       date=trm_data['valid_date'])
        else:
            # Create new record
            exchange_rate = ExchangeRate(
                from_currency="COP",
                to_currency="USD",
                rate=trm_data['rate'],
                source=trm_data['source'],
                valid_date=trm_data['valid_date'],
                spread=0.03  # 3% default spread
            )
            self.db.add(exchange_rate)
            logger.info("TRM saved (new record)",
                       rate=trm_data['rate'],
                       date=trm_data['valid_date'])
        
        self.db.commit()
        
        # Check for significant variation
        check_trm_variation.delay()
        
        # Send notification about TRM update
        send_trm_update_notification.delay(trm_data)
        
        return {
            'status': 'success',
            'rate': trm_data['rate'],
            'valid_date': trm_data['valid_date'].isoformat(),
            'source': trm_data['source']
        }
        
    except Exception as e:
        logger.error("Failed to update TRM",
                    task_id=self.request.id,
                    error=str(e))
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=min(300 * (2 ** self.request.retries), 3600))


@app.task(
    bind=True,
    base=ExchangeRateTask,
    name='src.tasks.exchange_rate_tasks.check_trm_variation',
    max_retries=3
)
def check_trm_variation(self, threshold_percentage: float = 5.0):
    """
    Check TRM variation and send alerts if threshold is exceeded
    This task is scheduled to run daily at 7:00 AM
    """
    try:
        logger.info("Checking TRM variation",
                   task_id=self.request.id,
                   threshold=threshold_percentage)
        
        # Get today's TRM
        today = datetime.now().date()
        today_trm = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == "COP",
            ExchangeRate.to_currency == "USD",
            ExchangeRate.valid_date == today
        ).first()
        
        if not today_trm:
            logger.warning("No TRM found for today")
            return {'status': 'no_trm_for_today'}
        
        # Get yesterday's TRM
        yesterday = today - timedelta(days=1)
        yesterday_trm = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == "COP",
            ExchangeRate.to_currency == "USD",
            ExchangeRate.valid_date == yesterday
        ).first()
        
        if not yesterday_trm:
            logger.warning("No TRM found for yesterday")
            return {'status': 'no_trm_for_yesterday'}
        
        # Calculate variation
        variation = ((today_trm.rate - yesterday_trm.rate) / yesterday_trm.rate) * 100
        
        result = {
            'today_rate': today_trm.rate,
            'yesterday_rate': yesterday_trm.rate,
            'variation_percentage': round(variation, 2),
            'threshold': threshold_percentage,
            'alert_triggered': abs(variation) > threshold_percentage
        }
        
        logger.info("TRM variation calculated",
                   variation=variation,
                   alert_triggered=result['alert_triggered'])
        
        # Send alert if threshold exceeded
        if result['alert_triggered']:
            send_trm_variation_alert.delay(result)
        
        return result
        
    except Exception as e:
        logger.error("Failed to check TRM variation",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e)


@app.task(
    bind=True,
    base=ExchangeRateTask,
    name='src.tasks.exchange_rate_tasks.get_historical_trm',
    max_retries=3
)
def get_historical_trm(self, date: str):
    """
    Get historical TRM for a specific date
    
    Args:
        date: Date string in YYYY-MM-DD format
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        
        logger.info("Getting historical TRM",
                   task_id=self.request.id,
                   date=date)
        
        # Check database first
        existing = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == "COP",
            ExchangeRate.to_currency == "USD",
            ExchangeRate.valid_date == target_date.date()
        ).first()
        
        if existing:
            return {
                'rate': existing.rate,
                'date': existing.valid_date.isoformat(),
                'source': existing.source,
                'from_cache': True
            }
        
        # Get from Banco de la República
        trm_data = self.banco_client.get_historical_trm(target_date)
        
        if trm_data:
            # Save to database
            exchange_rate = ExchangeRate(
                from_currency="COP",
                to_currency="USD",
                rate=trm_data['rate'],
                source=trm_data['source'],
                valid_date=trm_data['valid_date'],
                spread=0.03
            )
            self.db.add(exchange_rate)
            self.db.commit()
            
            return {
                'rate': trm_data['rate'],
                'date': trm_data['valid_date'].isoformat(),
                'source': trm_data['source'],
                'from_cache': False
            }
        
        return {'error': 'TRM not found for date'}
        
    except Exception as e:
        logger.error("Failed to get historical TRM",
                    task_id=self.request.id,
                    date=date,
                    error=str(e))
        raise self.retry(exc=e)


@app.task(
    name='src.tasks.exchange_rate_tasks.send_trm_update_notification'
)
def send_trm_update_notification(trm_data: Dict[str, Any]):
    """Send notification about TRM update"""
    logger.info("Sending TRM update notification",
               rate=trm_data['rate'],
               date=trm_data['valid_date'])
    
    # TODO: Implement actual notification
    # - Send email to finance team
    # - Update pricing system
    # - Notify relevant services
    
    notification = {
        'event': 'trm_updated',
        'rate': trm_data['rate'],
        'valid_date': trm_data['valid_date'].isoformat() if isinstance(trm_data['valid_date'], datetime) else trm_data['valid_date'],
        'source': trm_data['source'],
        'timestamp': datetime.now().isoformat()
    }
    
    # Example: Publish to message queue
    # publish_to_queue('exchange_rates.trm_update', notification)
    
    return notification


@app.task(
    name='src.tasks.exchange_rate_tasks.send_trm_variation_alert'
)
def send_trm_variation_alert(variation_data: Dict[str, Any]):
    """Send alert about significant TRM variation"""
    logger.warning("Sending TRM variation alert",
                  variation=variation_data['variation_percentage'],
                  today_rate=variation_data['today_rate'],
                  yesterday_rate=variation_data['yesterday_rate'])
    
    # TODO: Implement actual alerting
    # - Send email to management
    # - Send SMS to key personnel
    # - Post to Slack channel
    # - Create dashboard alert
    
    alert = {
        'event': 'trm_variation_alert',
        'variation_percentage': variation_data['variation_percentage'],
        'today_rate': variation_data['today_rate'],
        'yesterday_rate': variation_data['yesterday_rate'],
        'threshold': variation_data['threshold'],
        'timestamp': datetime.now().isoformat(),
        'severity': 'high' if abs(variation_data['variation_percentage']) > 10 else 'medium'
    }
    
    return alert


@app.task(
    bind=True,
    base=ExchangeRateTask,
    name='src.tasks.exchange_rate_tasks.convert_currency_async'
)
def convert_currency_async(self, amount: float, from_currency: str, to_currency: str, 
                          apply_spread: bool = True):
    """
    Asynchronously convert currency
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        apply_spread: Whether to apply spread to the rate
    """
    try:
        logger.info("Converting currency",
                   task_id=self.request.id,
                   amount=amount,
                   from_currency=from_currency,
                   to_currency=to_currency)
        
        if from_currency == to_currency:
            return {
                'original_amount': amount,
                'converted_amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'rate': 1.0,
                'spread_applied': 0.0
            }
        
        # Get exchange rate
        today = datetime.now().date()
        exchange_rate = self.db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
            ExchangeRate.valid_date == today
        ).first()
        
        if not exchange_rate:
            # Try reverse
            exchange_rate = self.db.query(ExchangeRate).filter(
                ExchangeRate.from_currency == to_currency,
                ExchangeRate.to_currency == from_currency,
                ExchangeRate.valid_date == today
            ).first()
            
            if exchange_rate:
                rate = 1 / exchange_rate.rate
            else:
                raise Exception(f"No exchange rate found for {from_currency}/{to_currency}")
        else:
            rate = exchange_rate.rate
        
        # Apply spread if requested
        spread = exchange_rate.spread if apply_spread else 0.0
        effective_rate = rate * (1 + spread)
        
        # Convert
        converted_amount = amount * effective_rate
        
        result = {
            'original_amount': amount,
            'converted_amount': round(converted_amount, 2),
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': rate,
            'spread_applied': spread,
            'effective_rate': effective_rate
        }
        
        logger.info("Currency converted successfully",
                   task_id=self.request.id,
                   result=result)
        
        return result
        
    except Exception as e:
        logger.error("Currency conversion failed",
                    task_id=self.request.id,
                    error=str(e))
        raise


@app.task(
    bind=True,
    base=ExchangeRateTask,
    name='src.tasks.exchange_rate_tasks.bulk_update_exchange_rates'
)
def bulk_update_exchange_rates(self, currency_pairs: list[tuple[str, str]]):
    """
    Update multiple exchange rates in bulk
    
    Args:
        currency_pairs: List of (from_currency, to_currency) tuples
    """
    results = []
    
    for from_currency, to_currency in currency_pairs:
        try:
            if from_currency == "COP" and to_currency == "USD":
                # Update TRM
                result = update_trm.apply_async()
                results.append({
                    'pair': f"{from_currency}/{to_currency}",
                    'task_id': result.id,
                    'status': 'queued'
                })
            else:
                # TODO: Implement other currency pairs
                results.append({
                    'pair': f"{from_currency}/{to_currency}",
                    'status': 'not_supported'
                })
        except Exception as e:
            results.append({
                'pair': f"{from_currency}/{to_currency}",
                'status': 'failed',
                'error': str(e)
            })
    
    return results