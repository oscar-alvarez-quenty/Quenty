from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Service Configuration
    service_name: str = "auth-service"
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql+asyncpg://auth:auth_pass@localhost:5436/auth_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/3"
    
    # JWT Configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    jwt_refresh_expiration_days: int = 7
    
    # OAuth Configuration
    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8003/auth/google/callback"
    
    # Azure OAuth
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_redirect_uri: str = "http://localhost:8003/auth/azure/callback"
    
    # Service Discovery
    consul_host: str = "localhost"
    consul_port: int = 8500
    
    # Security
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    # Email Configuration (for password reset, etc.)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    # Initial Admin User (for bootstrapping)
    initial_admin_username: Optional[str] = None
    initial_admin_password: Optional[str] = None
    initial_admin_email: Optional[str] = None
    initial_admin_first_name: Optional[str] = "System"
    initial_admin_last_name: Optional[str] = "Administrator"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()