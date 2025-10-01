.PHONY: help install dev test build run migrate clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev         - Run development server"
	@echo "  make test        - Run tests"
	@echo "  make migrate     - Run database migrations"
	@echo "  make worker      - Start Celery worker"
	@echo "  make beat        - Start Celery beat"
	@echo "  make flower      - Start Flower monitoring"
	@echo "  make docker-up   - Start all services with Docker"
	@echo "  make docker-down - Stop all Docker services"
	@echo "  make clean       - Clean up temporary files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn src.main:app --reload --port 8009

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

migrate:
	alembic upgrade head

rollback:
	alembic downgrade -1

worker:
	celery -A src.celery_app worker --loglevel=info --queues=default,quotes,labels,tracking,webhooks,priority

beat:
	celery -A src.celery_app beat --loglevel=info

flower:
	celery -A src.celery_app flower --port=5555

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +