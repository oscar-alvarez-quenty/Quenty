#!/bin/bash

# Start Celery beat scheduler
echo "Starting Celery beat scheduler..."

# Wait for RabbitMQ and Redis to be ready
echo "Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
  sleep 1
done

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done

echo "Starting beat scheduler..."

# Start beat with pidfile
celery -A src.celery_app beat \
  --loglevel=info \
  --pidfile=/tmp/celerybeat.pid \
  --schedule=/tmp/celerybeat-schedule