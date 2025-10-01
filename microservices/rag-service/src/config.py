import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Quenty RAG Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:quenty123@localhost:5432/rag_db"
    )
    
    # Vector database settings
    vector_db_url: str = os.getenv(
        "VECTOR_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/vector_db"
    )
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/2")
    
    # OpenAI settings (for embeddings and LLM)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # Alternative: Use local models
    use_local_models: bool = os.getenv("USE_LOCAL_MODELS", "true").lower() == "true"
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Microservices database connections
    auth_db_url: str = os.getenv(
        "AUTH_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/auth_db"
    )
    customer_db_url: str = os.getenv(
        "CUSTOMER_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/customer_db"
    )
    order_db_url: str = os.getenv(
        "ORDER_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/order_db"
    )
    carrier_db_url: str = os.getenv(
        "CARRIER_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/carrier_db"
    )
    analytics_db_url: str = os.getenv(
        "ANALYTICS_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/analytics_db"
    )
    franchise_db_url: str = os.getenv(
        "FRANCHISE_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/franchise_db"
    )
    international_db_url: str = os.getenv(
        "INTERNATIONAL_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/international_db"
    )
    microcredit_db_url: str = os.getenv(
        "MICROCREDIT_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/microcredit_db"
    )
    pickup_db_url: str = os.getenv(
        "PICKUP_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/pickup_db"
    )
    reverse_logistics_db_url: str = os.getenv(
        "REVERSE_LOGISTICS_DB_URL",
        "postgresql://postgres:quenty123@localhost:5432/reverse_logistics_db"
    )
    
    # RAG settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    
    # Cache settings
    cache_ttl: int = 3600  # 1 hour
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    
    # JWT settings for API authentication
    secret_key: str = os.getenv("SECRET_KEY", "change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()