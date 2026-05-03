from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/conflict_zero"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "dev-encryption-key-32chars-long!!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Conflict Zero API"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # External APIs
    SUNAT_API_URL: Optional[str] = None
    OSCE_API_URL: Optional[str] = None
    TCE_API_URL: Optional[str] = None
    FACTALIZA_API_KEY: Optional[str] = None
    
    # Culqi Webhook
    CULQI_WEBHOOK_SECRET: Optional[str] = None
    
    # Email
    SENDGRID_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "noreply@conflictzero.com"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
