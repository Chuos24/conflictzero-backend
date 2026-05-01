"""
Shared pytest fixtures for backend tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Crear tablas y yield sesión de DB."""
    from app.models_v2 import Base
    # Importar todos los modelos para registrar sus tablas en Base.metadata
    from app.models_v2 import Company, FounderApplication, Invite, PublicProfile, VerificationRequest, CompanyHierarchy, DigitalSignature, ApiKey, ComparisonRequest, Webhook, WebhookDelivery, AuditLog, SystemConfig
    from app.models_monitoring import SupplierSnapshot, SupplierChange, MonitoringAlert, MonitoringRule, MonitoringSchedule
    from app.models_network import SupplierNetwork, SupplierAlert, CompanySnapshot
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_company(db):
    """Crear empresa de prueba para autenticación."""
    from app.models_v2 import Company
    company = Company(
        ruc_encrypted=b"encrypted_20100012345",
        ruc_hash="abcd1234",
        razon_social="Empresa Test S.A.C.",
        status="active",
        plan_tier="bronze",
        is_founder=True,
        contact_email="test@example.com"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture(scope="function")
def client(db, test_company):
    """Crear cliente de test con DB inyectada y auth mockeada."""
    from app.main import app
    from app.core.database import get_db
    from app.core.security import get_current_company

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_current_company():
        return test_company

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_company] = override_get_current_company

    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers():
    """Headers de autenticación dummy (el auth está mockeado en client)."""
    return {"Authorization": "Bearer test-token"}
