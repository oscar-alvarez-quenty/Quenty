import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "MercadoLibre Integration Service"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # MercadoLibre API
    meli_client_id: str = os.getenv("MELI_CLIENT_ID", "")
    meli_client_secret: str = os.getenv("MELI_CLIENT_SECRET", "")
    meli_redirect_uri: str = os.getenv("MELI_REDIRECT_URI", "http://localhost:8012/auth/callback")
    meli_site_id: str = os.getenv("MELI_SITE_ID", "MCO")  # Colombia default
    meli_api_base_url: str = "https://api.mercadolibre.com"
    meli_auth_url: str = "https://auth.mercadolibre.com"
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:quenty123@localhost:5432/mercadolibre_db"
    )
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/4")
    
    # RabbitMQ
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    # Celery
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672/")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/4")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "32-byte-encryption-key-change-it")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Webhook
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
    webhook_base_url: str = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8012")
    
    # Sync Settings
    sync_interval_minutes: int = int(os.getenv("SYNC_INTERVAL_MINUTES", "30"))
    max_products_per_sync: int = int(os.getenv("MAX_PRODUCTS_PER_SYNC", "100"))
    max_orders_per_sync: int = int(os.getenv("MAX_ORDERS_PER_SYNC", "50"))
    
    # Rate Limiting
    rate_limit_calls_per_second: int = int(os.getenv("RATE_LIMIT_CALLS_PER_SECOND", "10"))
    rate_limit_burst: int = int(os.getenv("RATE_LIMIT_BURST", "20"))
    
    # CORS
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    
    # MercadoLibre Site Configuration
    @property
    def site_config(self) -> dict:
        """Get site-specific configuration"""
        sites = {
            "MLA": {"name": "Argentina", "currency": "ARS", "language": "es"},
            "MLB": {"name": "Brasil", "currency": "BRL", "language": "pt"},
            "MCO": {"name": "Colombia", "currency": "COP", "language": "es"},
            "MLM": {"name": "México", "currency": "MXN", "language": "es"},
            "MLU": {"name": "Uruguay", "currency": "UYU", "language": "es"},
            "MLC": {"name": "Chile", "currency": "CLP", "language": "es"},
            "MLV": {"name": "Venezuela", "currency": "VES", "language": "es"},
            "MPE": {"name": "Perú", "currency": "PEN", "language": "es"},
            "MEC": {"name": "Ecuador", "currency": "USD", "language": "es"},
        }
        return sites.get(self.meli_site_id, sites["MCO"])
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()