from celery import Task, group, chain, chord
from ..celery_app import app
from typing import Dict, Any, List
import structlog
from datetime import datetime, timedelta
import csv
import io
import json

from ..database import SessionLocal
from ..models import ShippingLabel, ShippingQuote, TrackingEvent, CarrierType
from .carrier_tasks import get_quote_async, generate_label_async
from .tracking_tasks import sync_tracking_async

logger = structlog.get_logger()


class BatchTask(Task):
    """Base task for batch operations"""
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
    base=BatchTask,
    name='src.tasks.batch_tasks.process_batch_shipments',
    max_retries=3
)
def process_batch_shipments(self, shipments: List[Dict[str, Any]], callback_url: str = None):
    """
    Process multiple shipments in batch
    
    Args:
        shipments: List of shipment data
        callback_url: Optional URL to send results to
    
    Returns:
        Batch processing results
    """
    try:
        logger.info("Processing batch shipments",
                   task_id=self.request.id,
                   count=len(shipments))
        
        # Create a chord: parallel execution with callback
        header = group(
            chain(
                get_quote_async.s(shipment),
                generate_label_async.s(shipment)
            ) for shipment in shipments
        )
        
        # Callback to collect results
        callback = collect_batch_results.s(callback_url)
        
        # Execute chord
        result = chord(header)(callback)
        
        return {
            'status': 'processing',
            'batch_id': self.request.id,
            'shipment_count': len(shipments),
            'result_task_id': result.id
        }
        
    except Exception as e:
        logger.error("Batch processing failed",
                    task_id=self.request.id,
                    error=str(e))
        raise self.retry(exc=e)


@app.task(
    name='src.tasks.batch_tasks.collect_batch_results'
)
def collect_batch_results(results: List[Dict[str, Any]], callback_url: str = None):
    """Collect and process batch results"""
    successful = [r for r in results if r and r.get('success')]
    failed = [r for r in results if r and not r.get('success')]
    
    summary = {
        'total': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    
    logger.info("Batch processing completed",
               total=summary['total'],
               successful=summary['successful'],
               failed=summary['failed'])
    
    # Send callback if provided
    if callback_url:
        import httpx
        try:
            with httpx.Client() as client:
                client.post(callback_url, json=summary, timeout=30.0)
        except Exception as e:
            logger.error("Failed to send batch callback", error=str(e))
    
    return summary


@app.task(
    bind=True,
    base=BatchTask,
    name='src.tasks.batch_tasks.import_shipments_csv',
    max_retries=2
)
def import_shipments_csv(self, csv_data: str, auto_process: bool = False):
    """
    Import shipments from CSV and optionally process them
    
    Args:
        csv_data: CSV string data
        auto_process: Whether to automatically process imported shipments
    
    Returns:
        Import results
    """
    try:
        logger.info("Importing shipments from CSV",
                   task_id=self.request.id)
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_data))
        shipments = []
        
        for row in reader:
            shipment = {
                'origin': {
                    'street': row.get('origin_street'),
                    'city': row.get('origin_city'),
                    'state': row.get('origin_state'),
                    'postal_code': row.get('origin_postal_code'),
                    'country': row.get('origin_country'),
                    'contact_name': row.get('origin_contact_name'),
                    'contact_phone': row.get('origin_contact_phone'),
                    'contact_email': row.get('origin_contact_email')
                },
                'destination': {
                    'street': row.get('dest_street'),
                    'city': row.get('dest_city'),
                    'state': row.get('dest_state'),
                    'postal_code': row.get('dest_postal_code'),
                    'country': row.get('dest_country'),
                    'contact_name': row.get('dest_contact_name'),
                    'contact_phone': row.get('dest_contact_phone'),
                    'contact_email': row.get('dest_contact_email')
                },
                'packages': [{
                    'weight_kg': float(row.get('weight_kg', 1)),
                    'length_cm': float(row.get('length_cm', 10)),
                    'width_cm': float(row.get('width_cm', 10)),
                    'height_cm': float(row.get('height_cm', 10)),
                    'declared_value': float(row.get('declared_value', 0)),
                    'currency': row.get('currency', 'USD')
                }],
                'service_type': row.get('service_type', 'standard'),
                'carrier': row.get('carrier'),
                'order_id': row.get('order_id')
            }
            shipments.append(shipment)
        
        logger.info("CSV parsed successfully",
                   shipment_count=len(shipments))
        
        # Process if requested
        if auto_process:
            result = process_batch_shipments.delay(shipments)
            return {
                'status': 'processing',
                'imported': len(shipments),
                'batch_task_id': result.id
            }
        
        return {
            'status': 'imported',
            'count': len(shipments),
            'shipments': shipments
        }
        
    except Exception as e:
        logger.error("CSV import failed",
                    task_id=self.request.id,
                    error=str(e))
        raise


