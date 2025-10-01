"""
Celery Application Configuration
"""
import os
from celery import Celery

# Create Celery app
celery_app = Celery(
    'shopify_tasks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/2'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/2'),
    include=['tasks.sync_tasks', 'tasks.webhook_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    beat_schedule={
        'sync-all-stores': {
            'task': 'tasks.sync_tasks.sync_all_stores',
            'schedule': 3600.0,  # Run every hour
        },
    }
)