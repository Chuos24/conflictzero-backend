"""
Conflict Zero - Configuración Centralizada
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # App
    APP_NAME: str = "Conflict Zero API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENV: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/conflict_zero"
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    ADMIN_TOKEN: str = "admin-dev-token"
    
    # Digital Signatures
    CERT_MODE: str = "demo"  # demo | production
    INDECOPI_CERT_PATH: str = "/app/certs/indecopi_cert.p12"
    INDECOPI_CERT_PASSWORD: str = ""
    
    # Email (SendGrid)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@czperu.com"
    EMAIL_ENABLED: bool = False
    
    # Frontend URLs
    FRONTEND_URL: str = "https://czperu.com"
    FOUNDERS_URL: str = "https://founders.czperu.com"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Founder Program
    FOUNDER_MAX_SLOTS: int = 10
    FOUNDER_DURATION_MONTHS: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retorna settings cacheados"""
    return Settings()
