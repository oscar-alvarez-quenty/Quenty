#!/bin/bash

# Start Flower monitoring dashboard
echo "Starting Flower monitoring dashboard..."

# Wait for RabbitMQ and Redis to be ready
echo "Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
  sleep 1
done

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done

echo "Starting Flower on port 5555..."

# Start Flower with authentication
celery -A src.celery_app flower \
  --port=5555 \
  --broker_api=http://guest:guest@rabbitmq:15672/api/ \
  --max_tasks=10000 \
  --persistent=true \
  --db=/tmp/flower.db \
  --state_save_interval=60000