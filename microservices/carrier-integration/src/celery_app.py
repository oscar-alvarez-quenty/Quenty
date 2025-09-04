from celery import Celery
from celery.schedules import crontab
import os
from kombu import Exchange, Queue

# Get configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/2")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672//")

# Create Celery app
app = Celery(
    'carrier_integration',
    broker=RABBITMQ_URL,  # Use RabbitMQ as message broker
    backend=REDIS_URL,     # Use Redis for result backend
    include=[
        'src.tasks.carrier_tasks',
        'src.tasks.tracking_tasks',
        'src.tasks.exchange_rate_tasks',
        'src.tasks.webhook_tasks',
        'src.tasks.batch_tasks'
    ]
)

# Celery configuration
app.conf.update(
    # Task configuration
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    
    # Task execution configuration
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=4,
    
    # Result backend configuration
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600
    },
    
    # Retry configuration
    task_default_retry_delay=60,  # 60 seconds
    task_max_retries=3,
    
    # Queue configuration
    task_default_queue='default',
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('quotes', Exchange('quotes'), routing_key='quotes.*'),
        Queue('labels', Exchange('labels'), routing_key='labels.*'),
        Queue('tracking', Exchange('tracking'), routing_key='tracking.*'),
        Queue('webhooks', Exchange('webhooks'), routing_key='webhooks.*'),
        Queue('batch', Exchange('batch'), routing_key='batch.*'),
        Queue('mailbox', Exchange('mailbox'), routing_key='mailbox.*'),
        Queue('priority', Exchange('priority'), routing_key='priority.*', priority=10),
    ),
    
    # Routing configuration
    task_routes={
        'src.tasks.carrier_tasks.get_quote_async': {'queue': 'quotes'},
        'src.tasks.carrier_tasks.generate_label_async': {'queue': 'labels'},
        'src.tasks.tracking_tasks.*': {'queue': 'tracking'},
        'src.tasks.webhook_tasks.*': {'queue': 'webhooks'},
        'src.tasks.batch_tasks.*': {'queue': 'batch'},
        'src.tasks.international_mailbox_tasks.*': {'queue': 'mailbox'},
        'src.tasks.carrier_tasks.urgent_*': {'queue': 'priority'},
    },
    
    # Worker configuration
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    worker_disable_rate_limits=False,
    worker_concurrency=4,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Update TRM every day at 6:00 AM
        'update-trm-daily': {
            'task': 'src.tasks.exchange_rate_tasks.update_trm',
            'schedule': crontab(hour=6, minute=0),
            'options': {'queue': 'default'}
        },
        # Check TRM variation every day at 7:00 AM
        'check-trm-variation': {
            'task': 'src.tasks.exchange_rate_tasks.check_trm_variation',
            'schedule': crontab(hour=7, minute=0),
            'options': {'queue': 'default'}
        },
        # Sync tracking updates every 30 minutes
        'sync-tracking-updates': {
            'task': 'src.tasks.tracking_tasks.sync_all_tracking',
            'schedule': crontab(minute='*/30'),
            'options': {'queue': 'tracking'}
        },
        # Health check all carriers every 5 minutes
        'health-check-carriers': {
            'task': 'src.tasks.carrier_tasks.health_check_all_carriers',
            'schedule': crontab(minute='*/5'),
            'options': {'queue': 'default'}
        },
        # Clean old tracking events daily at 2:00 AM
        'clean-old-tracking': {
            'task': 'src.tasks.tracking_tasks.clean_old_tracking_events',
            'schedule': crontab(hour=2, minute=0),
            'options': {'queue': 'default'}
        },
        # Generate daily reports at 11:00 PM
        'generate-daily-reports': {
            'task': 'src.tasks.batch_tasks.generate_daily_report',
            'schedule': crontab(hour=23, minute=0),
            'options': {'queue': 'batch'}
        }
    }
)

# Configure Celery to use JSON for serialization
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

if __name__ == '__main__':
    app.start()