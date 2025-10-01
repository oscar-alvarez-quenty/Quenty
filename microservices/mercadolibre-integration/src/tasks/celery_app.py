"""
Celery Application for MercadoLibre Integration
"""
import os
from celery import Celery

# Create Celery app
celery_app = Celery(
    'meli_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/4'),
    include=['src.tasks.product_tasks', 'src.tasks.order_tasks', 'src.tasks.question_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_routes={
        'src.tasks.product_tasks.*': {'queue': 'products'},
        'src.tasks.order_tasks.*': {'queue': 'orders'},
        'src.tasks.question_tasks.*': {'queue': 'questions'},
    },
    beat_schedule={
        'sync-products': {
            'task': 'src.tasks.product_tasks.sync_all_products',
            'schedule': 3600.0,  # Every hour
        },
        'sync-orders': {
            'task': 'src.tasks.order_tasks.sync_recent_orders',
            'schedule': 600.0,  # Every 10 minutes
        },
    }
)