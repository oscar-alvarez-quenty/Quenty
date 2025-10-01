#!/bin/bash

# Start Celery worker
echo "Starting Celery worker..."

# Wait for RabbitMQ and Redis to be ready
echo "Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
  sleep 1
done

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done

echo "Starting worker with queues: default, quotes, labels, tracking, webhooks, priority"

# Start worker with concurrency based on CPU cores
celery -A src.celery_app worker \
  --loglevel=info \
  --queues=default,quotes,labels,tracking,webhooks,priority \
  --concurrency=4 \
  --max-tasks-per-child=100 \
  --time-limit=600 \
  --soft-time-limit=540