@app.task(
    bind=True,
    base=BatchTask,
    name='src.tasks.batch_tasks.generate_daily_report'
)
def generate_daily_report(self, date: str = None):
    """
    Generate daily shipping report
    
    Args:
        date: Date for report (YYYY-MM-DD format), defaults to today
    
    Returns:
        Report data
    """
    try:
        if date:
            report_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            report_date = datetime.now().date()
        
        logger.info("Generating daily report",
                   task_id=self.request.id,
                   date=report_date)
        
        # Get shipments for the day
        start_time = datetime.combine(report_date, datetime.min.time())
        end_time = datetime.combine(report_date, datetime.max.time())
        
        # Query labels created
        labels = self.db.query(ShippingLabel).filter(
            ShippingLabel.created_at >= start_time,
            ShippingLabel.created_at <= end_time
        ).all()
        
        # Query quotes generated
        quotes = self.db.query(ShippingQuote).filter(
            ShippingQuote.created_at >= start_time,
            ShippingQuote.created_at <= end_time
        ).all()
        
        # Query tracking events
        tracking_events = self.db.query(TrackingEvent).filter(
            TrackingEvent.created_at >= start_time,
            TrackingEvent.created_at <= end_time
        ).all()
        
        # Calculate statistics by carrier
        carrier_stats = {}
        for carrier in CarrierType:
            carrier_labels = [l for l in labels if l.carrier == carrier]
            carrier_quotes = [q for q in quotes if q.carrier == carrier]
            
            carrier_stats[carrier.value] = {
                'labels_generated': len(carrier_labels),
                'quotes_generated': len(carrier_quotes),
                'total_value': sum(q.amount for q in carrier_quotes),
                'avg_quote_value': sum(q.amount for q in carrier_quotes) / len(carrier_quotes) if carrier_quotes else 0
            }
        
        # Calculate delivery statistics
        delivered = len([e for e in tracking_events if e.status.lower() in ['delivered', 'entregado']])
        in_transit = len([e for e in tracking_events if e.status.lower() in ['in transit', 'en transito']])
        exceptions = len([e for e in tracking_events if e.status.lower() in ['exception', 'failed']])
        
        report = {
            'date': report_date.isoformat(),
            'summary': {
                'total_labels': len(labels),
                'total_quotes': len(quotes),
                'total_tracking_events': len(tracking_events),
                'delivered': delivered,
                'in_transit': in_transit,
                'exceptions': exceptions
            },
            'carrier_breakdown': carrier_stats,
            'top_routes': self._get_top_routes(quotes),
            'generated_at': datetime.now().isoformat()
        }
        
        # Save report
        save_report.delay(report)
        
        # Send report
        send_daily_report.delay(report)
        
        logger.info("Daily report generated successfully",
                   task_id=self.request.id,
                   date=report_date)
        
        return report
        
    except Exception as e:
        logger.error("Failed to generate daily report",
                    task_id=self.request.id,
                    error=str(e))
        raise
    
    def _get_top_routes(self, quotes: List[ShippingQuote]) -> List[Dict]:
        """Get top shipping routes"""
        routes = {}
        for quote in quotes:
            route = f"{quote.origin_city}-{quote.destination_city}"
            if route not in routes:
                routes[route] = {'count': 0, 'total_value': 0}
            routes[route]['count'] += 1
            routes[route]['total_value'] += quote.amount
        
        # Sort by count and return top 10
        sorted_routes = sorted(routes.items(), key=lambda x: x[1]['count'], reverse=True)
        return [
            {
                'route': route,
                'count': data['count'],
                'total_value': data['total_value'],
                'avg_value': data['total_value'] / data['count'] if data['count'] > 0 else 0
            }
            for route, data in sorted_routes[:10]
        ]


@app.task(
    name='src.tasks.batch_tasks.save_report'
)
def save_report(report: Dict[str, Any]):
    """Save report to storage"""
    logger.info("Saving report", date=report['date'])
    
    # TODO: Implement report storage
    # - Save to S3
    # - Save to database
    # - Save to file system
    
    return {'status': 'saved'}


@app.task(
    name='src.tasks.batch_tasks.send_daily_report'
)
def send_daily_report(report: Dict[str, Any]):
    """Send daily report to stakeholders"""
    logger.info("Sending daily report", date=report['date'])
    
    # TODO: Implement report distribution
    # - Send email to management
    # - Post to Slack
    # - Update dashboard
    
    return {'status': 'sent'}


@app.task(
    bind=True,
    base=BatchTask,
    name='src.tasks.batch_tasks.reprocess_failed_shipments'
)
def reprocess_failed_shipments(self, time_range_hours: int = 24):
    """
    Reprocess shipments that failed in the last N hours
    
    Args:
        time_range_hours: Look back period in hours
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
        
        # TODO: Query failed shipments from database
        # This would require tracking failed attempts
        
        failed_shipments = []  # Placeholder
        
        if failed_shipments:
            # Reprocess in batch
            result = process_batch_shipments.delay(failed_shipments)
            
            return {
                'status': 'reprocessing',
                'count': len(failed_shipments),
                'batch_task_id': result.id
            }
        
        return {
            'status': 'no_failed_shipments',
            'count': 0
        }
        
    except Exception as e:
        logger.error("Failed to reprocess shipments",
                    task_id=self.request.id,
                    error=str(e))
        raise


@app.task(
    bind=True,
    name='src.tasks.batch_tasks.cancel_batch_shipments'
)
def cancel_batch_shipments(self, tracking_numbers: List[str]):
    """
    Cancel multiple shipments in batch
    
    Args:
        tracking_numbers: List of tracking numbers to cancel
    """
    results = []
    
    for tracking_number in tracking_numbers:
        try:
            # TODO: Implement actual cancellation with carriers
            # This would call carrier-specific cancellation APIs
            
            results.append({
                'tracking_number': tracking_number,
                'status': 'cancelled'
            })
        except Exception as e:
            results.append({
                'tracking_number': tracking_number,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'total': len(tracking_numbers),
        'cancelled': len([r for r in results if r['status'] == 'cancelled']),
        'failed': len([r for r in results if r['status'] == 'failed']),
        'results': results
    }