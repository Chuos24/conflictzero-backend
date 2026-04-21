"""
Tests para el módulo Mi Red (Supplier Network)
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models_v2 import Company, hash_ruc
from app.models_network import SupplierNetwork, SupplierAlert, CompanySnapshot


def test_hash_ruc():
    """Test que el hash de RUC funciona correctamente."""
    ruc = "20529400790"
    hashed = hash_ruc(ruc)
    assert len(hashed) == 64  # SHA-256 hex
    assert hashed == hash_ruc(ruc)  # Determinístico


def test_supplier_network_creation():
    """Test creación de SupplierNetwork."""
    supplier = SupplierNetwork(
        company_id=uuid4(),
        supplier_ruc_hash=hash_ruc("20529400790"),
        supplier_company_name="Test Company",
        is_active=True,
        alert_threshold=15,
        alert_on_score_change=True,
        alert_on_new_sanction=True,
        alert_on_debt_increase=True
    )
    
    assert supplier.is_active is True
    assert supplier.alert_threshold == 15
    assert supplier.alert_on_score_change is True
    assert supplier.alert_on_new_sanction is True


def test_supplier_network_soft_delete():
    """Test soft delete de SupplierNetwork."""
    supplier = SupplierNetwork(
        company_id=uuid4(),
        supplier_ruc_hash=hash_ruc("20529400790"),
        supplier_company_name="Test Company",
        is_active=True
    )
    
    supplier.soft_delete()
    
    assert supplier.deleted_at is not None
    assert supplier.is_active is False


def test_supplier_alert_creation():
    """Test creación de SupplierAlert."""
    alert = SupplierAlert(
        company_id=uuid4(),
        supplier_ruc_hash=hash_ruc("20529400790"),
        supplier_company_name="Test Company",
        alert_type="score_change",
        severity="high",
        previous_score=85,
        new_score=65,
        previous_risk_level="low",
        new_risk_level="high",
        change_details={"score_delta": -20},
        is_read=False
    )
    
    assert alert.alert_type == "score_change"
    assert alert.severity == "high"
    assert alert.is_read is False


def test_supplier_alert_mark_as_read():
    """Test marcar alerta como leída."""
    alert = SupplierAlert(
        company_id=uuid4(),
        supplier_ruc_hash=hash_ruc("20529400790"),
        supplier_company_name="Test Company",
        alert_type="new_sanction",
        severity="critical",
        is_read=False
    )
    
    assert alert.is_read is False
    
    alert.mark_as_read()
    
    assert alert.is_read is True
    assert alert.read_at is not None


def test_supplier_alert_score_delta():
    """Test cálculo de delta de score."""
    alert = SupplierAlert(
        company_id=uuid4(),
        supplier_ruc_hash=hash_ruc("20529400790"),
        supplier_company_name="Test Company",
        alert_type="score_change",
        previous_score=80,
        new_score=60
    )
    
    delta = alert.get_score_delta()
    assert delta == -20  # Empeoró


def test_company_snapshot_creation():
    """Test creación de CompanySnapshot."""
    snapshot = CompanySnapshot(
        ruc_hash=hash_ruc("20529400790"),
        company_name="Test Company",
        score=85,
        risk_level="low",
        sunat_debt=0,
        osce_sanctions_count=0,
        tce_sanctions_count=0,
        full_data={"ruc": "20529400790", "status": "active"}
    )
    
    assert snapshot.score == 85
    assert snapshot.risk_level == "low"


def test_company_snapshot_is_expired():
    """Test detección de snapshot expirado."""
    from datetime import timedelta
    
    # Snapshot expirado
    expired = CompanySnapshot(
        ruc_hash=hash_ruc("20529400790"),
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )
    assert expired.is_expired() is True
    
    # Snapshot válido
    valid = CompanySnapshot(
        ruc_hash=hash_ruc("20529400790"),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    assert valid.is_expired() is False
