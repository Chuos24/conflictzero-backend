"""
Conflict Zero - Database Configuration
PostgreSQL connection with SQLAlchemy
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/conflict_zero"
)

# Fix for Render's postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from app.models_v2 import (
        Company, FounderApplication, PublicProfile, Invite,
        VerificationRequest, CompanyHierarchy, ApiKey, Webhook,
        ApiCache, AuditLog, DigitalSignature, SystemConfig
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()
            print(f"✅ PostgreSQL connected: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
