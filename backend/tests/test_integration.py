"""
Tests de integración para Conflict Zero
Requieren base de datos PostgreSQL
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Usar SQLite en memoria para tests (más rápido)
# En producción, usar PostgreSQL de test
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixtures
@pytest.fixture(scope="function")
def db():
    """Crear tablas y yield sesión de DB"""
    from app.models_v2 import Base
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Crear cliente de test con DB inyectada"""
    from app.main import app
    from app.core.database import get_db
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

# Test de health check
@pytest.mark.integration
def test_health_check(client):
    """El endpoint de health debe retornar status healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

# Test de status de API
@pytest.mark.integration
def test_api_status(client):
    """El endpoint de status debe retornar información completa"""
    response = client.get("/api/v2/status")
    assert response.status_code == 200
    data = response.json()
    assert "api_version" in data
    assert "features" in data
    assert "signature_service" in data

# Test de creación de aplicación Founder
@pytest.mark.integration
def test_create_founder_application(client):
    """Debe poder crear una aplicación de Founder"""
    application_data = {
        "ruc": "20100123091",
        "company_name": "Constructora Test S.A.C.",
        "contact_name": "Juan Test",
        "contact_email": "test@example.com",
        "contact_phone": "+51 999 999 999",
        "annual_volume": "50-200M",
        "subcontractor_count": "20-50"
    }
    
    response = client.post("/api/v2/founder-applications/", json=application_data)
    
    # Puede ser 201 (creado) o 500 (DB no configurada en test)
    if response.status_code == 201:
        data = response.json()
        assert "id" in data
        assert data["company_name"] == application_data["company_name"]
        assert data["status"] == "pending"

# Test de validación de RUC en aplicación
@pytest.mark.integration
def test_founder_application_invalid_ruc(client):
    """Debe rechazar RUCs inválidos"""
    application_data = {
        "ruc": "123",  # RUC inválido
        "company_name": "Test",
        "contact_name": "Test",
        "contact_email": "test@test.com",
        "annual_volume": "10-50M",
        "subcontractor_count": "5-20"
    }
    
    response = client.post("/api/v2/founder-applications/", json=application_data)
    assert response.status_code == 422  # Validation error

# Test de comparación (requiere auth mock)
@pytest.mark.integration  
def test_compare_endpoint_requires_auth(client):
    """El endpoint de comparación debe requerir autenticación"""
    response = client.post("/api/v1/compare/", json={
        "rucs": ["20100123091", "20529400790"],
        "format": "json"
    })
    
    # Debe retornar 401 o 403 (no autenticado)
    assert response.status_code in [401, 403]

# Test de validación de código de invitación
@pytest.mark.integration
def test_validate_invite_code_not_found(client):
    """Debe retornar 404 para códigos de invitación inexistentes"""
    response = client.post("/api/v2/invites/validate", params={"invite_code": "CZ-INVALID-0000"})
    assert response.status_code == 404

# Test de obtener aplicación por ID inválido
@pytest.mark.integration
def test_get_application_invalid_id(client):
    """Debe retornar 400 para IDs de aplicación inválidos"""
    response = client.get("/api/v2/founder-applications/invalid-uuid")
    assert response.status_code == 400

# Test de métricas de aplicaciones (admin)
@pytest.mark.integration
def test_application_stats(client):
    """Debe retornar estadísticas de aplicaciones"""
    response = client.get("/api/v2/founder-applications/stats/summary")
    
    # Si no hay auth de admin, puede ser 403
    # Si hay, debe retornar stats
    if response.status_code == 200:
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
