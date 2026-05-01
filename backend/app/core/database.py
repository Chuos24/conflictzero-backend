from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Base class for models — usar el mismo Base que models_v2 para unificar metadata
from app.models_v2 import Base

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables."""
    from app.models_v2 import (
        Company, FounderApplication, Invite, PublicProfile,
        VerificationRequest, CompanyHierarchy, DigitalSignature,
        ApiKey, ComparisonRequest, Webhook, WebhookDelivery,
        AuditLog, SystemConfig
    )
    from app.models_monitoring import (
        SupplierSnapshot, SupplierChange, MonitoringAlert,
        MonitoringRule, MonitoringSchedule
    )
    from app.models_network import (
        SupplierNetwork, SupplierAlert, CompanySnapshot
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

def test_connection() -> bool:
    """Test database connection."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}")
        return False

# Connection event listeners
@event.listens_for(engine, "connect")
def on_connect(dbapi_conn, connection_record):
    logger.debug("Database connection established")

@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    logger.debug("Database connection checked out from pool")
