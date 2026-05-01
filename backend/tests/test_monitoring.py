"""
Tests para el módulo de monitoreo continuo.
Fase 2 - Conflict Zero
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models_monitoring import (
    SupplierSnapshot, SupplierChange, MonitoringAlert,
    MonitoringRule, MonitoringSchedule
)
from app.models_v2 import Company


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(autouse=True)
def mock_data_collection(monkeypatch):
    """Mock de colecta de datos externa para evitar conexiones reales."""
    def fake_collect(ruc):
        return {
            "ruc": ruc,
            "razon_social": "Empresa Test S.A.C.",
            "status": "active",
            "sanctions": [],
            "sanctions_count": 0,
            "risk_score": 50.0,
            "compliance_score": 80.0,
            "representatives": [],
            "address": "Av. Test 123"
        }
    def fake_risk_score(raw_data):
        return raw_data.get("risk_score", 50.0)
    
    monkeypatch.setattr("app.services.monitoring_service.collect_company_data", fake_collect)
    monkeypatch.setattr("app.services.monitoring_service.calculate_risk_score", fake_risk_score)


@pytest.fixture
def test_company(db: Session):
    """Crea una empresa de prueba."""
    company = Company(
        ruc_encrypted=b"encrypted_20100012345",
        ruc_hash="abcd1234",
        razon_social="Empresa Test S.A.C.",
        status="active",
        plan_tier="bronze",
        contact_email="test@example.com"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


TEST_RUC = "20100012345"


@pytest.fixture
def test_snapshot(db: Session, test_company):
    """Crea un snapshot de prueba."""
    snapshot = SupplierSnapshot(
        company_id=test_company.id,
        ruc=TEST_RUC,
        raw_data={"name": test_company.razon_social, "status": "active"},
        risk_score=75.0,
        status="active",
        snapshot_date=datetime.utcnow()
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@pytest.fixture
def test_change(db: Session, test_snapshot, test_company):
    """Crea un cambio detectado de prueba."""
    change = SupplierChange(
        snapshot_id=test_snapshot.id,
        company_id=test_company.id,
        change_type="risk_score_drop",
        severity="high",
        previous_value="75.0",
        new_value="45.0",
        description="Caída significativa del score de riesgo"
    )
    db.add(change)
    db.commit()
    db.refresh(change)
    return change


@pytest.fixture
def test_alert(db: Session, test_company, test_change):
    """Crea una alerta de prueba."""
    alert = MonitoringAlert(
        company_id=test_company.id,
        change_id=test_change.id,
        channel="email",
        status="pending",
        title="Alerta: Score de riesgo cayó",
        message="El proveedor tuvo una caída de 30 puntos en su score de riesgo."
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# ============================================================
# TESTS DE MODELOS
# ============================================================

class TestMonitoringModels:
    """Tests para los modelos de monitoreo."""

    def test_create_snapshot(self, db: Session, test_company):
        """Test creación de snapshot."""
        snapshot = SupplierSnapshot(
            company_id=test_company.id,
            ruc=TEST_RUC,
            raw_data={"test": "data"},
            risk_score=50.0,
            status="active"
        )
        db.add(snapshot)
        db.commit()

        assert snapshot.id is not None
        assert snapshot.ruc == TEST_RUC
        assert snapshot.risk_score == 50.0
        assert snapshot.status == "active"
        assert snapshot.created_at is not None

    def test_snapshot_company_id(self, db: Session, test_snapshot, test_company):
        """Test que snapshot tiene company_id correcto."""
        assert str(test_snapshot.company_id) == str(test_company.id)

    def test_create_change(self, db: Session, test_snapshot, test_company):
        """Test creación de cambio detectado."""
        change = SupplierChange(
            snapshot_id=test_snapshot.id,
            company_id=test_company.id,
            change_type="address_change",
            severity="medium",
            previous_value="Av. Antigua 123",
            new_value="Av. Nueva 456",
            description="Cambio de dirección fiscal"
        )
        db.add(change)
        db.commit()

        assert change.id is not None
        assert change.change_type == "address_change"
        assert change.severity == "medium"
        assert change.previous_value == "Av. Antigua 123"
        assert change.new_value == "Av. Nueva 456"

    def test_create_alert(self, db: Session, test_company, test_change):
        """Test creación de alerta."""
        alert = MonitoringAlert(
            company_id=test_company.id,
            change_id=test_change.id,
            channel="email",
            status="pending",
            title="Nueva sanción detectada",
            message="Se detectó una nueva sanción en OSCE"
        )
        db.add(alert)
        db.commit()

        assert alert.id is not None
        assert alert.status == "pending"
        assert alert.read_at is None

    def test_mark_alert_read(self, db: Session, test_alert):
        """Test marcar alerta como leída."""
        test_alert.status = "read"
        test_alert.read_at = datetime.utcnow()
        db.commit()
        db.refresh(test_alert)

        assert test_alert.status == "read"
        assert test_alert.read_at is not None

    def test_create_rule(self, db: Session, test_company):
        """Test creación de regla de monitoreo."""
        rule = MonitoringRule(
            company_id=test_company.id,
            rule_type="risk_score_drop",
            conditions={"threshold": 10.0},
            notify_email=True,
            notify_dashboard=True,
            frequency="daily"
        )
        db.add(rule)
        db.commit()

        assert rule.id is not None
        assert rule.rule_type == "risk_score_drop"
        assert rule.conditions == {"threshold": 10.0}
        assert rule.notify_email is True

    def test_create_schedule(self, db: Session):
        """Test creación de schedule."""
        schedule = MonitoringSchedule(
            status="scheduled",
            schedule_type="daily"
        )
        db.add(schedule)
        db.commit()

        assert schedule.id is not None
        assert schedule.status == "scheduled"
        assert schedule.completed_at is None


# ============================================================
# TESTS DE API
# ============================================================

class TestMonitoringAPI:
    """Tests para los endpoints de monitoreo."""

    def test_get_alerts(self, client: TestClient, auth_headers, test_alert):
        """Test GET /api/v2/monitoring/alerts."""
        response = client.get("/api/v2/monitoring/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_alerts_with_status_filter(self, client: TestClient, auth_headers, test_alert):
        """Test GET /api/v2/monitoring/alerts?status=pending."""
        response = client.get("/api/v2/monitoring/alerts?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(a["status"] == "pending" for a in data)

    def test_mark_alert_read(self, client: TestClient, auth_headers, test_alert):
        """Test POST /api/v2/monitoring/alerts/{id}/read."""
        response = client.post(
            f"/api/v2/monitoring/alerts/{test_alert.id}/read",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_dismiss_alert(self, client: TestClient, auth_headers, test_alert):
        """Test POST /api/v2/monitoring/alerts/{id}/dismiss."""
        response = client.post(
            f"/api/v2/monitoring/alerts/{test_alert.id}/dismiss",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_get_changes(self, client: TestClient, auth_headers, test_change):
        """Test GET /api/v2/monitoring/changes."""
        response = client.get("/api/v2/monitoring/changes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_changes_with_severity_filter(self, client: TestClient, auth_headers, test_change):
        """Test GET /api/v2/monitoring/changes?severity=high."""
        response = client.get("/api/v2/monitoring/changes?severity=high", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(c["severity"] == "high" for c in data)

    def test_get_change_detail(self, client: TestClient, auth_headers, test_change):
        """Test GET /api/v2/monitoring/changes/{id}."""
        response = client.get(
            f"/api/v2/monitoring/changes/{test_change.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert str(data["id"]) == str(test_change.id)
        assert data["change_type"] == test_change.change_type

    def test_create_snapshot(self, client: TestClient, auth_headers, test_company):
        """Test POST /api/v2/monitoring/snapshots/{company_id}."""
        response = client.post(
            f"/api/v2/monitoring/snapshots/{test_company.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert str(data["company_id"]) == str(test_company.id)
        assert "ruc" in data
        assert "snapshot_date" in data

    def test_get_snapshot_history(self, client: TestClient, auth_headers, test_company, test_snapshot):
        """Test GET /api/v2/monitoring/snapshots/{company_id}/history."""
        response = client.get(
            f"/api/v2/monitoring/snapshots/{test_company.id}/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_monitoring_stats(self, client: TestClient, auth_headers):
        """Test GET /api/v2/monitoring/stats."""
        response = client.get("/api/v2/monitoring/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_snapshots" in data
        assert "total_changes_detected" in data
        assert "pending_alerts" in data

    def test_run_monitoring_manual(self, client: TestClient, auth_headers):
        """Test POST /api/v2/monitoring/run."""
        response = client.post("/api/v2/monitoring/run", headers=auth_headers)
        # Puede ser 200 o 403 dependiendo de si el user es founder
        assert response.status_code in (200, 403)

    def test_create_rule(self, client: TestClient, auth_headers):
        """Test POST /api/v2/monitoring/rules."""
        payload = {
            "rule_type": "sanction_new",
            "conditions": {"threshold": 1.0},
            "notify_email": True,
            "notify_dashboard": True,
            "frequency": "daily"
        }
        response = client.post("/api/v2/monitoring/rules", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["rule_type"] == "sanction_new"

    def test_get_rules(self, client: TestClient, auth_headers):
        """Test GET /api/v2/monitoring/rules."""
        response = client.get("/api/v2/monitoring/rules", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_rule(self, client: TestClient, auth_headers):
        """Test PATCH /api/v2/monitoring/rules/{id}."""
        # Primero crear una regla
        payload = {
            "rule_type": "risk_score_drop",
            "conditions": {"threshold": 10.0},
            "notify_email": True,
            "frequency": "daily"
        }
        create_response = client.post("/api/v2/monitoring/rules", json=payload, headers=auth_headers)
        rule_id = create_response.json()["id"]

        # Actualizar
        update_payload = {"conditions": {"threshold": 15.0}, "notify_email": False}
        response = client.patch(
            f"/api/v2/monitoring/rules/{rule_id}",
            json=update_payload,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["id"] == rule_id

    def test_delete_rule(self, client: TestClient, auth_headers):
        """Test DELETE /api/v2/monitoring/rules/{id}."""
        payload = {
            "rule_type": "address_change",
            "conditions": {},
            "notify_email": True,
            "frequency": "daily"
        }
        create_response = client.post("/api/v2/monitoring/rules", json=payload, headers=auth_headers)
        rule_id = create_response.json()["id"]

        response = client.delete(f"/api/v2/monitoring/rules/{rule_id}", headers=auth_headers)
        assert response.status_code == 200
        assert "message" in response.json()


# ============================================================
# TESTS DE SERVICIO
# ============================================================

class TestMonitoringService:
    """Tests para monitoring_service."""

    def test_detect_risk_score_drop(self):
        """Test detección de caída de score de riesgo."""
        from app.services.monitoring_service import detect_changes

        old_data = {"risk_score": 75.0, "status": "active"}
        new_data = {"risk_score": 45.0, "status": "active"}

        changes = detect_changes(old_data, new_data)

        assert len(changes) >= 1
        risk_change = [c for c in changes if c["change_type"] == "risk_score_drop"]
        assert len(risk_change) == 1
        assert risk_change[0]["severity"] == "high"
        assert risk_change[0]["old_value"] == "75.0"
        assert risk_change[0]["new_value"] == "45.0"

    def test_detect_new_sanction(self):
        """Test detección de nueva sanción."""
        from app.services.monitoring_service import detect_changes

        old_data = {"sanctions_count": 0, "status": "active"}
        new_data = {"sanctions_count": 1, "status": "sanctioned"}

        changes = detect_changes(old_data, new_data)

        sanction_change = [c for c in changes if c["change_type"] == "sanction_new"]
        assert len(sanction_change) == 1
        assert sanction_change[0]["severity"] == "critical"

    def test_detect_address_change(self):
        """Test detección de cambio de dirección."""
        from app.services.monitoring_service import detect_changes

        old_data = {"address": "Av. Antigua 123"}
        new_data = {"address": "Av. Nueva 456"}

        changes = detect_changes(old_data, new_data)

        address_change = [c for c in changes if c["change_type"] == "address_change"]
        assert len(address_change) == 1
        assert address_change[0]["severity"] == "medium"

    def test_no_changes(self):
        """Test cuando no hay cambios."""
        from app.services.monitoring_service import detect_changes

        old_data = {"risk_score": 75.0, "status": "active"}
        new_data = {"risk_score": 75.0, "status": "active"}

        changes = detect_changes(old_data, new_data)
        assert len(changes) == 0

    def test_calculate_severity_risk_drop_small(self):
        """Test severidad para caída pequeña de score."""
        from app.services.monitoring_service import calculate_severity

        severity = calculate_severity("risk_score_drop", 5.0)
        assert severity == "low"

    def test_calculate_severity_risk_drop_medium(self):
        """Test severidad para caída media de score."""
        from app.services.monitoring_service import calculate_severity

        severity = calculate_severity("risk_score_drop", 15.0)
        assert severity == "medium"

    def test_calculate_severity_risk_drop_large(self):
        """Test severidad para caída grande de score."""
        from app.services.monitoring_service import calculate_severity

        severity = calculate_severity("risk_score_drop", 25.0)
        assert severity == "high"

    def test_calculate_severity_sanction(self):
        """Test severidad para nueva sanción."""
        from app.services.monitoring_service import calculate_severity

        severity = calculate_severity("sanction_new", 1.0)
        assert severity == "critical"
