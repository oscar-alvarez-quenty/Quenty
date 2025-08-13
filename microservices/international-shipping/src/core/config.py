from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = "international-shipping-service"
    database_url: str = "postgresql+asyncpg://intlship:intlship_pass@intl-shipping-db:5432/intl_shipping_db"
    redis_url: str = "redis://redis:6379/4"
    consul_host: str = "consul"
    consul_port: int = 8500
    auth_service_url: str = "http://auth-service:8003"

    class Config:
        env_file = ".env"


settings = Settings()