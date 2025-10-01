# WooCommerce Integration Service

Microservice for integrating WooCommerce stores with the Quenty logistics platform.

## Features

- **Store Management**: Connect multiple WooCommerce stores
- **Order Synchronization**: Automatic sync of WooCommerce orders  
- **Product Sync**: Bidirectional product catalog synchronization
- **Inventory Management**: Real-time stock updates
- **Webhook Support**: Real-time event processing from WooCommerce
- **Shipping Integration**: Automatic fulfillment with carrier tracking

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with AsyncPG
- **ORM**: SQLAlchemy 2.x (Async)
- **Migrations**: Alembic
- **API Client**: WooCommerce REST API v3

## Setup

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://woocommerce_user:woocommerce_pass@localhost:5432/woocommerce_db
SERVICE_PORT=8013
LOG_LEVEL=INFO
```

### Installation

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8013
```

## API Endpoints

- `POST /api/v1/stores` - Connect WooCommerce store
- `GET /api/v1/orders` - List synced orders
- `POST /api/v1/products/sync` - Sync products
- `POST /api/v1/webhooks` - Receive webhooks
