from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, List
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")
    
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
    ENV: str = "development"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Conflict Zero API"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
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
    SENDGRID_FROM_EMAIL: Optional[str] = None
    SENDGRID_FROM_NAME: Optional[str] = None
    EMAIL_ENABLED: bool = False
    
    # App Info
    APP_NAME: str = "Conflict Zero API"
    APP_VERSION: str = "1.0.0"
    
    # Admin
    ADMIN_TOKEN: Optional[str] = None
    
    # Frontend URLs
    FRONTEND_URL: Optional[str] = None
    FOUNDERS_URL: Optional[str] = None
    
    # Founder Program
    FOUNDER_MAX_SLOTS: int = 10
    FOUNDER_DURATION_MONTHS: int = 3
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Push Notifications
    EXPO_ACCESS_TOKEN: Optional[str] = None
    
    # Refresh token days (alternative to minutes)
    REFRESH_TOKEN_EXPIRE_DAYS: Optional[int] = None
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
